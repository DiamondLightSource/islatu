"""
This module tests the islatu.refl_profile module's Profile class .
"""

import numpy as np
from islatu.background import roi_subtraction
from islatu.cropping import crop_to_region
from islatu.refl_profile import Profile
from islatu.scan import Scan2D
from numpy.testing import assert_allclose


def test_profile_data(profile_01: Profile, scan2d_from_nxs_01: Scan2D):
    """
    Make sure that our profile has exactly the same q_vectors as its scan,
    intensities, intensity_e's, etc.
    """
    assert profile_01.energy == scan2d_from_nxs_01.energy
    assert (profile_01.intensity == scan2d_from_nxs_01.intensity).all()
    assert (profile_01.intensity_e == scan2d_from_nxs_01.intensity_e).all()

    assert_allclose(profile_01.q_vectors, scan2d_from_nxs_01.q_vectors, 1e-5)
    assert_allclose(profile_01.theta, scan2d_from_nxs_01.theta, 1e-5)


def test_profile_crop(profile_01: Profile):
    """
    Make sure that the profile's crop method crops its constituent scans'
    images.
    """
    region = profile_01.scans[0].metadata.signal_regions[0]
    profile_01.crop(crop_to_region, region=region)


def test_profile_bkg_sub(profile_01: Profile, scan2d_from_nxs_01: Scan2D):
    """
    Make sure that bkg_sub from the profile is the same as bkg_sub from the
    scan.
    """
    bkg_region = scan2d_from_nxs_01.metadata.background_regions[0]
    profile_01.bkg_sub(roi_subtraction, list_of_regions=[bkg_region])
    scan2d_from_nxs_01.bkg_sub(roi_subtraction, list_of_regions=[bkg_region])

    assert_allclose(profile_01.intensity_e, scan2d_from_nxs_01.intensity_e, 1e-4)
    assert_allclose(profile_01.intensity, scan2d_from_nxs_01.intensity, 1e-4)


def test_profile_subsample_q_01(profile_01: Profile):
    """
    Make sure subsample_q deletes the appropriate things. Because it just calls
    remove_data_points, which has already been tested extensively in test_data,
    we only need to check a couple of values to make sure the right qs have been
    deleted an we know that all the other attributes will have been handled
    correctly.
    """
    original_len = len(profile_01.scans[0].theta)
    # Defaults shouldn't change anything.
    profile_01.subsample_q("404876")
    assert len(profile_01.scans[0].theta) == original_len
    assert len(profile_01.theta) == original_len


def test_subsample_q_02(profile_01: Profile):
    """
    Make sure that we can set just an upper bound. Note that this dataset goes
    from 0.025Å to 0.06Å
    """
    q_max = 0.04

    assert max(profile_01.q_vectors) > q_max
    assert max(profile_01.scans[0].q_vectors) > q_max
    profile_01.subsample_q("404876", q_max=q_max)
    assert max(profile_01.q_vectors) <= q_max
    assert max(profile_01.scans[0].q_vectors) <= q_max


def test_subsample_q_03(profile_01: Profile):
    """
    Make sure that we can set a lower bound. Note that this dataset goes from
    0.025Å to 0.06Å.
    """
    q_min = 0.04

    assert min(profile_01.q_vectors) < q_min
    assert min(profile_01.scans[0].q_vectors) < q_min
    profile_01.subsample_q("404876", q_min=q_min)
    assert min(profile_01.q_vectors) >= q_min
    assert min(profile_01.scans[0].q_vectors) >= q_min


def test_subsample_q_04(profile_01: Profile):
    """
    Test that we can set both lower and upper bounds.
    """
    q_min = 0.032
    q_max = 0.051

    profile_01.subsample_q("404876", q_min, q_max)

    assert min(profile_01.q_vectors) >= q_min
    assert max(profile_01.q_vectors) <= q_max


def test_profile_footprint_correction(profile_01: Profile, scan2d_from_nxs_01):
    """
    Assert that calling the footprint_correction method in an instance of
    Profile is the same thing as calling it in all of its constituent Scans.
    Then, if the Scan footprint correction tests pass, then this must also
    work.
    """
    beam_width = 100e-6
    sample_size = 1e-3

    profile_01.footprint_correction(beam_width, sample_size)
    scan2d_from_nxs_01.footprint_correction(beam_width, sample_size)

    assert_allclose(profile_01.intensity, scan2d_from_nxs_01.intensity)
    assert_allclose(profile_01.intensity_e, profile_01.intensity_e)


def test_profile_transmission_normalisation(
    profile_01: Profile, scan2d_from_nxs_01: Scan2D
):
    """
    Assert that carrying out a transmission normalisation on an instance of
    Profile is the same thing as doing it on each of its constituent scans.
    """
    profile_01.transmission_normalisation()
    scan2d_from_nxs_01.transmission_normalisation()

    assert_allclose(profile_01.intensity, scan2d_from_nxs_01.intensity)
    assert_allclose(profile_01.intensity_e, profile_01.intensity_e)


def test_profile_qdcd_normalisation(
    profile_01: Profile, scan2d_from_nxs_01: Scan2D, dcd_norm_01_splev
):
    """
    Assert that carrying out the qdcd correction on an instance of Profile is
    the same thing as doing it on each of its constituent scans.
    """
    profile_01.qdcd_normalisation(dcd_norm_01_splev)
    scan2d_from_nxs_01.qdcd_normalisation(dcd_norm_01_splev)

    assert_allclose(profile_01.intensity, scan2d_from_nxs_01.intensity)
    assert_allclose(profile_01.intensity_e, profile_01.intensity_e)


def test_concatenate(profile_01: Profile):
    """
    Explicit simple check that concatenate is working. Note that, if it isn't
    working, many other tests would also raise.
    """
    profile_01.scans[0].intensity = 0
    profile_01.concatenate()

    assert profile_01.intensity == 0


def test_rebin_01(profile_0102: Profile):
    """
    Make sure that we can rebin the data using default parameters.
    """
    initial_length = len(profile_0102.q_vectors)
    profile_0102.rebin()
    assert initial_length > len(profile_0102.q_vectors)


def test_rebin_02(profile_0102: Profile):
    """
    Now that we know that rebin is doing something, lets make sure that it is
    doing sane things.
    """

    init = np.copy(profile_0102.intensity)

    profile_0102.rebin()

    new = profile_0102.intensity

    big, small = (init[3], init[8]) if init[3] > init[8] else init[8], init[3]
    assert small < new[3] and big > new[3]
