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
    """
    def __init__(self, file_paths, parser, q_axis_name="qdcd",
                 theta_axis_name="dcdtheta", pixel_max=10000000,
                 transpose=False):
        self.scans = []
        try:
            _ = len(pixel_max)
        except TypeError:
            pixel_max = [pixel_max] * len(file_paths)
        for i, fyle in enumerate(file_paths):
            self.scans.append(
                Scan(
                    fyle, parser, q_axis_name, theta_axis_name,
                    pixel_max=pixel_max[i], transpose=transpose))
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

    def crop_and_bkg_sub(self, crop_function, bkg_sub_function,
                         crop_kwargs=None, bkg_sub_kwargs=None,
                         progress=True):
        """
        Class method for the :func:`~islatu.refl_data.Scan.crop_and_bkg_sub`
        method for each :py:class:`~Scan` in the list.

        Args:
            crop_function (:py:attr:`callable`): Cropping function to be used.
            bkg_sub_function (:py:attr:`callable`): Background subtraction
                function to be used.
            crop_kwargs (:py:attr:`dict`, optional): Keyword arguments for the
                cropping function. Defaults to :py:attr:`None`.
            bkg_sub_kwargs (:py:attr:`dict`, optional): Keyword arguments for
                the background subtraction function. Defaults to
                :py:attr:`None`.
            progress (:py:attr:`bool`, optional): Show a progress bar.
                Requires the :py:mod:`tqdm` package. Defaults to
                :py:attr:`True`.
        """
        for scan in self.scans:
            scan.crop_and_bkg_sub(
                crop_function, bkg_sub_function, crop_kwargs,
                bkg_sub_kwargs, progress)

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

    def q_uncertainty_from_pixel(self, number_of_pixels=None,
                                 detector_distance=None, energy=None,
                                 pixel_size=172e-6):
        """
        Class method for
        :func:`~islatu.refl_data.Scan.q_uncertainty_from_pixel` for each
        :py:class:`~Scan` in the list.

       Args:
            number_of_pixels (:py:attr:`float`): Number of pixels of q
                uncertainty.
            detector_distance (:py:attr:`float`): Sample detector distance in
                metres
            energy (:py:attr:`float`): X-ray energy in keV
            pixel_size (:py:attr:`float`, optional): Pixel size in metres
        """
        for scan in self.scans:
            scan.q_uncertainty_from_pixel(
                number_of_pixels, detector_distance, energy, pixel_size
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

    def rebin(self, new_q=None, number_of_q_vectors=400):
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
            new_q, number_of_q_vectors)


class Scan:
    """
    This class stores scan specific information.

    Attributes:
        file_paths (:py:attr:`str`): File path for scan file.
        metadata (:py:attr:`dict`): The metadata from the ``.dat`` file.
        data (:py:class:`pandas.DataFrame`): The data from the ``.dat`` file.
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
    """

    def __init__(self, file_path, parser, q_axis_name="qdcd",
                 theta_axis_name="dcdtheta", energy=None, pixel_max=1000000,
                 transpose=False):
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
        self.pixel_max = pixel_max
        self.transpose = transpose

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

    def crop_and_bkg_sub(self, crop_function, bkg_sub_function,
                         crop_kwargs=None, bkg_sub_kwargs=None,
                         progress=True):
        """
        Preform cropping and background subtraction on each image in the Scan.

        Args:
            crop_function (:py:attr:`callable`): Cropping function to be used.
            bkg_sub_function (:py:attr:`callable`): Background subtraction
                function to be used.
            crop_kwargs (:py:attr:`dict`, optional): Keyword arguments for the
                cropping function. Defaults to :py:attr:`None`.
            bkg_sub_kwargs (:py:attr:`dict`, optional): Keyword arguments for
                the background subtraction function. Defaults
                to :py:attr:`None`.
            progress (:py:attr:`bool`, optional): Show a progress bar.
                Requires the :py:mod:`tqdm` package. Defaults
                to :py:attr:`True`.
        """
        iterator = _get_iterator(unp.nominal_values(self.q), progress)
        to_remove = []
        for i in iterator:
            try:
                if self.data['roi1_maxval'][i] > self.pixel_max:
                    to_remove.append(i)
                    continue
                img = image.Image(self.data["file"][i], self.data,
                                  self.metadata, transpose=self.transpose)
                if crop_kwargs is None:
                    img.crop(crop_function)
                else:
                    img.crop(crop_function, **crop_kwargs)
                if bkg_sub_kwargs is None:
                    img.background_subtraction(bkg_sub_function)
                else:
                    img.background_subtraction(
                        bkg_sub_function, **bkg_sub_kwargs)
                self.R[i] = ufloat(img.sum().n, img.sum().s)
                if img.n_pixel is None:
                    self.n_pixels[i] = None
                else:
                    self.n_pixels[i] = img.n_pixel.n
            except (ValueError, RuntimeError) as error:
                print(error)
                print('Current file: ', self.data["file"][i])
                to_remove.append(i)
                continue
        self.R = np.delete(self.R, to_remove)
        self.theta = np.delete(self.theta, to_remove)
        self.n_pixels = np.delete(self.n_pixels, to_remove)
        self.q = np.delete(self.q, to_remove)

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

    def q_uncertainty_from_pixel(self, number_of_pixels=None,
                                 detector_distance=None, energy=None,
                                 pixel_size=172e-6):
        """
        Calculate a q uncertainty from the area detector.

        Args:
            number_of_pixels (:py:attr:`float`): Number of pixels of q
                uncertainty.
            detector_distance (:py:attr:`float`): Sample detector distance in
                metres
            energy (:py:attr:`float`): X-ray energy in keV
            pixel_size (:py:attr:`float`, optional): Pixel size in metres

        Returns:
            :py:attr:`float`: Resulting q-uncertainty.
        """
        if number_of_pixels is None:
            number_of_pixels = self.n_pixels
        if detector_distance is None:
            detector_distance = self.metadata["diff1detdist"][0] * 1e-3
        if energy is None:
            energy = self.metadata["dcm1energy"][0]
        offset = np.arctan(
            pixel_size * 1.96 * number_of_pixels * 0.5 / (detector_distance)
        )
        planck = physical_constants["Planck constant in eV s"][0] * 1e-3
        speed_of_light = physical_constants[
            "speed of light in vacuum"][0] * 1e10
        q_uncertainty = energy * 4 * np.pi * unp.sin(
            offset) / (planck * speed_of_light)
        self.q = unp.uarray(
            unp.nominal_values(self.q), unp.std_devs(self.q) + q_uncertainty)

    def qdcd_normalisation(self, itp):
        """
        Perform normalisation by DCD variance.

        Args:
            itp (:py:attr:`tuple`): Containing interpolation knots
                (:py:attr:`array_like`), B-spline coefficients
                (:py:attr:`array_like`), and degree of spline (:py:attr:`int`).
        """
        self.R /= splev(unp.nominal_values(self.q), itp)


def _get_iterator(q_values, progress):
    """
    Create a q-value iterator.

    Args:
        q_values (:py:attr:`array_like`): q-values.
        progress (:py:attr:`bool`): Show progress bar.

    Returns:
        :py:attr:`range` or :py:class:`tqdm.std.tqdm`: Iterator object.
    """
    iterator = range(len(q_values))
    if progress:
        try:
            from tqdm import tqdm
            iterator = tqdm(range(len(q_values)))
        except ModuleNotFoundError:
            print(
                "For the progress bar, you need to have the tqdm package "
                "installed. No progress bar will be shown"
            )
    return iterator
