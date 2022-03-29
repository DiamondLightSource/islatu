"""
This module tests the islatu.runner module's processing capabilities.
"""

import os

import numpy as np

from islatu.runner import i07reduce


def test_i07reduce_dcd(tmp_path, path_to_resources, old_dcd_data):
    """
    Tests the i07reduce function with DCD data.
    """
    # Do the reduction.
    run_numbers = range(404875, 404883)
    yaml_file = os.path.join(path_to_resources, "dcd.yaml")
    i07reduce(run_numbers, yaml_file, path_to_resources, filename=tmp_path)

    # Make sure that the saved data is correct.
    reduced_data = np.loadtxt(os.path.join(tmp_path, os.listdir(tmp_path)[0]))

    assert np.allclose(reduced_data[0], old_dcd_data[0], 1e-3)
    assert np.allclose(reduced_data[1], old_dcd_data[1], 1e-3)
    assert np.allclose(reduced_data[2], old_dcd_data[2], 1e-3)
