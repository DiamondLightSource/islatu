"""
Module for testing the Data class, and the MeasurementBase class.
"""

import pytest
from pytest_lazyfixture import lazy_fixture as lazy
import numpy as np

from islatu.data import Data, MeasurementBase
from islatu.io import I07Nexus

# Fairly obvious disable for testing: we also need to test protected attrs.
# pylint: disable=protected-access


@pytest.mark.parametrize(
    'data',
    [lazy('generic_data_01'), lazy('generic_data_02')]
)
class TestDataSimple:
    """
    Simple tests for the Data class that don't require any additional fixtures.
    """

    def test_reflectivity_max(self, data: Data):
        """
        Make sure that max(reflectivity) is 1.
        """
        assert max(data.reflectivity) == 1


@pytest.mark.parametrize(
    'data, correct_intensity',
    [(lazy('generic_data_01'), np.arange(1100, 300, -45)[:10]),
     (lazy('generic_data_02'), (np.arange(11100012, 0, -12938)[:6]))]
)
def test_intensity_access(data, correct_intensity):
    """
    Make sure we can access data.intensity
    """
    assert (data.intensity == correct_intensity).all()


@pytest.mark.parametrize(
    'data, correct_intensity_e',
    [(lazy('generic_data_01'), np.sqrt(np.arange(1100, 300, -45)[:10])),
     (lazy('generic_data_02'), np.sqrt(np.arange(11100012, 0, -12938)[:6]))]
)
def test_intensity_e_access(data, correct_intensity_e):
    """
    Make sure we can access the I_e attribute.
    """
    assert(data.intensity_e == correct_intensity_e).all()


@pytest.mark.parametrize(
    'data,correct_energy',
    [(lazy('generic_data_01'), 12.5), (lazy('generic_data_02'), 8.04)])
def test_energy_access(data: Data, correct_energy):
    """
    Make sure we can access the data.energy attribute, and that it has the
    correct value.
    """
    assert data.energy == correct_energy


@pytest.mark.parametrize(
    'data, correct__theta',
    [(lazy('generic_data_01'), None), (lazy('generic_data_02'), np.arange(6))]
)
def test__theta_access(data: Data, correct__theta):
    """
    Make sure that we can access the _theta attribute, and that it has the
    correct values.
    """
    if correct__theta is not None:
        assert (data._theta == correct__theta).all()
    else:
        assert data._theta is correct__theta


@pytest.mark.parametrize(
    'data, correct__q',
    [
        (lazy('generic_data_01'), np.arange(10)/10),
        (lazy('generic_data_02'), None)
    ]
)
def test__q_access(data: Data, correct__q):
    """
    Make sure that we can access the data._q attribute, and that it has the
    correct value.
    """
    if correct__q is not None:
        assert (data._q == correct__q).all()
    else:
        assert correct__q is data._q


def test_conversion_to_q(generic_data_02: Data):
    """
    Check that we can correctly convert from theta to q. Basically any decent
    programmatic way of checking this would be completely circular: I would
    just re-implement the function I'm trying to test. So, I used a random
    online calculator to check the value against my function.
    """
    assert generic_data_02.q_vectors[1] == pytest.approx(0.142217, rel=1e-5)


def test_conversion_to_th(generic_data_01: Data):
    """
    Check that we can correctly convert from q to theta. As above, this number
    was calculated using online calculators. Don't hate the tester, hate the
    tests.
    """
    # Online calculator derped for these numbers so rel is small. These things
    # are dumb and throw away significant figures just for kicks.
    assert generic_data_01.theta[1] == pytest.approx(0.4525, rel=1e-3)


def test_measurement_base_metadata_type(measurement_base_01):
    """
    Make sure that our measurement base type is indeed I07Nexus. If it is, then
    the following tests just quickly make sure that its values have remained
    intact.
    """
    assert isinstance(measurement_base_01.metadata, I07Nexus)


def test_measurement_base_metadata_path(measurement_base_01,
                                        path_to_i07_nxs_01):
    """
    Make sure that we can access the metadata, and that its local_path is good.
    """
    assert measurement_base_01.metadata.local_path == path_to_i07_nxs_01


def test_measurement_base_metadata_energy(measurement_base_01):
    """
    Check that the metadata has the correct energy. The I07Nexus class
    """
    assert measurement_base_01.metadata.probe_energy == 12.5


def test_measurement_base_underlying_data(measurement_base_01: MeasurementBase,
                                          generic_data_01: Data):
    """
    Make sure that the instance of MeasurementBase has the same values of
    q, theta, intensity etc. as the instance of Data from which it was
    constructed.
    """
    # Note that, while there are multiple assertions here, they're really all
    # testing the same thing: pretty trivial attribute access, and equivalence
    # of parent and child for the subset of child that should be the same as
    # parent.
    assert (measurement_base_01._q == generic_data_01._q).all()
    assert measurement_base_01._theta == generic_data_01._theta
    assert (measurement_base_01.q_vectors == generic_data_01.q_vectors).all()
    assert (measurement_base_01.intensity == generic_data_01.intensity).all()
    assert (measurement_base_01.intensity_e ==
            generic_data_01.intensity_e).all()
    assert measurement_base_01.energy == generic_data_01.energy
    assert (measurement_base_01.reflectivity ==
            generic_data_01.reflectivity).all()
    assert (measurement_base_01.reflectivity_e ==
            generic_data_01.reflectivity_e).all()