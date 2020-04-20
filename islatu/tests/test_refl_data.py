"""
Tests for refl_data module
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

from unittest import TestCase
import numpy as np
from numpy.testing import assert_equal, assert_almost_equal
from uncertainties import unumpy as unp
from islatu import refl_data

class TestReflData(TestCase):
    """
    Unit tests for refl_data module
    """

    def test_init(self):
        pass 