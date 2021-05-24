"""
Parsers for inputing experimental files.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

from numpy.lib.type_check import imag
from islatu.scan import Scan2D
from islatu.image import Image
from islatu import detector
from islatu.metadata import Metadata
from islatu.data import Data
import pandas as pd
from uncertainties import unumpy as unp
import numpy as np


def i07_dat_parser(file_path, theta_axis_name):
    """
    Parsing the .dat file from I07.

    Args:
        (:py:attr:`str`): The ``.dat`` file to be read.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`dict`: The metadata from the ``.dat`` file.
            - :py:class:`pandas.DataFrame`: The data from the ``.dat`` file.
    """
    f_open = open(file_path, "r")
    # Neither the data nor the metadata are being read yet.
    data_reading = False
    metadata_reading = False

    # Create the dictionaries to be populated.
    data_dict = {}
    metadata_dict = {}
    # Create the list to be filled with lists for each line
    data_lines = []

    for line in f_open:
        # This string incidates the start of the metadata.
        if "<MetaDataAtStart>" in line:
            metadata_reading = True
        # This string indicates the end of the metadata.
        if "</MetaDataAtStart>" in line:
            metadata_reading = False
        # This string indicates the start of the data.
        if " &END" in line:
            data_reading = True
            # Set counter to minus two, such that when is
            # reaches the data it is 0.
            count = -2
        # When the metadata section is being read populate the metadata_dict
        if metadata_reading:
            if "=" in line:
                metadata_in_line = []
                for i in line.split("=")[1:]:
                    try:
                        j = float(i)
                    except ValueError:
                        j = i
                    metadata_in_line.append(j)
                metadata_dict[line.split("=")[0]] = metadata_in_line
        # When the data section is being read, make the list of the zeroth line
        # the titles and everything after is the data_lines list of lists.
        if data_reading:
            count += 1
            if count == 0:
                titles = line.split()
            if count > 0:
                data_lines.append(line.split())
    f_open.close()
    # Sort the data_lines list of lists to transpore and make into a dict where
    # the keys are the titles.
    for j in range(len(data_lines[0])):
        list_to_add = []
        for i in range(len(data_lines)):
            try:
                list_to_add.append(float(data_lines[i][j]))
            except ValueError:
                list_to_add.append(data_lines[i][j])
        count = 0
        if j >= len(titles):
            data_dict[str(count)] = list_to_add
            count += 1
        else:
            data_dict[titles[j]] = list_to_add

    # The "data_dict" actually contains a lot of metadata, and is small.
    # Appending this to the metadata_dict makes a lot of sense.
    metadata_dict.update(data_dict)

    # Now store this metadata in an object of type Metadata, checking to see if
    # we need to use the updated or legacy detector object to decipher this file
    if "diff1halpha" in metadata_dict:
        metadata = Metadata(detector.i07_pilatus_legacy, metadata_dict)
    elif detector.i07_excalibur.metakey_roi_1_maxval in metadata_dict:
        metadata = Metadata(detector.i07_excalibur, metadata_dict)
    elif detector.i07_pilatus.metakey_roi_1_maxval in metadata_dict:
        metadata = Metadata(detector.i07_pilatus, metadata_dict)

    # Now build a Data instance to hold the theta/intensity values. It is
    # important to note that this provides the most naive estimate of intensity,
    # simply using the maximum pixel value to represent the intensity.
    theta = unp.uarray(metadata.raw_metada[theta_axis_name],
                       np.zeros(metadata.raw_metada[theta_axis_name].size))
    intensity = unp.uarray(metadata.roi_1_maxval,
                           np.zeros(metadata.roi_1_maxval.size))
    energy = metadata.probe_energy
    data = Data(theta, intensity, energy)

    # This .dat file will point to images. Load them, use them to populate a
    # Scan2D object, and return the scan.
    images = [Image(metadata.file[i]) for i in range(theta.size)]
    return Scan2D(data, metadata, images)


def rigaku_data_parser(file_path):
    """
    Parses the .dat and .ras files from a Rigaku smartlab diffractometer.

    Args:
        (:py:attr:`str`): The ``.dat`` file to be read.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`dict`: The metadata from the ``.dat`` file.
            - :py:class:`pandas.DataFrame`: The data from the ``.dat`` file.
    """
    # work out what type of file we have, currently supporting .ras and .dat
    ras_ending = ".ras"
    dat_ending = ".dat"

    # if file_path argument wasn't a string, error naturally thrown here
    if file_path.endswith(ras_ending):
        file_ending = ras_ending
    elif file_path.endswith(dat_ending):
        file_ending = dat_ending
    else:
        raise IOError("Only .ras and .dat rigaku files are currently " +
                      "supported.")

    # prepare dictionaries to populate with data/metadata
    data_dict = {}
    metadata_dict = {}

    # prepare to store angles and intensities - the Q conversion will come later
    angles = []
    intensities = []
    attenuations = []

    with open(file_path) as open_file:
        # this flag is ignored for .dat files. For .ras, we start with metadata
        reading_metadata = True

        for line in open_file:
            # clean the line independent of file type
            line = line.strip()

            # dat files are very simple, just iterate through the file grabbing
            # 2theta and intensities
            if file_ending == dat_ending:
                split_line = line.split('\t')

                angle = float(split_line[0])
                intensity = float(split_line[1])

                angles.append(angle)
                intensities.append(intensity)
            elif file_ending == ras_ending:
                # ras files contain much more metadata. First grab this all
                if reading_metadata:
                    # intensity list is about to start, switch metadata flag
                    if "RAS_INT_START" in line:
                        reading_metadata = False
                    # skips the preamble and the useless _END flag
                    if line.strip().endswith("_START"):
                        continue
                    if line.strip().endswith("_END"):
                        continue
                    # metadata is given in the format <TITLE "DATA">

                    split_line = line.split(" ")

                    # strip quotation marks from DATA
                    split_line[1].strip('"')

                    # add title + data as key value pair to metadata dict
                    metadata_dict[split_line[0]] = split_line[1]
                # we're reading intensity/angle/attenuation now
                else:
                    # throw away the meaningless *RAS_END messages etc.
                    if "*" in line:
                        continue

                    # now it's safe to acces split_line[i] for i > 0
                    split_line = line.split(" ")
                    angle = float(split_line[0])
                    intensity = float(split_line[1])
                    attenuation = float(split_line[2])

                    # store the stuff
                    angles.append(angle)
                    intensities.append(intensity)
                    attenuations.append(attenuation)

    # populate the data dict (TODO: calculate Q-vectors from angles and include)
    data_dict["Angles"] = angles
    data_dict["Intensities"] = intensities

    # if this was from a .ras, then we also have attenuation information
    if file_ending == ras_ending:
        data_dict["Attenuation"] = attenuations

    return metadata_dict, pd.DataFrame(data_dict)
