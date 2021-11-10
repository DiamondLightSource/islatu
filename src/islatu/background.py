"""
Background substraction is a necessary component of reflectometry reduction,
where the background scattering is removed from the reflected intensity.

Herein are some functions to enable that for a two-dimensional detector image.
"""


import numpy as np
from scipy.stats import norm
from scipy.optimize import curve_fit


def roi_subtraction(image, list_of_rois):
    """
    Carry out background subtraction by taking a series of rectangular regions
    of interested (ROIs) as being fair Poissonian measurements of the 
    background. 

    Args:
        image:
            The islatu.image.Image object from which we should subtract 
            background from.
        list_of_rois:
            A list of dictionaries taking the form:
                [{'y_start': y1, 'y_end': y2, 'x_start': x1, 'x_end': x2}, ... ]
            where each dictionary specifies the coordinates of the corners of a 
            rectangle containing a fair Poissonian measurement of the background 
            level.
    """
    # We're going to need to count all intensity in all the background, as well
    # as the number of pixels used in our measurement of the background.
    sum_of_bkg_areas = 0
    total_num_pixels = 0

    # Add up all the intensity in all the pixels.
    for i in range(len(list_of_rois)):
        # This is a bit neater than doing everything in one line of code.
        y_start = list_of_rois[i]['y_start']
        y_end = list_of_rois[i]['y_end']
        x_start = list_of_rois[i]['x_start']
        x_end = list_of_rois[i]['y_end']

        # Make sure that x_end > x_start, etc.
        if x_end > x_start:
            x_start, x_end = x_end, x_start
        if y_end > y_start:
            y_start, y_end = y_end, y_start

        # Now add the total intensity in this particular background region to
        # the intensity measured in all the background regions so far.
        sum_of_bkg_areas += np.sum(
            image.array_original[y_start:y_end, x_start:x_end]
        )

        # Add the number of pixels in this background ROI to the total number of
        # pixels used to compute the background measurement overall.
        total_num_pixels += (y_end - y_start) * (x_end - x_start)

    # Now Poisson stats can be abused to only calculate a single sqrt.
    err_of_bkg_areas = np.sqrt(sum_of_bkg_areas)

    # Get the per pixel background mean and stddev.
    bkg_per_pixel = sum_of_bkg_areas / total_num_pixels
    bkg_error_per_pixel = err_of_bkg_areas / total_num_pixels

    # Store this information in the image object passed to us.
    image.bkg = bkg_per_pixel
    image.bkg_e = bkg_error_per_pixel

    # Compute the new value of the image's array and array error.
    image.array = np.float64(image.array) - image.bkg
    image.array_e = np.sqrt(image.bkg_e**2 + image.array_e**2)

    # Expose the calculated background and background_error per pixel.
    return bkg_per_pixel, bkg_error_per_pixel


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
            - :py:attr:`array_like`: The results (with uncertainties) for each 
                of the 6 parameters fit.
            - :py:attr:`int`: The index of the offset.
            - :py:attr:`None`: As it is not possible to describe the reflected 
                peak width.
    """

    ordinate = image.mean(axis=axis)

    # Now we can generate an array of errors.
    ordinate_e = np.sqrt(np.mean(image_e**2, axis=axis))

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
