"""
This module contains fixture definitions used when testing the islatu module.
"""

# The following pylint rule is, unfortunately, necessary due to how pytest works
# with fixtures. Consequently, all fixtures are defined in this file so that
# redefined-outer-name only needs to be disabled once.
# pylint: disable=redefined-outer-name

import os
import pytest
import numpy as np

from islatu.io import I07Nexus, i07_nxs_parser
from islatu.data import Data, MeasurementBase
from islatu.region import Region


@pytest.fixture
def path_to_i07_nxs_01():
    """
    Returns the path to an i07 nexus file. If it can't be found, raises.
    """
    path_from_tests_dir = os.path.join("resources", "i07-404876.nxs")
    if os.path.isdir('resources'):
        return path_from_tests_dir
    if os.path.isdir('tests') and os.path.isdir('src'):
        return os.path.join("tests", path_from_tests_dir)

    raise FileNotFoundError(
        "Couldn't locate the tests/resources directory. Make sure that " +
        "the pytest command is run from within the base islatu directory" +
        ", or from within the tests directory."
    )


@pytest.fixture
def path_to_i07_h5_01():
    """
    Returns the path to an i07 h5 file. If it can't be found, raises.
    """
    path_from_tests_dir = os.path.join(
        "resources", "excaliburScan404876_000001.h5")
    if os.path.isdir('resources'):
        return path_from_tests_dir
    if os.path.isdir('tests') and os.path.isdir('src'):
        return os.path.join("tests", path_from_tests_dir)

    raise FileNotFoundError(
        "Couldn't locate the tests/resources directory. Make sure that " +
        "the pytest command is run from within the base islatu directory" +
        ", or from within the tests directory."
    )


@pytest.fixture
def nexus_base_object_01(path_to_i07_nxs_01):
    """
    Returns the path's corresponding i07 nexus object.
    """
    return I07Nexus(path_to_i07_nxs_01)


@pytest.fixture
def i07_nexus_object_01(path_to_i07_nxs_01):
    """
    Returns the path's corresponding i07 nexus object.
    """
    return I07Nexus(path_to_i07_nxs_01)


@pytest.fixture
def signal_regions_01():
    """
    Returns the list of signal regions recorded in i07_nexus_object_01.
    """
    return [Region(1208, 1208+50, 206, 206+18)]


@pytest.fixture
def bkg_regions_01():
    """
    Returns the list of signal regions recorded in i07_nexus_object_01.
    """
    return [Region(1258, 1258+50, 206, 206+18),
            Region(1208, 1208+50, 188, 188+18)]


@pytest.fixture
def scan2d_from_nxs_01(path_to_i07_nxs_01):
    """
    Uses the i07_nxs_parser to produce an instance of Scan2D from the given
    path.
    """
    return i07_nxs_parser(path_to_i07_nxs_01)


@pytest.fixture
def generic_data_01():
    """
    Constructs a generic, valid, Data instance.
    """
    # Some meaningless values.
    q_vecs = np.arange(10)/10
    intensities = np.arange(1100, 300, -45)[:10]

    # A realistic value (in keV)
    energy = 12.5

    return Data(intensities, np.sqrt(intensities), energy, q_vectors=q_vecs)


@pytest.fixture
def generic_data_02():
    """
    Constructs another random Data instance, this time initializing with theta
    rather than q.
    """
    # More meaningless values.
    theta = np.arange(6)
    intensities = np.arange(11100012, 0, -12938)[:6]

    # Cu k-alpha
    energy = 8.04

    return Data(intensities, np.sqrt(intensities), energy, theta)


@pytest.fixture
def measurement_base_01(path_to_i07_nxs_01, generic_data_01: Data):
    """
    Constructs a fairly meaningless instance of MeasurementBase to test against.
    This uses generic_data_01 to populate its data, and gets metadata by
    parsing a nxs file.
    """
    i07_nxs_metadata = I07Nexus(path_to_i07_nxs_01)
    return MeasurementBase(generic_data_01.intensity,
                           generic_data_01.intensity_e, generic_data_01.energy,
                           i07_nxs_metadata, q=generic_data_01._q)
