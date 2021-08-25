"""
The two-dimension detector generates images of the reflected intensity.
The purpose of this class is the investigation and manipulation of these
images.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

import numpy as np
from PIL import Image as PILIm

from islatu.background import fit_gaussian_1d


class Image:
    """
    This class stores information about the detector images.

    Attributes:
        file_path (:py:attr:`str`): File path for the image.
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

    def __init__(self, array, transpose=False, pixel_min=0,
                 hot_pixel_max=2e5):
        """
        Initialisation of the :py:class:`islatu.image.Image` class, includes
        assigning uncertainties.
        """
        if transpose:
            array = array.T
        array = _average_out_hot(array, hot_pixel_max)
        array[np.where(array < pixel_min)] = 0
        self.array = array
        self.array_s = np.sqrt(array)
        self.array_original = np.copy(array)
        self.bkg = 0
        self.n_pixels = 0

    @classmethod
    def from_img_file_name(cls, file_path, transpose=False, pixel_min=0,
                           hot_pixel_max=2e5):
        img = PILIm.open(file_path)
        array = np.array(img)
        img.close()
        return cls(array, file_path, transpose, pixel_min, hot_pixel_max)

    @property
    def nominal_values(self):
        """
        Get the nominal values of the image array.

        Returns:
            :py:attr:`array_like`: Nominal values of image.
        """
        return self.array

    @property
    def std_devs(self):
        """
        Get the standard deviation values of the image array.

        Returns:
            :py:attr:`array_like`: Standard deviation values of image.
        """
        array_error = np.sqrt(self.array)
        array_error[np.where(self.array == 0)] = 1
        return array_error

    @property
    def n(self):
        """
        Get the nominal values of the image array.

        Returns:
            :py:attr:`array_like`: Nominal values of image.
        """
        return self.array

    @property
    def s(self):
        """
        Get the standard deviation values of the image array.

        Returns:
            :py:attr:`array_like`: Standard deviation values of image.
        """
        return self.std_devs

    @property
    def shape(self):
        """
        Array shape

        Returns:
            :py:attr:`tuple` of :py:attr:`int`: The shape of the image.
        """
        return self.array.shape

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
        self.array = crop_function(self.array, **kwargs)
        self.array_s = crop_function(self.array_s, **kwargs)

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
        if background_subtraction_function is None:
            # By default, don't do any fancy fitting - instead just subtract the
            # mean count of a specified background region.
            y_start = kwargs['y_start']
            y_end = kwargs['y_end']
            x_start = kwargs['x_start']
            x_end = kwargs['x_end']
            bkg_popt = (
                self.array_original[y_start:y_end, x_start:x_end]).mean()
            bkg_sigma = np.sqrt(
                self.array_original[y_start:y_end, x_start:x_end]).mean()
            self.bkg = bkg_popt
        else:
            bkg_popt, bkg_idx = background_subtraction_function(
                self.n, self.s, **kwargs
            )
            self.bkg, bkg_sigma = bkg_popt[0][bkg_idx], bkg_popt[1][bkg_idx]
        # Clipping ensures array is +ve definite before casting back to uint
        self.array = np.uint32((np.float64(self.array) - self.bkg).clip(0))
        self.array_s += bkg_sigma

    def sum(self, axis=None):
        """
        Perform a summation on the image

        Args:
            axis (:py:attr:`int`, optional): The axis of the array to perform
                the summation over. Defaults to :py:attr:`None`.
        """
        return self.array.sum(axis), self.array_s.sum(axis)

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
        self.n_pixels = bkg_popt[0][1]


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
