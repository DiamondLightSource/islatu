"""
This module contains the Scan and Scan2D classes. A Scan is a measurement and so
inherits from MeasurementBase. An instance of Scan contains scan metadata, as 
well as a suite of methods useful for data correction, uncertainty calculations
and the like.

A Scan2D is a Scan whose Data object's intensity values are computed from an 
image captured by an area detector. Many of Scan's methods are overloaded to
make use of the additional information provided by the area detector, and extra
image manipulation methods are included in Scan2D.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

from islatu.iterator import _get_iterator
from islatu.metadata import Metadata
from islatu.data import Data, MeasurementBase
from islatu import corrections

import numpy as np
from uncertainties import unumpy as unp
from uncertainties import ufloat
from scipy.constants import physical_constants
from scipy.interpolate import splev


class Scan(MeasurementBase):
    def __init__(self, data: Data, metadata: Metadata) -> None:
        super().__init__(data)
        self.metadata = metadata


class Scan2D(Scan):
    """
    Attributes:
        data (:py:attr:`islatu.data.Data`):
            The intensity as a function of Q data for this scan.
        metadata (:py:attr:`islatu.metadata.Metadata`):
            This scan's metadata.
        images (:py:attr:`list` of :py:class:`islatu.image.Image`): 
            The detector images in the given scan.
    """

    def __init__(self, data: Data, metadata: Metadata, images: list) -> None:
        super().__init__(data, metadata)
        self.images = images

    def crop(self, crop_function, kwargs=None, progress=True):
        """
        Crop every image in images according to crop_function

        args:
            crop_function (:py:attr:`callable`): Cropping function to be used.
            kwargs (:py:attr:`dict`, optional): Keyword arguments for the
                cropping function. Defaults to :py:attr:`None`.
            progress (:py:attr:`bool`, optional): Show a progress bar.
                Requires the :py:mod:`tqdm` package. Defaults
                to :py:attr:`True`.
        """
        iterator = _get_iterator(self.images, progress)
        for i in iterator:
            if kwargs is None:
                self.images[i].crop(crop_function)
            else:
                self.images[i].crop(crop_function, **kwargs)
            self.R[i] = ufloat(self.images[i].sum().n, self.images[i].sum().s)

    def bkg_sub(self, bkg_sub_function, kwargs=None, progress=True):
        """
        Perform background substraction for each image in a Scan.

        Args:
            bkg_sub_function (:py:attr:`callable`): Background subtraction
                function to be used.
            kwargs (:py:attr:`dict`, optional): Keyword arguments for
                the background subtraction function. Defaults
                to :py:attr:`None`.
            progress (:py:attr:`bool`, optional): Show a progress bar.
                Requires the :py:mod:`tqdm` package. Defaults
                to :py:attr:`True`.
        """
        iterator = _get_iterator(self.images, progress)
        for i in iterator:
            if kwargs is None:
                self.images[i].background_subtraction(bkg_sub_function)
            else:
                self.images[i].background_subtraction(
                    bkg_sub_function, **kwargs)
            self.R[i] = ufloat(self.images[i].sum().n, self.images[i].sum().s)

    def resolution_function(self, qz_dimension=1, progress=True,
                            detector_distance=None, energy=None,
                            pixel_size=172e-6):
        """
        Estimate the q-resolution function based on the reflected intensity
        on the detector and add this to the q uncertainty.

        Args:
            qz_dimension (:py:attr:`int`, optional): The dimension of q_z in
                the detector image (this should be the opposite index to that
                the summation is performed if the
                :py:func:`islatu.background.fit_gaussian_1d` background
                subtraction has been performed). Defaults to :py:attr:`1`.
            progress (:py:attr:`bool`, optional): Show a progress bar.
                Requires the :py:mod:`tqdm` package. Defaults
                to :py:attr:`True`.
            detector_distance (:py:attr:`float`): Sample detector distance in
                metres
            energy (:py:attr:`float`): X-ray energy in keV
            pixel_size (:py:attr:`float`, optional): Pixel size in metres
        """
        iterator = _get_iterator(self.images, progress)
        for i in iterator:
            self.images[i].q_resolution(qz_dimension)
        if detector_distance is None:
            detector_distance = self.metadata["diff1detdist"][0] * 1e-3
        if energy is None:
            energy = self.metadata["dcm1energy"][0]
        offset = np.arctan(
            pixel_size * 1.96 * self.n_pixels * 0.5 / (detector_distance)
        )
        planck = physical_constants["Planck constant in eV s"][0] * 1e-3
        speed_of_light = physical_constants[
            "speed of light in vacuum"][0] * 1e10
        q_uncertainty = energy * 4 * np.pi * unp.sin(
            offset) / (planck * speed_of_light)
        self.q = unp.uarray(
            unp.nominal_values(self.q), unp.std_devs(self.q) + q_uncertainty)

    def footprint_correction(self, beam_width, sample_size):
        """
        Class method for :func:`islatu.corrections.footprint_correction`.

        Args:
            beam_width (:py:attr:`float`): Width of incident beam, in metres.
            sample_size (:py:class:`uncertainties.core.Variable`): Width of
                sample in the dimension of the beam, in metres.
            theta (:py:attr:`float`): Incident angle, in degrees.
        """
        self.R /= corrections.footprint_correction(
            beam_width, sample_size, self.theta)

    def transmission_normalisation(self):
        """
        Perform the transmission correction.
        """
        self.R /= float(self.metadata["transmission"][0])

    def qdcd_normalisation(self, itp):
        """
        Perform normalisation by DCD variance.

        Args:
            itp (:py:attr:`tuple`): Containing interpolation knots
                (:py:attr:`array_like`), B-spline coefficients
                (:py:attr:`array_like`), and degree of spline (:py:attr:`int`).
        """
        self.R /= splev(unp.nominal_values(self.q), itp)
