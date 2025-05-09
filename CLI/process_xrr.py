#!/usr/bin/env python3


"Command line interface for the Islatu library."

import argparse
import os
from pathlib import Path
import subprocess
import time
import re

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
        "data to be processed on a cluster. (19/10/2021) Note: this is " +
        "currently finicky; if you *need* to get this to work email " +
        "richard.brearton@diamond.ac.uk"
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
        name of the file from which the scan was parsed.
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

    # Now we can import islatu. We need to do this after parsing args so that
    # the -h/--help option doesn't get slowed down by bad load times in hdf5/
    # nexusformat libs.
    from islatu.runner import i07reduce
    from islatu.debug import debug

    # Now we need to generate default values of inputs, where required.
    # Default to local dir.
    if args.data_path is None:
        args.data_path = os.getcwd()

    # Default to data_path/processing/.
    args.processing_path = os.path.join(args.data_path, "processing")

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

    # Set islatu's logger to requested verbosity.
    debug.logging_lvl = args.verbose


    # If execution reaches here, we're processing the scan locally. First look
    # for the .yaml file if we weren't explicitly told where it is.
    if args.yaml_path is None:
        debug.log("Searching for .yaml files in '" + args.data_path +
                  "' and '" + args.processing_path + "'.")

        # Search in both the processing directory and the data directory.
        files = []

        # Only check in the processing directory if it actually exists.
        if os.path.exists(args.processing_path):
            files.extend([args.processing_path + x
                          for x in os.listdir(args.processing_path)])

        # The data_path should definitely exist. If it doesn't, we shouldn't be
        # unhappy about an error being raised at this point.
        files.extend(os.listdir(args.data_path))

        # Work out which of these files are .yaml files.
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
        args.scan_numbers.sort()
        debug.log("Scan numbers found: " + str(args.scan_numbers) + ".")

        # Make sure we found some scans.
        if len(args.scan_numbers) == 0:
            raise FileNotFoundError(
                generic_cant_find_nxs +
                " whose scan numbers were greater than or equal to " +
                str(args.lower_bound) +
                " and less than or equal to " + str(args.upper_bound) + "."
            )

    if args.limit_q is not None:
        if len(args.limit_q) % 3 != 0:
            raise ValueError(
                f"""
                --limit_q must have a number of arguments passed to it that is
                a multiple of three. Instead, {len(args.limit_q)} arguments were
                found. Please use the pattern:
                    -L N1 qmin1 qmax1 N2 qmin2 qmax2 ...
                where N1 is a scan number, qmin1 is the minimum q for the
                scan with scan number N1, and qmax1 is the maximum acceptable q
                for the scan with scan number N1, etc.. Please refer to the
                --help for more information.
                """
            )
        # Okay, this is presumably properly formatted. Lets turn this into a
        # list of dictionaries that we can pass directly to the
        # profile.subsample_q method.
        q_subsample_dicts = []
        for i, _ in enumerate(args.limit_q):
            if i % 3 == 0:
                # We're on a new scan, so we'll need a new subsample dict.
                q_subsample_dicts.append({})

                # Now grab that dict we just created and give it our new scan
                # index. Note that if i%3 != 0, then we can skip the creation
                # of a new dictionary.
                q_subsample_dicts[-1]['scan_ID'] = args.limit_q[i]
            elif i % 3 == 1:
                # Convert every 2nd and 3rd value to a float – these will be
                # our q limits.
                args.limit_q[i] = float(args.limit_q[i])
                q_subsample_dicts[-1]['q_min'] = args.limit_q[i]
            elif i % 3 == 2:
                # Convert every 2nd and 3rd value to a float – these will be
                # our q limits.
                args.limit_q[i] = float(args.limit_q[i])
                q_subsample_dicts[-1]['q_max'] = args.limit_q[i]
        args.limit_q = q_subsample_dicts

    # If execution reaches here, we found the .yaml file and we have the scan
    # numbers we'll construct the XRR curve from. This is all that we need: a
    # recipe and some data; let's go ahead and process the data on this machine.
    # Now it's time to prepare to do some XRR reduction. If the user is in
    # diamond and wants to use a cluster, then we should go ahead and do that.
    if args.cluster:
        islatufolder=f'{Path.home()}/islatu'
        if not os.path.exists(islatufolder):
            os.makedirs(islatufolder)
        i=1
        save_path=f'{islatufolder}/jobscript_{i}.py'
        while (os.path.exists(str(save_path))):
            i += 1
            save_file_name = f'{islatufolder}/testscript_{i}.py'
            save_path = Path(save_file_name)
            if i > 1e7:
                raise ValueError(
                    "naming counter hit limit therefore exiting ")   
        f=open(save_path,'x')
        f.write("from islatu.runner import i07reduce\n")
        f.write(f"scans = {args.scan_numbers}\nyamlpath='{args.yaml_path}'\ndatapath='{args.data_path}'\noutfile='{args.output}'\nqsubdict={args.limit_q}\n")
        f.write("i07reduce(scans, yamlpath, datapath,filename=outfile, q_subsample_dicts=qsubdict)")
        #f.write(f"i07reduce({args.scan_numbers}, {args.yaml_path}, {args.data_path},\
        #      filename={args.output}, q_subsample_dicts={args.limit_q})")
        f.close()
            
        #load in template mapscript, new paths
        f=open('/dls_sw/apps/islatu/testing/islatu/CLI/islatuscript_template.sh')
        lines=f.readlines()
        f.close()
        jobfile=f'{islatufolder}//jobscript.sh'
        if os.path.exists(jobfile):
            f=open(jobfile,'w')
        else:
            f=open(jobfile,'x')
        for line in lines:
            if '$' in line:
                phrase=line[line.find('$'):line.find('}')+1]
                outphrase=phrase.strip('$').strip('{').strip('}')
                outline=line.replace(phrase,str(locals()[f'{outphrase}']))
                #print(outline)
                f.write(outline)
            else:
                f.write(line)
        f.close()
        
        #get list of slurm out files in home directory
        startfiles=os.listdir(f'{Path.home()}/islatu')
        startslurms=[x for x in startfiles if '.out' in x]
        startslurms.append(startfiles[0])
        startslurms.sort(key=lambda x: os.path.getmtime(f'{Path.home()}/islatu/{x}'))
        
        #get latest slurm file  before submitting job
        endfiles=os.listdir(f'{Path.home()}/islatu')
        endslurms=[x for x in endfiles if '.out' in x]
        endslurms.append(endfiles[0])
        endslurms.sort(key=lambda x: os.path.getmtime(f'{Path.home()}/islatu/{x}'))
        count=0
        limit=0

        #call subprocess to submit job using wilson
        subprocess.run(["ssh","wilson","cd islatu \nsbatch jobscript.sh"])
        while endslurms[-1]==startslurms[-1]:
            endfiles=os.listdir(f'{Path.home()}/islatu')
            endslurms=[x for x in endfiles if '.out' in x]
            endslurms.append(endfiles[0])
            endslurms.sort(key=lambda x: os.path.getmtime(f'{Path.home()}/islatu/{x}'))
            if count >50:
                limit=1
                break
            print(f'Job submitted, waiting for SLURM output.  Timer={5*count}',end="\r")
            time.sleep(5)
            count+=1
        if limit==1:
            print('Timer limit reached before new slurm ouput file found')
        else:
            print(f'Slurm output file: {Path.home()}/islatu//{endslurms[-1]}\n')
            breakerline='*'*35
            monitoring_line=f"\n{breakerline}\n ***STARTING TO MONITOR TAIL END OF FILE, TO EXIT THIS VIEW PRESS ANY LETTER FOLLOWED BY ENTER**** \n{breakerline} \n"
            print(monitoring_line)
            process = subprocess.Popen(["tail","-f",f"{Path.home()}/islatu//{endslurms[-1]}"], stdout=subprocess.PIPE, text=True)
            target_phrase="Reduced data stored"
            try:
                for line in process.stdout:
                    if "Loading images" in line:
                        print(line.strip(),'\n')
                    elif"Currently loaded" in line:
                        print(f"\r{line.strip()}", end='')
                    else:
                        print(line.strip())  # Print each line of output
                    if re.search(target_phrase, line):
                        print(f"Target phrase '{target_phrase}' found. Closing tail.")
                        break
                    if( "Errno" in line) or ("error" in line) or ("Error" in line):
                        print("error found. closing tail")
                        break
            finally:
                process.terminate()
                process.wait()
        print("Python script on cluster completed successfully")
        
    else:
        i07reduce(args.scan_numbers, args.yaml_path, args.data_path,
              filename=args.output, q_subsample_dicts=args.limit_q)
