"""
A profile is a measurement resulting from a scan, or a series of scans. Profiles
are the central objects in the islatu library, containing the total reflected 
intensity as a function of scattering vector data.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

from islatu import stitching
from islatu.stitching import concatenate
from islatu.data import Data, MeasurementBase


class Profile(MeasurementBase):
    def __init__(self, data: Data, scans: list) -> None:
        super().__init__(data)
        self.scans = scans

    @classmethod
    def fromfilenames(cls, filenames, parser, scan_axis_name):
        """
        Instantiate a profile from a list of scan filenames.

        Args:
            filenames (:py:attr:`list`): 
                List of files, one for each reflectometry scan. Can have length
                one.
            parser (:py:attr:`callable`): 
                Parser function for the reflectometry scan files.
            scan_axis_name (:py:attr:`str`):
                Name of the independent variable scanned, typically a theta- or 
                q- axis.
        """
        # Load the scans.
        scans = [parser(filename, scan_axis_name) for filename in filenames]

        # Now that the individual scans have been loaded, data needs to be
        # constructed. The simplest way to do this is by concatenating the
        # data from each of the constituent scans.
        q_vectors, reflectivities = concatenate(scans)

        # Note: we are making the implicit assumption that energy is independent
        # of scan number at this point.
        energy = scans[0].metadata.probe_energy

        data = Data(None, reflectivities, energy, q_vectors)

        return cls(data, scans)

    def crop(self, crop_function, kwargs=None, progress=True):
        """
        Calls the Class method for the :func:`~islatu.scan.Scan2D.crop` 
        method for each :py:class:`~Scan2D` in :py:attr:`self.scans`.

        Args:
            crop_function (:py:attr:`callable`): Cropping function to be used.
            kwargs (:py:attr:`dict`, optional): Keyword arguments for the
                cropping function. Defaults to :py:attr:`None`.
            progress (:py:attr:`bool`, optional): Show a progress bar.
                Requires the :py:mod:`tqdm` package. Defaults to
                :py:attr:`True`.
        """
        for scan in self.scans:
            scan.crop(crop_function, kwargs, progress)

    def bkg_sub(self, bkg_sub_function, kwargs=None, progress=True):
        """
        Class method for the :func:`~islatu.refl_data.Scan.bkg_sub` method for
        each :py:class:`~Scan` in the list.

        Args:
            bkg_sub_function (:py:attr:`callable`): Background subtraction
                function to be used.
            kwargs (:py:attr:`dict`, optional): Keyword arguments for
                the background subtraction function. Defaults to
                :py:attr:`None`.
            progress (:py:attr:`bool`, optional): Show a progress bar.
                Requires the :py:mod:`tqdm` package. Defaults to
                :py:attr:`True`.
        """
        for scan in self.scans:
            scan.bkg_sub(bkg_sub_function, kwargs, progress)

    def footprint_correction(self, beam_width, sample_size):
        """
        Class method for :func:`~islatu.refl_data.Scan.footprint_correction`
        for each :py:class:`~Scan` in the list.

        Args:
            beam_width (:py:attr:`float`): Width of incident beam, in metres.
            sample_size (:py:class:`uncertainties.core.Variable`): Width of
                sample in the dimension of the beam, in metres.
            theta (:py:attr:`float`): Incident angle, in degrees.
        """
        for scan in self.scans:
            scan.footprint_correction(beam_width, sample_size)

    def transmission_normalisation(self, allow_stitching=False):
        """
        Perform the transmission correction
        (:func:`~islatu.refl_data.Scan.transmission_normalisation`) for each
        :py:class:`~Scan` in the list and fine attenutation correction
        (:func:`~islatu.stitching.correction_attenutation`).
        """
        for scan in self.scans:
            scan.transmission_normalisation()

        if allow_stitching:
            self.scans = stitching.correct_attentuation(
                self.scans, allow_stitching)

    def resolution_function(self, qz_dimension=1, progress=True,
                            pixel_size=172e-6):
        """
        Class method for
        :func:`~islatu.refl_data.Scan.q_uncertainty_from_pixel` for each
        :py:class:`~Scan` in the list.

       Args:
           qz_dimension (:py:attr:`int`, optional): The dimension of q_z in
               the detector image (this should be the opposite index to that
               the summation is performed if the
               :py:func:`islatu.background.fit_gaussian_1d` background
               subtraction has been performed). Defaults to :py:attr:`1`.
            number_of_pixels (:py:attr:`float`): Number of pixels of q
                uncertainty.
            detector_distance (:py:attr:`float`): Sample detector distance in
                metres
            energy (:py:attr:`float`): X-ray energy in keV
            pixel_size (:py:attr:`float`, optional): Pixel size in metres
        """
        for scan in self.scans:
            scan.resolution_function(
                qz_dimension, progress, pixel_size
            )

    def qdcd_normalisation(self, itp):
        """
        Class method for :func:`~islatu.refl_data.Scan.qdcd_normalisation` for
        each :py:class:`~Scan` in the list.

        Args:
            normalisation_file (:py:attr:`str`): The ``.dat`` file that
                contains the normalisation data.
        """
        for scan in self.scans:
            scan.qdcd_normalisation(itp)

    def concatenate(self):
        """
        Class method for :func:`~islatu.stitching.concatenate`.
        """
        self.q_vectors, self.reflected_intensity = stitching.concatenate(
            self.scans)

    def normalise_ter(self, max_q=0.1):
        """
        Class method for :func:`~islatu.stitching.normalise_ter`.

        Args:
            max_q (:py:attr:`float`): The maximum q to be included in finding
                the critical angle.
        """
        self.reflected_intensity = stitching.normalise_ter(
            self.q_vectors, self.reflected_intensity, max_q
        )

    def rebin(self, new_q=None, number_of_q_vectors=400, interpolate=False):
        """
        Class method for :func:`islatu.stitching.rebin`.

        Args:
            new_q (:py:attr:`array_like`): Array of potential q-values.
                Defaults to :py:attr:`None`.
            number_of_q_vectors (:py:attr:`int`, optional): The max number of
                q-vectors to be using initially in the rebinning of the data.
                Defaults to :py:attr:`400`.
        """
        self.q_vectors, self.reflected_intensity = stitching.rebin(
            self.q_vectors, self.reflected_intensity, new_q,
            number_of_q_vectors, interpolate
        )
