"""
The refl_data module includes two classes, ``Profile`` and ``Scan`` which 
are integral to the use of ``islatu`` for the reduction of x-ray reflectometry data. 
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
        scans (list of islatu.refl_data.Scan): Reflectometry scans that make up the profile.
        q_vectors (np.ndarray): q-vectors from the reflectometry scan, populated after concatentation.
        reflected_intensity (np.ndarray): Reflected intensities from the reflectometry scan, populated after concatentation.
    
    Args:
        file_paths (list): List of files, one for each reflectometry scan.
        parser (callable): Parser function for the reflectometry scan files.
        q_axis_name (str): Label for the q-axis in the scan. Defaults to ``'q_axis_name'``. 
        theta_axis_name (str, optional): Label for the theta axis in the scan. Defaults to ``'dcdtheta'``.
    """
    def __init__(self, file_paths, parser, q_axis_name="qdcd", theta_axis_name="dcdtheta"):
        self.scans = []
        for f in file_paths:
            self.scans.append(Scan(f, parser, q_axis_name, theta_axis_name))
        self.q_vectors = None
        self.reflected_intensity = None

    @property
    def R(self):
        """
        Reflected intensity values.

        Returns:
            (np.ndarray) Intensity values.
        """
        return unp.nominal_values(self.reflected_intensity)

    @property
    def dR(self):
        """
        Reflected intensity uncertainties.

        Returns:
            (np.ndarray) Intensity uncertainties.
        """
        return unp.std_devs(self.reflected_intensity)

    @property
    def q(self):
        """
        q-value values.

        Returns:
            (np.ndarray) q-value values.
        """
        return unp.nominal_values(self.q_vectors)

    @property
    def dq(self):
        """
        q-value uncertainties.

        Returns:
            (np.ndarray) q-value uncertainties.
        """
        return unp.std_devs(self.q_vectors)
        
    def crop_and_bkg_sub(
        self,
        crop_function,
        bkg_sub_function,
        crop_kwargs=None,
        bkg_sub_kwargs=None,
        progress=True,
    ):
        """
        Class method for the ``islatu.refl_data.Scan.crop_and_bkg_sub`` method for each ``Scan`` in the list.

        Args:
            crop_function (callable): Cropping function to be used.
            bkg_sub_function (callable): Background subtraction function to be used. 
            crop_kwargs (dict, optional): Keyword arguments for the cropping function. Defaults to ``None``.
            bkg_sub_kwargs (dict, optional): Keyword arguments for the background subtraction function. Defaults to ``None``.
            progress (bool, optional): Show a progress bar. Requires the ``tqdm`` package. Defaults to ``True``.
        """
        for s in self.scans:
            s.crop_and_bkg_sub(crop_function, bkg_sub_function, crop_kwargs, bkg_sub_kwargs, progress)
    
    def footprint_correction(self, beam_width, sample_size):
        """
        Class method for ``islatu.refl_data.Scan.footprint_correction`` for each member of the `scans` list. 

        Args:
            beam_width (float): Width of incident beam, in metres.
            sample_size (uncertainties.core.Variable): Width of sample in the
                dimension of the beam, in metres.
            theta (float): Incident angle, in degrees.
        """
        for s in self.scans:
            s.footprint_correction(beam_width, sample_size)

    def transmission_normalisation(self):
        """
        Perform the transmission correction (islatu.refl_data.Scan.transmission_normalisation) for each member of the `scans` list and fine attenutation correction (islatu.stitching.correction_attenutation). 
        """
        for s in self.scans:
            s.transmission_normalisation()
        self.scans = stitching.correct_attentuation(self.scans)

    def q_uncertainty_from_pixel(
        self,
        number_of_pixels=None,
        detector_distance=None,
        energy=None,
        pixel_size=172e-6,
    ): 
        """
        Class method for ``islatu.refl_data.Scan.q_uncertainty_from_pixel`` for each member of the `scans` list.

        Args:
            number_of_pixels (float)
            detector_distance (float): metres
            energy (float): keV
            pixel_size (float, optional): metres

        Returns:
            q_uncertainty: (float)
        """
        for s in self.scans:
            s.q_uncertainty_from_pixel(number_of_pixels, detector_distance, energy, pixel_size)
    
    def qdcd_normalisation(self, itp):
        """
        Class method for ``islatu.refl_data.Scan.qdcd_normalisation`` for each member of the `scans` list.

        Args:
            normalisation_file (str): The ``.dat`` file that contains the
                normalisation data.
        """
        for s in self.scans:
            s.qdcd_normalisation(itp)
    
    def concatenate(self):
        """
        Class method for ``islatu.stitching.concatenate``. 
        """
        self.q_vectors, self.reflected_intensity = stitching.concatenate(self.scans)

    def normalise_ter(self, max_q=0.1):
        """
        Class method for ``islatu.stitching.normalise_ter``.

        Args:
            max_q (float): The maximum q to be included in finding the critical angle.
        """
        self.reflected_intensity = stitching.normalise_ter(self.q_vectors, self.reflected_intensity, max_q)

    def rebin(self, new_q=None, number_of_q_vectors=400):
        """
        Class method for ``islatu.stitching.rebin``. 

        Args:
            new_q (np.ndarray): Array of potential q-values. Defaults to ``None``.
            number_of_q_vectors (int, optional): The max number of
                q-vectors to be using initially in the rebinning of the data. Defaults to ``400``.
        """
        self.q_vectors, self.reflected_intensity = stitching.rebin(self.q_vectors, self.reflected_intensity, new_q, number_of_q_vectors)
        

class Scan:
    def __init__(
        self, file_path, parser, q_axis_name="qdcd", theta_axis_name="dcdtheta", energy=None
    ):
        self.file_path = file_path
        self.metadata, self.data = parser(self.file_path)
        if q_axis_name is None:
            h = physical_constants["Planck constant in eV s"][0] * 1e-3
            c = physical_constants["speed of light in vacuum"][0] * 1e10
            if energy is None:
                energy = self.metadata['dcm1energy'][0]
            q = energy * 4 * np.pi * unp.sin(unp.radians(self.data[theta_axis_name])) / (h * c)
            self.q = unp.uarray(
                q, np.zeros(self.data[theta_axis_name].size)
            )
        else:
            self.q = unp.uarray(
                self.data[q_axis_name], np.zeros(self.data[q_axis_name].size)
            )
        self.data = self._check_files_exist()
        self.theta = unp.uarray(
            self.data[theta_axis_name],
            np.zeros(self.data[theta_axis_name].size),
        )
        self.R = unp.uarray(
            np.zeros(self.q.size),
            np.zeros(self.q.size),
        )
        self.n_pixels = np.zeros(self.q.size)

    def __str__(self):
        """
        Custom string output
        """
        return 'The file: {} contains {} images from q = {:.4f} to q = {:.4f}.'.format(self.file_path, self.q.size, self.q[0].n, self.q[-1].n)

    def __repr__(self):
        """
        Custom repr output
        """
        return self.__str__() 

    def _check_files_exist(self):
        """
        Check that image files exist
        """
        iterator = _get_iterator(unp.nominal_values(self.q), False)
        for i in iterator:
            im_file = self.data["file"][i]
            if path.isfile(im_file):
                continue
            else:
                im_file = self.data["file"][i].split(path.sep)[-2:]
                im_file = path.join(im_file[0], im_file[1])
                im_file = path.join(path.dirname(self.file_path), im_file)
                if path.isfile(im_file):
                    self.data.iloc[i, self.data.keys().get_loc("file")] = im_file
                    continue
                else:
                    im_file = self.data["file"][i].split(path.sep)[-1]
                    im_file = path.join(path.dirname(self.file_path), im_file)
                    if path.isfile(im_file):
                        self.data.iloc[i, self.data.keys().get_loc("file")] = im_file                       
                        continue
                    else:
                        raise FileNotFoundError("The following image file could not be found: {}.".format(self.data["file"][i]))
        return self.data

    def crop_and_bkg_sub(
        self,
        crop_function,
        bkg_sub_function,
        crop_kwargs=None,
        bkg_sub_kwargs=None,
        progress=True,
    ):
        """
        Class method for the ``islatu.refl_data.Scan.crop_and_bkg_sub`` method for each ``Scan`` in the list.

        Args:
            crop_function (callable): Cropping function to be used.
            bkg_sub_function (callable): Background subtraction function to be used. 
            crop_kwargs (dict, optional): Keyword arguments for the cropping function. Defaults to ``None``.
            bkg_sub_kwargs (dict, optional): Keyword arguments for the background subtraction function. Defaults to ``None``.
            progress (bool, optional): Show a progress bar. Requires the ``tqdm`` package. Defaults to ``True``.
        """
        iterator = _get_iterator(unp.nominal_values(self.q), progress)
        for i in iterator:
            im = image.Image(self.data["file"][i], self.data, self.metadata)
            if crop_kwargs is None:
                im.crop(crop_function)
            else:
                im.crop(crop_function, **crop_kwargs)
            if bkg_sub_kwargs is None:
                im.background_subtraction(bkg_sub_function)
            else:
                im.background_subtraction(bkg_sub_function, **bkg_sub_kwargs)
            self.R[i] = ufloat(im.sum().n, im.sum().s)
            self.n_pixels[i] = im.n_pixel.n

    def footprint_correction(self, beam_width, sample_size):
        """
        Class method for ``islatu.corrections.footprint_correction``. 

        Args:
            beam_width (float): Width of incident beam, in metres.
            sample_size (uncertainties.core.Variable): Width of sample in the
                dimension of the beam, in metres.
            theta (float): Incident angle, in degrees.
        """
        self.R /= corrections.footprint_correction(
            beam_width, sample_size, self.theta
        )

    def transmission_normalisation(self):
        """
        Perform the transmission correction. 
        """
        self.R /= float(self.metadata["transmission"][0])

    def q_uncertainty_from_pixel(
        self,
        number_of_pixels=None,
        detector_distance=None,
        energy=None,
        pixel_size=172e-6,
    ):
        """
        Calculate a q uncertainty from the area detector.

        Args:
            number_of_pixels (float)
            detector_distance (float): metres
            energy (float): keV
            pixel_size (float, optional): metres

        Returns:
            q_uncertainty: (float)
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
        h = physical_constants["Planck constant in eV s"][0] * 1e-3
        c = physical_constants["speed of light in vacuum"][0] * 1e10
        q_uncertainty = energy * 4 * np.pi * unp.sin(offset) / (h * c)
        self.q = unp.uarray(
            unp.nominal_values(self.q), unp.std_devs(self.q) + q_uncertainty
        )

    def qdcd_normalisation(self, itp):
        """
        Perform normalisation by DCD variance.

        Args:
            normalisation_file (str): The ``.dat`` file that contains the
                normalisation data.
        """
        self.R /= splev(unp.nominal_values(self.q), itp)


def _get_iterator(q, progress):
    """
    Create a q-value iterator.

    Args:
        q (np.ndarray): q-values.
        progress (bool): Show progress bar.
    
    Returns:
        (range or tqdm.std.tqdm): Iterator object. 
    """
    iterator = range(len(q))
    if progress:
        try:
            from tqdm import tqdm

            iterator = tqdm(range(len(q)))
        except ModuleNotFoundError:
            print(
                "For the progress bar, you need to have the tqdm package "
                "installed. No progress bar will be shown"
            )
    return iterator