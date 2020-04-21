"""
Often the detector is a lot larger than the reflected intensity peak. 
Therefore, we crop the image down, these functions help with this.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

import numpy as np


def crop_2d(array, x_start, x_end, y_start, y_end):
    """
    Crop the data (`array`) with some given start and stop point.

    Args:
        array (np.ndarray): The intensity map collected by the 2
            dimensional detector.
        x_start (int): Start point in x-axis.
        x_end (int): End point in x-axis.
        y_start (int): Start point in y-axis.
        y_end (int): End point in y-axis.

    Returns:
        (np.ndarray): A cropped intensity map.
    """
    cropped_array = array[x_start:x_end, y_start:y_end]
    return cropped_array


def crop_around_peak_2d(array, array_e=None, x_size=20, y_size=20):
    """
    Crop the data (`array`) around the most intense peak, creating an array
    of dimensions [x_size, y_size].

    Args:
        array (np.ndarray): Intensity map collected by the 2
            dimensional detector.
        array_e (np.ndarray): Uncertainty map collected by the 2-D detector.
        x_size (int, optional): Size of the cropped image in x-axis. Defaults to 20.
        y_size (int, optional): Size of the cropped image in y-axis. Defaults to 20. 

    Returns:
        (np.ndarray): A cropped intensity map.
    """
    max_inten = np.unravel_index(np.argmax(array, axis=None), array.shape)
    half_x_size = int(x_size / 2)
    half_y_size = int(y_size / 2)
    cropped_array = crop_2d(
        array,
        max_inten[0] - half_x_size,
        max_inten[0] + half_x_size,
        max_inten[1] - half_y_size,
        max_inten[1] + half_y_size,
    )
    if array_e is not None:
        cropped_array_error = crop_2d(
            array_e,
            max_inten[0] - half_x_size,
            max_inten[0] + half_x_size,
            max_inten[1] - half_y_size,
            max_inten[1] + half_y_size,
        )
        return cropped_array, cropped_array_error
    return cropped_array
