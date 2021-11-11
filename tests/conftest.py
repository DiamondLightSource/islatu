"""
This module contains fixture definitions used when testing the islatu module.
"""

# The following pylint rule is, unfortunately, necessary due to how pytest works
# with fixtures. Consequently, all fixtures are defined in this file so that
# redefined-outer-name only needs to be disabled once.
# pylint: disable=redefined-outer-name

import os
import pytest

from islatu.io import I07Nexus


@pytest.fixture
def path_to_i07_nxs_01():
    """
    Returns the path to an i07 nexus file. If it can't be found, raises.
    """
    path_from_tests_dir = os.path.join("resources", "i07-404875.nxs")
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
