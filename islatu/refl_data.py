"""
The corrections module for the islatu pipeline
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
from islatu import corrections, image


class ReflData:
    def __init__(
        self, file_path, parser, q_axis_name="qdcd", theta_axis_name="dcdtheta"
    ):
        self.file_path = file_path
        self.metadata, self.data = parser(self.file_path)
        self.q = unp.uarray(
            self.data[q_axis_name], np.zeros(self.data[q_axis_name].size)
        )
        self.data = self._check_files_exist()
        self.theta = unp.uarray(
            self.data[theta_axis_name],
            np.zeros(self.data[theta_axis_name].size),
        )
        self.R = unp.uarray(
            np.zeros(self.data[q_axis_name].size),
            np.zeros(self.data[q_axis_name].size),
        )
        self.n_pixels = np.zeros(self.data[q_axis_name].size)

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
        """
        self.R /= corrections.footprint_correction(
            beam_width, sample_size, self.theta
        )

    def transmission_normalisation(self):
        """
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