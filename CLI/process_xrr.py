#!/usr/bin/env python3

"""Command line interface for the Islatu library."""

import argparse
from islatu.runner import ProcessArgs

version_path=__file__.split('islatu/CLI',maxsplit=1)[0]
python_version=version_path+'/conda_env/bin/python'

if __name__ == "__main__":
    # First deal with the parsing of the command line arguments using the
    # argparse library.
    HELP_STR = (
        "Command line interface to the Islatu library's autoprocessing " +
        "functionality."
    )
    parser = argparse.ArgumentParser(description=HELP_STR)

    # The most important argument is the path to the data. If this is not
    # provided, we'll assume that we're in the data directory. Note that the
    # default argument is never passed to add_argument because the default
    # behaviour implemented here is too complex in some cases to be replaced by
    # simple hardcoded values. Instead, default values are calculated after
    # parse_args is called.
    HELP_STR = (
        "Path to the directory in which the data is stored. If this " +
        "is not specified, your current directory will be used."
    )
    parser.add_argument("-d", "--data_path", help=HELP_STR)

    HELP_STR = (
        "Path to the .yaml recipe file. " +
        "If this is not specified, this module will search your data " +
        "directory, and data_path/processing/, for a .yaml file."
    )
    parser.add_argument("-y", "--yaml_path", help=HELP_STR)

    HELP_STR = (
        "Use this flag if you are on site in diamond and would like your " +
        "data to be processed on a cluster."
    )
    parser.add_argument("-c", "--cluster", help=HELP_STR, action="store_true")

    HELP_STR = (
        "Specify the first scan number to process. If this is not specified, " +
        "no lower bound on scan number will be placed on scans found in the " +
        "data directory. If neither lower nor upper bounds are placed, all  " +
        "scans found in the data directory will be used to construct a profile."
    )
    parser.add_argument("-l", "--lower_bound", help=HELP_STR, type=int)

    HELP_STR = (
        "Specify the final scan number to process. If this is not specified, " +
        "no upper bound will be placed on scan number for scans found in the " +
        "data directory."
    )
    parser.add_argument("-u", "--upper_bound", help=HELP_STR, type=int)

    HELP_STR = (
        "Directly specify the scan numbers to be used to construct the " +
        "profile. Simply sequentially list the scan numbers. Example usage: " +
        "python3 process_xrr.py --scan_numbers 401320 401321 401324 401326 " +
        "-d data/ -o processed_curves/. This argument overwrites -l and -u."
    )
    parser.add_argument("-N", "--scan_numbers",
                        help=HELP_STR, nargs='*', type=int)

    HELP_STR = (
        "Specify the directory in which you would like your processed " +
        "reflectivity curve to be stored. Defaults to data_path/processing/"
    )
    parser.add_argument("-o", "--output", help=HELP_STR)

    HELP_STR = (
        """
        Specify a list of scans whose q values should be limited, as well as the
        corresponding acceptable minimum and maximum q-values. For example:
            -Q 413243 0 0.4 413244 0.3 0.6 413248 0.8 inf
        Would ignore any q-values higher than 0.4 in scan 413243, would
        ignore any q-values smaller than 0.3 or larger than 0.6 in scan number
        413244, and would ignore any q-values lower than 0.8 present in scan
        number 413248. As implied in the example, a value of 0 indicates
        "no lower limit" and a value of inf indicates "no upper limit". In
        general, the numbers "413243" etc. given above must be unique to the
        name of the file from which the scan was parse
import sys
print(sys.executable)d.
        """
    )
    parser.add_argument("-Q", "--limit_q",
                        help=HELP_STR, nargs='*', type=str)

    HELP_STR = (
        "Specify a list of "
    )

    # A switch to allow verbosity toggle.
    HELP_STR = "Increase output verbosity. -v = verbose, -vv = very verbose!"
    parser.add_argument("-v", "--verbose", help=HELP_STR, action="count")

    # Extract the arguments from the parser.
    args = parser.parse_args()
    args.version_path=version_path
    args.python_version=python_version

    args.jobfile_template=f'{version_path}/islatu/CLI/islatuscript_template.sh'
    args.jobfile_name='jobscript_local.sh'

    process_args = ProcessArgs(**vars(args))
    process_args.parse_and_reduce()
