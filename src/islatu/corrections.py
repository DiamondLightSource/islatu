"""
Reflectometry data must be corrected as a part of reduction.
These functions facilitate this, including the footprint and
DCD q-variance corrections.
"""


import numpy as np
from scipy.stats import norm
from scipy.interpolate import splrep


def footprint_correction(beam_width, sample_size, theta):
    """
    The factor by which the intensity should be multiplied to account for the
    scattering geometry, where the beam is Gaussian in shape.

    Args:
        beam_width (:py:attr:`float`):
            Width of incident beam, in metres.
        sample_size (:py:attr:`float`):
            Width of sample in the dimension of the beam, in metres.
        theta (:py:attr:`float`):
            Incident angle, in degrees.

    Returns:
        Array of correction factors.
    """
    # Deal with the [trivial] theta=0 case.
    theta = np.array([10**(-3) if t == 0 else t for t in theta])

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
