"""
The background subtraction for the islatu pipeline
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey

import numpy as np
from scipy.stats import multivariate_normal
from scipy.optimize import curve_fit
from uncertainties import ufloat


def bivariate_normal(data, mu_1, mu_2, sigma_1, sigma_2, offset, factor):
    """
    Function to produce a bivariate normal distribution. 

    Note: the covariance of the two dimensions is assumed to be zero to unsure greater stability.

    Args:
        data (array_like): Abscissa data
        mu_1 (float): Mean in dimension 0
        mu_2 (float): Mean in dimension 1
        sigma_1 (float): Variance in dimension 0
        sigma_2 (float): Variance in dimension 1
        offset (float): Offset from the 0 for the ordinate
        factor (float): Multiplicative factor for area of normal
    
    Returns:
        (array_like): Flatten ordinate data for bivariate normal distribution. 
    """
    pos = np.empty(data[0].shape + (2,))
    pos[:, :, 0] = data[0]
    pos[:, :, 1] = data[1]
    rv = multivariate_normal([mu_1, mu_2], [[sigma_1, 0], [0, sigma_2]])
    return offset + rv.pdf(pos).flatten() * factor


def fit_gaussian_2d(image, image_e, p0=None, bounds=None):
    """
    Fit a two-dimensional Gaussian function with some ordinate offset to an image with an
    uncertainty and return the offset.

    Args:
        image (array_like): The data to fit the Gaussian to.
        image_e (array_like): The data uncertainty. 
        p0 (list, optional): An initial guess at the parameters. 
        bounds (tuple_of_list, optional): Bounds for the fitting.

    Returns:
        (uncertainties.core.Variable): The offset and associated uncertainty.
    """
    if p0 is None:
        p0 = [
            image.shape[0] / 2,
            image.shape[1] / 2,
            1,
            1,
            image.min(),
            image.max(),
        ]
    if bounds is None:
        bounds = (
            0,
            [
                image.shape[0],
                image[1],
                100,
                100,
                image.max(),
                image.max() * 10,
            ],
        )
    abscissa = np.array(np.mgrid[0 : len(image[0]) : 1, 0 : len(image[1]) : 1])
    popt, pcov = curve_fit(
        bivariate_normal,
        abscissa,
        image.flatten(),
        bounds=bounds,
        sigma=image_e.flatten(),
        p0=p0,
        maxfev=2000 * (len(p0) + 1),
    )
    p_sigma = np.sqrt(np.diag(pcov))
    return ufloat(popt[4], p_sigma[4])
