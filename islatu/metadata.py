"""
This module contains the Metadata class, returned by parser methods in the
islatu.io module. This class provides a consistent way to refer to metadata
returned by different detectors/instruments, and also contains a dictionary
of all of the metadata as scraped from the parsed file.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

from islatu.detector import Detector


class Metadata:
    def __init__(self, detector: Detector, raw_metadata: dict) -> None:
        self.detector = detector
        self.raw_metada = raw_metadata

        # Explicitly add a few important attributes for intelligent code
        # completion. This is redundant, but convenient.
        self.is_2d_detector = detector.is_2d_detector
        self.probe_mass = detector.probe_mass
        self.is_point_detector = detector.is_point_detector

        # Now retrieve the dictionary data from the raw_metadata using the keys
        # in the detector object.
        for attr_name in dir(detector):
            attr = getattr(detector, attr_name)

            if attr is None:
                continue

            if attr_name.startswith('metakey_'):
                setattr(self, attr_name.replace("metakey_", ""),
                        raw_metadata[attr])
