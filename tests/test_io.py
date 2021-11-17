"""
This file contains a suite of tests for the islatu.io module.
"""

# The following is necessary to use classes to share parameters using
# mark.parametrize.
# pylint: disable=no-self-use

# The following is necessary because of the dynamic nature of the nexusformat
# package's type generation.
# pylint: disable=no-member

# The following is to stop pylint from complaining about protected member tests.
# pylint: disable=protected-access

import pytest
import numpy as np
import nexusformat.nexus.tree as nx
from pytest_lazyfixture import lazy_fixture as lazy

from islatu.io import I07Nexus
from islatu.region import Region


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
    'nexus_base',
    [lazy('nexus_base_object_01'), lazy('i07_nexus_object_01')])
class TestNexusBasePaths:
    """
    Tests in this class ensure that we can properly parse paths stored within
    a .nxs file.
    """

    @pytest.mark.parametrize(
        'path',
        [
            lazy('path_to_i07_nxs_01'), lazy('path_to_i07_nxs_01')
        ]
    )
    def test_local_nxs_path(self, nexus_base, path):
        """
        Make sure that the local_nxs_paths of our nexus_base objects are
        correct.
        """
        assert nexus_base.local_nxs_path == path

    @pytest.mark.parametrize(
        'path',
        [
            '/dls/i07/data/2021/si28707-1/i07-404876.nxs',
            '/dls/i07/data/2021/si28707-1/i07-404876.nxs'
        ]
    )
    def test_src_nxs_path(self, nexus_base, path):
        """
        Checks that the parsed nxs path is correct. Worth noting that, when
        extending this test for more .nxs files, it's important to manually
        scrape the src_nxs_path by parsing nxfile.tree, unless you already know
        what value this will take (because, e.g., you just downloaded the file).
        """
        assert nexus_base.src_nxs_path == path


@pytest.mark.parametrize(
    'i07_nexus',
    [
        lazy('i07_nexus_object_01')
        # More fixtures should be added here.
    ]
)
class TestI07Nexus:
    """
    This class contains tests for the I07Nexus class.
    """
    @pytest.mark.parametrize(
        'path',
        [
            '/dls/i07/data/2021/si28707-1/excaliburScan404876_000001.h5',
        ]
    )
    def test_src_data_path(self, i07_nexus: I07Nexus, path):
        """
        Make sure we can properly find the path to where the data was originally
        stored, as referenced in the .nxs file. This is used to guess where the
        .h5 file is stored locally.
        """
        assert i07_nexus._src_data_path == path

    @pytest.mark.parametrize(
        'path',
        [
            lazy('path_to_i07_h5_01')
        ]
    )
    def test_local_data_path(self, i07_nexus: I07Nexus, path):
        """
        Tests our class' ability to find .h5 files stored locally. This test
        only makes sure that our class can find .h5 files that are stored in the
        same directory as the .nxs file. More directories are searched, but
        these are not tested (a test generating .h5 files throughout the
        directory structure would not be portable, and would merit tests of its
        own).
        """
        assert i07_nexus.local_data_path == path

    @pytest.mark.parametrize(
        'correct_num',
        [3]
    )
    def test_number_of_regions(self, i07_nexus: I07Nexus, correct_num):
        """
        Makes sure that we can correctly determine the number of regions of
        interest in the nexus file.
        """
        assert i07_nexus._number_of_regions == correct_num

    @pytest.mark.parametrize(
        'region_number, kind, result',
        [
            (1, 'x_1', 'Region_1_X'), (1, 'x_start', 'Region_1_X'),
            (17, 'Height', 'Region_17_Height'), (9917, 'y_1', 'Region_9917_Y'),
            (6, 'Width', 'Region_6_Width'), (4, 'y_start', 'Region_4_Y')
        ]
    )
    def test_region_bounds_keys(self, i07_nexus: I07Nexus,
                                region_number, kind, result):
        """
        Makes sure that region bounds keys are being generated correctly.
        """
        assert i07_nexus._get_region_bounds_key(region_number, kind) == result

    @pytest.mark.parametrize(
        'regions',
        [
            lazy('signal_regions_01')
        ]
    )
    def test_signal_regions_len(self, i07_nexus, regions):
        """
        Make sure our signal regions has the correct length.
        """
        assert len(i07_nexus.signal_regions) == len(regions)

    @pytest.mark.parametrize(
        'regions',
        [
            lazy('signal_regions_01')
        ]
    )
    def test_signal_regions(self, i07_nexus: I07Nexus, regions):
        """
        Tests the I07Nexus class' ability to parse signal regions of interest.
        """
        # Note: this should probably always be a for loop with just 1 iteration.
        for i, _ in enumerate(regions):
            assert i07_nexus.signal_regions[i] == regions[i]

    @pytest.mark.parametrize(
        'regions',
        [
            lazy('bkg_regions_01')
        ]
    )
    def test_bkg_regions_len(self, i07_nexus: I07Nexus, regions):
        """
        Makes sure that we can extract background regions from an I07 nexus
        file.
        """
        assert len(i07_nexus.background_regions) == len(regions)

    @pytest.mark.parametrize(
        'regions',
        [
            lazy('bkg_regions_01')
        ]
    )
    def test_bkg_regions(self, i07_nexus: I07Nexus, regions):
        """
        Makes sure that we can extract background regions from an I07 nexus
        file.
        """
        for i, _ in enumerate(regions):
            assert i07_nexus.background_regions[i] == regions[i]

    @pytest.mark.parametrize(
        'transmission',
        [0.000448426658633058]
    )
    def test_transmission(self, i07_nexus: I07Nexus, transmission):
        """
        Make sure we can correctly parse the transmission coefficient.
        """
        assert i07_nexus.transmission == transmission

    @pytest.mark.parametrize(
        'probe_energy',
        [12.5]
    )
    def test_probe_energy(self, i07_nexus: I07Nexus, probe_energy):
        """
        Make sure we can extract the energy of the probe particle from the .nxs
        file.
        """
        assert i07_nexus.probe_energy == probe_energy

    @pytest.mark.parametrize(
        'detector_distance',
        [1.1155]
    )
    def test_detector_distance(self, i07_nexus: I07Nexus, detector_distance):
        """
        Make sure that we can extract the detector distance from the .nxs file.
        """
        assert i07_nexus.detector_distance == detector_distance

    @pytest.mark.parametrize(
        'description',
        ['q']
    )
    def test_default_axis_description(self, i07_nexus: I07Nexus, description):
        """
        Make sure that we are correctly identifying the kind of axis data
        stored in the nexus file.
        """
        assert i07_nexus.default_axis_description == description


@pytest.mark.parametrize(
    'i, ith_region',
    [
        (1, Region(1208, 1208+50, 206, 206+18)),
        (2, Region(1258, 1258+50, 206, 206+18)),
        (3, Region(1208, 1208+50, 188, 188+18))
    ]
)
def test_ith_region_nxs_01(i07_nexus_object_01: I07Nexus,
                           i, ith_region):
    """
    Make sure that we can extract the ith region from i07_nexus_object_01.
    """
    assert i07_nexus_object_01.get_ith_region(i) == ith_region
