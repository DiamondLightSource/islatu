#!/usr/bin/env python3

"Command line interface for the Islatu library."

import argparse
import os
from islatu.runner import i07reduce
from islatu.debug import Debug


class FileNotFoundError(Exception):
    """
    A simple exception to throw when we can't find a file.
    """


if __name__ == "__main__":
    # First deal with the parsing of the command line arguments using the
    # argparse library.
    help_str = (
        "Command line interface to the Islatu library's autoprocessing " +
        "functionality."
    )
    parser = argparse.ArgumentParser(description=help_str)

    # The most important argument is the path to the data. If this is not
    # provided, we'll assume that we're in the data directory. Note that the
    # default argument is never passed to add_argument because the default
    # behaviour implemented here is too complex in some cases to be replaced by
    # simple hardcoded values. Instead, default values are calculated after
    # parse_args is called.
    help_str = (
        "Path to the directory in which the data is stored. If this " +
        "is not specified, your current directory will be used."
    )
    parser.add_argument("-d", "--data_path", help=help_str)

    help_str = (
        "Path to the .yaml recipe file. " +
        "If this is not specified, this module will search your data " +
        "directory, and data_path/processing/, for a .yaml file."
    )
    parser.add_argument("-y", "--yaml_path", help=help_str)

    help_str = (
        "Use this flag if you are on site in diamond and would like your " +
        "data to be processed on a cluster."
    )
    parser.add_argument("-c", "--cluster", help=help_str, action="store_true")

    help_str = (
        "Specify the first scan number to process. If this is not specified, " +
        "no lower bound on scan number will be placed on scans found in the " +
        "data directory. If neither lower nor upper bounds are placed, all  " +
        "scans found in the data directory will be used to construct a profile."
    )
    parser.add_argument("-l", "--lower_bound", help=help_str, type=int)

    help_str = (
        "Specify the final scan number to process. If this is not specified, " +
        "no upper bound will be placed on scan number for scans found in the " +
        "data directory."
    )
    parser.add_argument("-u", "--upper_bound", help=help_str, type=int)

    help_str = (
        "Directly specify the scan numbers to be used to construct the " +
        "profile. Simply sequentially list the scan numbers. Example usage: " +
        "python3 process_xrr.py --scan_numbers 401320 401321 401324 401326 " +
        "-d data/ -o processed_curves/. This argument overwrites -l and -u."
    )
    parser.add_argument("-N", "--scan_numbers",
                        help=help_str, nargs='*', type=int)

    help_str = (
        "Specify the directory in which you would like your processed " +
        "reflectivity curve to be stored. Defaults to your processing path."
    )
    parser.add_argument("-o", "--output", help=help_str)

    # A switch to allow verbosity toggle.
    help_str = "Increase output verbosity."
    parser.add_argument("-v", "--verbose", help=help_str, action="count")

    # Extract the arguments from the parser.
    args = parser.parse_args()

    # Now we need to generate default values of inputs, where required.
    # Default to local dir.
    if args.data_path is None:
        args.data_path = "./"

    # Default to data_path/processing/.
    if args.yaml_path is None:
        args.processing_path = args.data_path + "processing/"

    # Default to smallest possible scan number (0).
    if args.lower_bound is None:
        args.lower_bound = 0

    # Make a number that will always be bigger than all other numbers.
    if args.upper_bound is None:
        args.upper_bound = float('inf')

    # Output should be stored in the processing directory by default.
    if args.output is None:
        args.output = args.processing_path

    if args.verbose is None:
        args.verbose = 0
    # Set our logger according to requested verbosity.
    debug = Debug(args.verbose)

    # Now it's time to prepare to do some XRR reduction. If the user is in
    # diamond and wants to use a cluster, then we should go ahead and do that.
    if args.cluster:
        # We'll need a list of scans if this is being run on site.
        if args.scan_numbers is None:
            args.scan_numbers = list(
                range(args.lower_bound, args.upper_bound+1))

        # We'll need to load the cluster submitter script.
        from os import chdir
        submitter_module_path = "/dls/i07/scripts/staffScripts/autoProcessing/"
        chdir(submitter_module_path)
        from dls_resubmitter_core import DlsResubmitterCore

        # Now that everything is ready, submit the job.
        DlsResubmitterCore().activemq_data_processing(args.data_path,
                                                      args.scan_numbers)

    # If execution reaches here, we're processing the scan locally. First look
    # for the .yaml file if we weren't explicitly told where it is.
    if args.yaml_path is None:
        debug.log("Searching for .yaml files in '" + args.data_path +
                  "' and '" + args.processing_path + "'.")

        # Search in both the processing directory and the data directory.
        files = [
            args.processing_path + x for x in os.listdir(args.processing_path)]
        files.extend(os.listdir(args.data_path))
        yaml_files = [x for x in files if x.endswith(".yaml")]
        debug.log(".yaml files found: " + str(yaml_files))

        # If we didn't find exactly one .yaml file, complain.
        if len(yaml_files) != 1:
            generic_err_str = (
                "Could not uniquely determine location of .yaml file.\n" +
                "Searched directories " + args.processing_path + " and " +
                args.data_path + ".\n" + "Hoped to find exactly one file, " +
                "but found " + str(len(yaml_files)) + ". "
            )
            if len(yaml_files) > 1:
                generic_err_str += "Names of found files are: " + \
                    str(yaml_files) + "."
            raise FileNotFoundError(generic_err_str)
        else:
            # We only found one .yaml, so that's our guy.
            args.yaml_path = yaml_files[0]

    # If execution reaches here, we've successfully found the .yaml file.
    # Next lets try to work out what scan numbers are in the data directory if
    # we weren't told explicitly which scan numbers we should be looking at.
    if args.scan_numbers is None:
        debug.log(
            "Scan numbers not explicitly given. Searching for scans " +
            "in directory " + args.data_path + "."
        )
        # Grab every valid looking nexus file in the directory.
        nexus_files = [x for x in os.listdir(
            args.data_path) if x.endswith(".nxs")]

        # Make noise if we didn't find any .nxs files.
        generic_cant_find_nxs = (
            "Couldn't find any nexus (.nxs) files in the data directory '" +
            args.data_path
        )
        if len(nexus_files) == 0:
            raise FileNotFoundError(
                generic_cant_find_nxs + "'."
            )

        # So, we found some .nxs files. Now lets grab the scan numbers from
        # these files.
        debug.log("Scans located: " + str(nexus_files))
        nexus_files = [int(x.replace(".nxs", '').replace("i07-", ''))
                       for x in nexus_files]

        # Now select the subset of these scan numbers that lies within the
        # closed interval [args.lower_bound, args.upper_bound].
        args.scan_numbers = [x for x in nexus_files if
                             x >= args.lower_bound and x <= args.upper_bound]
        debug.log("Scan numbers found: " + str(args.scan_numbers) + ".", 2)

        # Make sure we found some scans.
        if len(args.scan_numbers) == 0:
            raise FileNotFoundError(
                generic_cant_find_nxs +
                " whose scan numbers were greater than or equal to " +
                str(args.lower_bound) +
                " and less than or equal to " + str(args.upper_bound) + "."
            )

    # If execution reaches here, we found the .yaml file and we have the scan
    # numbers we'll construct the XRR curve from. This is all that we need: a
    # recipe and some data; let's go ahead and process the data on this machine.
    i07reduce(args.scan_numbers, args.yaml_path, args.data_path,
              log_lvl=args.verbose)