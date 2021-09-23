"""
Background substraction is a necessary component of reflectometry reduction,
where the background scattering is removed from the reflected intensity.

Herein are some functions to enable that for a two-dimensional detector image.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey (andrew.mccluskey@diamond.ac.uk)
# pylint: disable=R0913,C0103

import numpy as np
from scipy.stats import multivariate_normal, norm
from scipy.optimize import curve_fit


def univariate_normal(data, mu, sigma, offset, factor):
    """
    Produce a univariate normal distribution.

    Args:
        data (:py:attr:`array_like`): Abscissa data.
        mu (:py:attr:`float`): Mean (horizontal).
        sigma (:py:attr:`float`): Variance (horizontal).
        offset (:py:attr:`float`): Offset from the 0 for the ordinate, this is
            the background level.
        factor (:py:attr:`float`): Multiplicative factor for area of normal
            distribution.

    Returns:
        :py:attr:`array_like`: Ordinate data for univariate normal distribution.
    """
    # Creation of the bivariate normal distribution
    normal = norm(loc=mu, scale=sigma)
    return offset + normal.pdf(data).flatten() * factor


def fit_gaussian_1d(image, image_e, p0=None, bounds=None, axis=0):
    """
    Fit a one-dimensional Gaussian function with some ordinate offset to an
    image with uncertainty. This is achieved by averaging in a given ``axis``
    before performing the fit. Return the results, and index of the offset.

    Args:
        image (:py:attr:`array_like`): The data to fit the Gaussian to.
        image_e (:py:attr:`array_like`): The data uncertainty.
        p0 (:py:attr:`list`, optional): An initial guess at the parameters.
            Defaults to values based on the image.
        bounds (:py:attr:`list` of :py:attr:`tuple`, optional): Bounds for the
            fitting. Defaults to values based on the image.
        axis (:py:attr:`int`): The dimension in which to perform the averaging.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`array_like`: The results (with uncertainties) for each of the 6 parameters fit.
            - :py:attr:`int`: The index of the offset.
            - :py:attr:`None`: As it is not possible to describe the reflected peak width.
    """
    ordinate = image.mean(axis=axis)

    # A small quantity by which we can shift parameters such that they're > 0.
    # This can prevent various silly /0 errors, and forces upper bounds > lower.
    # Crucially, this ensures that none of the image's data has an error of
    # exactly 0.
    epsilon = 0.001

    # If errors haven't been calculated on this image before, then we'll have
    # been passed an array of zeros as image_e. In that case, we should go ahead
    # and calculate the errors on our intensity array now.
    if np.amax(image_e) == 0:
        image_e = np.sqrt(image) + epsilon

    # Now we can generate an array of errors.
    ordinate_e = image_e.mean(axis=axis)

    # Now we generate the initial values for our Gaussian fit.
    # These values are crucial - as this is a high dimensional fitting problem,
    # it is likely that we'll get stuck in a local minimum if these aren't good.

    # Guess that the Gaussian is centred at the most intense mean pixel value.
    mean0 = np.argmax(ordinate)
    # Guess that the standard deviation is a single pixel.
    sdev0 = 1
    # Guess that the background (offset) is the median pixel value.
    offset0 = np.median(ordinate)
    # Guess that the scale is equal to the largest recorded value.
    scale0 = image.max()

    # Setting default values.
    if p0 is None:
        p0 = [mean0, sdev0, offset0, scale0]
    if bounds is None:
        bounds = ([0, 0, 0, 0],
                  [ordinate.shape[0], ordinate.shape[0], scale0, scale0 * 10])

    # Perform the fitting.
    popt, pcov = curve_fit(
        univariate_normal,
        np.arange(0, ordinate.shape[0], 1), ordinate, bounds=bounds,
        sigma=ordinate_e, p0=p0, maxfev=2000 * (len(p0) + 1))

    # Determine uncertainty from covarience matrix.
    # Note: the stddev of the fit Gaussian can be accessed via popt[1]
    p_sigma = np.sqrt(np.diag(pcov))

    return (popt, p_sigma), 2
