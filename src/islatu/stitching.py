"""
As reflectometry measurements typically consist of multiple scans at different
attenutation, we must stitch these together.
"""

import numpy as np
import pandas as pd

from islatu.debug import debug
from islatu.scan import Scan


def concatenate(scan_list: list[Scan]):
    """
    Concatenate each of the datasets together.

    Args:
        scans:
            List of reflectometry scans.

    Returns:
        :py:attr:`tuple`: Containing:
            - q-values.
            - Reflected intensities.
            – Errors on reflected intensities.
    """

    q_vectors = np.array([])
    intensity = np.array([])
    intensity_e = np.array([])
    for scan in scan_list:
        q_vectors = np.append(q_vectors, scan.q_vectors)
        intensity = np.append(intensity, scan.intensity)
        intensity_e = np.append(intensity_e, scan.intensity_e)
    return q_vectors, intensity, intensity_e


def match_overlap_resolution(data_df: pd.DataFrame):
    debug.log("matching resolution of overlapping sections", unimportance=2)
    overlap_indices = np.argwhere(data_df["q"].diff() < 0).flatten()
    starts = np.array([0])
    starts = np.concatenate([starts, overlap_indices])
    ends = np.array([len(data_df)])
    ends = np.concatenate([overlap_indices, ends]) - 1
    chunklist = []
    for start, end in zip(starts, ends):
        chunklist.append(data_df.loc[start:end].copy())

    drop_indices = np.array([])

    for ind in np.arange(len(chunklist) - 1):
        overlap_q = chunklist[ind + 1]["q"].values[0]
        overlap_chunk_lower = chunklist[ind][chunklist[ind]["q"] >= overlap_q]
        overlap_chunk_upper = chunklist[ind + 1][
            (overlap_chunk_lower["q"].values[-1] >= chunklist[ind + 1]["q"])
        ]
        if len(overlap_chunk_lower) <= 1 or len(overlap_chunk_upper) <= 1:
            continue

        step_ratio = round(
            np.nanmean(overlap_chunk_upper["q"].diff().values)
            / np.nanmean(overlap_chunk_lower["q"].diff().values)
        )
        matched_indices = overlap_chunk_lower.index.values[0::step_ratio]
        lower_indices = overlap_chunk_lower.index.values
        chunk_drop_indices = lower_indices[~np.isin(lower_indices, matched_indices)]
        print(f"    removed indices for chunk {ind} = {chunk_drop_indices}")
        drop_indices = np.append(drop_indices, chunk_drop_indices)

    return data_df.drop(drop_indices)


def rebin(
    q_vectors,
    reflected_intensity,
    new_q=None,
    rebin_as="linear",
    number_of_q_vectors=5000,
):
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

    # match resolution of overlapping sections of the data, dropping points from the higher resolution data to match the lower resolution data.
    data_df = pd.DataFrame({"q": q.round(4), "R": R, "R_e": R_e})
    overlap_df = match_overlap_resolution(data_df)

    q = overlap_df["q"].values
    R = overlap_df["R"].values
    R_e = overlap_df["R_e"].values

    # Required so that logspace/linspace encapsulates the whole data.
    epsilon = 0.001

    if new_q is None:
        # Our new q vectors have not been specified, so we should generate some.
        if rebin_as == "log":
            new_q = np.logspace(
                np.log10(q[0]), np.log10(q[-1] + epsilon), number_of_q_vectors
            )
        elif rebin_as == "linear":
            new_q = np.linspace(q.min(), q.max() + epsilon, number_of_q_vectors)

    binned_q = np.zeros_like(new_q)
    binned_R = np.zeros_like(new_q)
    binned_R_e = np.zeros_like(new_q)

    for i in range(len(new_q) - 1):
        indices = []
        inverse_var = []
        for j in range(len(q)):
            if new_q[i] <= q[j] < new_q[i + 1]:
                indices.append(j)
                inverse_var.append(1 / float(R_e[j] ** 2))

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
            binned_R[i] += R[j] / (R_e[j] ** 2)
            binned_q[i] += q[j] / (R_e[j] ** 2)

        # Divide by the sum of the weights.
        binned_R[i] /= sum_of_inverse_var
        binned_q[i] /= sum_of_inverse_var

        # The stddev of an inverse variance weighted mean is always:
        binned_R_e[i] = np.sqrt(1 / sum_of_inverse_var)

    # Get rid of any empty, unused elements of the array.
    cleaned_q = np.delete(binned_q, np.argwhere(binned_R == 0))
    cleaned_R = np.delete(binned_R, np.argwhere(binned_R == 0))
    cleaned_R_e = np.delete(binned_R_e, np.argwhere(binned_R == 0))

    return cleaned_q, cleaned_R, cleaned_R_e
