"""
As reflectometry measurements typically consist of multiple scans at different
attenutation, we must stitch these together.
"""

# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# author: Andrew R. McCluskey
import warnings
import numpy as np
from scipy.stats import linregress
from scipy.interpolate import splrep, splev


def correct_attentuation(scan_list):
    """
    Correct the attentuation level between different scans.

    Args:
        scans (:py:attr:`list` of :py:class:`islatu.refl_data.Scan`):
            Reflectometry scans.

    Returns:
        :py:attr:`list` of :py:class:`islatu.refl_data.Scan`: 
            Reflectometry scans with attenuation corrected.
    """

    for i in range(len(scan_list) - 1):
        overlap_start = scan_list[i + 1].q[0].n
        overlap_end = scan_list[i].q[-1].n
        if overlap_start > overlap_end:
            warnings.warn('Using extrapolation to correct attenuation between '
                          'scans {} and {}. Please double check these '
                          'results.'.format(scan_list[i].metadata.file,
                                            scan_list[i+1].metadata.file))
            overlap_start_index = -2
            overlap_end_index = 1
        else:
            overlap_start_index = np.argmin(
                np.abs(scan_list[i].q - overlap_start))
            overlap_end_index = np.argmin(
                np.abs(scan_list[i + 1].q - overlap_end))
        res = linregress(
            (scan_list[i].q[overlap_start_index:]),
            np.log(scan_list[i].intensity[overlap_start_index:]))
        target_r = np.exp(
            scan_list[
                i+1].q[: overlap_end_index + 1] * res.slope + res.intercept)
        vary_r = scan_list[i+1].intensity[: overlap_end_index + 1]
        ratio = target_r.mean() / vary_r.mean()
        scan_list[i + 1].intensity *= ratio
    return scan_list


def concatenate(scan_list):
    """
    Concatenate each of the datasets together.

    Args:
        scans (:py:attr:`list` of :py:class:`islatu.refl_data.Scan`):
            Reflectometry scans.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`array_like`: q-values.
            - :py:attr:`array_like`: Reflected intensities.
    """

    q_vectors = np.array([])
    intensity = np.array([])
    intensity_e = np.array([])
    for scan in scan_list:
        q_vectors = np.append(q_vectors, scan.q)
        intensity = np.append(intensity, scan.intensity)
        intensity_e = np.append(intensity_e, scan.intensity_e)
    return q_vectors, intensity, intensity_e


def normalise_ter(q, reflected_intensity, max_q=0.1):
    """
    Find the total external reflection region and normalise this to 1.

    Args:
        max_q (:py:attr:`float`): The maximum q to be included in finding the
            critical angle.

    Returns:
        :py:attr:`array_like`: Reflected intensities.
    """
    max_q_idx = q[np.where(q < max_q)].size
    if max_q_idx <= 1:
        end_of_ter_index = 1
    else:
        end_of_ter_index = np.argmax(
            np.abs(np.gradient((reflected_intensity)[:max_q_idx]))
        )
    if end_of_ter_index == 0:
        end_of_ter_index = 1
    ter_region_mean_r = reflected_intensity[:end_of_ter_index].mean()
    reflected_intensity /= ter_region_mean_r
    return reflected_intensity


def rebin(q_vectors, reflected_intensity, new_q=None, rebin_as="linear",
          number_of_q_vectors=400):
    """
    Rebin the data on a linear or logarithmic q-scale.

    Args:
        q_vectors:
            q - the current q vectors.
        reflected_intensity (:py:attr:`tuple`):
            (I, I_e) - The current reflected intensities, and their errors.
        new_q (:py:attr:`array_like`): 
            Array of potential q-values. Defaults to :py:attr:`None`. If this
            argument is not specified, then the new q, R values are binned 
            according to rebin_as and number_of_q_vectors.
        rebin_as (py:attr:`str`):
            String specifying how the data should be rebinned. Options are 
            "linear" and "log". This is only used if the new_q are unspecified.
        number_of_q_vectors (:py:attr:`int`, optional):
            The max number of q-vectors to be using initially in the rebinning 
            of the data. Defaults to :py:attr:`400`.

    Returns:
        :py:attr:`tuple`: Containing:
            - q: rebinned q-values.
            - intensity: rebinned intensities.
            - intensity_e: rebinned intensity errors.
    """

    # Unpack the arguments.
    q = q_vectors
    R, R_e = reflected_intensity

    # Required so that logspace/linspace encapsulates the whole data.
    epsilon = 0.001

    if new_q is None:
        # Our new q vectors have not been specified, so we should generate some.
        if rebin_as == "log":
            new_q = np.logspace(
                np.log10(q[0]),
                np.log10(q[-1] + epsilon), number_of_q_vectors)
        elif rebin_as == "linear":
            new_q = np.linspace(q[0], q[-1] + epsilon, number_of_q_vectors)

    binned_q = np.zeros_like(new_q)
    binned_R = np.zeros_like(new_q)
    binned_R_e = np.zeros_like(new_q)

    for i in range(len(new_q)-1):
        indices = []
        inverse_var = []
        for j in range(len(q)):
            if new_q[i] <= q[j] < new_q[i + 1]:
                indices.append(j)
                inverse_var.append(1/float(R_e[j]**2))

        # Don't bother doing maths if there were no recorded q-values between
        # the two bin points we were looking at.
        if len(indices) == 0:
            continue

        # We will be using inverse-variance weighting to minimize the variance
        # of the weighted mean.
        sum_of_inverse_var = np.sum(inverse_var)

        # If we measured multiple qs between these bin locations, then average
        # the data, weighting by inverse variance.
        for j in indices:
            binned_R[i] += R[j]/(R_e[j]**2)
            binned_q[i] += q[j]/(R_e[j]**2)

        # Divide by the sum of the weights.
        binned_R[i] /= sum_of_inverse_var
        binned_q[i] /= sum_of_inverse_var

        # The stddev of an inverse variance weighted mean is always:
        binned_R_e[i] = np.sqrt(1/sum_of_inverse_var)

        print(binned_R_e[i])

    # Get rid of any empty, unused elements of the array.
    cleaned_q = np.delete(binned_q, np.argwhere(binned_R == 0))
    cleaned_R = np.delete(binned_R, np.argwhere(binned_R == 0))
    cleaned_R_e = np.delete(binned_R_e, np.argwhere(binned_R == 0))

    return cleaned_q, cleaned_R, cleaned_R_e
