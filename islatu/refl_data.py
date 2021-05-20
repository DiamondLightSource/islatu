"""
The refl_data module includes two classes,
:py:class:`~islatu.refl_data.Profile` and :py:class:`~islatu.refl_data.Scan`
that are integral to the use of :py:mod`islatu` for the reduction of x-ray
reflectometry data.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Andrew R. McCluskey, Richard Brearton

import os
import numpy as np
from scipy.constants import physical_constants
from scipy.interpolate import splev
from uncertainties import ufloat
from uncertainties import unumpy as unp
from islatu import corrections, image, stitching
import islatu.detector


class Profile:
    """
    This class stores information about the reflectometry profile.

    Attributes:
        scans (:py:attr:`list` of :py:class:`islatu.refl_data.Scan`):
            Reflectometry scans that make up the profile.
        q_vectors (:py:attr:`array_like`): q-vectors from the reflectometry
            scan, populated after concatentation.
        reflected_intensity (:py:attr:`array_like`): Reflected intensities
            from the reflectometry scan, populated after concatentation.

    Args:
        file_paths (:py:attr:`list`): List of files, one for each
            reflectometry scan.
        parser (:py:attr:`callable`): Parser function for the reflectometry
            scan files.
        q_axis_name (:py:attr:`str`, optional): Label for the q-axis in the
            scan. Defaults to :py:attr:`'q_axis_name'`.
        theta_axis_name (:py:attr:`str`, optional): Label for the theta axis
            in the scan. Defaults to :py:attr:`'dcdtheta'`.
        energy (:py:attr:`float`): The energy of the probing X-ray, in keV.
            Defaults to finding from metadata if no value given.
        pixel_min (:py:attr:`int`): The minimum pixel value possible, all
            pixels found with less than this value will have this value
            assigned. Defaults to :py:attr:`0`.
        pixel_max (:py:attr:`int`): The maximum pixel value allowed, if any
            detector image has a pixel over this value, the whole image is
            removed from the dataset. This is due to the risk of non-linear
            counting at very high counts. Defaults to :py:attr:`1e6`.
        hot_pixel_max (:py:attr:`int`): The value of a hot pixel that will be
            set to the average of the surrounding pixels. Logically, this
            should be less than the :py:attr:`pixel_max` value. Defaults to
            :py:attr:`2e5`.
        progress (:py:attr:`bool`, optional): Show a progress bar.
            Requires the :py:mod:`tqdm` package. Defaults to :py:attr:`True`.
    """

    def __init__(self, file_paths, parser, q_axis_name="qdcd",
                 theta_axis_name="dcdtheta", energy=None, pixel_min=0,
                 pixel_max=1000000, hot_pixel_max=1e5, transpose=False):
        self.scans = []
        try:
            _ = len(pixel_min)
        except TypeError:
            pixel_min = [pixel_min] * len(file_paths)
        try:
            _ = len(pixel_max)
        except TypeError:
            pixel_max = [pixel_max] * len(file_paths)
        try:
            _ = len(hot_pixel_max)
        except TypeError:
            hot_pixel_max = [hot_pixel_max] * len(file_paths)
        for i, fyle in enumerate(file_paths):
            self.scans.append(
                Scan(fyle, parser, q_axis_name, theta_axis_name,
                     pixel_min=pixel_min[i], pixel_max=pixel_max[i],
                     hot_pixel_max=hot_pixel_max[i], transpose=transpose))
        self.q_vectors = None
        self.reflected_intensity = None

    @property
    def R(self):
        """
        Reflected intensity values.

        Returns:
            :py:attr:`array_like`: Intensity values.
        """
        return unp.nominal_values(self.reflected_intensity)

    @property
    def dR(self):
        """
        Reflected intensity uncertainties.

        Returns:
            :py:attr:`array_like`: Intensity uncertainties.
        """
        return unp.std_devs(self.reflected_intensity)

    @property
    def q(self):
        """
        q-value values.

        Returns:
            :py:attr:`array_like`: q-value values.
        """
        return unp.nominal_values(self.q_vectors)

    @property
    def dq(self):
        """
        q-value uncertainties.

        Returns:
            :py:attr:`array_like`: q-value uncertainties.
        """
        return unp.std_devs(self.q_vectors)

    def crop(self, crop_function, kwargs=None, progress=True):
        """
        Class method for the :func:`~islatu.refl_data.Scan.crop` method for
        each :py:class:`~Scan` in the list.

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

    def transmission_normalisation(self):
        """
        Perform the transmission correction
        (:func:`~islatu.refl_data.Scan.transmission_normalisation`) for each
        :py:class:`~Scan` in the list and fine attenutation correction
        (:func:`~islatu.stitching.correction_attenutation`).
        """
        for scan in self.scans:
            scan.transmission_normalisation()
        self.scans = stitching.correct_attentuation(self.scans)

    def resolution_function(self, qz_dimension=1, progress=True,
                            detector_distance=None, energy=None,
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
                qz_dimension, progress, detector_distance,
                energy, pixel_size
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
            self.q_vectors, self.reflected_intensity,
            new_q, number_of_q_vectors, interpolate)


class Scan:
    """
    This class stores scan specific information.

    Attributes:
        file_paths (:py:attr:`str`): File path for scan file.
        metadata (:py:attr:`dict`): The metadata from the ``.dat`` file.
        data (:py:class:`pandas.DataFrame`): The data from the ``.dat`` file.
        detector (instance of :py:class:`islatu.detector.Detector`):
            Information pertaining to the detector used in the experiment.
        images (:py:attr:`list` of :py:class:`islatu.image.Image`): The
            detector images in the given scan.
        q (:py:attr:`array_like`): The measured q-values in the scan.
        theta (:py:attr:`array_like`): The measured theta values in the scan.
        R (:py:attr:`array_like`): The reflected intensity values in the scan.
        n_pixels (:py:attr:`array_like`): The width in pixels of the beam in
            each image.

    Args:
        file_paths (:py:attr:`list`): List of files, one for each
            reflectometry scan.
        parser (:py:attr:`callable`): Parser function for the reflectometry
            scan files.
        q_axis_name (:py:attr:`str`, optional): Label for the q-axis in the
            scan. Defaults to :py:attr:`None`.
        theta_axis_name (:py:attr:`str`, optional): Label for the theta axis
            in the scan. Defaults to :py:attr:`'dcdtheta'`.
        energy (:py:attr:`float`): The energy of the probing X-ray, in keV.
            Defaults to finding from metadata if no value given. Defaults to
            :py:attr:`None`.
        pixel_min (:py:attr:`int`): The minimum pixel value possible, all
            pixels found with less than this value will have this value
            assigned. Defaults to :py:attr:`0`.
        pixel_max (:py:attr:`int`): The maximum pixel value allowed, if any
            detector image has a pixel over this value, the whole image is
            removed from the dataset. This is due to the risk of non-linear
            counting at very high counts. Defaults to :py:attr:`1e6`.
        hot_pixel_max (:py:attr:`int`): The value of a hot pixel that will be
            set to the average of the surrounding pixels. Logically, this
            should be less than the :py:attr:`pixel_max` value. Defaults to
            :py:attr:`2e5`.
        progress (:py:attr:`bool`, optional): Show a progress bar.
            Requires the :py:mod:`tqdm` package. Defaults to :py:attr:`True`.
    """

    def __init__(self, file_path, parser, q_axis_name=None,
                 theta_axis_name="dcdtheta", energy=None, pixel_min=0,
                 pixel_max=1000000, hot_pixel_max=2e5,
                 transpose=False, progress=True):
        self.file_path = file_path
        self.metadata, self.data = parser(self.file_path)

        # Now that the metadata has been extracted, attempt to infer which
        # detector was used to carry out this scan.
        self.detector = self._infer_detector(parser)

        # If q data wasn't directly recorded, then calculate it from the data.
        if q_axis_name is None:
            self._calculate_q(theta_axis_name, energy)
        else:
            self.q = unp.uarray(
                self.data[q_axis_name], np.zeros(self.data[q_axis_name].size)
            )

        # If the file parsed by scan did not contain the raw intensity data,
        # but instead pointed to that data, then ensure that the intensity
        # data files can be found before continuing.
        self.data = self._check_and_correct_file_data()

        # Initialize theta, R, and metadata such as n_pixels and transpose.
        self.theta = unp.uarray(
            self.data[theta_axis_name],
            np.zeros(self.data[theta_axis_name].size))
        self.R = unp.uarray(np.zeros(self.q.size), np.zeros(self.q.size),)
        self.n_pixels = np.zeros(self.q.size)
        self.transpose = transpose

        # Now load the intensity data. If the detector is a 2D detector, then
        # the images from the 2D detector should be loaded into RAM. In the case
        # of a point detector, population of R is trivial and should be done
        # immediately.
        if self.detector.is_2d_detector:
            # A 2D detector's scan will generally be comprised of a series of
            # images.
            self.images = []
            # Loading could take time, so show a loading bar.
            iterator = _get_iterator(unp.nominal_values(self.q), progress)
            to_remove = []
            for i in iterator:
                hottest_pixel = self.data[self.detector.metakey_roi_1_maxval][i]
                if hottest_pixel <= pixel_max:
                    # TODO: generalize image loading process properly.
                    img = image.Image(
                        self.data[self.detector.metakey_file][i], self.data,
                        self.metadata, pixel_min=pixel_min,
                        hot_pixel_max=hot_pixel_max, transpose=self.transpose)
                    self.images.append(img)
                else:
                    to_remove.append(i)
            # Remove any images containing a pixel hotter than hot_pixel_max.
            self._remove_data_points(to_remove)
        else:
            raise NotImplementedError(
                "Non-area detectors are not currently supported.")

    def __str__(self):
        """
        Custom string output.

        Returns:
            :py:attr:`str`: Description of scan.
        """
        return ("The file: {} contains {} images from q = {:.4f} to "
                "q = {:.4f}.".format(self.file_path, self.q.size,
                                     self.q[0].n, self.q[-1].n))

    def __repr__(self):
        """
        Custom repr output.

        Returns:
            :py:attr:`str`: Description of scan.
        """
        return self.__str__()

    def _remove_data_points(self, data_point_indices):
        """
        Removes the set of data points defined by data_point_indices from the 
        R, theta, n_pixes, q and images lists/arrays.

        Args:
            data_point_indices (:py:attr:`list` of :py:attr:`int`): 
                The indices of the data points to be deleted.
        """
        # Delete the simple stuff.
        self.R = np.delete(self.R, data_point_indices)
        self.theta = np.delete(self.theta, data_point_indices)
        self.n_pixels = np.delete(self.n_pixels, data_point_indices)
        self.q = np.delete(self.q, data_point_indices)

        # There may not be a need to delete images; perhaps they were never
        # loaded. If they were loaded, then there will be more images than
        # q-vectors for instance, seeing as some q-vectors were just deleted.
        if len(self.images) != len(self.q):
            self.images = np.delete(self.images, data_point_indices)

    def _calculate_q(self, theta_axis_name, energy):
        """
        Tries to calculate the scattering vector Q from diffractometer theta. If
        energy isn't none, this is used directly. If energy is not provided, it
        is acquired from the metadata. 

        Args:
            theta_axis_name (:py:attr:`str`): Dictionary key for the theta axis. 
            energy (:py:attr:`float`): Energy of the incident probe particle.

        Raises:
            KeyError: Raised when islatu cannot locate energy metadata from the
                user's input file.
            NotImplementedError: Raised for neutron data.
        """
        # Calculate q for x-ray reflectometry data.
        if self.detector.probe_mass == 0:
            planck = physical_constants["Planck constant in eV s"][0] * 1e-3
            speed_of_light = physical_constants[
                "speed of light in vacuum"][0] * 1e10
            # If the user didn't supply an energy as an input, then parse it
            # from the scraped metadata.
            try:
                if energy is None:
                    energy = self.metadata[
                        self.detector.metakey_probe_energy][0]
            except KeyError as e:
                print(
                    "Islatu was unable to locate any energy metadata in " +
                    "your input file, and consequently failed to " +
                    "calculate Q-vectors from your experimental data. " +
                    "Consider passing your beam's energy directly to " +
                    "this Scan's initializer, or, if your file type " +
                    "should be supported by islatu, raising an issue on " +
                    "the islatu github page."
                )
                raise e
            q_values = energy * 4 * np.pi * unp.sin(
                unp.radians(
                    self.data[theta_axis_name])) / (planck * speed_of_light)
            self.q = unp.uarray(
                q_values, np.zeros(self.data[theta_axis_name].size))
        # calculate q for neutron reflectometry data
        else:
            raise NotImplementedError(
                "Reflectometry for massive probe particles is not yet " +
                "supported."
            )

    def _check_and_correct_file_data(self):
        """
        Check that data files exist if the file parsed by parser pointed to a 
        separate file containing intensity information. If the intensity data
        file could not be found in its original location, check a series of
        probable locations for the data file. If the data file is found in one
        of these locations, update file's entry in self.data.

        Returns:
            :py:class:`pandas.DataFrame`:
                If no modification was necessary, returns :py:attr:`self.data`.
                If modifications were necessary, returns modified data with 
                corrected file paths.
        """
        # Firstly, if the file parsed doesn't point to a separate data file,
        # just return self.data as is (as nothing needs to be done).
        if self.detector.metakey_file == None:
            return self.data

        # If execution reaches here, we've got at least one data file to check.
        data_files = self.data[self.detector.metakey_file]

        # If we had only one file, make a list out of it.
        if not hasattr(data_files, "__iter__"):
            data_files = [data_files]

        # This line allows for a loading bar to show as we check the file.
        iterator = _get_iterator(data_files, False)
        for i in iterator:
            # Better to be safe... Note: windows is happy with / even though it
            # defaults to \
            data_files[i] = str(data_files[i]).replace('\\', '/')

            # Maybe we can see the file in its original storage location?
            if os.path.isfile(data_files[i]):
                continue

            # If not, maybe it's stored locally? If the file was stored at
            # location /a1/a2/.../aN/file originally, for a local directory LD,
            # check locations LD/aj/aj+1/.../aN for all j<N and all LD's of
            # interest. This algorithm is a generalization of Andrew McCluskey's
            # original approach.
            local_start_directories = [
                os.cwd,  # maybe the file is stored near the current working dir
                self.file_path  # maybe it's stored near the parsed file
            ]

            # now generate a list of all directories that we'd like to check
            candidate_paths = []
            split_file_path = str(data_files[i]).split('/')
            for j in range(len(split_file_path)):
                local_guess = '/'.join(split_file_path[j:])
                for start_dir in local_start_directories:
                    candidate_paths.append(
                        os.path.join(start_dir, local_guess))

            # Iterate over each of the candidate paths to see if any of them
            # contain the data file we're looking for.
            found_file = False
            for candidate_path in candidate_paths:
                if os.path.isfile(candidate_path):
                    # We found the file! Now update file's entry in self.data
                    # with the correct file location.
                    self.data.iloc[
                        i, self.data.keys().get_loc(
                            self.detector.metakey_file)] = candidate_path
                    found_file = not found_file
                    break

            # If we didn't find the file, tell the user.
            if not found_file:
                raise FileNotFoundError(
                    "The data file with the name " + data_files[i] + " could "
                    "not be found. The following paths were searched:\n" +
                    "\n".join(candidate_paths)
                )
        return self.data

    def _infer_detector(self, parser):
        """
        Attempt to infer which detector was used to carry out this scan. This is
        currently done somewhat crudely by checking self.metadata for keys known
        to be unique to a particular detector. Additionally, parser.__name__ is
        used to disambiguate between detectors.

        Args:
            parser (:py:attr:`callable`): Parser function for the reflectometry
                scan files.

        Returns:
            :py:class:`islatu.detector.Detector`:
                Information pertaining to the detector used in the experiment.
        """
        class FileNotRecognizedError(NotImplementedError):
            """
            A convenience error class for throwing detailed not implemented
            errors. This is a particularly important exception to throw; here
            we can prompt users to help maintain the code by raising issues on
            the github page when a file format of theirs is not supported, but
            could be parsed. This will occur when metadata keys at an instrument
            are changed, for instance.

            Attributes:
                message (:py:attr:`str`): the message to be passed on to the 
                    base exception.

            Args:
                parser (:py:attr:`callable`): Parser function for the 
                    reflectometry scan files.
            """

            def __init__(self, parser):
                self.parser = parser
                self.message = (
                    "Islatu does not recognize your data file. Did you mean " +
                    "to use a different parser? Parser detected: " +
                    parser.__name__ + ". If metadata at your instrument has " +
                    "been updated, please raise an issue on islatu's github " +
                    "repository, indicating the instrument whose data we are " +
                    "unable to parse.")
                super().__init__(self.message)

        if str(parser.__name__).startswith("i07_"):
            # check to see if we've got older data
            if "diff1halpha" in self.metadata:
                # this key has been renamed and does not appear in modern scans
                return islatu.detector.i07_pilatus_legacy

            # If execution reaches here, it's a new detector. Check to see if
            # it's the excalibur detector or the pilatus detector. This is easy,
            # since they use different keys to report regions of interest
            if islatu.detector.i07_excalibur.metakey_roi_1_maxval in self.data:
                return islatu.detector.i07_excalibur
            if islatu.detector.i07_pilatus.metakey_roi_1_maxval in self.data:
                return islatu.detector.i07_pilatus

        # If execution reaches here, we haven't been able to identify the
        # detector. Alert the user, and prompt them to raise an issue on
        # github.
        raise FileNotRecognizedError(parser)

    def crop(self, crop_function, kwargs=None, progress=True):
        """
        Perform detector image cropping.

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


def _get_iterator(to_iter, progress):
    """
    Create an iterator.

    Args:
        to_iter (:py:attr:`array_like`): The list or array to iterate.
        progress (:py:attr:`bool`): Show progress bar.

    Returns:
        :py:attr:`range` or :py:class:`tqdm.std.tqdm`: Iterator object.
    """
    iterator = range(len(to_iter))
    if progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(range(len(to_iter)))
        except ModuleNotFoundError:
            print(
                "For the progress bar, you need to have the tqdm package "
                "installed. No progress bar will be shown"
            )
    return iterator
