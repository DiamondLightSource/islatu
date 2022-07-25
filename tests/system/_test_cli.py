"""
This module tests the command line interface to islatu.
"""

import os
import subprocess

import numpy as np


def test_process_xrr_01(process_xrr_path):
    """
    Make sure that we raise a FileNotFoundError when there's no file to be
    processed by the process_xrr script.
    """
    proc = subprocess.run(
        [process_xrr_path], capture_output=True, text=True
    )

    error_type = proc.stderr.split('\n')[3].split(':')[0].strip()
    assert error_type == "FileNotFoundError"


def test_process_xrr_02(process_xrr_path, path_to_resources, tmp_path,
                        old_dcd_data):
    """
    Make sure that the processing is running, and that it is producing
    acceptable results.
    """
    yaml_path = path_to_resources + os.sep + "dcd.yaml"
    proc = subprocess.run(
        [process_xrr_path, '-d', path_to_resources, '-y', yaml_path,
         '-o', tmp_path],
        capture_output=True, text=True
    )

    # Make sure no errors were thrown during reduction.
    # This will only print if the assertion fails.
    print(proc.stdout)
    print(proc.stderr)
    assert proc.stdout.split('\n')[204].strip().startswith(
        "Reduced data stored at "
    )

    # Make sure that the saved data is correct.
    reduced_data = np.loadtxt(os.path.join(tmp_path, os.listdir(tmp_path)[0]))
    assert np.allclose(reduced_data[0], old_dcd_data[0], 1e-3)
    assert np.allclose(reduced_data[1], old_dcd_data[1], 1e-3)
    assert np.allclose(reduced_data[2], old_dcd_data[2], 1e-3)


def test_process_xrr_03(process_xrr_path, path_to_resources, tmp_path,
                        old_dcd_data):
    """
    Make sure that we can subsample q, and that we can select only specific
    scan numbers.
    """
    yaml_path = path_to_resources + os.sep + "dcd.yaml"
    proc = subprocess.run(
        [process_xrr_path, '-d', path_to_resources, '-y', yaml_path,
         '-o', tmp_path], capture_output=True, text=True)

    # Make sure no errors were thrown during reduction.
    # This will only print if the assertion fails.
    print(proc.stdout)
    print(proc.stderr)
    assert proc.stdout.split('\n')[204].strip().startswith(
        "Reduced data stored at "
    )

    # Make sure that the saved data is correct.
    reduced_data = np.loadtxt(os.path.join(tmp_path, os.listdir(tmp_path)[0]))
    assert np.allclose(reduced_data[0], old_dcd_data[0], 1e-3)
    assert np.allclose(reduced_data[1], old_dcd_data[1], 1e-3)
    assert np.allclose(reduced_data[2], old_dcd_data[2], 1e-3)
