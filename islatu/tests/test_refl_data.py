"""
Tests for refl_data module
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

from os import path
import islatu
from unittest import TestCase
import numpy as np
from scipy.interpolate import splrep
from numpy.testing import assert_equal, assert_almost_equal
from uncertainties import unumpy as unp
from islatu import refl_data, io, background, cropping

class TestReflData(TestCase):
    """
    Unit tests for refl_data module
    """
    def test_init_a(self):
        """
        Test init with correct file path
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_a.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        assert_equal(len(r.data["file"]), 3)
        assert_equal(r.data["file"][0], "islatu/tests/test_files/location/pilatus1/tiff_a.tif")
        assert_equal(r.data["file"][1], "islatu/tests/test_files/location/pilatus1/tiff_b.tif")
        assert_equal(r.data["file"][2], "islatu/tests/test_files/location/pilatus1/tiff_c.tif")

    def test_init_b(self):
        """
        Test init with -2: file path correct
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_b.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        assert_equal(len(r.data["file"]), 3)
        assert_equal(r.data["file"][0], path.join(path.dirname(islatu.__file__), "tests/test_files/pilatus1/tiff_a.tif"))
        assert_equal(r.data["file"][1], path.join(path.dirname(islatu.__file__), "tests/test_files/pilatus1/tiff_b.tif"))
        assert_equal(r.data["file"][2], path.join(path.dirname(islatu.__file__), "tests/test_files/pilatus1/tiff_c.tif"))

    def test_init_c(self):
        """
        Test init with -1 file path correct
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_c.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        assert_equal(len(r.data["file"]), 3)
        assert_equal(r.data["file"][0], path.join(path.dirname(islatu.__file__), "tests/test_files/tiff_a.tif"))
        assert_equal(r.data["file"][1], path.join(path.dirname(islatu.__file__), "tests/test_files/tiff_b.tif"))
        assert_equal(r.data["file"][2], path.join(path.dirname(islatu.__file__), "tests/test_files/tiff_c.tif"))

    def test_init_d(self):
        """
        Test init with wrong file path
        """
        with self.assertRaises(FileNotFoundError):
            file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_d.dat')
            r = refl_data.Scan(file_name, io.i07_dat_parser)

    def test_crop_bkg(self):
        """
        Test crop and bkg sub
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_a.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser) 
        r.crop_and_bkg_sub(cropping.crop_around_peak_2d, background.fit_gaussian_2d)
        a2 = np.zeros((3))
        np.any(np.not_equal(unp.nominal_values(r.R), a2))
        np.any(np.not_equal(unp.std_devs(r.R), a2))
        np.any(np.not_equal(r.n_pixels, a2))

    def test_crop_bkg_kwargs(self):
        """
        Test crop and bkg sub with kwargs
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_a.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        p0 = [
            5,
            5,
            1,
            1,
            1,
            1000,
        ]
        r.crop_and_bkg_sub(cropping.crop_around_peak_2d, background.fit_gaussian_2d, crop_kwargs={'x_size': 20}, bkg_sub_kwargs={'p0': p0})
        a2 = np.zeros((3))
        np.any(np.not_equal(unp.nominal_values(r.R), a2))
        np.any(np.not_equal(unp.std_devs(r.R), a2))
        np.any(np.not_equal(r.n_pixels, a2))

    def test_footprint(self):
        """
        Test footprint corrections
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_a.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser) 
        r.crop_and_bkg_sub(cropping.crop_around_peak_2d, background.fit_gaussian_2d)
        r_store = r.R
        r.footprint_correction(100e-6, 100e-3)
        np.any(np.not_equal(unp.nominal_values(r.R), unp.nominal_values(r_store)))

    def test_transmission(self):
        """
        Test transmission correction
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_a.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser) 
        r.crop_and_bkg_sub(cropping.crop_around_peak_2d, background.fit_gaussian_2d)
        r_store = r.R
        r.transmission_normalisation()
        np.any(np.not_equal(unp.nominal_values(r.R), unp.nominal_values(r_store)))

    def test_qdcd_normalisation(self):
        """
        Test qdcd normalisation
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/qdcd_norm.dat')
        normalisation_metadata, normalisation_data = io.i07_dat_parser(file_name)
        itp = splrep(normalisation_data['qdcd_'], normalisation_data['adc2'])
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_a.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser) 
        r.crop_and_bkg_sub(cropping.crop_around_peak_2d, background.fit_gaussian_2d)
        r_store = r.R
        r.qdcd_normalisation(itp)
        np.any(np.not_equal(unp.nominal_values(r.R), unp.nominal_values(r_store)))

    def test_q_uncertainty(self):
        """
        Test q_uncertainty from pixel
        """
        file_name = path.join(path.dirname(islatu.__file__), 'tests/test_files/test_a.dat')
        r = refl_data.Scan(file_name, io.i07_dat_parser) 
        r.crop_and_bkg_sub(cropping.crop_around_peak_2d, background.fit_gaussian_2d)
        q_store = unp.nominal_values(r.q)
        r.q_uncertainty_from_pixel()
        assert_equal(unp.nominal_values(r.q), q_store)
        np.any(np.not_equal(unp.std_devs(r.q), np.zeros((3))))
