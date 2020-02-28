"""
Tests for background module

Copyright (c) Andrew R. McCluskey

Distributed under the terms of the MIT License

@author: Andrew R. McCluskey
"""

# pylint: disable=R0201

import unittest
import numpy as np
from numpy.testing import assert_almost_equal, assert_equal
from islatu import background


class TestBackground(unittest.TestCase):
    """
    Unit tests for background module
    """

    def test_bivariate_normal(self):
        x_1 = np.linspace(-1, 1, 100)
        x_2 = np.linspace(-1, 1, 100)
        input_x = np.array([x_1, x_2])
        abscissa = np.array(
            np.mgrid[0 : len(input_x[0]) : 1, 0 : len(input_x[1]) : 1]
        )

        output = background.bivariate_normal(abscissa, 0, 0, 1, 1, 1, 10)
        assert_equal(10000, output.size)
        output = output.reshape((100, 100))
        max_inten = np.unravel_index(
            np.argmax(output, axis=None), output.shape
        )
        assert_equal([0, 0], max_inten)

    def test_fit_gaussian_2d(self):
        x_1 = np.linspace(-1, 1, 100)
        x_2 = np.linspace(-1, 1, 100)
        input_x = np.array([x_1, x_2])
        abscissa = np.array(
            np.mgrid[0 : len(input_x[0]) : 1, 0 : len(input_x[1]) : 1]
        )
        to_fit = background.bivariate_normal(abscissa, 0, 0, 1, 1, 15, 10)
        to_fit = to_fit.reshape((100, 100))
        to_fit_e = to_fit * 0.1

        result = background.fit_gaussian_2d(to_fit, to_fit_e)
        assert_almost_equal(15, result.n)
