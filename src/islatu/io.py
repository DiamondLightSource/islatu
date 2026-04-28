"""
This module contains:

Parsing functions used to extract information from experimental files.

Classes used to help make parsing more modular. These include the NexusBase
class and its children.
"""

# We've gotta access the _value attribute on some NXobjects.
# pylint: disable=protected-access

import os
from typing import List

import h5py
import numpy as np
import pandas as pd
from diffraction_utils.io import I07Nexus

from islatu.data import Data
from islatu.debug import debug
from islatu.image import Image
from islatu.scan import Scan2D, Scan2D_noload, Scan2D_noload_diff


def i07_dat_to_dict_dataframe(file_path):
    """
    Parses a .dat file recorded by I07, returning a [now mostly obsolete] tuple
    containing a metadata dictionary and a pandas dataframe of the data.

    Though outdated, this is still a handy way to parse the DCD normalization
    .dat file.

    Args:
        (:py:attr:`str`): The ``.dat`` file to be read.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`dict`: The metadata from the ``.dat`` file.
            - :py:class:`pandas.DataFrame`: The data from the ``.dat`` file.
    """
    f_open = open(file_path, "r", encoding="utf-8")
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
    for j, _ in enumerate(data_lines[0]):
        list_to_add = []
        for i, _ in enumerate(data_lines):
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
    return metadata_dict, pd.DataFrame(data_dict)


def load_ind_image_from_h5(h5_file_path, datanxfilepath, ind, transpose=False):
    internal_data_path = datanxfilepath  #'data'
    debug.log("Loading images from file " + h5_file_path, unimportance=0)
    with h5py.File(h5_file_path, "r") as file_handle:
        dataset = file_handle[internal_data_path]  # [()]
        image = Image(dataset[ind], transpose=transpose)
    return image


def check_total_images_in_h5(h5_file_path, datanxfilepath):
    internal_data_path = datanxfilepath  #'data'
    debug.log("Counting images from file " + h5_file_path, unimportance=0)
    with h5py.File(h5_file_path, "r") as file_handle:
        dataset = file_handle[internal_data_path]  # [()]
        num_images = dataset.shape[0]
    return num_images


def load_images_from_h5(h5_file_path, datanxfilepath, transpose=False):
    """
    Loads images from a .h5 file.

    Args:
        h5_file_path:
            Path to the h5 file from which we're loading images.
        transpose:
            Should we take the transpose of these images? Defaults to True.
    """
    internal_data_path = datanxfilepath  #'data'
    images = []
    debug.log("Loading images from file " + h5_file_path, unimportance=0)
    with h5py.File(h5_file_path, "r") as file_handle:
        dataset = file_handle[internal_data_path]  # [()]

        num_images = dataset.shape[0]
        # Prepare to show a progress bar for image loading.
        debug.log(f"Loading {num_images} images.", unimportance=2)
        for i in range(num_images):
            debug.log("Currently loaded " + str(i + 1) + " images.", end="\r")
            images.append(Image(dataset[i], transpose=transpose))
        # This line is necessary to prevent overwriting due to end="\r".
        debug.log("")
        debug.log(f"Loaded all {num_images} images.", unimportance=2)

    return images


def parse_adjustments(i07_nxs, adjustments):
    axis = i07_nxs.default_axis
    axis_name = i07_nxs.default_axis_name
    axis_type = i07_nxs.default_axis_type
    theta_offset = 0
    q_offset = 0

    if hasattr(adjustments, "new_axis_name"):
        axis_name = adjustments.new_axis_name
        if hasattr(i07_nxs.nx_instrument[f"{axis_name}"], "value_set"):
            axis = i07_nxs.nx_instrument[f"{axis_name}"].value_set.nxdata
        else:
            axis = i07_nxs.nx_instrument[f"{axis_name}"].value.nxdata
    if hasattr(adjustments, "new_axis_type"):
        axis_type = adjustments.new_axis_type
    if hasattr(adjustments, "theta_offset"):
        theta_offset = adjustments.theta_offset
    if hasattr(adjustments, "q_offset"):
        q_offset = adjustments.q_offset

    return axis, axis_name, axis_type, theta_offset, q_offset


def make_data(axis, axis_name, axis_type, shared_vals, q_offset, theta_offset):
    rough_intensity, rough_intensity_e, probe_energy = shared_vals
    if axis_type == "q":
        return Data(
            rough_intensity,
            rough_intensity_e,
            probe_energy,
            q_vectors=axis - q_offset,
        )
    if axis_type == "th":
        return Data(
            rough_intensity,
            rough_intensity_e,
            probe_energy,
            theta=axis - theta_offset,
        )
    if axis_type == "tth":
        return Data(
            rough_intensity,
            rough_intensity_e,
            probe_energy,
            theta=(axis / 2 - theta_offset),
        )

    raise NotImplementedError(
        f"{axis_type} is not a supported axis type. Axis name={axis_name}"
    )


def i07_nxs_parser_noload(file_path: str, remove_indices=None, adjustments=None):
    """
    copy of i07_nxs_parser  that doesnt load all images at the start - only loads images when needed
    Parses a .nxs file acquired from the I07 beamline at diamond, returning an
    instance of Scan2D. This process involves loading the images contained in
    the .h5 file pointed at by the .nxs file, as well as retrieving the metadata
    from the .nxs file that is relevant for XRR reduction.

    Args:
        file_path:
            Path to the .nxs file.

    Returns:
        An initialized Scan2D object containing all loaded detector frames, as
        well as the relevant metadata from the .nxs file.
    """
    # Use the magical parser class that does everything for us.
    i07_nxs = I07Nexus(file_path)
    detname = i07_nxs.detector_name
    if "attenuation_filters_moving" in i07_nxs.entry[f"{detname}"].keys():
        try:
            attenuationvalues = i07_nxs.entry[f"{detname}/attenuation_value"].nxdata
            movingfilters = [
                0 if attenuationvalues[i] == attenuationvalues[i - 1] else 1
                for i in np.arange(1, len(attenuationvalues[0:5]))
            ]
        except (AttributeError, TypeError):
            debug.log(
                "unable to read in attenuation information, possible missing attenuation h5 file. Will assume no moving attenuation.",
                unimportance=2,
            )
            attenuationvalues = i07_nxs.entry[f"{detname}/attenuation_value"]
            movingfilters = []
        remove_indices = np.where(movingfilters)[0]
        # remove_indices=np.where(np.array(i07_nxs.entry[f'{detname}/attenuation_filters_moving']))[0]
        remove_indices += 1

    image_paths = [i07_nxs.local_data_path, i07_nxs._src_data_path[1]]
    # The dependent variable.
    rough_intensity = i07_nxs.default_signal
    rough_intensity_e = np.sqrt(rough_intensity)

    # The independent variable.

    axis, axis_name, axis_type, theta_offset, q_offset = parse_adjustments(
        i07_nxs, adjustments
    )
    shared_vals = [rough_intensity, rough_intensity_e, i07_nxs.probe_energy]

    data = make_data(axis, axis_name, axis_type, shared_vals, q_offset, theta_offset)

    # Returns the Scan2D object
    return Scan2D_noload(
        data, i07_nxs, image_paths=image_paths, remove_indices=remove_indices
    )


def i07_nxs_parser_noload_diff(file_path: str, remove_indices=None, adjustments=None):
    """
    copy of i07_nxs_parser  that doesnt load all images at the start - only loads images when needed
    Parses a .nxs file acquired from the I07 beamline at diamond, returning an
    instance of Scan2D. This process involves loading the images contained in
    the .h5 file pointed at by the .nxs file, as well as retrieving the metadata
    from the .nxs file that is relevant for XRR reduction.

    Args:
        file_path:
            Path to the .nxs file.

    Returns:
        An initialized Scan2D object containing all loaded detector frames, as
        well as the relevant metadata from the .nxs file.
    """
    # Use the magical parser class that does everything for us.
    i07_nxs = I07Nexus(file_path)
    detname = i07_nxs.detector_name
    if "attenuation_filters_moving" in i07_nxs.nx_entry[f"{detname}"].keys():
        try:
            attenuationvalues = i07_nxs.nx_entry[f"{detname}/attenuation_value"].nxdata
            movingfilters = [
                0 if attenuationvalues[i] == attenuationvalues[i - 1] else 1
                for i in np.arange(1, len(attenuationvalues[0:5]))
            ]
        except (AttributeError, TypeError):
            debug.log(
                "unable to read in attenuation information, possible missing attenuation h5 file. Will assume no moving attenuation.",
                unimportance=2,
            )
            attenuationvalues = i07_nxs.nx_entry[f"{detname}/attenuation_value"]
            movingfilters = []
        remove_indices = np.where(movingfilters)[0]
        # remove_indices=np.where(np.array(i07_nxs.entry[f'{detname}/attenuation_filters_moving']))[0]
        remove_indices += 1

    internal_path = i07_nxs._parse_hdf5_internal_path()
    detector_in_file = i07_nxs._parse_nx_detector()._name
    if detector_in_file == "exr":
        internal_path = "/entry/exr_data/data"
    image_paths = [
        i07_nxs.local_path,
        internal_path.replace("detector", detector_in_file),
    ]

    # The dependent variable.
    rough_intensity = i07_nxs.default_signal
    rough_intensity_e = np.sqrt(rough_intensity)

    # The independent variable.

    axis, axis_name, axis_type, theta_offset, q_offset = parse_adjustments(
        i07_nxs, adjustments
    )
    shared_vals = [rough_intensity, rough_intensity_e, i07_nxs.probe_energy]

    data = make_data(axis, axis_name, axis_type, shared_vals, q_offset, theta_offset)

    # Returns the Scan2D object
    return Scan2D_noload_diff(
        data, i07_nxs, image_paths=image_paths, remove_indices=remove_indices
    )


def i07_nxs_parser(file_path: str, remove_indices=None, adjustments=None):
    """
    Parses a .nxs file acquired from the I07 beamline at diamond, returning an
    instance of Scan2D. This process involves loading the images contained in
    the .h5 file pointed at by the .nxs file, as well as retrieving the metadata
    from the .nxs file that is relevant for XRR reduction.

    Args:
        file_path:
            Path to the .nxs file.

    Returns:
        An initialized Scan2D object containing all loaded detector frames, as
        well as the relevant metadata from the .nxs file.
    """
    # Use the magical parser class that does everything for us.
    i07_nxs = I07Nexus(file_path)
    detname = i07_nxs.detector_name
    if "attenuation_filters_moving" in i07_nxs.entry[f"{detname}"].keys():
        try:
            attenuationvalues = i07_nxs.entry[f"{detname}/attenuation_value"].nxdata
            movingfilters = [
                0 if attenuationvalues[i] == attenuationvalues[i - 1] else 1
                for i in np.arange(1, len(attenuationvalues[0:5]))
            ]
        except (AttributeError, TypeError):
            debug.log(
                "unable to read in attenuation information, possible missing attenuation h5 file. Will assume no moving attenuation.",
                unimportance=2,
            )
            attenuationvalues = i07_nxs.entry[f"{detname}/attenuation_value"]
            movingfilters = []
        remove_indices = np.where(movingfilters)[0]
        # remove_indices=np.where(np.array(i07_nxs.entry[f'{detname}/attenuation_filters_moving']))[0]
        remove_indices += 1

    # Load the images, taking a transpose if necessary (because which axis is
    # x and which is why is determined by fast vs slow detector axes in memory).
    if i07_nxs.detector_name in [
        I07Nexus.excalibur_detector_2021,
        I07Nexus.excalibur_04_2022,
        I07Nexus.pilatus_2022,
        I07Nexus.excalibur_2022_fscan,
        I07Nexus.pilatus_eh2_scan,
    ]:
        images = load_images_from_h5(
            i07_nxs.local_data_path, i07_nxs._src_data_path[1], transpose=False
        )

    # The dependent variable.
    rough_intensity = i07_nxs.default_signal
    rough_intensity_e = np.sqrt(rough_intensity)

    # The independent variable.
    axis = i07_nxs.default_axis
    axis_type = i07_nxs.default_axis_type
    theta_offset = 0
    q_offset = 0

    if hasattr(adjustments, "new_axis_name"):
        axis_name = adjustments.new_axis_name
        if hasattr(i07_nxs.instrument[f"{axis_name}"], "value_set"):
            axis = i07_nxs.instrument[f"{axis_name}"].value_set.nxdata
        else:
            axis = i07_nxs.instrument[f"{axis_name}"].value.nxdata
    if hasattr(adjustments, "new_axis_type"):
        axis_type = adjustments.new_axis_type
    if hasattr(adjustments, "theta_offset"):
        theta_offset = adjustments.theta_offset
    if hasattr(adjustments, "q_offset"):
        q_offset = adjustments.q_offset

    if axis_type == "q":
        data = Data(
            rough_intensity,
            rough_intensity_e,
            i07_nxs.probe_energy,
            q_vectors=axis - q_offset,
        )
    elif axis_type == "th":
        data = Data(
            rough_intensity,
            rough_intensity_e,
            i07_nxs.probe_energy,
            theta=axis - theta_offset,
        )
    elif axis_type == "tth":
        data = Data(
            rough_intensity,
            rough_intensity_e,
            i07_nxs.probe_energy,
            theta=(axis / 2 - theta_offset),
        )
    else:
        raise NotImplementedError(
            f"{axis_type} is not a supported axis type. Axis name={axis_name}"
        )

    # Returns the Scan2D object
    return Scan2D(data, i07_nxs, images, remove_indices)


def _try_to_find_files(filenames: List[str], additional_search_paths: List[str]):
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
    start_dirs = [
        cwd,  # maybe file is stored near the current working dir
        # To search additional directories, add them in here manually.
    ]
    start_dirs.extend(additional_search_paths)

    local_start_directories = [x.replace("\\", "/") for x in start_dirs]
    num_start_directories = len(local_start_directories)

    # Now extend the additional search paths.
    for i in range(num_start_directories):
        search_path = local_start_directories[i]
        split_srch_path = search_path.split("/")
        for j in range(len(split_srch_path)):
            extra_path_list = split_srch_path[: -(j + 1)]
            extra_path = "/".join(extra_path_list)
            local_start_directories.append(extra_path)

    # This line allows for a loading bar to show as we check the file.
    for i, _ in enumerate(filenames):
        # Better to be safe... Note: windows is happy with / even though it
        # defaults to \
        filenames[i] = str(filenames[i]).replace("\\", "/")

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
        split_file_path = str(filenames[i]).split("/")
        for j in range(len(split_file_path)):
            local_guess = "/".join(split_file_path[j:])
            for start_dir in local_start_directories:
                candidate_paths.append(os.path.join(start_dir, local_guess))

        # Iterate over each of the candidate paths to see if any of them contain
        # the data file we're looking for.
        found_file = False
        for candidate_path in candidate_paths:
            if os.path.isfile(candidate_path):
                # File found - add the correct file location to found_files
                found_files.append(candidate_path)
                found_file = not found_file
                debug.log("Data file found at " + candidate_path + ".")
                break

        # If we didn't find the file, tell the user.
        if not found_file:
            raise FileNotFoundError(
                "The data file with the name " + filenames[i] + " could "
                "not be found. The following paths were searched:\n"
                + "\n".join(candidate_paths)
            )
    return found_files
