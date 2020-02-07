"""
The cropping options for the data reduction islatu pipeline.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey

import numpy as np


def crop_2d(image, x_start, x_end, y_start, y_end):
    """
    Crop the data (`image`) with some given start and stop point.

    Args:
        image (array_like): The intensity map collected by the 2
        dimensional detector.
        x_start (int): Start point in x-axis.
        x_end (int): End point in x-axis.
        y_start (int): Start point in y-axis.
        y_end (int): End point in y-axis.

    Returns:
        (array_like): A cropped intensity map.
    """
    cropped_image = image[x_start:x_end, y_start:y_end]
    return cropped_image


def crop_around_peak_2d(image, x_size=20, y_size=20):
    """
    Crop the data (`image`) around the most intense peak, creating an array
    of dimensions [x_size, y_size].

    Args:
        image (array_like): The intensity map collected by the 2
        dimensional detector.

    Returns:
        (array_like): A cropped intensity map.
    """
    max_inten = np.unravel_index(np.argmax(image, axis=None), image.shape)
    half_x_size = int(x_size / 2)
    half_y_size = int(y_size / 2)
    cropped_image = crop_2d(
        image,
        max_inten[0]-half_x_size,
        max_inten[0]+half_x_size,
        max_inten[1]-half_y_size,
        max_inten[1]+half_y_size
    )
    return cropped_image
