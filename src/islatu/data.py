"""
This module contains both the Data class and the MeasurementBase class.
In a reflectometry measurement, the experimental data corresponds to the
reflected intensity as a function of scattering vector Q. In a typical
diffractometer, Q is a virtual axis, calculated geometrically from various motor
positions. The Data class takes care of these conversions, exposing q, theta,
intensity, reflectivity, and energy.

The MeasurementBase class defines a simple class that is Data, but that also has
metadata.
"""

import numpy as np
from scipy.constants import physical_constants


class Data:
    """
        The base class of all Islatu objects that contain data.

        Attributes:
            intensity:
                A numpy array containing intensities in this dataset.
            intensity_e:
                A numpy array containing the corresponding errors in intensity.
            theta:
                A numpy array containing the probe particle's angle of
                incidence at each intensity.
            q_vectors:
                A numpy array containing the magnitude of the probe particle's
                scattering vector for each intensity value.
            energy:
                The energy of the probe particle used to acquire this data. This
                is necessary to swap between theta and q.

        Args:
            intensity:
                A numpy array of the intensities in this dataset.
            intensity_e:
                The errors on the intensities.
            energy:
                The energy of the probe particle used to acquire this data.
            theta:
                A numpy array containing the probe particle's angle of
                incidence at each intensity. NOTE: only one of theta/q needs to
                be provided.
            q_vectors:
                A numpy array containing the magnitude of the probe particle's
                scattering vector for each intensity value. NOTE: only one of
                theta/q needs to be provided.
        """

    def __init__(self, intensity, intensity_e, energy, theta=None,
                 q_vectors=None):

        self.intensity = intensity
        self.intensity_e = intensity_e
        self.energy = energy

        if (theta is None) and (q_vectors is None):
            raise ValueError(
                "Either theta or q must be provided to create a Data instance"
            )

        # When using properties, it wont matter which of these ends up as None.
        self._theta = theta
        self._q = q_vectors

    @property
    def reflectivity(self) -> np.array:
        """
        Returns the intensity, normalized such that the maximum value of the
        intensity is equal to 1. To acquire
        """
        return self.intensity/np.amax(self.intensity)

    @property
    def reflectivity_e(self) -> np.array:
        """
        Returns the errors on the intensity, divided by the maximum value of the
        intensity array.
        """
        return self.intensity_e/np.amax(self.intensity)

    @property
    def q_vectors(self) -> np.array:
        """
        Returns self._q if this instance of Data was generated from q-data.
        Otherwise, converts from self._theta to q.
        """
        if (self._q is None) and (self._theta is not None):
            return self._theta_to_q(self._theta, self.energy)
        else:
            return self._q

    @q_vectors.setter
    def q_vectors(self, value) -> None:
        """
        Sets self._q.
        """
        self._q = value

    @property
    def theta(self) -> np.array:
        """
        Returns self._theta if this instance of Data was generate from th-data.
        Otherwise, converts from scattered q to theta.
        """
        if (self._theta is None) and (self._q is not None):
            return self._q_to_theta(self._q, self.energy)
        else:
            return self._theta

    @theta.setter
    def theta(self, value) -> None:
        self._theta = value

    def _theta_to_q(self, theta, energy) -> np.array:
        """
        Calculates the scattering vector Q from diffractometer theta.

        Args:
            theta (:py:attr:`str`):
                Array of theta values to be converted.
            energy (:py:attr:`float`):
                Energy of the incident probe particle.
        """
        planck = physical_constants["Planck constant in eV s"][0] * 1e-3
        speed_of_light = physical_constants[
            "speed of light in vacuum"][0] * 1e10
        q_values = np.sin(np.radians(theta)) / (planck * speed_of_light)

        q_values *= energy * 4.0 * np.pi
        return q_values

    def _q_to_theta(self, q_values, energy) -> np.array:
        """
        Calculates the diffractometer theta from scattering vector Q.

        Args:
            theta (:py:attr:`str`):
                Array of theta values to be converted.
            energy (:py:attr:`float`):
                Energy of the incident probe particle.
        """
        planck = physical_constants["Planck constant in eV s"][0] * 1e-3
        speed_of_light = physical_constants[
            "speed of light in vacuum"][0] * 1e10
        theta_values = planck * speed_of_light * \
            np.arcsin(q_values / (energy * 4 * np.pi))

        theta_values = theta_values*180/np.pi

        return theta_values

    def remove_data_points(self, indices):
        """
        Convenience method for the removal of a specific data point by its
        index.

        Args:
            indices:
                The indices to be removed.
        """
        if self._q is not None:
            self._q = np.delete(self._q, indices)
        if self._theta is not None:
            self._theta = np.delete(self._theta, indices)

        self.intensity = np.delete(self.intensity, indices)
        self.intensity_e = np.delete(self.intensity_e, indices)


class MeasurementBase(Data):
    """
    All measurements derive from this class.

    Attrs:
        metadata:
            The metadata relevant to this measurement.
    """

    def __init__(self, intensity, intensity_e, energy, metadata, theta=None,
                 q=None) -> None:
        # Initialize the Data.
        super().__init__(intensity, intensity_e, energy, theta, q)
        # Store the metadata.
        self.metadata = metadata
