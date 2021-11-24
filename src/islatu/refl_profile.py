"""
A profile is a measurement resulting from a scan, or a series of scans. Profiles
are the central objects in the islatu library, containing the total reflected
intensity as a function of scattering vector data.
"""

from typing import List

from .scan import Scan
from .stitching import concatenate, rebin
from .data import Data


class Profile(Data):
    """
    The object that is used to store all information relating to a reflectivity
    profile.
    """

    def __init__(self, data: Data, scans: List[Scan]) -> None:
        super().__init__(data.intensity, data.intensity_e, data.energy,
                         data.theta)
        self.scans = scans

    @classmethod
    def fromfilenames(cls, filenames, parser):
        """
        Instantiate a profile from a list of scan filenames.

        Args:
            filenames (:py:attr:`list`):
                List of files, one for each reflectometry scan. Can have length
                one.
            parser (:py:attr:`callable`):
                Parser function for the reflectometry scan files.
        """

        # Load the scans, specifying the scan axis name if necessary.
        scans = [parser(filename) for filename in filenames]

        # Now that the individual scans have been loaded, data needs to be
        # constructed. The simplest way to do this is by concatenating the
        # data from each of the constituent scans.
        q_vectors, intensity, intensity_e = concatenate(scans)

        # Note: we are making the implicit assumption that energy is independent
        # of scan number at this point.
        energy = scans[0].metadata.probe_energy

        data = Data(intensity, intensity_e, energy, q_vectors=q_vectors)

        return cls(data, scans)

    def crop(self, crop_function, **kwargs):
        """
        Calls the Class method for the :func:`~islatu.scan.Scan2D.crop`
        method for each :py:class:`~Scan2D` in :py:attr:`self.scans`.

        Args:
            crop_function (:py:attr:`callable`): Cropping function to be used.
            kwargs (:py:attr:`dict`, optional): Keyword arguments for the
                cropping function. Defaults to :py:attr:`None`.
        """
        for scan in self.scans:
            scan.crop(crop_function, **kwargs)
        self.concatenate()

    def bkg_sub(self, bkg_sub_function, **kwargs):
        """
        Class method for the :func:`~islatu.refl_data.Scan.bkg_sub` method for
        each :py:class:`~Scan` in the list.

        Args:
            bkg_sub_function (:py:attr:`callable`): Background subtraction
                function to be used.
            kwargs (:py:attr:`dict`, optional): Keyword arguments for
                the background subtraction function. Defaults to
                :py:attr:`None`.
        """
        # When a scan subtracts background from each of its images, its
        # background subtraction function may expose information relating to the
        # subtraction process. This information will be stored in bkg_sub_info.
        bkg_sub_info = []
        # Now just iterate over all of the scans in the profile and subtract the
        # background, storing the return values in bkg_sub_info.
        for scan in self.scans:
            bkg_sub_info.append(scan.bkg_sub(
                bkg_sub_function, **kwargs))

        self.concatenate()

        # Expose the optimized fit parameters for meta-analysis.
        return bkg_sub_info

    def subsample_q(self, scan_identifier, q_min=0, q_max=float('inf')):
        """
        For the scan with identifier scan_identifier, delete all data points for
        which q < q_min or q > q_max.

        Args:
            scan_identifier:
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
            print(scan_identifier, scan.metadata.src_path)
            if scan_identifier in scan.metadata.src_path:
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

    def transmission_normalisation(self):
        """
        Perform the transmission correction.
        """
        for scan in self.scans:
            scan.transmission_normalisation()

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
        self.q_vectors, self.intensity, self.intensity_e = \
            concatenate(self.scans)

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
        self.q_vectors, self.intensity, self.intensity_e = rebin(
            self.q_vectors, (self.intensity, self.intensity_e), new_q,
            rebin_as=rebin_as, number_of_q_vectors=number_of_q_vectors)
