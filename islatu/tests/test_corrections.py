"""
Tests for corrections module
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

from os import path
from unittest import TestCase
import numpy as np
from numpy.testing import assert_almost_equal, assert_equal
from uncertainties import ufloat
import islatu
from islatu import corrections, io


class TestCorrections(TestCase):
    """
    Unit tests for corrections module
    """

    def test_geometry_correction(self):
        """
        Test the implementation of the geometry correction.
        """
        beam_width = 50e-6
        sample_size = ufloat(2e-3, 1e-5)
        # The first value is below the spill over angle and the second is above
        theta = np.array([0.01, 0.2])
        result = corrections.footprint_correction(beam_width, sample_size, theta)
        assert_almost_equal(result[0].n, 0.006558435584346212)
        assert_almost_equal(result[1].n, 0.1305814681032167)

    def test_get_interpolator(self):
        """
        Test the get interpolator
        """
        file_name = path.join(
            path.dirname(islatu.__file__), "tests/test_files/qdcd_norm.dat"
        )
        itp = corrections.get_interpolator(file_name, io.i07_dat_parser)
        assert_equal(isinstance(itp, tuple), True)
        assert_equal(isinstance(itp[0], np.ndarray), True)
        assert_equal(isinstance(itp[1], np.ndarray), True)
        assert_equal(isinstance(itp[2], int), True)
