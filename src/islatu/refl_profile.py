"""
A profile is a measurement resulting from a scan, or a series of scans. Profiles
are the central objects in the islatu library, containing the total reflected 
intensity as a function of scattering vector data.
"""

from islatu import stitching
from islatu.stitching import concatenate
from islatu.data import Data, MeasurementBase


class Profile(MeasurementBase):
    def __init__(self, data: Data, scans: list) -> None:
        super().__init__(data)
        self.scans = scans

    @classmethod
    def fromfilenames(cls, filenames, parser, log_lvl=1, scan_axis_name=None):
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
                q- axis. Specifying this parameter is not necessary for file 
                formats such as .nxs for which the independent variable can be
                inferred.
        """

        # Load the scans, specifying the scan axis name if necessary.
        if scan_axis_name is not None:
            scans = [parser(filename, scan_axis_name, log_lvl)
                     for filename in filenames]
        else:
            scans = [parser(filename, log_lvl) for filename in filenames]

        # Now that the individual scans have been loaded, data needs to be
        # constructed. The simplest way to do this is by concatenating the
        # data from each of the constituent scans.
        q, intensity, intensity_e = concatenate(scans)

        # Note: we are making the implicit assumption that energy is independent
        # of scan number at this point.
        energy = scans[0].metadata.probe_energy

        data = Data(intensity, intensity_e, energy, q=q)

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
        self.concatenate()

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
        # When a scan subtracts background from each of its images, its
        # background subtraction function may expose information relating to the
        # subtraction process. This information will be stored in bkg_sub_info.
        bkg_sub_info = []
        # Now just iterate over all of the scans in the profile and subtract the
        # background, storing the return values in bkg_sub_info.
        for scan in self.scans:
            bkg_sub_info.append(scan.bkg_sub(
                bkg_sub_function, kwargs, progress))

        self.concatenate()

        # Expose the optimized fit parameters for meta-analysis.
        return bkg_sub_info

    def subsample_q(self, scan_ID, q_min=0, q_max=float('inf')):
        """
        For the scan scan_ID, delete all data points for which q < q_min or
        q > q_max.

        Args:
            scan_ID:
                The scan ID of the scan to be subsampled. This must be a unique
                substring of the filename from which the scan was taken. For 
                example, if a scan's nexus filename is i07-413244.nxs, then
                a valid scan_ID would be "413244", as this string will uniquely
                identify the correct scan from within the profile.
            q_min:
                The smallest acceptable value of q. Defaults to 0 Å.
            q_max:
                The largest acceptable value of q. Defaults to inf Å.
        """
        for scan in self.scans:
            if scan_ID in scan.metadata.filename:
                scan.subsample_q(q_min, q_max)
        self.concatenate()

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
        self.concatenate()

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
        self.concatenate()

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
        self.concatenate()

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
        self.concatenate()

    def concatenate(self):
        """
        Class method for :func:`~islatu.stitching.concatenate`.
        """
        self.q, self.intensity, self.intensity_e = stitching.concatenate(
            self.scans)

    def normalise_ter(self, max_q=0.1):
        """
        Class method for :func:`~islatu.stitching.normalise_ter`.

        Args:
            max_q (:py:attr:`float`): The maximum q to be included in finding
                the critical angle.
        """
        self.reflected_intensity = stitching.normalise_ter(
            self.q, self.intensity, max_q
        )
        self.concatenate()

    def rebin(self, new_q=None, rebin_as="linear", number_of_q_vectors=5000):
        """
        Class method for :func:`islatu.stitching.rebin`.

        Args:
            new_q (:py:attr:`array_like`): 
                Array of potential q-values. Defaults to :py:attr:`None`. If 
                this argument is not specified, then the new q, R values are 
                binned according to rebin_as and number_of_q_vectors.
            rebin_as (py:attr:`str`):
                String specifying how the data should be rebinned. Options are 
                "linear" and "log". This is only used if the new_q are 
                unspecified.
            number_of_q_vectors (:py:attr:`int`, optional):
                The max number of q-vectors to be using initially in the 
                rebinning of the data. Defaults to :py:attr:`400`.
        """
        self.q, self.intensity, self.intensity_e = stitching.rebin(
            self.q, (self.intensity, self.intensity_e), new_q,
            rebin_as=rebin_as, number_of_q_vectors=number_of_q_vectors)