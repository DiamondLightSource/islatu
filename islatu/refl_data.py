"""
The refl_data module includes two classes,
:py:class:`~islatu.refl_data.Profile` and :py:class:`~islatu.refl_data.Scan`
that are integral to the use of :py:mod`islatu` for the reduction of x-ray
reflectometry data.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey

from os import path
import numpy as np
from scipy.constants import physical_constants
from scipy.interpolate import splev
from uncertainties import ufloat
from uncertainties import unumpy as unp
from islatu import corrections, image, stitching


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
                     pixel_min=pixel_min[i], pixel_max=pixel_max[i], hot_pixel_max=hot_pixel_max[i], transpose=transpose))
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

    def __init__(self, file_path, parser, q_axis_name="qdcd",
                 theta_axis_name="dcdtheta", energy=None, pixel_min=0,
                 pixel_max=1000000, hot_pixel_max=2e5,
                 transpose=False, progress=True):
        self.file_path = file_path
        self.metadata, self.data = parser(self.file_path)
        if q_axis_name is None:
            planck = physical_constants["Planck constant in eV s"][0] * 1e-3
            speed_of_light = physical_constants[
                "speed of light in vacuum"][0] * 1e10
            if energy is None:
                energy = self.metadata["dcm1energy"][0]
            q_values = energy * 4 * np.pi * unp.sin(
                unp.radians(
                    self.data[theta_axis_name])) / (planck * speed_of_light)
            self.q = unp.uarray(
                q_values, np.zeros(self.data[theta_axis_name].size))
        else:
            self.q = unp.uarray(
                self.data[q_axis_name], np.zeros(self.data[q_axis_name].size)
            )
        self.data = self._check_files_exist()
        self.theta = unp.uarray(
            self.data[theta_axis_name],
            np.zeros(self.data[theta_axis_name].size))
        self.R = unp.uarray(np.zeros(self.q.size), np.zeros(self.q.size),)
        self.n_pixels = np.zeros(self.q.size)
        self.transpose = transpose
        self.images = []
        iterator = _get_iterator(unp.nominal_values(self.q), progress)
        to_remove = []
        for i in iterator:
            if self.data['roi1_maxval'][i] <= pixel_max:
                img = image.Image(self.data["file"][i], self.data,
                                  self.metadata, pixel_min=pixel_min,
                                  hot_pixel_max=hot_pixel_max,
                                  transpose=self.transpose)
                self.images.append(img)
            else:
                to_remove.append(i)
        self.R = np.delete(self.R, to_remove)
        self.theta = np.delete(self.theta, to_remove)
        self.n_pixels = np.delete(self.n_pixels, to_remove)
        self.q = np.delete(self.q, to_remove)


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

    def _check_files_exist(self):
        """
        Check that image files exist.

        Returns:
            :py:class:`pandas.DataFrame`: Modified data with corrected file paths.
        """
        iterator = _get_iterator(unp.nominal_values(self.q), False)
        for i in iterator:
            im_file = self.data["file"][i]
            if path.isfile(im_file):
                continue
            im_file = self.data["file"][i].split('/')[-2:]
            im_file = path.join(im_file[0], im_file[1])
            im_file = path.join(path.dirname(self.file_path), im_file)
            if path.isfile(im_file):
                self.data.iloc[
                    i, self.data.keys().get_loc("file")] = im_file
                continue
            im_file = self.data["file"][i].split('/')[-1]
            im_file = path.join(path.dirname(self.file_path), im_file)
            if path.isfile(im_file):
                self.data.iloc[
                    i, self.data.keys().get_loc("file")] = im_file
                continue
            raise FileNotFoundError(
                "The following image file could not be "
                "found: {}.".format(self.data["file"][i]))
        return self.data

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
