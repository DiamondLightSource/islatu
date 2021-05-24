"""
A profile is a measurement resulting from a scan, or a series of scans. Profiles
are the central objects in the islatu library, containing the total reflected 
intensity as a function of scattering vector data.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton and Andrew R. McCluskey

from islatu.stitching import concatenate
from islatu.data import Data, MeasurementBase


class Profile(MeasurementBase):
    def __init__(self, data: Data, scans: list) -> None:
        super().__init__(data)
        self.scans = scans

    @classmethod
    def fromfilenames(cls, filenames, parser, scan_axis_name):
        """
        Instantiate a profile from a list of scan filenames.

        Args:
            filenames (:py:attr:`list`): 
                List of files, one for each reflectometry scan. Can have length
                one.
            parser (:py:attr:`callable`): 
                Parser function for the reflectometry scan files.
            scan_axis_name (:py:attr:`str`, optional):
                Name of the independent variable scanned, typically a theta- or 
                q- axis.
        """
        # Load the scans.
        scans = [parser(filename, scan_axis_name) for filename in filenames]

        # Now that the individual scans have been loaded, data needs to be
        # constructed. The simplest way to do this is by concatenating the
        # data from each of the constituent scans.
        q_vectors, reflectivities = concatenate(scans)

        # Note: we are making the implicit assumption that energy is independent
        # of scan number at this point.
        energy = scans[0].metadata.probe_energy

        data = Data(None, reflectivities, energy, q_vectors)

        return cls(data, scans)
