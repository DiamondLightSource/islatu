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
from uncertainties import unumpy as unp


class Data:
    def __init__(self, theta, intensity, energy, q=None) -> None:
        self._theta = theta
        self.intensity = intensity
        self.energy = energy
        self._q = q

    @property
    def R(self) -> unp.uarray:
        return self.intensity/unp.maximum(self.intensity)

    @property
    def q(self) -> unp.uarray:
        if (self._q is None) and (self._theta is not None):
            return self._theta_to_q(self._theta, self.energy)
        else:
            return self._q

    @q.setter
    def q(self, value) -> None:
        self._q = value

    @property
    def theta(self) -> unp.uarray:
        if (self._theta is None) and (self._q is not None):
            return self._q_to_theta(self._q, self.energy)
        else:
            return self._theta

    @theta.setter
    def theta(self, value) -> None:
        self._theta = value

    def _theta_to_q(self, theta, energy) -> unp.uarray:
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

        q_values = energy * 4 * np.pi * unp.sin(
            unp.radians(theta)) / (planck * speed_of_light)
        return unp.uarray(q_values, np.zeros(theta.size))

    def _q_to_theta(self, q_values, energy) -> unp.uarray:
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
            unp.arcsin(q_values / (energy * 4 * np.pi))

        return theta_values


class MeasurementBase:
    def __init__(self, data: Data) -> None:
        self.data = data

    # Define some properties to make accessing things in self.data a bit cleaner
    # and more intuitive.
    @property
    def q(self) -> unp.uarray:
        return self.data.q

    @q.setter
    def q(self, value) -> None:
        self.data.q = value

    @property
    def theta(self) -> unp.uarray:
        return self.data.theta

    @theta.setter
    def theta(self, value) -> None:
        self.data.theta = value

    @property
    def intensity(self):
        return self.data.intensity

    @intensity.setter
    def intensity(self, value):
        self.data.intensity = value
