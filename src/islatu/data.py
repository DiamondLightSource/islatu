"""
This module contains both the Data class and the MeasurementBase class.
In a reflectometry measurement, the experimental data corresponds to the
reflected intensity as a function of scattering vector Q. In a typical
diffractometer, Q is a virtual axis, calculated geometrically from various motor
positions. The Data class takes care of these conversions, exposing q, theta,
intensity, reflectivity, and energy.

The MeasurementBase class defines a simple class that has Data, including
convenience properties to allow for the direct access of the Data and simple
data manipulation methods.
"""

# Copyright (c) 2021 Richard Brearton
# Copyright (c) Andrew R. McCluskey
# Distributed under the terms of the MIT License
# authors: Richard Brearton, Andrew R. McCluskey

import numpy as np
from scipy.constants import physical_constants


class Data:
    def __init__(self, intensity, intensity_e, energy, theta=None, q=None):
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
            q:
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
            q:
                A numpy array containing the magnitude of the probe particle's
                scattering vector for each intensity value. NOTE: only one of
                theta/q needs to be provided.
        """
        self.intensity = intensity
        self.intensity_e = intensity_e
        self.energy = energy

        if (theta is None) and (q is None):
            raise ValueError(
                "Either theta or q must be provided to create a Data instance"
            )

        # When using properties, it wont matter which of these ends up as None.
        self._theta = theta
        self._q = q

    @property
    def R(self) -> np.array:
        """
        Returns the intensity, normalized such that the maximum value of the
        intensity is equal to 1. To acquire
        """
        return self.intensity/np.amax(self.intensity)

    @property
    def R_e(self) -> np.array:
        """
        Returns the errors on the intensity, divided by the maximum value of the
        intensity array.
        """
        return self.intensity_e/np.amax(self.intensity)

    @property
    def q(self) -> np.array:
        if (self._q is None) and (self._theta is not None):
            return self._theta_to_q(self._theta, self.energy)
        else:
            return self._q

    @q.setter
    def q(self, value) -> None:
        self._q = value

    @property
    def theta(self) -> np.array:
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


class MeasurementBase:
    def __init__(self, data: Data) -> None:
        self.data = data

    # Define some properties to make accessing things in self.data a bit cleaner
    # and more intuitive.
    @property
    def q(self) -> np.array:
        return self.data.q

    @q.setter
    def q(self, value) -> None:
        self.data.q = value

    @property
    def theta(self) -> np.array:
        return self.data.theta

    @theta.setter
    def theta(self, value) -> None:
        self.data.theta = value

    @property
    def R(self):
        return self.data.R

    @property
    def R_e(self):
        return self.data.R_e

    @property
    def intensity(self) -> np.array:
        return self.data.intensity

    @intensity.setter
    def intensity(self, value):
        self.data.intensity = value

    @property
    def intensity_e(self) -> np.array:
        return self.data.intensity_e

    @intensity_e.setter
    def intensity_e(self, value):
        self.data.intensity_e = value

    def remove_data_points(self, indices):
        """
        Convenience method for the removal of a specific data point by its
        index.

        Args:
            idx:
                The index number to be removed.
        """
        if self.data._q is not None:
            self.data._q = np.delete(self.data._q, indices)
        if self.data._theta is not None:
            self.data._theta = np.delete(self.data._theta, indices)

        self.data.intensity = np.delete(self.data.intensity, indices)
        self.data.intensity_e = np.delete(self.data.intensity_e, indices)
