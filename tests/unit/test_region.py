"""
This module tests the simple islatu.region module's Region class.
"""

from islatu.region import Region


def test_region_attr_access(region_01: Region):
    """
    Make sure that we can access a region's start and end attributes.
    """
    assert region_01.x_start == 1056
    assert region_01.x_end == 1124
    assert region_01.y_start == 150
    assert region_01.y_end == 250


def test_region_instantiation():
    """
    Make sure that regions correctly set their end to be after their start.
    """
    region = Region(2, 1, 4, 3)

    assert region.x_start == 1
    assert region.x_end == 2
    assert region.y_start == 3
    assert region.y_end == 4


def test_region_length(region_01: Region):
    """
    Make sure that regions have the correct length.
    """
    assert region_01.x_length == 1124 - 1056
    assert region_01.y_length == 250 - 150


def test_region_num_pixels(region_01: Region):
    """
    Make sure that regions are correctly calculating the number of pixels
    contained in them.
    """
    assert region_01.num_pixels == (1124 - 1056)*(250 - 150)


def test_region_equality(region_01: Region):
    """
    Make sure that out __eq__ method is working.
    """
    assert Region(1056, 1124, 150, 250) == region_01
