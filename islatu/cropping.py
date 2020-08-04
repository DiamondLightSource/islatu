"""
Often the detector is a lot larger than the reflected intensity peak.
Therefore, we crop the image down, these functions help with this.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

import numpy as np


def crop_2d(array, array_e, x_start=0, x_end=-1, y_start=0, y_end=-1):
    """
    Crop the data (:py:attr:`array`) with some given start and stop point.

    Args:
        array (:py:attr:`array_like`): The intensity map collected by the 2-D
            detector.
        array_e (:py:attr:`array_like`): Uncertainty map collected by the 2-D
            detector.
        x_start (:py:attr:`int`): Start point in x-axis.
        x_end (:py:attr:`int`): End point in x-axis.
        y_start (:py:attr:`int`): Start point in y-axis.
        y_end (:py:attr:`int`): End point in y-axis.

    Returns:
        :py:attr:`array_like`: A cropped intensity map.
    """
    cropped_array = array[y_start:y_end, x_start:x_end]
    if array_e is not None:
        cropped_error = array_e[y_start:y_end, x_start:x_end]
        return cropped_array, cropped_error
    return cropped_array


def crop_around_peak_2d(array, array_e, x_size=20, y_size=20):
    """
    Crop the data (`array`) around the most intense peak, creating an array
    of dimensions [x_size, y_size].

    Args:
        array (:py:attr:`array_like`): Intensity map collected by the 2-D
            detector.
        array_e (:py:attr:`array_like`): Uncertainty map collected by the 2-D
            detector.
        x_size (:py:attr:`int`, optional): Size of the cropped image in x-axis.
            Defaults to :py:attr:`20`.
        y_size (:py:attr:`int`, optional): Size of the cropped image in y-axis.
            Defaults to :py:attr:`20`.

    Returns:
        :py:attr:`array_like`: A cropped intensity map.
    """
    max_inten = np.unravel_index(np.argmax(array, axis=None), array.shape)
    half_x_size = int(x_size / 2)
    half_y_size = int(y_size / 2)
    return crop_2d(
        array, array_e, max_inten[1] - half_x_size,
        max_inten[1] + half_x_size, max_inten[0] - half_y_size,
        max_inten[0] + half_y_size)
