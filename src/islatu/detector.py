"""
The detector module contains information pertaining to the structure of data
output by different detectors. This apparatus-specific data is stored in 
instances of the :py:class:`~islatu.detector.Detector` dataclass.
"""

# Copyright (c) Richard Brearton
# Distributed under the terms of the MIT License
# author: Richard Brearton
import dataclasses


@dataclasses.dataclass
class Detector:
    """
    A dataclass for storing information pertaining to the structure of data 
    output by different detectors at different instruments.

    Attributes:
        detector_name (:py:attr:`str`):
            Unique, readable ID for the detector name.
        is_2d_detector (:py:attr:`bool`):
            :py:attr:`True` if this detector is a 2D detector.
        probe_mass (:py:attr:`float`): 
            Mass of the probe particle incident on this detector, in kg.
        metakey_detector_distance (:py:attr:`str`):
            Metadata key for distance between detector and centre of rotation.
        metakey_probe_energy (:py:attr:`str`):
            Metadata key for energy of incident probe particle.
        metakey_file (:py:attr:`str`):
            Metadata key for the path to the file containing intensity data, 
                pointed to by the file parsed by parser. Takes the value 
                :py:attr:`None` if the file parsed by the parser contained the
                intensity data.
        metakey_transmission (:py:attr:`str`):
            Metadata key for the transmission.
        metakey_roi_1_maxval (:py:attr:`str`):
            Metadata key for the maximum intensity value recorded by any pixel
                within the first region of interest in a detector.
        metakey_roi_2_maxval (:py:attr:`str`):
            Metadata key for the maximum intensity value recorded by any pixel
                within the second region of interest in a detector.
        is_point_detector (:py:attr:`bool`):
            :py:attr:`True` if the detector is a point detector.

    Args:
        detector_name (:py:attr:`str`):
            Unique, readable ID for the detector name.
        is_2d_detector (:py:attr:`bool`):
            :py:attr:`True` if this detector is a 2D detector.
        probe_mass (:py:attr:`float`): 
            Mass of the probe particle incident on this detector, in kg.
        metakey_detector_distance (:py:attr:`str`, optional):
            Metadata key for distance between detector and centre of rotation.
                Defaults to :py:attr:`None`.
        metakey_probe_energy (:py:attr:`str`, optional):
            Metadata key for energy of incident probe particle. Defaults to 
                :py:attr:`None`.
        metakey_file (:py:attr:`str`, optional):
            Metadata key for the path to the file containing intensity data, 
                pointed to by the file parsed by parser. Takes the value 
                :py:attr:`None` if the file parsed by the parser contained the
                intensity data. Defaults to :py:attr:`None`.
        metakey_transmission (:py:attr:`str`, optional):
            Metadata key for the transmission. Defaults to :py:attr:`None`.
        metakey_roi_1_maxval (:py:attr:`str`, optional): 
            Metadata key for the maximum intensity value recorded by any pixel
                within the first region of interest in a detector. Defaults to
                :py:attr:`None`.
        metakey_roi_2_maxval (:py:attr:`str`, optional):
            Metadata key for the maximum intensity value recorded by any pixel
                within the second region of interest in a detector. Defaults to
                :py:attr:`None`.
        is_point_detector (:py:attr:`bool`, optional):
            :py:attr:`True` if the detector is a point detector. Defaults to 
                :: not is_2d_detector ::.
    """
    # TODO: build units into the detector dataclass, and automatically noramlize
    # units on initialization of a metadata instance.

    # a unique, readable ID for the detector name (e.g. "I07_pilatus")
    detector_name: str
    is_2d_detector: bool
    # mass of the probe particle, 0 for light
    probe_mass: float

    # When a file collected using this detector is parsed using a parser in
    # islatu.io, the parser will return a dictionary of metadata scraped from
    # the file. In different detectors, the same information will be stored
    # under different names. Below are the keys one should use for this
    # detector to access its metadata. These default to None, as one cannot
    # guarantee that detectors will yield metadata.
    metakey_detector_distance: str = None
    # energy of the incident probe particle
    metakey_probe_energy: str = None
    # this must only be not None when the parsed file points to data
    metakey_file: str = None
    metakey_transmission: str = None
    metakey_roi_1_maxval: str = None
    metakey_roi_2_maxval: str = None
    is_point_detector: bool = None

    def __post_init__(self):
        if self.is_point_detector is None:
            self.is_point_detector = not self.is_2d_detector


i07_pilatus_legacy = Detector(
    detector_name="I07_pilatus_pre_2020",
    is_2d_detector=True,
    probe_mass=0,
    metakey_detector_distance="diff1detdist",
    metakey_probe_energy="dcm1energy",
    metakey_file="file",
    metakey_transmission="transmission",
    metakey_roi_1_maxval="roi1_maxval"
)

# The pilatus from 2021 will output some metadata keys differently than it did
# pre-2020. But, these keys are not currently in use other than to distinguish
# between i07_pilatus and i07_pilatus_legacy
i07_pilatus = i07_pilatus_legacy

i07_excalibur_nxs = Detector(
    detector_name="i07_excalibur_saved_as_nexus",
    is_2d_detector=True,
    probe_mass=0,
    metakey_detector_distance="/root/entry/instrument/diff1detdist/value",
    metakey_probe_energy="/root/entry/instrument/dcm1energy/value",
    metakey_file="/root/entry/excroi_data/data",
    metakey_transmission="/root/entry/instrument/filterset/transmission",
    metakey_roi_1_maxval="Region_1_max_val",
    metakey_roi_2_maxval="Region_2_max_val"
)

i07_excalibur = Detector(
    detector_name="I07_Excalibur",
    is_2d_detector=True,
    probe_mass=0,
    metakey_detector_distance="diff1detdist",
    metakey_probe_energy="dcm1energy",
    metakey_file="CURRENTLY_BUGGED",  # TODO: fix when fixed!
    metakey_transmission="transmission",
    metakey_roi_1_maxval="Region_1_max_val",
    metakey_roi_2_maxval="Region_2_max_val"
)