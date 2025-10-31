"""
This module contains fixture definitions used when testing the islatu module.
"""

# The following pylint rule is, unfortunately, necessary due to how pytest works
# with fixtures. Consequently, all fixtures are defined in this file so that
# redefined-outer-name only needs to be disabled once.
# pylint: disable=redefined-outer-name

# We need to test protected members too.
# pylint: disable=protected-access

import os
import pytest
import numpy as np
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from yaml import load, dump
from islatu.io import I07Nexus, i07_nxs_parser, i07_dat_to_dict_dataframe
from islatu.corrections import get_interpolator
from islatu.data import Data, MeasurementBase
from islatu.region import Region
from islatu.refl_profile import Profile


@pytest.fixture
def path_to_resources():
    """
    Returns the path to the resources folder.
    """
    if os.path.isdir("resources"):
        return "resources" + os.sep
    if os.path.isdir("tests") and os.path.isdir("src"):
        return "tests" + os.sep + "resources" + os.sep
    raise FileNotFoundError(
        "Couldn't locate the tests/resources directory. Make sure that " +
        "the pytest command is run from within the base islatu directory" +
        ", or from within the tests directory."
    )


@pytest.fixture
def path_to_i07_nxs_01(path_to_resources):
    """
    Returns the path to an i07 nexus file. If it can't be found, raises.
    """
    return os.path.join(path_to_resources, "i07-404876.nxs")


@pytest.fixture
def path_to_i07_nxs_02(path_to_resources):
    """
    Returns the path to a second i07 nexus file. If it cant be found, raises.
    """
    return os.path.join(path_to_resources, "i07-404877.nxs")

@pytest.fixture
def path_to_yaml(path_to_resources):
    """
    returns the path to the example yaml file. 
    """
    return os.path.join(path_to_resources,"dcd.yaml")

@pytest.fixture
def example_recipe_dcd_01(path_to_yaml):

    with open(path_to_yaml, 'r', encoding='utf-8') as y_file:
        recipe = load(y_file, Loader=Loader)
    return recipe

@pytest.fixture
def path_to_dcd_normalisation_01(path_to_resources):
    """
    Returns the path to the qdcd normalisation file corresponding to i07_nxs_01.
    """
    return os.path.join(path_to_resources, "404863.dat")


@pytest.fixture
def parsed_dcd_normalisation_01(path_to_dcd_normalisation_01):
    """
    Returns the ([metadata] dict, [data] dataframe) relating to the first
    dcd normalisation file.
    """
    return i07_dat_to_dict_dataframe(path_to_dcd_normalisation_01)


@pytest.fixture
def dcd_norm_01_splev(path_to_dcd_normalisation_01):
    """
    Returns the scipy splev corresponding to the first dcd normalisation file.
    """
    return get_interpolator(path_to_dcd_normalisation_01,
                            i07_dat_to_dict_dataframe)


@pytest.fixture
def path_to_i07_h5_01(path_to_resources):
    """
    Returns the path to an i07 h5 file. If it can't be found, raises.
    """
    return os.path.join(path_to_resources, "excaliburScan404876_000001.h5")


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
def custom_bkg_region_01():
    """
    Returns a decent background regions, specifically chosen for scan_01.
    """
    return Region(1340, 1420, 220, 300)


@pytest.fixture
def scan2d_from_nxs_01(path_to_i07_nxs_01):
    """
    Uses the i07_nxs_parser to produce an instance of Scan2D from the given
    path.
    """
    return i07_nxs_parser(path_to_i07_nxs_01)


@pytest.fixture
def scan2d_from_nxs_01_copy(path_to_i07_nxs_01):
    """
    An exact copy of the above Scan2D instance. Useful to have in some tests.
    """
    return i07_nxs_parser(path_to_i07_nxs_01)


@pytest.fixture
def scan_02(path_to_i07_nxs_02):
    """
    Returns another scan at higher q.
    """
    return i07_nxs_parser(path_to_i07_nxs_02)


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


@pytest.fixture
def region_01():
    """
    Returns a fairly generic instance of islatu.region's Region class.
    """
    return Region(x_start=1056, x_end=1124, y_start=150, y_end=250)

@pytest.fixture
def region_02():
    """
    Returns a fairly generic instance of islatu.region's Region class, but loaded from dict 
    """
    return Region.from_dict({'x': 1056, 'width': 1124-1056, 'y': 150, 'height': 250-150})
    


@pytest.fixture
def profile_01(path_to_i07_nxs_01):
    """
    Returns an instance of the Profile class that containts just scan_01.
    """
    return Profile.fromfilenames([path_to_i07_nxs_01], i07_nxs_parser)


@pytest.fixture
def profile_0102(path_to_i07_nxs_01, path_to_i07_nxs_02):
    """
    Returns an instance of the Profile class that contains scan_01 and scan_02.
    """
    return Profile.fromfilenames([path_to_i07_nxs_01, path_to_i07_nxs_02],
                                 i07_nxs_parser)


@pytest.fixture
def old_dcd_data(path_to_resources):
    """
    Returns a np.ndarray of the data as processed by islatu prior to a
    substantial refactor. This old DCD data was confirmed to be correctly
    reduced by beamline staff.
    """
    return np.loadtxt(os.path.join(
        path_to_resources, "XRR_404875_dcd_template2021-11-01_15h35m02s.dat"))


@pytest.fixture
def process_xrr_path(path_to_resources):
    """
    Uses relative pathfinding to return a valid path to process_xrr.py
    """
    return os.path.join(
        path_to_resources, '../../CLI/process_xrr.py'
    )
