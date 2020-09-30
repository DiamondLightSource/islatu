"""
The two-dimension detector generates images of the reflected intensity.
The purpose of this class is the investigation and manipulation of these
images.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

import numpy as np
from PIL import Image as PILIm
from uncertainties import unumpy as unp

from islatu.background import fit_gaussian_1d


class Image:
    """
    This class stores information about the detector images.

    Attributes:
        file_path (:py:attr:`str`): File path for the image.
        data (:py:class:`pandas.DataFrame`): Experimental data about the
            measurement.
        metadata (:py:attr:`dict`): Metadata regarding the measurement.
        array (:py:attr:`array_like`): The image described as an array.
        bkg (:py:class:`uncertainties.cores.Variable`): The background that
            was subtracted from the image.
        n_pixels (:py:attr:`float`): The width of the peak in number of
            pixels, used to calculate an uncertainty in q on the detector.

    Args:
        file_path (:py:attr:`str`): The file path for the image.
        data (:py:class:`pandas.DataFrame`, optional): Experimental data about
            the measurement. Defaults to :py:attr:`None`.
        metadata (:py:attr:`dict`, optional): Metadata regarding the
            measurement. Defaults to :py:attr:`None`.
        transpose (:py:attr:`bool`, optional): Should the data be rotated by
            90 degrees? Defaults to :py:attr:`False`.
        pixel_min (:py:attr:`int`): The minimum pixel value possible, all
            pixels found with less than this value will have this value
            assigned. Defaults to :py:attr:`0`.
        hot_pixel_max (:py:attr:`int`): The value of a hot pixel that will be
            set to the average of the surrounding pixels. Logically, this
            should be less than the :py:attr:`pixel_max` value. Defaults to
            :py:attr:`2e5`.
    """
    def __init__(self, file_path, data=None, metadata=None, transpose=False,
                 pixel_min=0, hot_pixel_max=2e5):
        """
        Initialisation of the :py:class:`islatu.image.Image` class, includes
        assigning uncertainties.
        """
        self.file_path = file_path
        self.data = data
        self.metadata = metadata
        img = PILIm.open(file_path)
        array = np.array(img)
        img.close()
        if transpose:
            array = array.T
        array = _average_out_hot(array, hot_pixel_max)
        array[np.where(array < pixel_min)] = 0
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
            :py:attr:`array_like`: Nominal values of image.
        """
        return unp.nominal_values(self.array)

    @property
    def std_devs(self):
        """
        Get the standard deviation values of the image array.

        Returns:
            :py:attr:`array_like`: Standard deviation values of image.
        """
        return unp.std_devs(self.array)

    @property
    def n(self):
        """
        Get the nominal values of the image array.

        Returns:
            :py:attr:`array_like`: Nominal values of image.
        """
        return unp.nominal_values(self.array)

    @property
    def s(self):
        """
        Get the standard deviation values of the image array.

        Returns:
            :py:attr:`array_like`: Standard deviation values of image.
        """
        return unp.std_devs(self.array)

    @property
    def shape(self):
        """
        Array shape

        Returns:
            :py:attr:`tuple` of :py:attr:`int`: The shape of the image.
        """
        return unp.nominal_values(self.array).shape

    def __repr__(self):
        """
        Custom representation.

        Returns:
            :py:attr:`array_like`: Image array.
        """
        return self.array

    def __str__(self):
        """
        Custom string.

        Returns:
            :py:attr:`array_like`: Image array.
        """
        return self.array

    def crop(self, crop_function, **kwargs):
        """
        Perform an image crop based on some function.

        Args:
            crop_function (:py:attr:`callable`): The function to crop the data.
            **kwargs (:py:attr:`dict`): The crop function keyword arguments.
        """
        self.array = unp.uarray(*crop_function(self.n, self.s, **kwargs))

    def background_subtraction(self, background_subtraction_function,
                               **kwargs):
        """
        Perform a background subtraction based on some function.

        Args:
            background_subtraction_function (:py:attr:`callable`): The
                function to model the data and therefore remove the background.
            **kwargs (:py:attr:`dict`): The background substraction function
                keyword arguments.
        """
        bkg_popt, bkg_idx = background_subtraction_function(
            self.n, self.s, **kwargs
        )
        self.bkg = bkg_popt[bkg_idx]
        self.array -= self.bkg

    def sum(self, axis=None):
        """
        Perform a summation on the image

        Args:
            axis (:py:attr:`int`, optional): The axis of the array to perform
                the summation over. Defaults to :py:attr:`None`.
        """
        return self.array.sum(axis)

    def q_resolution(self, qz_dimension=1):
        """
        Estimate the q-resolution function based on the reflected intensity
        on the detector.

        Args:
            qz_dimension (:py:attr:`int`, optional): The dimension of q_z in
                the detector image (this should be the opposite index to that
                the summation is performed if the
                :py:func:`islatu.background.fit_gaussian_1d` background
                subtraction has been performed). Defaults to :py:attr:`1`.
        """
        bkg_popt, bkg_idx = fit_gaussian_1d(
            self.n, self.s, axis=qz_dimension
        )
        self.n_pixel = bkg_popt[1]


def _average_out_hot(array, hot_pixel_max=2e5):
    """
    Make hot pixels equal to the local average.

    Args:
        array (:py:attr:`array_like`): The array to have hot pixels removed.
        hot_pixel_max (:py:attr:`float`, optional): The definition of a hot
            pixel.

    Returns:
       :py:attr:`array_like`: Image array with hot pixels removed.
    """
    x, y = np.where(array > hot_pixel_max)
    for i in range(x.size):
        a = x[i]
        b = y[i]
        j = 1
        k = 1
        if a == 0:
            a = 1
            j = 0
        elif a == array.shape[0] - 1:
            a = array.shape[0] - 1
            j = 1
        if b == 0:
            b = 1
            k = 0
        elif b == array.shape[1] - 1:
            b = array.shape[1] - 1
            k = 1
        local = np.copy(array[a-1:a+2, b-1:b+2])
        local[j, k] = 0
        if local.mean() < (array[x[i], y[i]]) / 100:
            array[x[i], y[i]] = local.sum() / (local.size - 1)
    return array
