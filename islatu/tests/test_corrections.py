"""
Tests for corrections module
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

from unittest import TestCase
import numpy as np
from numpy.testing import assert_almost_equal
from uncertainties import ufloat
from islatu import corrections


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
        result = corrections.footprint_correction(
            beam_width, sample_size, theta
        )
        assert_almost_equal(result[0].n, 0.006558435584346212)
        assert_almost_equal(result[1].n, 0.1305814681032167)
