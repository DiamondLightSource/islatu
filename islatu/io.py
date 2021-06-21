"""
Parsers for inputing experimental files.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

import os
from re import search, split

from nexusformat import nexus
from nexusformat.nexus.tree import NeXusError
from islatu import metadata
from islatu.refl_data import _get_iterator
from numpy.lib.type_check import imag
from islatu.scan import Scan2D
from islatu.image import Image
from islatu import detector
from islatu.metadata import Metadata
from islatu.data import Data
import pandas as pd
from uncertainties import unumpy as unp
import numpy as np
import h5py


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
    theta = unp.uarray(np.array(metadata.raw_metadata[theta_axis_name]),
                       np.zeros(len(metadata.raw_metadata[theta_axis_name])))
    intensity = unp.uarray(np.array(metadata.roi_1_maxval),
                           np.zeros(len(metadata.roi_1_maxval)))

    energy = metadata.probe_energy
    data = Data(theta, intensity, energy)

    # Our metadata's file information is most likely wrong (unless this code is
    # being run on site). Try to correct these files.
    metadata.file = _try_to_find_files(metadata.file,
                                       additional_search_paths=[file_path])

    # This .dat file will point to images. Load them, use them to populate a
    # Scan2D object, and return the scan.
    images = [Image.from_img_file_name(metadata.file[i])
              for i in range(len(metadata.file))]
    return Scan2D(data, metadata, images)


def i07_nxs_parser(file_path, theta_axis_name):
    """Location of the data:
    "entry/excroi_data/data"
    found by:
    infile["entry/excroi_data"].dir()
    Otherwise, walk through the .nxs file recursively and grab all metadata.
    This can be done using for example:

    from nexusformat.nexus import nxload
    in_file = nxload("/path/to/file.nxs")

    for line in in_file.tree.split("\n"):
        if ":" not in line:
            do_logic_to_work_out_relative_path_name()
            store_data_in_dictionary()

    Metadata dict should be dealt with using full .nxs paths as keys, i.e.:
    metadata.raw_metadata["Region_1.max_val"] should instead be:
    metadata.raw_metadata["entry/excroi_Region_1.max_val/Region_1.max_val"]
    ... while a little unwieldy, this is the most general way to avoid naming
    conflicts. 
    """
    from nexusformat.nexus import nxload

    nx_file = nxload(file_path)

    # ------------- BEGIN GENERIC NEXUS PARSER ----------------------------- #
    # Split up the .nxs file.
    file_lines = nx_file.tree.split("\n")

    # The following is a reasonably general routine for the compactification of
    # a .nxs file onto a dictionary.
    entry_path = []
    raw_metadata = {}
    for line in file_lines:
        # Check the indentation level.
        stripped_line = line.lstrip(" ")
        indent_lvl = int((len(line) - len(stripped_line))/2)

        if len(stripped_line.split(" = ")) != 1:
            # We found data/metadata.
            split_line = stripped_line.split(" = ")
        elif len(stripped_line.split(" -> ")) != 1:
            # We found a pointer/link.
            split_line = stripped_line.split(" -> ")
            # Make sure that information is not lost by putting the pointer
            # symbol back in.
            split_line[1] = " -> " + split_line[1]
        else:
            # We found a new class. This should be obvious by its file_contents.
            split_line = stripped_line.split(":")

        # Something went wrong if our delimiter has shown up twice. Note that
        # this bans dumb NXClass names with colons in them, etc..
        if len(split_line) != 2:
            raise ValueError("Islatu cannot parse this .nxs file.")
        file_name = split_line[0]
        file_contents = split_line[1]

        # Form the new path.
        if indent_lvl > len(entry_path):
            entry_path.append(file_name)
        else:
            entry_path = entry_path[:indent_lvl]
            entry_path.append(file_name)
        current_path = "/" + "/".join(entry_path)

        # Now update the metadata dictionary.
        raw_metadata[current_path] = file_contents

        # Useful for debugging/double checking.
        if ("Region_" in file_contents) or ("Region_" in current_path):
            # print(current_path, file_contents)
            pass
    # ------------- END GENERIC NEXUS PARSER ----------------------------- #

    # Now grab the real metadata corresponding to each path we found.
    # for path in raw_metadata:
    #     new_path = path.lstrip("/root")
    #     if new_path == "":
    #         continue
    #     try:
    #         contents = nx_file[new_path]._value
    #     except:
    #         continue
    #     print(new_path + " || " + str(contents))

    # The raw_metada dictionary is now populated.
    # Key pieces of metadata:
    # detector_distance = /entry/instrument/diff1detdist/value
    # probe_energy = /entry/instrument/dcm1energy/value
    # file = /entry/excroi_data/data
    # transmission = /entry/instrument/filterset/transmission
    # roi_1_maxval = /entry/instrument/excroi/Region_1.max_val
    # roi_2_maxval = /entry/instrument/excroi/Region_2.max_val

    # Scrape the essential metadata by force.
    metadata = Metadata(detector.i07_excalibur_nxs, nx_file)
    metadata.detector_distance = nx_file["/entry/instrument/diff1detdist/value"]
    metadata.probe_energy = nx_file["/entry/instrument/dcm1energy/value"]._value
    metadata.file = [nx_file["/entry/excroi_data/data"]._filename]

    metadata.x_end = [
        nx_file["/entry/instrument/excroi/Region_1.max_x"]]
    metadata.x = [
        nx_file["/entry/instrument/excroi/Region_1_X"]]
    # print("X METADATA: ", metadata.x)
    # print("X end METADATA: ", metadata.x_end)

    metadata.transmission = nx_file["/entry/instrument/filterset/transmission"]
    metadata.roi_1_maxval = nx_file["/entry/instrument/excroi/Region_1.max_val"]
    metadata.roi_2_maxval = nx_file["/entry/instrument/excroi/Region_2.max_val"]

    print("---------------------------------------------------------------")
    # Now prepare the Data object.
    # TODO: work out how to find this generally.
    theta_parsed = nx_file["/entry/instrument/diff1delta/value"]._value
    theta = theta_parsed
    theta = unp.uarray(theta_parsed, np.zeros(len(theta_parsed)))
    intensity = unp.uarray(np.array(metadata.roi_1_maxval),
                           np.zeros(len(metadata.roi_1_maxval)))

    energy = metadata.probe_energy
    data = Data(theta, intensity, energy)

    # Our metadata's file information is most likely wrong (unless this code is
    # being run on site). Try to correct these files.
    # TODO: find file properly, fixing file mod error.
    metadata.file = _try_to_find_files(metadata.file,
                                       additional_search_paths=[file_path])

    # This .dat file will point to images. Load them, use them to populate a
    # Scan2D object, and return the scan.

    # Now load the images from the file:
    # TODO: do this properly!
    # file_path = "i07_test/excaliburScan394602_000001.h5"
    internal_data_path = 'data'

    print("Loading images from file " + metadata.file[0])
    with h5py.File(metadata.file[0], "r") as file_handle:
        dataset = file_handle[internal_data_path][()]
        # images = [Image(dataset[i]) for i in range(dataset.shape[0])]
        images = []
        for i in range(dataset.shape[0]):
            print("Loading image " + str(i+1) + " of " + str(dataset.shape[0]))
            images.append(Image(dataset[i]))
        # images = [Image(dataset[i]) for i in range(3)]

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


def _try_to_find_files(filenames, additional_search_paths):
    """
    Check that data files exist if the file parsed by parser pointed to a
    separate file containing intensity information. If the intensity data
    file could not be found in its original location, check a series of
    probable locations for the data file. If the data file is found in one
    of these locations, update file's entry in self.data.

    Returns:
        :py:attr:`list` of :py:attr:`str`:
            List of the corrected, actual paths to the files.
    """
    found_files = []

    # If we had only one file, make a list out of it.
    if not hasattr(filenames, "__iter__"):
        filenames = [filenames]

    cwd = os.getcwd()
    local_start_directories = [
        cwd,  # maybe file is stored near the current working dir
        # To search additional directories, add them in here manually.
    ]
    local_start_directories.extend(additional_search_paths)

    # Better to be consistent.
    for i in range(len(local_start_directories)):
        local_start_directories[i] = local_start_directories[i].replace(
            '\\', '/')

    # Now extend the additional search paths.
    for i in range(len(local_start_directories)):
        search_path = local_start_directories[i]
        split_srch_path = search_path.split('/')
        for j in range(len(split_srch_path)):
            extra_path_list = split_srch_path[:-(j+1)]
            extra_path = '/'.join(extra_path_list)
            local_start_directories.append(extra_path)

    # This line allows for a loading bar to show as we check the file.
    iterator = _get_iterator(filenames, False)
    for i in iterator:
        # Better to be safe... Note: windows is happy with / even though it
        # defaults to \
        filenames[i] = str(filenames[i]).replace('\\', '/')

        # Maybe we can see the file in its original storage location?
        if os.path.isfile(filenames[i]):
            found_files.append(filenames[i])
            continue

        # If not, maybe it's stored locally? If the file was stored at
        # location /a1/a2/.../aN/file originally, for a local directory LD,
        # check locations LD/aj/aj+1/.../aN for all j<N and all LD's of
        # interest. This algorithm is a generalization of Andrew McCluskey's
        # original approach.

        # now generate a list of all directories that we'd like to check
        candidate_paths = []
        split_file_path = str(filenames[i]).split('/')
        for j in range(len(split_file_path)):
            local_guess = '/'.join(split_file_path[j:])
            for start_dir in local_start_directories:
                candidate_paths.append(
                    os.path.join(start_dir, local_guess))

        # Iterate over each of the candidate paths to see if any of them contain
        # the data file we're looking for.
        found_file = False
        for candidate_path in candidate_paths:
            if os.path.isfile(candidate_path):
                # File found - add the correct file location to found_files
                found_files.append(candidate_path)
                found_file = not found_file
                print("Data file found at " + candidate_path + ".")
                break

        # If we didn't find the file, tell the user.
        if not found_file:
            raise FileNotFoundError(
                "The data file with the name " + filenames[i] + " could "
                "not be found. The following paths were searched:\n" +
                "\n".join(candidate_paths)
            )
    return found_files
