"""
Often the detector is a lot larger than the reflected intensity peak, so it
makes sense to crop the image to the peak.
"""


import numpy as np

from islatu.region import Region


def crop_to_region(array: np.ndarray, region: Region):
    """
    Crops the input array to the input region.

    Args:
        array:
            The array to crop.
        region:
            The instance of Region to crop to.
    """
    return array[region.x_start:region.x_end, region.y_start:region.y_end]
