"""
The corrections module for the islatu pipeline
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey

from scipy.stats import norm
from uncertainties import unumpy as unp


def geometry_correction(beam_width, sample_size, theta):
    """
    Factor by which intensity should be multiplied in the area correction.

    Args:
        beam_width (float): Width of incident beam.
        sample_size (ufloat): Width of sample.
        theta (float): Incident angle.

    Returns:
        (ufloat): Correction factor.
    """
    beam = norm(loc=0, scale=beam_width / 2)
    ts = sample_size * unp.sin(unp.radians(theta)) / 2
    uncertainty = beam.cdf(
        unp.nominal_values(ts) + unp.std_devs(ts)
    ) - beam.cdf(unp.nominal_values(ts) - unp.std_devs(ts))
    return unp.uarray(beam.cdf(unp.nominal_values(ts)), uncertainty / 2)
