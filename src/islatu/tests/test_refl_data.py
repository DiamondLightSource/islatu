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

    def test_init_profile(self):
        """
        Test init with correct file paths
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        assert_equal(len(r.scans), 2)

    def test_crop_bkg_profile(self):
        """
        Test crop and bkg sub profile
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        a2 = np.zeros((3))
        np.any(np.not_equal(unp.nominal_values(r.scans[0].R), a2))
        np.any(np.not_equal(unp.nominal_values(r.scans[1].R), a2))
        np.any(np.not_equal(unp.std_devs(r.scans[0].R), a2))
        np.any(np.not_equal(unp.std_devs(r.scans[1].R), a2))
        np.any(np.not_equal(r.scans[0].n_pixels, a2))
        np.any(np.not_equal(r.scans[1].n_pixels, a2))

    def test_footprint_profile(self):
        """
        Test footprint corrections profile
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r_store0 = r.scans[0].R
        r_store1 = r.scans[1].R
        r.footprint_correction(100e-6, 100e-3)
        np.any(
            np.not_equal(unp.nominal_values(r.scans[0].R), unp.nominal_values(r_store0))
        )
        np.any(
            np.not_equal(unp.nominal_values(r.scans[1].R), unp.nominal_values(r_store1))
        )

    def test_transmission_profile(self):
        """
        Test transmission correction profile
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r_store0 = r.scans[0].R
        r_store1 = r.scans[1].R
        r.transmission_normalisation()
        np.any(
            np.not_equal(unp.nominal_values(r.scans[0].R), unp.nominal_values(r_store0))
        )
        np.any(
            np.not_equal(unp.nominal_values(r.scans[1].R), unp.nominal_values(r_store1))
        )

    def test_qdcd_normalisation_profile(self):
        """
        Test qdcd normalisation profile
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/qdcd_norm.dat"
        )
        normalisation_metadata, normalisation_data = io.i07_dat_parser(file_name)
        itp = splrep(normalisation_data["qdcd_"], normalisation_data["adc2"])
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r_store0 = r.scans[0].R
        r_store1 = r.scans[1].R
        r.qdcd_normalisation(itp)
        np.any(
            np.not_equal(unp.nominal_values(r.scans[0].R), unp.nominal_values(r_store0))
        )
        np.any(
            np.not_equal(unp.nominal_values(r.scans[1].R), unp.nominal_values(r_store1))
        )

    def test_resolution_function_profile(self):
        """
        Test resolution_function from pixel profile
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        q_store0 = unp.nominal_values(r.scans[0].q)
        q_store1 = unp.nominal_values(r.scans[1].q)
        r.resolution_function(1)
        assert_equal(unp.nominal_values(r.scans[0].q), q_store0)
        np.any(np.not_equal(unp.std_devs(r.scans[0].q), np.zeros((3))))
        assert_equal(unp.nominal_values(r.scans[1].q), q_store1)
        np.any(np.not_equal(unp.std_devs(r.scans[1].q), np.zeros((3))))

    def test_concatentate_profile(self):
        """
        Test profile concatentation
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r.concatenate()
        assert_equal(r.q.size, 6)
        assert_equal(r.R.size, 6)
        assert_equal(r.dq.size, 6)
        assert_equal(r.dR.size, 6)

    def test_normalise_ter_profile(self):
        """
        Test profile ter normalisation
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r.concatenate()
        store = r.R
        dstore = r.dR
        r.normalise_ter()
        assert_equal(r.q.size, 6)
        assert_equal(r.R.size, 6)
        np.any(np.not_equal(r.R, store))
        np.any(np.not_equal(r.dR, dstore))

    def test_rebin_profile(self):
        """
        Test profile rebin
        """
        file_name1 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        file_name2 = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        files = [file_name1, file_name2]
        r = refl_data.Profile(files, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r.concatenate()
        r.rebin(number_of_q_vectors=3)
        assert_equal(r.q.size, 2)
        assert_equal(r.R.size, 2)

    def test_init_a(self):
        """
        Test init with correct file path
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        assert_equal(len(r.data["file"]), 3)
        assert_equal(
            r.data["file"][0], "islatu/tests/test_files/location/pilatus1/tiff_a.tif"
        )
        assert_equal(
            r.data["file"][1], "islatu/tests/test_files/location/pilatus1/tiff_b.tif"
        )
        assert_equal(
            r.data["file"][2], "islatu/tests/test_files/location/pilatus1/tiff_c.tif"
        )

    def test_init_b(self):
        """
        Test init with -2: file path correct
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_b.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        assert_equal(len(r.data["file"]), 3)
        assert_equal(
            r.data["file"][0],
            path.join(
                path.dirname(islatu.__file__), "tests/test_files/pilatus1/tiff_a.tif"
            ),
        )
        assert_equal(
            r.data["file"][1],
            path.join(
                path.dirname(islatu.__file__), "tests/test_files/pilatus1/tiff_b.tif"
            ),
        )
        assert_equal(
            r.data["file"][2],
            path.join(
                path.dirname(islatu.__file__), "tests/test_files/pilatus1/tiff_c.tif"
            ),
        )

    def test_init_c(self):
        """
        Test init with -1 file path correct
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_c.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        assert_equal(len(r.data["file"]), 3)
        assert_equal(
            r.data["file"][0],
            path.join(path.dirname(islatu.__file__), "tests/test_files/tiff_a.tif"),
        )
        assert_equal(
            r.data["file"][1],
            path.join(path.dirname(islatu.__file__), "tests/test_files/tiff_b.tif"),
        )
        assert_equal(
            r.data["file"][2],
            path.join(path.dirname(islatu.__file__), "tests/test_files/tiff_c.tif"),
        )

    def test_init_e(self):
        """
        Test init with correct file path but q_axis as none
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser, q_axis_name=None)
        assert_equal(len(r.data["file"]), 3)
        assert_almost_equal(unp.nominal_values(r.q), r.data["qdcd"], decimal=5)

    def test_str(self):
        """
        Test string output
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser, q_axis_name=None)
        assert_equal(
            r.__str__(),
            "The file: {} contains 3 images from q = 0.0100 to q = 0.0110.".format(
                file_name
            ),
        )

    def test_repr(self):
        """
        Test string output
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser, q_axis_name=None)
        assert_equal(
            r.__repr__(),
            "The file: {} contains 3 images from q = 0.0100 to q = 0.0110.".format(
                file_name
            ),
        )

    def test_init_d(self):
        """
        Test init with wrong file path
        """
        with self.assertRaises(FileNotFoundError):
            file_name = path.join(
                path.dirname(islatu.__file__), "tests/test_files/test_d.dat"
            )
            r = refl_data.Scan(file_name, io.i07_dat_parser)

    def test_crop_bkg(self):
        """
        Test crop and bkg sub
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        a2 = np.zeros((3))
        np.any(np.not_equal(unp.nominal_values(r.R), a2))
        np.any(np.not_equal(unp.std_devs(r.R), a2))
        np.any(np.not_equal(r.n_pixels, a2))

    def test_crop_bkg_kwargs(self):
        """
        Test crop and bkg sub with kwargs
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        p0 = [
            5,
            5,
            1,
            1,
            1,
            1000,
        ]
        r.crop(
            cropping.crop_around_peak_2d,
            kwargs={"x_size": 20},
        )
        r.bkg_sub(
            background.fit_gaussian_2d,
            kwargs={"p0": p0},
        )
        a2 = np.zeros((3))
        np.any(np.not_equal(unp.nominal_values(r.R), a2))
        np.any(np.not_equal(unp.std_devs(r.R), a2))
        np.any(np.not_equal(r.n_pixels, a2))

    def test_footprint(self):
        """
        Test footprint corrections
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r_store = r.R
        r.footprint_correction(100e-6, 100e-3)
        np.any(np.not_equal(unp.nominal_values(r.R), unp.nominal_values(r_store)))

    def test_transmission(self):
        """
        Test transmission correction
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r_store = r.R
        r.transmission_normalisation()
        np.any(np.not_equal(unp.nominal_values(r.R), unp.nominal_values(r_store)))

    def test_qdcd_normalisation(self):
        """
        Test qdcd normalisation
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/qdcd_norm.dat"
        )
        normalisation_metadata, normalisation_data = io.i07_dat_parser(file_name)
        itp = splrep(normalisation_data["qdcd_"], normalisation_data["adc2"])
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        r_store = r.R
        r.qdcd_normalisation(itp)
        np.any(np.not_equal(unp.nominal_values(r.R), unp.nominal_values(r_store)))

    def test_resolution_function(self):
        """
        Test resolution_function from pixel
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/test_a.dat"
        )
        r = refl_data.Scan(file_name, io.i07_dat_parser)
        r.crop(cropping.crop_around_peak_2d)
        r.bkg_sub(background.fit_gaussian_2d)
        q_store = unp.nominal_values(r.q)
        r.resolution_function(1)
        assert_equal(unp.nominal_values(r.q), q_store)
        np.any(np.not_equal(unp.std_devs(r.q), np.zeros((3))))
