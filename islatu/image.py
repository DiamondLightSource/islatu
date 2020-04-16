"""
The image class for the islatu pipeline
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey

import numpy as np
from PIL import Image as PILIm
from uncertainties import unumpy as unp


class Image(object):
    """
    The image class

    Attributes:
        file_path (str): The file path for the image.
        array (array_like): The image described as an array.
        bkg (uncertainties.cores.Variable): The background that was
            subtracted from the image.

    Args:
        file_path (str): The file path for the image.
        transpose (bool, optional): Should the data be rotated by 90 degrees?
    """

    def __init__(self, file_path, data=None, metadata=None, transpose=False):
        """
        Class initialisation
        """
        self.file_path = file_path
        self.data = data
        self.metadata = metadata
        im = PILIm.open(file_path)
        array = np.array(im)
        im.close()
        if transpose:
            array = array.T
        # Remove dead pixels
        array = _find_hot_pixels(array)
        array[np.where(array > 500000)] = 0
        array[np.where(array < 0)] = 0
        array_error = np.sqrt(array)
        array_error[np.where(array == 0)] = 1
        self.array = unp.uarray(array, array_error)
        self.bkg = 0
        self.n_pixel = 0

    @property
    def nominal_values(self):
        """
        Get the nominal values of the image array.

        Returns:
            (array_like): Nominal values of image.
        """
        return unp.nominal_values(self.array)

    @property
    def std_devs(self):
        """
        Get the standard deviation values of the image array.

        Returns:
            (array_like): Standard deviation values of image.
        """
        return unp.std_devs(self.array)

    @property
    def n(self):
        """
        Get the nominal values of the image array.

        Returns:
            (array_like): Nominal values of image.
        """
        return unp.nominal_values(self.array)

    @property
    def s(self):
        """
        Get the standard deviation values of the image array.

        Returns:
            (array_like): Standard deviation values of image.
        """
        return unp.std_devs(self.array)

    @property
    def shape(self):
        """
        Array shape

        Returns:
            (tuple_of_int): The shape of the image.
        """
        return unp.nominal_values(self.array).shape

    def __repr__(self):
        """
        Custom representation.

        Returns:
            (array_like): Image array.
        """
        return self.array

    def __str__(self):
        """
        Custom string.

        Returns:
            (array_like): Image array.
        """
        return self.array

    def crop(self, crop_function, **kwargs):
        """
        Perform an image crop based on some function.

        Args:
            crop_function (callable): The function to crop the data.
            **kwargs (dict): The function keyword arguments.
        """
        self.array = unp.uarray(*crop_function(self.n, self.s, **kwargs))

    def background_subtraction(
        self, background_subtraction_function, **kwargs
    ):
        """
        Perform a background subtraction based on some function.

        Args:
            background_subtraction_function (callable): The function to model
                the data and therefore remove the background.
            **kwargs (dict): The function keyword arguments.
        """
        self.bkg_popt, bkg_idx, pixel_idx = background_subtraction_function(
            self.n, self.s, **kwargs
        )
        self.bkg = self.bkg_popt[bkg_idx]
        self.n_pixel = self.bkg_popt[pixel_idx]
        self.array -= self.bkg

    def sum(self, axis=None):
        """
        Perform a summation on the image

        Args:
            axis (int, optional): The axis of the array to perform the
                summation over.
        """
        return self.array.sum(axis)


def _find_hot_pixels(array, threshold=200000):
    """
    Find some dead pixels and mask them.
    """
    sorted_array = np.sort(array.flatten())[::-1]
    for i in sorted_array:
        if i >= 200000:
            coords = np.where(array == i)
            a = np.copy(
                array[
                    coords[0][0] - 1:coords[0][0] + 2,
                    coords[1][0] - 1:coords[1][0] + 2,
                ]
            )
            a[1, 1] = 0
            local_average = np.nanmean(a)
            local_std = np.nanstd(a)
            if i > local_average + 2 * local_std:
                array[coords] = local_average
        else:
            break
    return array
