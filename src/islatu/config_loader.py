"""
module to load in process configurations and check against preset schemas
"""

import ast
import datetime

from schema import And, Optional, Or, Schema, SchemaError, Use


def validate_instrument(inst):
    """
    check instrument is from allowed types
    """
    valid_instruments = ["i07"]
    if inst not in valid_instruments:
        raise ValueError(
            f"instrument {inst} not in valid instrument list {valid_instruments}"
        )
    return True


def validate_crop_method(method):
    """
    check crop method is from allowed types
    """
    valid_methods = ["crop"]
    if method not in valid_methods:
        raise ValueError(
            f"method {method} not in valid crop method list {valid_methods}"
        )
    return True


def validate_background_method(method):
    """
    check background method is from allowed types
    """
    valid_methods = ["roi_subtraction", "None", "none"]
    if method not in valid_methods:
        raise ValueError(
            f"method {method} not in valid background method list {valid_methods}"
        )
    return True


def validate_new_axis(name):
    """
    check new axis name is from allowed types
    """
    valid_new_axes = ["diff1chi", "diff1delta", "diff2alpha"]
    if name not in valid_new_axes:
        raise ValueError(
            f"axis name {name} not in valid new axis list {valid_new_axes}"
        )
    return True


def validate_new_type(type):
    """
    check new axis type is from allowed types
    """
    valid_types = ["th", "tth", "q"]
    if type not in valid_types:
        raise ValueError(f" type {type} not in valid types list {valid_types}")
    return True


normalisation_schema = Schema(
    {
        "maxnorm": bool,
    }
)
transmission_schema = Schema(
    {
        "values": lambda t: (
            isinstance(t, list) and len(t) == 2 and all(isinstance(x, float) for x in t)
        ),
    }
)

setup_schema = Schema(
    {
        "sample size": And(
            Use(lambda s: ast.literal_eval(s)),  # Convert string to tuple
            lambda t: (
                isinstance(t, tuple)
                and len(t) == 2
                and all(isinstance(x, float) for x in t)
            ),
        ),
        "beam width": And(Use(float), lambda f: isinstance(f, float)),
        Optional("dcd normalisation"): str,
    }
)
visit_schema = Schema(
    {
        "local contact": str,
        "user": str,
        "user affiliation": str,
        "visit id": str,
        "date": And(lambda d: isinstance(d, datetime.date)),
    }
)

region_schema1 = Schema(
    {
        "x_start": int,
        "x_end": int,
        "y_start": int,
        "y_end": int,
    }
)

region_schema2 = Schema(
    {
        "x": int,
        "width": int,
        "y": int,
        "height": int,
    }
)

crop_schema = Schema(
    {
        "method": And(str, validate_crop_method),
        Optional("kwargs"): And(dict, Or(region_schema1, region_schema2)),
    }
)

background_schema = Schema(
    {
        "method": And(str, validate_background_method),
        Optional("kwargs"): And(dict, Or(region_schema1, region_schema2)),
    }
)


adjust_schema = Schema(
    {
        Optional("new_axis_name"): And(str, validate_new_axis),
        Optional("new_axis_type"): And(str, validate_new_type),
        Optional("theta_offset"): float,
        Optional("q_offset"): float,
    }
)

rebin_schema = Schema(
    {
        "n qvectors": int,
    }
)

config_schema = Schema(
    {
        "instrument": And(str, validate_instrument),
        "setup": setup_schema,
        "visit": visit_schema,
        Optional("crop"): crop_schema,
        Optional("background"): background_schema,
        Optional("adjustments"): adjust_schema,
        Optional("rebin"): rebin_schema,
        Optional("normalisation"): normalisation_schema,
        Optional("transmission"): transmission_schema,
        Optional("output_columns"): int,
    }
)


def check_config_schema(input_config: dict):
    """
    check a process configuration against define scheme
    """
    try:
        config_schema.validate(input_config)
        print("config values loaded")
        return True
    except SchemaError as se:
        raise se
