"""
This module contains the Metadata class, returned by parser methods in the
islatu.io module. This class provides a consistent way to refer to metadata
returned by different detectors/instruments, and also contains a dictionary
of all of the metadata as scraped from the parsed file.
"""

from abc import abstractmethod

import numpy as np


class Metadata:
    """
    An ABC for classes that store metadata parsed from data files. This defines
    the properties that must be implemented by parsing classes.
    """

    def __init__(self, local_path):
        self.local_path = local_path

    @property
    @abstractmethod
    def probe_energy(self):
        """
        This must be overridden.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def default_axis(self) -> np.ndarray:
        """
        Returns a numpy array of data associated with the default axis, where
        "default axis" should be understood in the NeXus sense to mean the
        experiment's dependent variable.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def default_axis_name(self) -> str:
        """
        Returns the name of the default axis, as it was recorded in the data
        file stored at local_path.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def default_axis_type(self) -> str:
        """
        Returns what type of default axis we have. Options are 'q', 'th' or
        'tth'.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def transmission(self):
        """
        Proportional to the fraction of probe particles allowed by an attenuator
        to strike the sample.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def detector_distance(self):
        """
        Returns the distance between sample and detector.
        """
        raise NotImplementedError()
