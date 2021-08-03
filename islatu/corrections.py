"""
Reflectometry data must be corrected as a part of reduction.
These functions facilitate this, including the footprint and
DCD q-variance corrections.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

import numpy as np
from scipy.stats import norm
from scipy.interpolate import splrep
from uncertainties import unumpy as unp


def footprint_correction(beam_width, sample_size, theta):
    """
    The factor by which the intensity should be multiplied to account for the
    scattering geometry, where the beam is Gaussian in shape.

    Args:
        beam_width (:py:attr:`float`): Width of incident beam, in metres.
        sample_size (:py:class:`uncertainties.core.Variable`): Width of sample
            in the dimension of the beam, in metres.
        theta (:py:attr:`float`): Incident angle, in degrees.

    Returns:
        (:py:class:`uncertainties.core.Variable`): Correction factor.
    """
    # The footprint correction is just a number. It doesn't make sense to think
    # of uncertainties in sample size or theta, we just want to calculate our
    # best estimate of the footprint correction.
    theta = unp.nominal_values(theta)
    sample_size = unp.nominal_values(sample_size)

    # Deal with [the trivial point] theta being exactly 0.
    for i in range(len(theta)):
        if theta[i] == 0:
            # The footprint correction for theta=0 is infinite, so just choose
            # a small value. Theta=0 data is trivial anyway.
            theta[i] = 1 * 10**(-3)

    beam_sd = beam_width / 2 / np.sqrt(2 * np.log(2))
    projected_beam_sd = beam_sd / np.sin(np.radians(theta))
    frac_of_beam_sampled = (
        norm.cdf(sample_size/2, 0, projected_beam_sd) -
        norm.cdf(-sample_size/2, 0, projected_beam_sd)
    )
    return frac_of_beam_sampled


def get_interpolator(
        file_path, parser, q_axis_name="qdcd_", intensity_axis_name="adc2"):
    """
    Get an interpolator object from scipy, this is useful for the DCD
    q-normalisation step.

    Args:
        file_path (:py:attr:`str`): File path to the normalisation file.
        parser (:py:attr:`callable`): Parser function for the normalisation
            file.
        q_axis_name (:py:attr:`str`, optional): Label for the q-value in the
            normalisation file. Defaults to ``'qdcd_'``.
        intensity_axis_name (:py:attr:`str`, optional): Label for the
            intensity in the normalisation file. Defaults to ``'adc2'``.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`array_like`: Interpolation knots.
            - :py:attr:`array_like`: B-spline coefficients.
            - :py:attr:`int`: Degree of spline.
    """
    normalisation_data = parser(file_path)[1]
    return splrep(
        normalisation_data[q_axis_name],
        normalisation_data[intensity_axis_name])
