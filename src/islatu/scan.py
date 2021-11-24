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

from typing import List

import numpy as np
from scipy.interpolate import splev

from islatu import corrections
from islatu.metadata import Metadata
from islatu.data import Data, MeasurementBase
from islatu.image import Image


class Scan(MeasurementBase):
    """
    A class used to store reflectometry scans taken with a point detector.
    """

    def __init__(self, data: Data, metadata: Metadata) -> None:
        # Initialize the MeasurementBase from Data. This is much simpler than
        # passing a million arguments directly to the scan.
        super().__init__(data.intensity, data.intensity_e, data.energy,
                         metadata, data.theta)

    def subsample_q(self, q_min=0, q_max=float('inf')):
        """
        Delete data points less than q_min and more than q_max.

        Args:
            q_min:
                The minimum q to be included in this scan. Defaults to 0 Å.
            q_max:
                The maximum q to be included in this scan. Defaults to inf Å.
        """
        # A place to store all the indices violating our condition on q.
        illegal_q_indices = np.where(
            (self.q_vectors <= q_min) | (self.q_vectors >= q_max)
        )[0]
        # [0] necessary because np.where returns a tuple of arrays of length 1.
        # This is a quirk of np.where – I don't think it's actually designed to
        # be used like this, and they encourage np.asarray(condition).nonzero()

        # Now remove all data points at these qs.
        self.remove_data_points(illegal_q_indices)

    def transmission_normalisation(self):
        """
        Perform the transmission correction.
        """
        self.intensity /= float(self.metadata.transmission)
        self.intensity_e /= float(self.metadata.transmission)

    def qdcd_normalisation(self, itp):
        """
        Perform normalisation by DCD variance.

        Args:
            itp (:py:attr:`tuple`): Containing interpolation knots
                (:py:attr:`array_like`), B-spline coefficients
                (:py:attr:`array_like`), and degree of spline (:py:attr:`int`).
        """
        self.intensity /= splev(self.q_vectors, itp)
        self.intensity_e /= splev(self.q_vectors, itp)

    def footprint_correction(self, beam_width, sample_size):
        """
        Class method for :func:`islatu.corrections.footprint_correction`.

        Args:
            beam_width (:py:attr:`float`): Width of incident beam, in metres.
            sample_size (:py:class:`uncertainties.core.Variable`): Width of
                sample in the dimension of the beam, in metres.
            theta (:py:attr:`float`): Incident angle, in degrees.
        """
        frac_of_beam_sampled = corrections.footprint_correction(
            beam_width, sample_size, self.theta)
        self.intensity /= frac_of_beam_sampled
        self.intensity_e /= frac_of_beam_sampled


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

    def __init__(self, data: Data, metadata: Metadata, images: List[Image]) \
            -> None:
        super().__init__(data, metadata)
        self.images = images

    def crop(self, crop_function, **kwargs):
        """
        Crop every image in images according to crop_function.

        args:
            crop_function (:py:attr:`callable`):
                Cropping function to be used.
            kwargs (:py:attr:`dict`, optional):
                Keyword arguments for the cropping function. Defaults to
                :py:attr:`None`.
            progress (:py:attr:`bool`, optional):
                Show a progress bar. Requires the :py:mod:`tqdm` package.
                Defaults to :py:attr:`True`.
        """

        (vals, stdevs) = (np.zeros(len(self.intensity)),
                          np.zeros(len(self.intensity)))
        for i, image in enumerate(self.images):
            image.crop(crop_function, **kwargs)
            vals[i], stdevs[i] = self.images[i].sum()

        self.intensity = np.array(vals)
        self.intensity_e = np.array(stdevs)

    def bkg_sub(self, bkg_sub_function, **kwargs):
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
        vals, stdevs = np.zeros(
            len(self.intensity)), np.zeros(len(self.intensity))

        # We keep track of the bkg_sub_infos for meta-analyses.
        bkg_sub_info = [
            image.background_subtraction(bkg_sub_function, **kwargs)
            for image in self.images
        ]

        # Also update the image intensities & errors.
        for i, image in enumerate(self.images):
            vals[i], stdevs[i] = image.sum()

        # Store the intensity(Q) to the new value.
        self.intensity = np.array(vals)
        self.intensity_e = np.array(stdevs)

        # Expose the information relating to the background subtraction.
        return bkg_sub_info

    def remove_data_points(self, indices):
        """
        Convenience method for the removal of specific data points by their
        indices.

        Args:
            indices:
                The indices to be removed.
        """
        super().remove_data_points(indices)

        # Delete images in reverse order if you don't like errors.
        for idx in sorted(indices, reverse=True):
            del self.images[idx]
