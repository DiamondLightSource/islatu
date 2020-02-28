"""
Tests for image module

Copyright (c) Andrew R. McCluskey

Distributed under the terms of the MIT License

@author: Andrew R. McCluskey
"""

# pylint: disable=R0201

import unittest
import numpy as np
import io
from numpy.testing import assert_almost_equal, assert_equal
from uncertainties import unumpy as unp
from islatu.image import Image
from islatu import cropping, background

EXAMPLE_FILE = (
    "0.   0.   1.   1.   4. 113. 117.   7.   1.   0. \n"
    "0.   0.   0.   3.   4. 127. 144.   9.   2.   0. \n"
    "2.   0.   0.   7.   7. 232. 271.  13.   5.   2. \n"
    "1.   0.   5.   6.  31. 672. 703.  55.  10.   3. \n"
    "2.0000e+00 2.0000e+00 5.0000e+00 1.3000e+01 "
    "3.5800e+02 3.4490e+04 3.1763e+04 9.1100e+02 "
    "5.5000e+01 7.0000e+00 \n"
    "2.0000e+00 2.0000e+00 9.0000e+00 2.0000e+01 "
    "9.6300e+02 9.0385e+04 5.5515e+04 1.4450e+03 "
    "8.2000e+01 1.0000e+01 \n"
    "2.000e+00 2.000e+00 3.000e+00 2.100e+01 "
    "1.080e+02 5.337e+03 3.077e+03 1.900e+02 "
    "2.500e+01 8.000e+00 \n"
    "0.   2.   1.   2.  27. 697. 324.  25.   6.   0. \n"
    "0.   2.   1.   3.  16. 525. 245.  15.   4.   3. \n"
    "0.   0.   0.   1.   4. 355. 167.   4.   1.   0."
)


class TestImage(unittest.TestCase):
    """
    Unit tests for Image class
    """

    def test_init(self):
        """
        Test file reading
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        data = io.StringIO(EXAMPLE_FILE)
        expected_image = np.loadtxt(data)
        assert_equal((10, 10), test_image.shape)
        assert_almost_equal(expected_image, test_image.n)

    def test_init_with_transpose(self):
        """
        Test for transposing with reading
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data, transpose=True)
        data = io.StringIO(EXAMPLE_FILE)
        expected_image = np.loadtxt(data, unpack=True)
        assert_equal((10, 10), test_image.shape)
        assert_almost_equal(expected_image, test_image.n)

    def test_nominal_values(self):
        """
        Test nominal values
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        data = io.StringIO(EXAMPLE_FILE)
        expected_image = np.loadtxt(data)
        assert_equal((10, 10), test_image.shape)
        assert_almost_equal(expected_image, test_image.n)
        assert_almost_equal(expected_image, test_image.nominal_values)

    def test_std_devs(self):
        """
        Test standard devs
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        data = io.StringIO(EXAMPLE_FILE)
        load = np.loadtxt(data)
        expected_image = np.sqrt(load)
        expected_image[np.where(load == 0)] = 1
        assert_equal((10, 10), test_image.shape)
        assert_almost_equal(expected_image, test_image.std_devs)
        assert_almost_equal(expected_image, test_image.s)

    def test_repr(self):
        """
        Test repr
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        data = io.StringIO(EXAMPLE_FILE)
        load = np.loadtxt(data)
        expected_image_e = np.sqrt(load)
        expected_image_e[np.where(load == 0)] = 1
        assert_almost_equal(load, unp.nominal_values(test_image.__repr__()))
        assert_almost_equal(
            expected_image_e, unp.std_devs(test_image.__repr__())
        )

    def test_str(self):
        """
        Test str
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        data = io.StringIO(EXAMPLE_FILE)
        load = np.loadtxt(data)
        expected_image_e = np.sqrt(load)
        expected_image_e[np.where(load == 0)] = 1
        assert_almost_equal(load, unp.nominal_values(test_image.__str__()))
        assert_almost_equal(
            expected_image_e, unp.std_devs(test_image.__str__())
        )

    def test_crop(self):
        """
        Test crop
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        test_image.crop(cropping.crop_around_peak_2d, x_size=2, y_size=2)
        assert_equal((2, 2), test_image.shape)

    def test_background_subtraction(self):
        """
        Test background_subtraction
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        test_image.background_subtraction(background.fit_gaussian_2d)
        assert_equal((10, 10), test_image.shape)

    def test_sum(self):
        """
        Test sum
        """
        data = io.StringIO(EXAMPLE_FILE)
        test_image = Image(data)
        assert_equal(isinstance(test_image.sum().n, float), True)
        assert_equal(isinstance(test_image.sum().s, float), True)
