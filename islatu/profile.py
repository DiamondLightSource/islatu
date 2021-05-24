"""
A profile is a measurement resulting from a scan, or a series of scans. Profiles
are the central objects in the islatu library, containing the total reflected 
intensity as a function of scattering vector data.
"""

from islatu.data import Data, MeasurementBase


class Profile(MeasurementBase):
    def __init__(self, data: Data, scans: list) -> None:
        super().__init__(data)
        self.scans = scans
