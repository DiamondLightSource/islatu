"""
This module tests the central islatu.scan module's Scan and Scan2D classes .
"""

import numpy as np
import pytest
from islatu.background import fit_gaussian_1d, roi_subtraction
from islatu.cropping import crop_to_region
from islatu.region import Region
from islatu.scan import Scan2D
from pytest_lazyfixture import lazy_fixture as lazy
from scipy.interpolate import interp1d


def test_subsample_q_01(scan2d_from_nxs_01: Scan2D):
    """
    Make sure subsample_q deletes the appropriate things. Because it just calls
    remove_data_points, which has already been tested extensively in test_data,
    we only need to check a couple of values to make sure the right qs have been
    deleted an we know that all the other attributes will have been handled
    correctly.
    """
    original_len = len(scan2d_from_nxs_01.theta)
    # Defaults shouldn't change anything.
    scan2d_from_nxs_01.subsample_q()
    assert len(scan2d_from_nxs_01.theta) == original_len


def test_subsample_q_02(scan2d_from_nxs_01: Scan2D):
    """
    Make sure that we can set just an upper bound. Note that this dataset goes
    from 0.025Å to 0.06Å
    """
    q_max = 0.04

    assert max(scan2d_from_nxs_01.q_vectors) > q_max
    scan2d_from_nxs_01.subsample_q(q_max=q_max)
    assert max(scan2d_from_nxs_01.q_vectors) <= q_max


def test_subsample_q_03(scan2d_from_nxs_01: Scan2D):
    """
    Make sure that we can set a lower bound. Note that this dataset goes from
    0.025Å to 0.06Å.
    """
    q_min = 0.04

    assert min(scan2d_from_nxs_01.q_vectors) < q_min
    scan2d_from_nxs_01.subsample_q(q_min=q_min)
    assert min(scan2d_from_nxs_01.q_vectors) >= q_min


def test_subsample_q_04(scan2d_from_nxs_01: Scan2D):
    """
    Test that we can set both lower and upper bounds.
    """
    q_min = 0.032
    q_max = 0.051

    scan2d_from_nxs_01.subsample_q(q_min, q_max)

    assert min(scan2d_from_nxs_01.q_vectors) >= q_min
    assert max(scan2d_from_nxs_01.q_vectors) <= q_max


@pytest.mark.parametrize(
    "scan, transmission", [(lazy("scan2d_from_nxs_01"), 0.000448426658633058)]
)
def test_transmission_normalisation_intensities(scan: Scan2D, transmission):
    """
    Make sure that we can correct for the attenuation of the beam. The
    transmission values have been manually read from the .nxs file using a GUI.
    """
    intensity_0 = np.copy(scan.intensity)
    scan.transmission_normalisation()

    for i, intensity in enumerate(scan.intensity):
        assert intensity == intensity_0[i] / transmission


@pytest.mark.parametrize(
    "scan, transmission", [(lazy("scan2d_from_nxs_01"), 0.000448426658633058)]
)
def test_transmission_normalisation_errors(scan: Scan2D, transmission):
    """
    Make sure that we can correct for the attenuation of the beam. The
    transmission values have been manually read from the .nxs file using a GUI.
    This function checks the intensity_e values have been dealt with properly.
    """
    intensity_e_0 = np.copy(scan.intensity_e)
    scan.transmission_normalisation()

    for i, intensity_e in enumerate(scan.intensity_e):
        assert intensity_e == intensity_e_0[i] / transmission


def test_qdcd_name_assumes(parsed_dcd_normalisation_01):
    """
    Takes a parsed DCD normalisation pandas dataframe and makes sure that
    we can find the qdcd data, which is [in]conveniently called qdcd_.
    """
    _, dataframe = parsed_dcd_normalisation_01
    assert "qdcd_" in dataframe
    assert "adc2" in dataframe


def test_qdcd_normalisation_01(scan2d_from_nxs_01: Scan2D, dcd_norm_01_splev):
    """
    Make sure that our qdcd normalisation is doing something, and isn't failing
    silently. (This is a dumb test, but it's really quite hard to test that
    this is working without just rewriting a division by splev).
    """
    intensities_0 = np.copy(scan2d_from_nxs_01.intensity)
    intensities_e_0 = np.copy(scan2d_from_nxs_01.intensity_e)

    scan2d_from_nxs_01.qdcd_normalisation(dcd_norm_01_splev)

    assert (intensities_0 != scan2d_from_nxs_01.intensity).all()
    assert (intensities_e_0 != scan2d_from_nxs_01.intensity_e).all()


def test_qdcd_normalisation_02(
    scan2d_from_nxs_01: Scan2D, dcd_norm_01_splev, parsed_dcd_normalisation_01
):
    """
    Make sure that our nice splev normalisation does something similar to what
    would be achieved using a simple cubic scipy.interpolate.interp1D.
    """

    # First, generate some test intensities by dividing by an interp1D function.
    intensities_0 = np.copy(scan2d_from_nxs_01.intensity)
    intensities_e_0 = np.copy(scan2d_from_nxs_01.intensity_e)

    _, dataframe = parsed_dcd_normalisation_01

    interp = interp1d(dataframe["qdcd_"], dataframe["adc2"], kind="cubic")

    test_intensities = intensities_0 / interp(scan2d_from_nxs_01.q_vectors)
    test_intensities_e = intensities_e_0 / interp(scan2d_from_nxs_01.q_vectors)

    # Now, carry out the qdcd normalisation as normal.
    scan2d_from_nxs_01.qdcd_normalisation(dcd_norm_01_splev)

    # These interpolation methods could be decently different, but lets enforce
    # that our values are the same to within 1%.
    for i, test_intensity in enumerate(test_intensities):
        assert test_intensity == pytest.approx(
            scan2d_from_nxs_01.intensity[i], rel=0.01
        )

    for i, test_inten_e in enumerate(test_intensities_e):
        assert test_inten_e == pytest.approx(
            scan2d_from_nxs_01.intensity_e[i], rel=0.01
        )


def test_footprint_correction_01(scan2d_from_nxs_01: Scan2D):
    """
    Makes sure that the footprint correction acually does something for a
    reasonable beam FWHM and a small (1mm) sample.
    """
    # 100 micron beam.
    beam_width = 100e-6
    # 1 mm sample.
    sample_size = 1e-3
    intensities_0 = np.copy(scan2d_from_nxs_01.intensity)
    intensities_e_0 = np.copy(scan2d_from_nxs_01.intensity_e)
    scan2d_from_nxs_01.footprint_correction(beam_width, sample_size)

    assert (intensities_0 != scan2d_from_nxs_01.intensity).all()
    assert (intensities_e_0 != scan2d_from_nxs_01.intensity_e).all()


def test_footprint_correction_02(scan2d_from_nxs_01: Scan2D):
    """
    Do a really naive footprint correction assuming a step function beam.
    Enforce that this is the same as our fancy correction, to within 10%.
    (Note: they are actually about 10% out from each other).
    """

    # 100 micron beam.
    beam_width = 100e-6
    # 1 mm sample.
    sample_size = 1e-3

    intensities_0 = np.copy(scan2d_from_nxs_01.intensity)
    intensities_e_0 = np.copy(scan2d_from_nxs_01.intensity_e)

    beam_size_on_sample = beam_width / np.sin(np.radians(scan2d_from_nxs_01.theta))

    incident_beam_fraction = sample_size / beam_size_on_sample

    test_intensities = intensities_0 / incident_beam_fraction
    test_intensities_e = intensities_e_0 / incident_beam_fraction

    scan2d_from_nxs_01.footprint_correction(beam_width, sample_size)
    for i, test_intensity in enumerate(test_intensities):
        assert test_intensity == pytest.approx(scan2d_from_nxs_01.intensity[i], 0.1)

    for i, test_intensity_e in enumerate(test_intensities_e):
        assert test_intensity_e == pytest.approx(scan2d_from_nxs_01.intensity_e[i], 0.1)


def test_crop_01(scan2d_from_nxs_01: Scan2D, region_01):
    """
    Check that crop is decreasing the size of the image.
    """
    initial_shape = scan2d_from_nxs_01.images[0].shape
    scan2d_from_nxs_01.crop(crop_to_region, region=region_01)

    assert scan2d_from_nxs_01.images[0].shape[0] < initial_shape[0]
    assert scan2d_from_nxs_01.images[0].shape[1] < initial_shape[1]


def test_crop_02(scan2d_from_nxs_01: Scan2D, region_01: Region):
    """
    Make sure that our cropped region has the correct size.
    """
    scan2d_from_nxs_01.crop(crop_to_region, region=region_01)
    assert (
        scan2d_from_nxs_01.images[0].shape[0] * scan2d_from_nxs_01.images[0].shape[1]
    ) == region_01.num_pixels


def test_crop_03(scan2d_from_nxs_01: Scan2D, region_01: Region):
    """
    Make sure that the region we've cropped to has the specified shape.
    """
    scan2d_from_nxs_01.crop(crop_to_region, region=region_01)
    assert scan2d_from_nxs_01.images[0].shape[0] == region_01.y_length
    assert scan2d_from_nxs_01.images[0].shape[1] == region_01.x_length


def test_bkg_sub_01(scan2d_from_nxs_01: Scan2D):
    """
    Make sure that we start out with no background.
    """
    assert scan2d_from_nxs_01.images[0].bkg == 0
    assert scan2d_from_nxs_01.images[0].bkg_e == 0


def test_bkg_sub_02(scan2d_from_nxs_01: Scan2D):
    """
    Make sure that the background subtraction function is doing something.
    """
    region_list = scan2d_from_nxs_01.metadata.background_regions
    scan2d_from_nxs_01.bkg_sub(roi_subtraction, list_of_regions=region_list)

    assert scan2d_from_nxs_01.images[0].bkg != 0
    assert scan2d_from_nxs_01.images[0].bkg_e != 0


def test_bkg_sub_03(scan2d_from_nxs_01: Scan2D):
    """
    Make sure that the background subtraction decreases our intensity.
    """
    vals, stdevs = (
        np.zeros(len(scan2d_from_nxs_01.intensity)),
        np.zeros(len(scan2d_from_nxs_01.intensity)),
    )

    # Also update the image intensities & errors.
    for i, image in enumerate(scan2d_from_nxs_01.images):
        vals[i], stdevs[i] = image.sum()

    # Store the intensity(Q) to the new value.
    scan2d_from_nxs_01.intensity = np.array(vals)
    scan2d_from_nxs_01.intensity_e = np.array(stdevs)

    region_list = scan2d_from_nxs_01.metadata.background_regions
    scan2d_from_nxs_01.bkg_sub(roi_subtraction, list_of_regions=region_list)

    assert (vals > scan2d_from_nxs_01.intensity).all()


def test_bkg_sub_04(
    scan2d_from_nxs_01: Scan2D, scan2d_from_nxs_01_copy, custom_bkg_region_01
):
    """
    Make sure that using two background regions yields a lower uncertainty
    measurement of the background than using just one background region.
    """
    regions_1 = [scan2d_from_nxs_01.metadata.background_regions[0]]
    regions_2 = [scan2d_from_nxs_01.metadata.background_regions[0]] + [
        custom_bkg_region_01
    ]
    scan2d_from_nxs_01.bkg_sub(roi_subtraction, list_of_regions=regions_1)
    scan2d_from_nxs_01_copy.bkg_sub(roi_subtraction, list_of_regions=regions_2)

    for i, image_1 in enumerate(scan2d_from_nxs_01.images):
        image_2 = scan2d_from_nxs_01_copy.images[i]
        assert image_1.bkg_e > image_2.bkg_e


def test_gauss_bkg_01(scan2d_from_nxs_01: Scan2D):
    """
    Make sure that our Gaussian fit background subtraction function is doing
    something.

    Note that this function is not being tested for sensible results because
    this doesn't generally seem to be a sensible technique to use on I07. As
    more instruments are supported, if this technique becomes useful, its
    tests will need to be extended. For now, only the minimum is being done
    to ensure that it is roughly functional.
    """
    scan2d_from_nxs_01.bkg_sub(fit_gaussian_1d)

    assert scan2d_from_nxs_01.images[0].bkg != 0
    assert scan2d_from_nxs_01.images[0].bkg_e != 0


def test_gauss_bkg_02(scan2d_from_nxs_01: Scan2D):
    """
    Make sure that carrying out this subtraction decreases our intensity.

    Note that this function is not being tested for sensible results because
    this doesn't generally seem to be a sensible technique to use on I07. As
    more instruments are supported, if this technique becomes useful, its
    tests will need to be extended. For now, only the minimum is being done
    to ensure that it is roughly functional.
    """
    vals = np.zeros(len(scan2d_from_nxs_01.intensity))
    # Also update the image intensities & errors.
    for i, image in enumerate(scan2d_from_nxs_01.images):
        vals[i], _ = image.sum()
    # Store the intensity(Q) to the new value.
    scan2d_from_nxs_01.intensity = np.array(vals)

    intensity_0 = np.copy(scan2d_from_nxs_01.intensity)
    scan2d_from_nxs_01.bkg_sub(fit_gaussian_1d)

    assert (scan2d_from_nxs_01.intensity < intensity_0).all()
