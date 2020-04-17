"""
Corrections to be performed on the reflectometry data.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)

import numpy as np
from scipy.stats import norm
from uncertainties import unumpy as unp


def footprint_correction(beam_width, sample_size, theta):
    """
    The factor by which the intensity should be multiplied to account for the
    scattering geometry, where the beam is Gaussian in shape.

    Args:
        beam_width (float): Width of incident beam, in metres.
        sample_size (uncertainties.core.Variable): Width of sample in the
            dimension of the beam, in metres.
        theta (float): Incident angle, in degrees.

    Returns:
        (uncertainties.core.Variable): Correction factor.
    """
    beam_sd = beam_width / 2 / np.sqrt(2 * np.log(2))
    length = sample_size * unp.sin(unp.radians(theta))
    mid = unp.nominal_values(length) / 2.0 / beam_sd
    upper = (unp.nominal_values(length) + unp.std_devs(length)) / 2.0 / beam_sd
    lower = (unp.nominal_values(length) - unp.std_devs(length)) / 2.0 / beam_sd
    probability = 2.0 * (
        unp.uarray(norm.cdf(mid), (norm.cdf(upper) - norm.cdf(lower)) / 2)
        - 0.5
    )
    return probability
