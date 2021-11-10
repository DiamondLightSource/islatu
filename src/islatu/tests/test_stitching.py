"""
Tests for refl_data module
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

import unittest
from os import path
import numpy as np
from numpy.testing import assert_almost_equal, assert_equal
import islatu
from islatu import stitching, refl_data, io
from uncertainties import unumpy


class TestStitcher(unittest.TestCase):
    """
    Unit tests for stitching module
    """

    def test_correct_attentuation(self):
        """
        Test correction of attenutation
        """
        y1 = np.ones(10) * 10
        dy1 = np.ones(10)
        y2 = np.ones(10) * 5
        dy2 = np.ones(10) * 0.5

        x1 = np.arange(1, 11, 1)
        dx1 = np.copy(x1) * 0.05
        x2 = np.arange(8, 18, 1)
        dx2 = np.copy(x2) * 0.05

        scan1 = refl_data.Scan(
            path.join(path.dirname(islatu.__file__), "tests/test_files/test_a.dat"),
            io.i07_dat_parser,
        )
        scan2 = refl_data.Scan(
            path.join(path.dirname(islatu.__file__), "tests/test_files/test_a.dat"),
            io.i07_dat_parser,
        )

        scan1.q = unumpy.uarray(x1, dx1)
        scan1.R = unumpy.uarray(y1, dy1)
        scan2.q = unumpy.uarray(x2, dx2)
        scan2.R = unumpy.uarray(y2, dy2)
        scan_list = [scan1, scan2]

        exp_y1 = np.ones(10) * 10
        exp_dy1 = np.ones(10)
        exp_y2 = np.ones(10) * 10
        exp_dy2 = np.append(np.ones(3) * 0.8164966, np.ones(7) * 1.1547005)

        scan_list = stitching.correct_attentuation(scan_list)

        assert_almost_equal(unumpy.nominal_values(scan_list[0].R), exp_y1)
        assert_almost_equal(unumpy.std_devs(scan_list[0].R), exp_dy1)
        assert_almost_equal(unumpy.nominal_values(scan_list[1].R), exp_y2)
        assert_almost_equal(unumpy.std_devs(scan_list[1].R), exp_dy2)

    def test_concatenate(self):
        """
        Test concatenation
        """
        y1 = np.ones(10) * 10
        dy1 = np.ones(10)
        y2 = np.ones(10) * 5
        dy2 = np.ones(10) * 0.5

        x1 = np.arange(1, 11, 1)
        dx1 = np.copy(x1) * 0.05
        x2 = np.arange(8, 18, 1)
        dx2 = np.copy(x2) * 0.05

        scan1 = refl_data.Scan(
            path.join(path.dirname(islatu.__file__), "tests/test_files/test_a.dat"),
            io.i07_dat_parser,
        )
        scan2 = refl_data.Scan(
            path.join(path.dirname(islatu.__file__), "tests/test_files/test_a.dat"),
            io.i07_dat_parser,
        )

        scan1.q = unumpy.uarray(x1, dx1)
        scan1.R = unumpy.uarray(y1, dy1)
        scan2.q = unumpy.uarray(x2, dx2)
        scan2.R = unumpy.uarray(y2, dy2)
        scan_list = [scan1, scan2]

        exp_y1 = unumpy.uarray(np.append(y1, y2), np.append(dy1, dy2))
        exp_x1 = unumpy.uarray(np.append(x1, x2), np.append(dx1, dx2))

        q, r = stitching.concatenate(scan_list)

        assert_almost_equal(unumpy.nominal_values(r), unumpy.nominal_values(exp_y1))
        assert_almost_equal(unumpy.std_devs(r), unumpy.std_devs(exp_y1))
        assert_almost_equal(unumpy.nominal_values(q), unumpy.nominal_values(exp_x1))
        assert_almost_equal(unumpy.std_devs(q), unumpy.std_devs(exp_x1))

    def test_normalise_ter(self):
        """
        Test normalisation to 1
        """
        y = [1e9, 1e9, 1e9, 3.16e8, 1.29e8, 6.25e7, 3.37e7, 2.00e7]
        dy = [1e7, 1e7, 1e7, 3.16e6, 1.29e6, 6.25e5, 3.37e5, 2.00e5]

        x = np.logspace(-2, -0.8, 8)

        reflected_intensity = unumpy.uarray(y, dy)

        exp_y = unumpy.uarray(y, dy) / 1e9

        reflected_intensity = stitching.normalise_ter(x, reflected_intensity)

        assert_almost_equal(
            unumpy.nominal_values(reflected_intensity), unumpy.nominal_values(exp_y)
        )
        assert_almost_equal(
            unumpy.std_devs(reflected_intensity),
            [
                0.008165,
                0.008165,
                0.008165,
                0.0036489,
                0.0014896,
                0.0007217,
                0.0003891,
                0.0002309,
            ],
        )

    def test_normalise_ter_a(self):
        """
        Test normalisation to 1 where only one point is before cut-off
        """
        y = [1e9, 1e9, 1e9, 3.16e8, 1.29e8, 6.25e7, 3.37e7, 2.00e7]
        dy = [1e7, 1e7, 1e7, 3.16e6, 1.29e6, 6.25e5, 3.37e5, 2.00e5]

        x = np.logspace(-1.5, 4, 8)

        reflected_intensity = unumpy.uarray(y, dy)

        exp_y = unumpy.uarray(y, dy) / 1e9

        reflected_intensity = stitching.normalise_ter(x, reflected_intensity)

        assert_almost_equal(
            unumpy.nominal_values(reflected_intensity), unumpy.nominal_values(exp_y)
        )
        assert_almost_equal(
            unumpy.std_devs(reflected_intensity),
            [
                0.0,
                0.0141421,
                0.0141421,
                0.0044689,
                0.0018243,
                0.0008839,
                0.0004766,
                0.0002828,
            ],
        )

    def test_normalise_ter_b(self):
        """
        Test normalisation to 1 where the gradient max is after the first point
        """
        y = [1e9, 1.29e8, 6.25e7, 3.37e7, 2.00e7]
        dy = [1e7, 1.29e6, 6.25e5, 3.37e5, 2.00e5]

        x = np.logspace(-2, -0.8, 5)

        reflected_intensity = unumpy.uarray(y, dy)

        exp_y = unumpy.uarray(y, dy) / 1e9

        reflected_intensity = stitching.normalise_ter(x, reflected_intensity)

        assert_almost_equal(
            unumpy.nominal_values(reflected_intensity), unumpy.nominal_values(exp_y)
        )
        assert_almost_equal(
            unumpy.std_devs(reflected_intensity),
            [0.0, 0.0018243, 0.0008839, 0.0004766, 0.0002828],
        )

    def test_rebin(self):
        """
        Test rebin with specific q
        """
        reflected_intensity = unumpy.uarray(
            np.arange(1, 9, 1), np.arange(1, 9, 1) * 0.1
        )
        q_vectors = unumpy.uarray([1, 2, 3, 4, 4, 5, 6, 7], np.zeros(8))

        exp_y = [1, 2, 3, 4.5, 6, 7]
        new_x = [1, 2, 3, 4, 5, 6, 7]
        exp_x = [1, 2, 3, 4, 5, 6]

        q, r = stitching.rebin(q_vectors, reflected_intensity, new_q=new_x)

        assert_almost_equal(unumpy.nominal_values(r), exp_y)
        assert_almost_equal(unumpy.nominal_values(q), exp_x)

    def test_rebin_interpolate(self):
        """
        Test rebin with specific q with interpolate
        """
        reflected_intensity = unumpy.uarray(
            np.linspace(1, 9, 5), np.linspace(1, 9, 5) * 0.01
        )
        q_vectors = unumpy.uarray([1, 3, 5, 7, 9], np.zeros(5))

        exp_y = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        new_x = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        q, r = stitching.rebin(q_vectors, reflected_intensity, new_q=new_x,
                               interpolate=True)

        assert_almost_equal(unumpy.nominal_values(r), exp_y)

    def test_rebin_a(self):
        """
        Test rebin with default
        """
        reflected_intensity = unumpy.uarray(
            np.arange(1, 9, 1), np.arange(1, 9, 1) * 0.1
        )
        q_vectors = unumpy.uarray([1, 2, 3, 4, 4, 5, 6, 7], np.zeros(8))

        exp_y = [1, 2, 3, 4.5, 6, 7]

        q, r = stitching.rebin(q_vectors, reflected_intensity)

        assert_almost_equal(unumpy.nominal_values(r), exp_y)
