"""
Background substraction is a necessary component of reflectometry reduction,
where the background scattering is removed from the reflected intensity.

Herein are some functions to enable that for a two-dimensional detector image,
as well as simple dataclasses in which we can store some information relating to
the background subtraction, and any fitting that we might have carried out.
"""

from dataclasses import dataclass
from typing import Callable, List

import numpy as np
from scipy.stats import norm
from scipy.optimize import curve_fit

from .region import Region
from .image import Image


@dataclass
class FitInfo:
    """
    A simple dataclass in which we can store data relating to the quality of a
    fit.
    """
    popt: np.ndarray
    pcov: np.ndarray
    fit_function: Callable


@dataclass
class BkgSubInfo:
    """
    A simple data class in which we can store information relating to a
    background subtraction.
    """
    bkg: float
    bkg_e: float
    bkg_sub_function: Callable
    fit_info: FitInfo = None


def roi_subtraction(image, list_of_regions: List[Region]):
    """
    Carry out background subtraction by taking a series of rectangular regions
    of interested (ROIs) as being fair Poissonian measurements of the
    background.

    Args:
        image:
            The islatu.image.Image object from which we should subtract
            background from.
        list_of_regions:
            A list of instances of the Regions class corresponding to background
            regions.
    """
    # We're going to need to count all intensity in all the background, as well
    # as the number of pixels used in our measurement of the background.
    sum_of_bkg_areas = 0
    total_num_pixels = 0

    # Make sure we've been given multiple regions. If not, np: make a list.
    if isinstance(list_of_regions, Region):
        list_of_regions = [list_of_regions]

    # Add up all the intensity in all the pixels.
    for region in list_of_regions:
        # Now add the total intensity in this particular background region to
        # the intensity measured in all the background regions so far.
        sum_of_bkg_areas += np.sum(
            image.array_original[
                int(region.x_start):int(region.x_end),
                int(region.y_start):int(region.y_end)
            ]
        )
        # Add the number of pixels in this background ROI to the total number of
        # pixels used to compute the background measurement overall.
        total_num_pixels += region.num_pixels

    # Now Poisson stats can be abused to only calculate a single sqrt.
    err_of_bkg_areas = np.sqrt(sum_of_bkg_areas)
    if err_of_bkg_areas == 0:
        err_of_bkg_areas = 1

    # Get the per pixel background mean and stddev.
    bkg_per_pixel = sum_of_bkg_areas / total_num_pixels
    bkg_error_per_pixel = err_of_bkg_areas / total_num_pixels

    # Expose the calculated background and background_error per pixel.
    return BkgSubInfo(bkg_per_pixel, bkg_error_per_pixel, roi_subtraction)


def univariate_normal(data, mean, sigma, offset, factor):
    """
    Produce a univariate normal distribution.

    Args:
        data (:py:attr:`array_like`): Abscissa data.
        mean (:py:attr:`float`): Mean (horizontal).
        sigma (:py:attr:`float`): Variance (horizontal).
        offset (:py:attr:`float`): Offset from the 0 for the ordinate, this is
            the background level.
        factor (:py:attr:`float`): Multiplicative factor for area of normal
            distribution.

    Returns:
        :py:attr:`array_like`: Ordinate data for univariate normal distribution.
    """
    # Creation of the bivariate normal distribution
    normal = norm(loc=mean, scale=sigma)
    return offset + normal.pdf(data).flatten() * factor


def fit_gaussian_1d(image: Image, params_0=None, bounds=None, axis=0):
    """
    Fit a one-dimensional Gaussian function with some ordinate offset to an
    image with uncertainty. This is achieved by averaging in a given ``axis``
    before performing the fit. Return the results, and index of the offset.

    Args:
        image:
            The islatu image object to fit.
        params_0 (:py:attr:`list`, optional):
            An initial guess at the parameters. Defaults to values based on the
            image.
        bounds (:py:attr:`list` of :py:attr:`tuple`, optional):
            Bounds for the fitting. Defaults to values based on the image.
        axis (:py:attr:`int`):
            The dimension along which the averaging will be performed.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`array_like`: The results (with uncertainties) for each
                of the 6 parameters fit.
            - :py:attr:`int`: The index of the offset.
            - :py:attr:`None`: As it is not possible to describe the reflected
                peak width.
    """
    arr, arr_e = image.array, image.array_e
    ordinate = arr.mean(axis=axis)

    # Now we can generate an array of errors.
    ordinate_e = np.sqrt(np.mean(arr_e**2, axis=axis))

    # Setting default values.
    if params_0 is None:
        # Now we generate the initial values for our Gaussian fit.
        # These values are crucial – as this is a high dimensional fitting
        # problem, it is likely that we'll get stuck in a local minimum if these
        # aren't good.
        # Guess that the Gaussian mean is at the most intense mean pixel value.
        mean0 = np.argmax(ordinate)
        # Guess that the standard deviation is a single pixel.
        sdev0 = 1
        # Guess that the background (offset) is the median pixel value.
        offset0 = np.median(ordinate)
        # Guess that the scale is equal to the largest recorded value.
        scale0 = arr.max()
        params_0 = [mean0, sdev0, offset0, scale0]
    if bounds is None:
        bounds = ([0, 0, 0, 0],
                  [ordinate.shape[0], ordinate.shape[0], scale0, scale0 * 10])

    # Perform the fitting.
    fit_popt_pcov = curve_fit(
        univariate_normal,
        np.arange(0, ordinate.shape[0], 1), ordinate, bounds=bounds,
        sigma=ordinate_e, p0=params_0, maxfev=2000 * (len(params_0) + 1))

    fit_info = FitInfo(fit_popt_pcov[0], fit_popt_pcov[1], univariate_normal)

    # Determine uncertainty from covarience matrix.
    # Note: the stddev of the fit Gaussian can be accessed via popt[1].
    p_sigma = np.sqrt(np.diag(fit_info.pcov))

    return BkgSubInfo(fit_info.popt[2], p_sigma[2], fit_gaussian_1d, fit_info)
