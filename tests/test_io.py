"""
This file contains a suite of tests for the islatu.io module.
"""

# The following is necessary to use classes to share parameters using
# mark.parametrize.
# pylint: disable=no-self-use

# The following is necessary because of the dynamic nature of the nexusformat
# package's type generation.
# pylint: disable=no-member

import pytest
import numpy as np
import nexusformat.nexus.tree as nx
from pytest_lazyfixture import lazy_fixture as lazy


@pytest.mark.parametrize(
    'nexus_base',
    [lazy('nexus_base_object_01'), lazy('i07_nexus_object_01')])
class TestNexusBaseAttrTypes:
    """
    This class checks that the types of each of the fixtures that inherits from
    NexusBase have attributes whose types are correct, and that can be accessed
    without raising e.g. a ValueError (as would happen if assumptions relating
    to the structure of the nexus file are broken).
    """

    def test_local_nxs_path(self, nexus_base):
        """
        Make sure that we can access the local_nxs_path.
        """
        assert isinstance(nexus_base.local_nxs_path, str)

    def test_nxfile(self, nexus_base):
        """
        Makes sure that our nxfile has the correct type.
        """
        assert isinstance(nexus_base.nxfile, nx.NXroot)

    def test_src_nexus_path(self, nexus_base):
        """
        Makes sure that our src_nexus_path can be acquired. Also make sure that
        it isn't an empty string.
        """
        assert isinstance(nexus_base.src_nxs_path, str)
        assert len(nexus_base.src_nxs_path) != 0

    def test_entry(self, nexus_base):
        """
        Makes sure that there is only one entry in the nexus_base. Otherwise, a
        ValueError will be thrown. This also tests that the entry has the
        correct type.
        """
        assert isinstance(nexus_base.entry, nx.NXentry)

    def test_instrument(self, nexus_base):
        """
        Makes sure that we can access the instrument property without throwing,
        and that our instrument has the correct type.
        """
        assert isinstance(nexus_base.instrument, nx.NXinstrument)

    def test_detector(self, nexus_base):
        """
        Makes sure that we can access the detector property of our nexus_base
        without throwing anything, and that it has the correct type.
        """
        assert isinstance(nexus_base.detector, nx.NXdetector)

    def test_default_axis_nxdata(self, nexus_base):
        """
        Makes sure that our default axis is provided as a numpy array.
        """
        assert isinstance(nexus_base.default_axis, np.ndarray)

    def test_default_signal_nxdata(self, nexus_base):
        """
        Make sure that we can access our default signal, and that its type is
        np.ndarray.
        """
        assert isinstance(nexus_base.default_signal, np.ndarray)


@pytest.mark.parametrize(
    'nexus_base,path',
    [
        (lazy('nexus_base_object_01'), lazy('path_to_i07_nxs_01')),
        (lazy('i07_nexus_object_01'), lazy('path_to_i07_nxs_01'))
    ]
)
def test_nexusbase_local_nxs_path_name(nexus_base, path):
    """
    Make sure that the local_nxs_paths of our nexus_base objects are correct.
    """
    assert nexus_base.local_nxs_path == path


@pytest.mark.parametrize(
    'nexus_base,path',
    [
        (lazy('nexus_base_object_01'),
         '/dls/i07/data/2021/si28707-1/i07-404875.nxs'),
        (lazy('i07_nexus_object_01'),
         '/dls/i07/data/2021/si28707-1/i07-404875.nxs')
    ]
)
def test_nexusbase_src_nxs_path(nexus_base, path):
    """
    Checks that the parsed nxs path is correct. Worth noting that, when
    extending this test for more .nxs files, it's important to manually scrape
    the src_nxs_path by parsing nxfile.tree, unless you already know what value
    this will take (because, e.g., you just downloaded the file).
    """
    assert nexus_base.src_nxs_path == path
