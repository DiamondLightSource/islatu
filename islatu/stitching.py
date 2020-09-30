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
from uncertainties import unumpy as unp


def correct_attentuation(scan_list):
    """
    Correct the attentuation level between a a series of elements in lists.

    Args:
        scans (:py:attr:`list` of :py:class:`islatu.refl_data.Scan`):
            Reflectometry scans.

    Returns:
        :py:attr:`list` of :py:class:`islatu.refl_data.Scan`: Reflectometry scans with attenuation corrected.
    """
    for i in range(len(scan_list) - 1):
        overlap_start = scan_list[i + 1].q[0].n
        overlap_end = scan_list[i].q[-1].n
        if overlap_start > overlap_end:
            warnings.warn('Using extrapolation to correct attenuation between '
                          'scans {} and {}. Please double check these '
                          'results.'.format(scan_list[i].file_path,
                                            scan_list[i+1].file_path))
            overlap_start_index = -2
            overlap_end_index = 1
        else:
            overlap_start_index = np.argmin(
                np.abs(scan_list[i].q - overlap_start))
            overlap_end_index = np.argmin(
                np.abs(scan_list[i + 1].q - overlap_end))
        res = linregress(
            unp.nominal_values(scan_list[i].q[overlap_start_index:]),
            np.log(unp.nominal_values(scan_list[i].R[overlap_start_index:])))
        target_r = unp.exp(
            scan_list[
                i+1].q[: overlap_end_index + 1] * res.slope + res.intercept)
        vary_r = scan_list[i+1].R[: overlap_end_index + 1]
        ratio = target_r.mean() / vary_r.mean()
        scan_list[i + 1].R *= ratio
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
    reflected_intensity = np.array([])
    q_vectors = np.array([])
    for scan in scan_list:
        reflected_intensity = np.append(reflected_intensity, scan.R)
        q_vectors = np.append(q_vectors, scan.q)
    return q_vectors, reflected_intensity


def normalise_ter(q_vectors, reflected_intensity, max_q=0.1):
    """
    Find the total external reflection region and normalise this to 1.

    Args:
        max_q (:py:attr:`float`): The maximum q to be included in finding the
            critical angle.

    Returns:
        :py:attr:`array_like`: Reflected intensities.
    """
    q = unp.nominal_values(q_vectors)
    max_q_idx = q[np.where(q < max_q)].size
    if max_q_idx <= 1:
        end_of_ter_index = 1
    else:
        end_of_ter_index = np.argmax(
            np.abs(
                np.gradient(
                    unp.nominal_values(reflected_intensity)[:max_q_idx]))
        )
    if end_of_ter_index == 0:
        end_of_ter_index = 1
    ter_region_mean_r = reflected_intensity[:end_of_ter_index].mean()
    reflected_intensity /= ter_region_mean_r
    return reflected_intensity


def rebin(q_vectors, reflected_intensity, new_q=None, number_of_q_vectors=400,
          interpolate=False):
    """
    Rebin the data on a logarithmic q-scale.

    Args:
        q_vectors (:py:attr:`array_like`): The current q-values.
        reflected_intensity (:py:attr:`array_like`): The current reflected
            intensity.
        new_q (:py:attr:`array_like`): Array of potential q-values. Defaults
            to :py:attr:`None`.
        number_of_q_vectors (:py:attr:`int`, optional): The max number of
            q-vectors to be using initially in the rebinning of the data.
            Defaults to :py:attr:`400`.
        interpolate (:py:attr:`bool`, optional): Should values be interpolated
            if no measured values are present for the given q-value.

    Returns:
        :py:attr:`tuple`: Containing:
            - :py:attr:`array_like`: q-values.
            - :py:attr:`array_like`: Reflected intensities.
    """
    if new_q is None:
        new_q = np.logspace(
            np.log10(q_vectors[0].n),
            np.log10(q_vectors[-1].n), number_of_q_vectors)

    binned_q = unp.uarray(np.zeros_like(new_q), np.zeros_like(new_q))
    binned_r = unp.uarray(np.zeros_like(new_q), np.zeros_like(new_q))
    for i in range(len(new_q) - 1):
        count = 0
        for j, q in enumerate(q_vectors):
            if new_q[i] <= q < new_q[i + 1]:
                binned_q[i] += q
                binned_r[i] += reflected_intensity[j]
                count += 1
        if count > 0:
            binned_q[i] /= count
            binned_r[i] /= count
    cleaned_q = np.delete(binned_q, np.argwhere(binned_r == 0))
    cleaned_r = np.delete(binned_r, np.argwhere(binned_r == 0))
    if interpolate:
        r = unp.nominal_values(cleaned_r)
        dr = unp.std_devs(cleaned_r)
        itp1 = splrep(unp.nominal_values(cleaned_q), r + dr)
        itp2 = splrep(unp.nominal_values(cleaned_q), r)
        r_max = splev(new_q, itp1)
        r_new = splev(new_q, itp2)
        cleaned_q = new_q
        cleaned_r = unp.uarray(r_new, r_max-r_new)

    return cleaned_q, cleaned_r
