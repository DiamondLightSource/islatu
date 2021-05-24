"""
This module contains the Scan and Scan2D classes. A Scan is a measurement and so
inherits from MeasurementBase. An instance of Scan contains scan metadata, as 
well as a suite of methods useful for data correction, uncertainty calculations
and the like.

A Scan2D is a Scan whose Data object's intensity values are computed from an 
image captured by an area detector. Many of Scan's methods are overloaded to
make use of the additional information provided by the area detector, and extra
image manipulation methods are included in Scan2D.
"""

from islatu.metadata import Metadata
from islatu.data import Data, MeasurementBase


class Scan(MeasurementBase):
    def __init__(self, data: Data, metadata: Metadata) -> None:
        super().__init__(data)
        self.metadata = metadata


class Scan2D(Scan):
    """
    Attributes:
        data:
        metadata:
        images (:py:attr:`list` of :py:class:`islatu.image.Image`): The
            detector images in the given scan.
    """

    def __init__(self, data: Data, metadata: Metadata, images: list) -> None:
        super().__init__(data, metadata)
        self.images = images
