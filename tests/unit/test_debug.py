"""
This module contains a couple of simple tests for Islatu's debugger.
"""

from islatu.debug import debug


def test_debug_default_log_lvl():
    """
    Make sure that the debugger starts out with a logging_lvl of 1.
    """
    assert debug.logging_level == 1


def test_debug_log_lvl_change():
    """
    Make sure that we can change the logging level, if required.
    """
    debug.logging_level = 2
    assert debug.logging_level == 2
    debug.logging_level = 1
    assert debug.logging_level == 1
