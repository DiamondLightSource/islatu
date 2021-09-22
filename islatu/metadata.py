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
from nexusformat.nexus.tree import NXgroup


class Metadata:
    # In the far future, this would be useful to bullet-proof everything:
    # TODO: build units into the detector dataclass, and automatically noramlize
    # units on initialization of a metadata instance.
    def __init__(self, detector: Detector, raw_metadata) -> None:
        self.detector = detector
        self.raw_metadata = raw_metadata

        # Explicitly add a few important attributes for intelligent code
        # completion. This is redundant, but convenient.
        self.is_2d_detector = detector.is_2d_detector
        self.probe_mass = detector.probe_mass
        self.is_point_detector = detector.is_point_detector

        # If the raw_metadata is an NXgroup, give up hope.
        if isinstance(raw_metadata, NXgroup):
            return

        # Now retrieve the dictionary data from the raw_metadata using the keys
        # in the detector object.
        for attr_name in dir(detector):
            attr = getattr(detector, attr_name)

            if attr is None:
                continue

            if attr_name.startswith('metakey_'):
                # If this metadata is in a list of length one, it probably
                # shouldn't be wrapped in a list.
                try:
                    stripped_name = attr_name.strip().replace("metakey_", "")
                    if len(self.raw_metadata[attr]) == 1:
                        self.raw_metadata[attr] = self.raw_metadata[attr][0]

                    setattr(self, stripped_name,
                            (self.raw_metadata[attr]))
                except KeyError as e:
                    print("Could not find necessary metadata with name: " +
                          stripped_name + ", is your input file malformed?")
                    raise e
