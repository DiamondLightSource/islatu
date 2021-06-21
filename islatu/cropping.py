"""
Often the detector is a lot larger than the reflected intensity peak.
Therefore, we crop the image down, these functions help with this.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

import numpy as np


def crop_2d(array, x_start=0, x_end=-1, y_start=0, y_end=-1):
    """
    Crops the input array.
    """
    return array[y_start:y_end, x_start:x_end]


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
    print()
    max_inten = np.unravel_index(np.argmax(array, axis=None), array.shape)
    half_x_size = int(x_size / 2)
    half_y_size = int(y_size / 2)
    return crop_2d(
        array, array_e, max_inten[1] - half_x_size,
        max_inten[1] + half_x_size, max_inten[0] - half_y_size,
        max_inten[0] + half_y_size)
