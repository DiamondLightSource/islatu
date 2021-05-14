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
                pointed to by the file parsed by parser. 
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
                pointed to by the file parsed by parser. Defaults to 
                :py:attr:`None`.
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
    # this must only be not none when points_to_data is true
    metakey_file: str = None
    metakey_transmission: str = None
    metakey_roi_1_maxval: str = None
    metakey_roi_2_maxval: str = None
    is_point_detector: bool = not is_2d_detector


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

i07_excalibur = Detector(
    detector_name="I07_Excalibur",
    is_2d_detector=True,
    probe_mass=0,
    metakey_detector_distance="diff1detdist",
    metakey_probe_energy="dcm1energy",
    metakey_file="file",  # TODO UPDATE THIS!!!
    metakey_transmission="transmission",
    metakey_roi_1_maxval="Region_1_max_val",
    metakey_roi_2_maxval="Region_2_max_val"
)
