"""
This class is designed to perform the stitching of multiple
X-ray reflectometry datasets together

Last updated: 2019-12-18

Author: Andrew McCluskey (andrew.mccluskey@diamond.ac.uk)
"""
import numpy as np
from uncertainties import unumpy as unp


def correct_attentuation(scan_list):
    """
    Correct the attentuation level between a a series of elements in lists.

    Args:

    Returns:
    """
    for i in range(len(scan_list) - 1):
        overlap_start = scan_list[i + 1].q[0].n
        overlap_end = scan_list[i].q[-1].n

        overlap_start_index = np.argmin(np.abs(scan_list[i].q - overlap_start))
        overlap_end_index = np.argmin(np.abs(scan_list[i + 1].q - overlap_end))

        target_r = scan_list[i].R[overlap_start_index:]
        vary_r = scan_list[i + 1].R[: overlap_end_index + 1]

        ratio = target_r.mean() / vary_r.mean()

        scan_list[i + 1].R *= ratio
    return scan_list


def concatenate(scan_list):
    """
    Concatenate each of the datasets together.
    """
    reflected_intensity = np.array([])
    q_vectors = np.array([])
    for i in range(len(scan_list)):
        reflected_intensity = np.append(reflected_intensity, scan_list[i].R)
        q_vectors = np.append(q_vectors, scan_list[i].q)
    return q_vectors, reflected_intensity


def normalise_ter(q_vectors, reflected_intensity, max_q=0.1):
    """
    Find the total external reflection region and normalise this to 1.
    """
    q = unp.nominal_values(q_vectors)
    max_q_idx = q[np.where(q < max_q)].size
    if max_q_idx <= 1:
        end_of_ter_index = 1
    else:
        end_of_ter_index = np.argmax(
            np.abs(np.gradient(unp.nominal_values(reflected_intensity)[:max_q_idx]))
        )
    if end_of_ter_index == 0:
        end_of_ter_index = 1
    ter_region_mean_r = reflected_intensity[:end_of_ter_index].mean()
    reflected_intensity /= ter_region_mean_r
    return reflected_intensity


def rebin(q_vectors, reflected_intensity, new_q=None, number_of_q_vectors=400):
    """
    Rebin the data on a logarithmic q-scale.

    Args:
        number_of_q_vectors (int, default = 200): The max number of
            q-vectors to be using initially in the rebinning of the data.
    """
    if new_q is not None:
        new_q = new_q
    else:
        new_q = np.logspace(
            np.log10(q_vectors[0].n),
            np.log10(q_vectors[-1].n),
            number_of_q_vectors,
        )

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

    return cleaned_q, cleaned_r
