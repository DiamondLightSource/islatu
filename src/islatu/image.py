"""
The two-dimension detector generates images of the reflected intensity.
The purpose of the Image class stored in this module is the investigation
and manipulation of these images.
"""


import numpy as np


class Image:
    """
    This class stores information about the detector images.

    Attributes:
        file_path (:py:attr:`str`):
            File path for the image.
        array (:py:attr:`array_like`):
            The image described as an array.
        array_original (:py:attr:`array_like`):
            The original value of the image array when it was loaded from disk.
        array_e (:py:attr:`array_like`):
            The errors on each pixel of the array.
        bkg (:py:attr:`float`):
            The background that was subtracted from the image.
        bkg_e (:py:attr:`float`):
            The uncertainty on the background.

    Args:
        file_path (:py:attr:`str`): The file path for the image.
        data (:py:class:`pandas.DataFrame`, optional): Experimental data about
            the measurement. Defaults to :py:attr:`None`.
        transpose (:py:attr:`bool`, optional): Should the data be rotated by
            90 degrees? Defaults to :py:attr:`False`.
    """

    def __init__(self, array: np.ndarray, transpose: bool = False):
        """
        Initialisation of the :py:class:`islatu.image.Image` class, includes
        assigning uncertainties.
        """
        if transpose:
            array = array.T
        self.array = array
        self.array_original = np.copy(array)
        self.array_e = self.initial_std_devs
        self.bkg = 0
        self.bkg_e = 0

    @property
    def nominal_values(self):
        """
        Get the nominal values of the image array.

        Returns:
            :py:attr:`array_like`: Nominal values of image.
        """
        return self.array

    @property
    def initial_std_devs(self):
        """
        Get the standard deviation values of the original raw image array.

        Returns:
            :py:attr:`array_like`: Standard deviation values of image.
        """
        array_error = np.sqrt(self.array_original)
        array_error[np.where(self.array_original == 0)] = 1
        return array_error

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
        self.array_e = crop_function(self.array_e, **kwargs)

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

        bkg_sub_info = background_subtraction_function(
            self, **kwargs
        )
        # Store the calculated background, and its error.
        self.bkg, self.bkg_e = bkg_sub_info.bkg, bkg_sub_info.bkg_e

        # Do the subtraction.
        self.array = self.array - self.bkg
        self.array_e = np.sqrt(self.bkg_e**2 + self.array_e**2)

        # Expose information relating to the background subtraction for
        # meta-analyses.
        return bkg_sub_info

    def sum(self):
        """
        Perform a summation on the image's array.

        Returns:
            A tuple taking the form (summed_intensity, summed_intensity_e).
        """
        intensity = np.sum(self.array)
        intensity_e = np.sqrt(np.sum(self.array_e**2))

        return intensity, intensity_e
