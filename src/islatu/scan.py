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

from islatu.iterator import _get_iterator
from islatu.metadata import Metadata
from islatu.data import Data, MeasurementBase
from islatu import corrections

import numpy as np
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
        iterator = _get_iterator(self.q, progress)
        (vals, stdevs) = (np.zeros(len(self.intensity)),
                          np.zeros(len(self.intensity)))
        for i in iterator:
            if kwargs is None:
                self.images[i].crop(crop_function)
            else:
                self.images[i].crop(crop_function, **kwargs)

            vals[i], stdevs[i] = self.images[i].sum()
        self.intensity = np.array(vals)
        self.intensity_e = np.array(stdevs)

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
        # Required for the progress bar.
        iterator = _get_iterator(self.q, progress)
        vals, stdevs = np.zeros(
            len(self.intensity)), np.zeros(len(self.intensity))

        # Required to expose fitting parameters, or other information relating
        # to the background subtraction that might be returned by a subtraction
        # function.
        bkg_sub_info = []
        for i in iterator:
            if kwargs is None:
                bkg_sub_info.append(
                    self.images[i].background_subtraction(
                        bkg_sub_function))
            else:
                bkg_sub_info.append(
                    self.images[i].background_subtraction(
                        bkg_sub_function, **kwargs))

        # TODO: this should be the only code required here.
        # for i in iterator:
        #     bkg_sub_info.append(
        #         self.images[i].background_subtraction(
        #             bkg_sub_function, **kwargs))

            vals[i], stdevs[i] = self.images[i].sum()

        # Store the intensity(Q) to the new value.
        self.intensity = np.array(vals)
        self.intensity_e = np.array(stdevs)

        # Expose the optimized fit parameters for meta-analysis.
        return bkg_sub_info

    def resolution_function(self, qz_dimension=1, progress=True,
                            pixel_size=172e-6):
        """
        Estimate the q-resolution function based on the reflected intensity
        on the detector and returns this q uncertainty.

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

        Returns:
            (py:attr:`float`):
                The uncertainty in q, estimated from the peak profile.
        """
        iterator = _get_iterator(self.q, progress)
        for i in iterator:
            self.images[i].q_resolution(qz_dimension)
        # Grab the detector distance from the metadata. TODO: build units into
        # the detector dataclass, and automatically noramlize units on
        # initialization of a metadata instance.
        detector_distance = self.metadata.detector_distance * 1e-3
        energy = self.metadata.probe_energy
        # The width of the peak in pixels should be indep. of image.
        n_pixels = self.images[0].n_pixels
        offset = np.arctan(
            pixel_size * 1.96 * n_pixels * 0.5 / (detector_distance)
        )
        planck = physical_constants["Planck constant in eV s"][0] * 1e-3
        speed_of_light = physical_constants[
            "speed of light in vacuum"][0] * 1e10
        q_uncertainty = energy * 4 * np.pi * np.sin(
            np.array(offset)) / (planck * speed_of_light)

        return q_uncertainty

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
            (self.q < q_min) | (self.q > q_max)
        )[0]
        # [0] necessary because np.where returns a tuple of arrays of length 1.
        # This is a quirk of np.where – I don't think it's actually designed to
        # be used like this, and they encourage np.asarray(condition).nonzero()

        # Now remove all data points at these qs.
        self.remove_data_points(illegal_q_indices)

    def remove_data_points(self, indices):
        """
        Convenience method for the removal of specific data points by their 
        indices.

        Args:
            idx:
                The index number to be removed.
        """
        super().remove_data_points(indices)

        # Delete in reverse order, or face the wrath of your interpreter!
        for idx in sorted(indices, reverse=True):
            del self.images[idx]

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
        self.intensity /= splev(self.q, itp)
        self.intensity_e /= splev(self.q, itp)