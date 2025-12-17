"""
This module contains functions whose purpose is simply to use the islatu
library to process data acquired from a specific instrument.
"""

from dataclasses import dataclass
from typing import List
from os import path
import os
from datetime import datetime
from ast import literal_eval as make_tuple
from types import SimpleNamespace
import os
from pathlib import Path
import subprocess
import time
import re
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from yaml import load, dump
import numpy as np

from islatu.debug import debug
import islatu
import islatu.background as background
import islatu.corrections as corrections
import islatu.cropping as cropping
import islatu.io as io
from islatu.region import Region
from islatu.io import i07_dat_to_dict_dataframe
from islatu.refl_profile import Profile
from islatu.debug import debug
from islatu.config_loader import check_config_schema


# This could be done by reflection, but it feels slightly less arcane to use
# this kind of function map. It also gives these scripts a little more
# flexibility.
function_map = {
    'roi_subtraction': background.roi_subtraction,
    'None': None,
    'i07': io.i07_nxs_parser,
    'crop': cropping.crop_to_region
}


@dataclass
class Creator:
    """
    Simple dataclass to store information relating to the person that created
    this dataset.
    """
    name: str = 'Unknown'
    affiliation: str = 'Unknown'
    time: datetime = datetime.now()


@dataclass
class Origin:
    """
    Simple dataclass to store information relating to the experiment.
    """
    contact: str = 'My local contact'
    facility: str = 'Diamond Light Source'
    id: str = None
    title: str = None
    directory_path: str = None
    date: str = str(datetime.now())
    year: str = None


@dataclass
class Measurement:
    """
    This dataclass stores measurement-specific metadata.
    """
    scheme: str = 'q-dispersive'
    q_range: List[str] = (str(-np.inf), str(np.inf))
    theta_axis_name: str = 'dcdtheta'
    q_axis_name: str = 'qdcd'
    transpose: bool = False
    qz_dimension: int = 1
    qxy_dimension: int = 0


@dataclass
class Experiment:
    """
    This dataclass stores more instrument-specific metadata.
    """
    instrument: str = 'i07'
    probe: str = 'x-ray'
    energy: float = 12.5
    measurement: Measurement = Measurement()
    sample: str = None


class DataSource:
    """
    This class stores information relating both to the experiment, and to the
    data processor.
    """

    def __init__(self, title, origin=Origin(), experiment=Experiment(),
                 links=None):
        self.origin = origin
        self.origin.title = title
        self.experiment = experiment
        self.links = links


@dataclass
class Software:
    """
    This dataclass stores information relating to the software used to carry
    out the any reduction/processing steps (in this case, islatu of course).
    """
    name: str = 'islatu'
    link: str = 'https://islatu.readthedocs.io'
    version: str = islatu.__version__


@dataclass
class DataState:
    """
    This class stores more reduction specific parameters.
    """

    background = None
    resolution = None
    dcd = None
    transmission = None
    intensity = None
    rebinned = None

@dataclass
class ProcessArgs:
    """
    a class to hold all information about the processing settings requested, and provide parsing checks, then job submission    
    """

    data_path: str
    yaml_path: str
    version_path: str
    python_version: str
    cluster: str | None = None
    lower_bound: int | None = None
    upper_bound: int | None = None
    scan_numbers: list[int] | None = None
    output: str | None = None
    limit_q: list[str] = None
    verbose: int = 0
    islatufolder= str = None
    jobfile_template: str = None
    jobfile_name: str = None



    def resolve_defaults(self):
        """
        cast all string paths into proper path objects
        """
        self.islatufolder = Path(self.islatufolder or Path.home() / "islatu")
        self.version_path = Path(self.version_path)
        self.data_path = Path(self.data_path)
        self.yaml_path = Path(self.yaml_path)
        self.output = Path(self.output or self.data_path / "processed")
        self.jobfile_template = Path(self.jobfile_template or self.version_path / "template.sh")
        self.jobfile_name = self.jobfile_name or "jobscript_local.sh"
        self.processing_path = self.data_path / "processing"

    def set_logging(self):

        if self.verbose is None:
            self.verbose = 0

        # Set islatu's logger to requested verbosity.
        debug.logging_lvl = self.verbose

    def parse_yaml(self):
        # If execution reaches here, we're processing the scan locally. First look
        # for the .yaml file if we weren't explicitly told where it is.
        if self.yaml_path is not None:
            return self
        debug.log("Searching for .yaml files in '" + self.data_path +
                    "' and '" + self.processing_path + "'.")

        # Search in both the processing directory and the data directory.
        files = []

        # Only check in the processing directory if it actually exists.
        if os.path.exists(self.processing_path):
            files.extend([self.processing_path + x
                            for x in os.listdir(self.processing_path)])

        # The data_path should definitely exist. If it doesn't, we shouldn't be
        # unhappy about an error being raised at this point.
        files.extend(os.listdir(self.data_path))

        # Work out which of these files are .yaml files.
        yaml_files = [x for x in files if x.endswith(".yaml")]
        debug.log(".yaml files found: " + str(yaml_files))

        # If we didn't find exactly one .yaml file, complain.
        if len(yaml_files) != 1:
            generic_err_str = (
                "Could not uniquely determine location of .yaml file.\n" +
                "Searched directories " + self.processing_path + " and " +
                self.data_path + ".\n" + "Hoped to find exactly one file, " +
                "but found " + str(len(yaml_files)) + ". "
            )
            if len(yaml_files) > 1:
                generic_err_str += "Names of found files are: " + \
                    str(yaml_files) + "."
            raise FileNotFoundError(generic_err_str)
        else:
            # We only found one .yaml, so that's our guy.
            self.yaml_path = yaml_files[0]

    def parse_scan_numbers(self):

        # Default to smallest possible scan number (0).
        if self.lower_bound is None:
            self.lower_bound = 0

        # Make a number that will always be bigger than all other numbers.
        if self.upper_bound is None:
            self.upper_bound = float('inf')



        # If execution reaches here, we've successfully found the .yaml file.
        # Next lets try to work out what scan numbers are in the data directory if
        # we weren't told explicitly which scan numbers we should be looking at.
        if self.scan_numbers is None:
            debug.log(
                "Scan numbers not explicitly given. Searching for scans " +
                "in directory " + str(self.data_path) + "."
            )
            # Grab every valid looking nexus file in the directory.
            nexus_files = [x for x in os.listdir(
                self.data_path) if x.endswith(".nxs")]

            # Make noise if we didn't find any .nxs files.
            generic_cant_find_nxs = (
                "Couldn't find any nexus (.nxs) files in the data directory '" +
                str(self.data_path)
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
            # closed interval [self.lower_bound, self.upper_bound].
            self.scan_numbers = [x for x in nexus_files if
                                x >= self.lower_bound and x <= self.upper_bound]
            self.scan_numbers.sort()
            debug.log("Scan numbers found: " + str(self.scan_numbers) + ".")

            # Make sure we found some scans.
            if len(self.scan_numbers) == 0:
                raise FileNotFoundError(
                    generic_cant_find_nxs +
                    " whose scan numbers were greater than or equal to " +
                    str(self.lower_bound) +
                    " and less than or equal to " + str(self.upper_bound) + "."
                )

    def parse_q_limits(self):
        if self.limit_q is not None:
            if len(self.limit_q) % 3 != 0:
                raise ValueError(
                    f"""
                    --limit_q must have a number of arguments passed to it that is
                    a multiple of three. Instead, {len(self.limit_q)} arguments were
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
            for i, _ in enumerate(self.limit_q):
                if i % 3 == 0:
                    # We're on a new scan, so we'll need a new subsample dict.
                    q_subsample_dicts.append({})

                    # Now grab that dict we just created and give it our new scan
                    # index. Note that if i%3 != 0, then we can skip the creation
                    # of a new dictionary.
                    q_subsample_dicts[-1]['scan_ID'] = self.limit_q[i]
                elif i % 3 == 1:
                    # Convert every 2nd and 3rd value to a float – these will be
                    # our q limits.
                    self.limit_q[i] = float(self.limit_q[i])
                    q_subsample_dicts[-1]['q_min'] = self.limit_q[i]
                elif i % 3 == 2:
                    # Convert every 2nd and 3rd value to a float – these will be
                    # our q limits.
                    self.limit_q[i] = float(self.limit_q[i])
                    q_subsample_dicts[-1]['q_max'] = self.limit_q[i]
            self.limit_q = q_subsample_dicts

    def create_jobscript(self):
        self.islatufolder=f'{Path.home()}/islatu'
        if not os.path.exists(self.islatufolder):
            os.makedirs(self.islatufolder)
        i=1
        self.save_path=f'{self.islatufolder}/jobscript_{i}.py'
        while (os.path.exists(str(self.save_path))):
            i += 1
            save_file_name = f'{self.islatufolder}/jobscript_{i}.py'
            self.save_path = Path(save_file_name)
            if i > 1e7:
                raise ValueError(
                    "naming counter hit limit therefore exiting ")   
        with open(self.save_path,'x') as f:
            f.write("from islatu.runner import i07reduce\n")
            f.write(f"scans = {self.scan_numbers}\nyamlpath='{self.yaml_path}'\ndatapath='{self.data_path}'\noutfile='{self.output}'\nqsubdict={self.limit_q}\n")
            f.write("i07reduce(scans, yamlpath, datapath,filename=outfile, q_subsample_dicts=qsubdict)")
        #f.write(f"i07reduce({self.scan_numbers}, {self.yaml_path}, {self.data_path},\
        #      filename={self.output}, q_subsample_dicts={self.limit_q})")

    def create_jobfile(self):
        if self.jobfile_template is None:
            self.jobfile_template: str = Path(f'{self.version_path}/islatu/CLI/islatuscript_template.sh')
        if self.jobfile_name is None:
            self.jobfile_name: str = 'jobscript_local.sh'
        #load in template mapscript, new paths
        with open(self.jobfile_template) as f:
            lines=f.readlines()

        self.jobfile=f'{self.islatufolder}//{self.jobfile_name}'
        if os.path.exists(self.jobfile):
            f=open(self.jobfile,'w')
        else:
            f=open(self.jobfile,'x')
        save_path=self.save_path
        for line in lines:
            phrase_matches=list(re.finditer(r'\${[^}]+\}',line))
            phrase_positions=[(match.start(),match.end()) for match in phrase_matches]
            outline=line
            for pos in phrase_positions:
                phrase=line[pos[0]:pos[1]]
                outphrase=phrase.strip('$').strip('{').strip('}')
                outline=outline.replace(phrase,str(locals()[f'{outphrase}']))
            f.write(outline)
        f.close()

    def check_slurmfiles(self):
        files=os.listdir(f'{Path.home()}/islatu')
        slurms=[x for x in files if '.out' in x]
        slurms.append(files[0])
        slurms.sort(key=lambda x: os.path.getmtime(f'{Path.home()}/islatu/{x}'))
        return slurms

    def run_cluster_job(self):

        self.create_jobscript()
        self.create_jobfile()

        startslurms=self.check_slurmfiles()
        endslurms=self.check_slurmfiles()
        count=0
        limit=0

        #call subprocess to submit job using wilson
        subprocess.run(["ssh","wilson",f"cd islatu \nsbatch {self.jobfile_name}"])
        while endslurms[-1]==startslurms[-1]:
            endslurms=self.check_slurmfiles()
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

    def parse_and_reduce(self):

        self.resolve_defaults()
        self.parse_yaml()
        self.parse_scan_numbers()
        self.parse_q_limits()
        if not self.cluster:
            i07reduce(self.scan_numbers, self.yaml_path, directory=self.data_path,
                filename=self.output, q_subsample_dicts=self.limit_q)
        else:
            self.run_cluster_job()


class Reduction:
    """
    This class contains all of the information pertaining to data reduction
    carried out on this reflectometry data.
    """

    def __init__(self, software=Software(), input_files=None,
                 data_state=DataState(), parser=io.i07_nxs_parser,
                 crop_function=cropping.crop_to_region, crop_kwargs=None,
                 bkg_function=background.fit_gaussian_1d, bkg_kwargs=None,
                 dcd_normalisation=None, sample_size=None, beam_width=None,
                 overwrite_transmission=None,normalisation=True,new_axis_name=None,new_axis_type=None):
        if input_files is None:
            input_files = []
        self.software = software
        self.input_files = input_files
        self.data_state = data_state
        self.parser = parser
        self.crop_function = crop_function
        self.crop_kwargs = crop_kwargs
        self.bkg_function = bkg_function
        self.bkg_kwargs = bkg_kwargs
        self.dcd_normalisation = dcd_normalisation
        self.sample_size = sample_size
        self.beam_width = beam_width
        self.overwrite_transmission=overwrite_transmission
        self.normalisation=normalisation
        self.new_axis_name=new_axis_name
        self.new_axis_type=new_axis_type


class Data:
    """
    This class stores information pertaining to the data collected in the
    experiment.
    """

    def __init__(self, columns=None, n_qvectors=50, q_min=None, q_max=None,
                 q_step=None, q_shape='linear'):
        if columns is None:
            columns = ['Qz / Aa^-1', 'RQz', 'sigma RQz, standard deviation',
                       'sigma Qz / Aa^-1, standard deviation']
        self.column_1 = columns[0]
        self.column_2 = columns[1]
        self.column_3 = columns[2]
        if len(columns) == 4:
            self.column_4 = columns[3]
        if columns == 'both':
            self.both = True
            self.column_4 = columns[3]
        self.rebin = True
        self.n_qvectors = n_qvectors
        self.q_min = q_min
        self.q_max = q_max
        self.q_step = q_step
        self.q_shape = q_shape


class Foreperson:
    """
    This class brings together all of the above classes and dataclasses into
    one big ball of yaml-able information.
    """

    def __init__(self, run_numbers, yaml_file, directory, title):
        self.creator = Creator()
        self.data_source = DataSource(title)
        self.reduction = Reduction()
        self.data = Data()
        self.yaml_file = yaml_file
        y_file = open(yaml_file, 'r', encoding='utf-8')
        recipe = load(y_file, Loader=Loader)
        y_file.close()

        self.setup(recipe)

        directory_path = directory.format(
            self.data_source.experiment.instrument,
            self.data_source.origin.year,
            self.data_source.origin.id)
        if path.isdir(directory_path):
            self.directory_path = directory_path
        else:
            raise FileNotFoundError(
                "The experiment directory <" + directory_path +
                "> cannot be found.")

        self.reduction.input_files = [
            self.directory_path + 'i07-' + str(r) + '.nxs' for r in run_numbers]

    def setup(self, recipe):
        """
        This is a McClusky special. I inherited it, and it works.
        Don't ask questions.
        """
        check_config_schema(recipe)

        keys = recipe.keys()
        # Populate information from the visit section
        if 'visit' in keys:
            self.data_source.origin.id = recipe['visit']['visit id']
            if 'date' in recipe['visit'].keys():
                self.data_source.origin.date = datetime.strptime(
                    str(recipe['visit']['date']), '%Y-%m-%d')
                self.data_source.origin.year = self.data_source.origin.date.year
            if 'local contact' in recipe['visit'].keys():
                self.data_source.origin.contact = recipe[
                    'visit']['local contact']
            if 'user' in recipe['visit'].keys():
                self.creator.name = recipe['visit']['user']
            if 'affiliation' in recipe['visit'].keys():
                self.creator.affiliation = recipe['visit']['user affiliation']
        else:
            raise ValueError(
                f"No visit given in {self.yaml_file}. " +
                "You must at least give a visit id")
        # Populate informatio from the information section
        if 'instrument' in keys:
            self.data_source.experiment.instrument = recipe['instrument']
            self.reduction.parser = function_map[recipe['instrument']]
        # Populate cropping information
        if 'crop' in keys:
            self.reduction.crop_function = function_map[
                recipe['crop']['method']]
            if 'kwargs' in recipe['crop']:
                self.reduction.crop_kwargs = recipe['crop']['kwargs']
        # Populate background subtraction method
        if 'background' in keys:
            self.reduction.bkg_function = function_map[
                recipe['background']['method']]
            if 'kwargs' in recipe['background']:
                self.reduction.bkg_kwargs = recipe['background']['kwargs']
        if 'transmission' in keys:
            self.reduction.overwrite_transmission=recipe['transmission']['values']
            
        if 'normalisation' in keys:
            self.reduction.normalisation=recipe['normalisation']['maxnorm']
            
        if 'adjustments'  in keys:
            if recipe['adjustments'] is not None:
                log_processing_stage("Setting adjustments")
                self.reduction.adjustments=SimpleNamespace(**recipe['adjustments'])
                for key,val in vars(self.reduction.adjustments).items():
                    debug.log(f'            {key} = {val}')
            # if 'new_axis_name' in recipe['adjustments'].keys():
            #     self.reduction.new_axis_name=recipe['adjustments']['new_axis_name']
            # if 'new_axis_type' in recipe['adjustments'].keys():
            #     self.reduction.new_axis_type=recipe['adjustments']['new_axis_type']
        # Populate the setup information
        if 'setup' in keys:
            if 'dcd normalisation' in recipe['setup'].keys():
                self.reduction.dcd_normalisation = recipe[
                    'setup']['dcd normalisation']
                self.data_source.links = {
                    'instrument reference': 'doi:10.1107/S0909049512009272'}
            if 'sample size' in recipe['setup'].keys():
                self.reduction.sample_size = make_tuple(recipe[
                    'setup']['sample size'])
                try:
                    _ = len(self.reduction.sample_size)
                    self.reduction.sample_size = self.reduction.sample_size[0]
                except TypeError:
                    pass
            else:
                raise ValueError("No sample size given in setup of {}.".format(
                    self.yaml_file))
            if 'beam width' in recipe['setup'].keys():
                self.reduction.beam_width = make_tuple(recipe[
                    'setup']['beam width'])
                try:
                    _ = len(self.reduction.beam_width)
                    self.reduction.beam_width = self.reduction.beam_width[0]
                except TypeError:
                    pass
            else:
                raise ValueError(
                    f"No beam width given in setup of {self.yaml_file}"
                )
            if 'theta axis' in recipe['setup'].keys():
                self.data_source.experiment.measurement.theta_axis_name = (
                    recipe['setup']['theta axis'])
            if 'q axis' in recipe['setup'].keys():
                self.data_source.experiment.measurement.q_axis_name = (
                    recipe['setup']['q axis'])
            if 'transpose' in recipe['setup'].keys():
                self.data_source.experiment.measurement.transpose = (
                    recipe['setup']['transpose'])
                if self.data_source.experiment.measurement.transpose:
                    self.data_source.experiment.measurement.qz_dimension = 0
                    self.data_source.experiment.measurement.qxy_dimension = 1
            if 'pixel max' in recipe['setup'].keys():
                self.data_source.experiment.measurement.pixel_max = recipe[
                    'setup']['pixel max']
            if 'hot pixel max' in recipe['setup'].keys():
                self.data_source.experiment.measurement.hot_pixel_max = recipe[
                    'setup']['hot pixel max']
        else:
            raise ValueError(f"No setup given in {self.yaml_file}.")
        if 'output_columns' in keys:
            if recipe['output_columns'] == 3:
                self.data = Data(
                    columns=[
                        'Qz / Aa^-1', 'RQz', 'sigma RQz, standard deviation'])
            if recipe['output_columns'] == 4:
                self.data = Data(columns='both')
        if 'rebin' in keys:
            if 'n qvectors' in recipe['rebin'].keys():
                self.data.n_qvectors = recipe['rebin']['n qvectors']
            elif 'min' in recipe['rebin'].keys() and 'max' in recipe[
                    'rebin'].keys() and 'step' in recipe['rebin'].keys():
                self.data.q_step = recipe['rebin']['step']
                if 'shape' in recipe['rebin'].keys():
                    self.data.q_shape = recipe['rebin']['shape']
            else:
                raise ValueError("Please define parameters of " +
                                 f"rebin in {self.yaml_file}.")
        else:
            self.data.rebin = False


def log_processing_stage(processing_stage):
    """
        Simple function to make logging slightly neater.
        """
    debug.log("-" * 10)
    debug.log(processing_stage, unimportance=0)
    debug.log("-" * 10)


def i07reduce(run_numbers, yaml_file, directory='/dls/{}/data/{}/{}/',
              title='Unknown', filename=None, q_subsample_dicts=None):
    """
    The runner that parses the yaml file and performs the data reduction.

    run_numbers (:py:attr:`list` of :py:attr:`int`):
        Reflectometry scans that make up the profile.
    yaml_file (:py:attr:`str`):
        File path to yaml config file
    directory (:py:attr:`str`):
        Outline for directory path.
    title (:py:attr:`str`):
        A title for the experiment.
    filename:
        Either a full path to the .dat file that will be produced by this
        function, or a directory. If a directory is given, then the filename
        will be automatically generated and the file will be placed in the
        specified directory.
    q_subsample_dicts:
        A list of dictionaries, which takes the form:
            [{'scan_ID': ID, 'q_min': q_min, 'q_max': q_max},...]
        where type(ID) = str, type(q_min)=float, type(q_max)=float.
    """

    # Make sure the directory is properly formatted.
    if not str(directory).endswith(os.sep):
        directory = str(directory) + os.sep
        the_boss = Foreperson(run_numbers, yaml_file, directory, title)

        # Necessary to distnguish the same data processed by different pipelines.
        yaml_pipeline_name = str(yaml_file).split(os.sep)[-1][:-5]

    files_to_reduce = the_boss.reduction.input_files

    log_processing_stage("File parsing")
    #return the_boss,files_to_reduce
    if hasattr(the_boss.reduction,"adjustments"):
        refl = Profile.fromfilenames(files_to_reduce, the_boss.reduction.parser,adjustments=the_boss.reduction.adjustments)
    else:
        refl = Profile.fromfilenames(files_to_reduce, the_boss.reduction.parser)

    # Set the energy correctly.
    the_boss.data_source.experiment.energy = refl.energy

    log_processing_stage("Cropping")
    # Currently, only crop_to_region is implemented.
    if the_boss.reduction.crop_function is not cropping.crop_to_region and \
            the_boss.reduction.crop_function is not None:
        raise NotImplementedError(
            "The only implemented cropping function is crop_to_region.")

    # Check to see if we were given an explicit cropping region. If not, use
    # the first (and likely only) signal region.
    if (the_boss.reduction.crop_function is cropping.crop_to_region and
            the_boss.reduction.crop_kwargs is None):
        roi = refl.scans[0].metadata.signal_regions[0]
        the_boss.reduction.crop_kwargs = {'region': roi}
        debug.log(f"Crop ROI '{str(roi)}' generated from the .nxs file.")
    elif 'x_end' in the_boss.reduction.crop_kwargs:
        the_boss.reduction.crop_kwargs = {
            'region': Region(**the_boss.reduction.crop_kwargs)
        }
    elif 'width' in the_boss.reduction.crop_kwargs:
        the_boss.reduction.crop_kwargs = {
            'region': Region.from_dict(region_dict=the_boss.reduction.crop_kwargs)
        }
    refl.crop(the_boss.reduction.crop_function,
              **the_boss.reduction.crop_kwargs)



    log_processing_stage("Subtracting background")
    # Before subtracting background, make sure that, by default, we're at least
    # trying to subtract background from roi_2.
    if the_boss.reduction.bkg_function is background.roi_subtraction:
        # Make sure we have the desired background regions.
        if the_boss.reduction.bkg_kwargs is None:
            the_boss.reduction.bkg_kwargs = {
                'list_of_regions': refl.scans[0].metadata.background_regions}
        elif 'x_end' in the_boss.reduction.bkg_kwargs:
            the_boss.reduction.bkg_kwargs = {
                'list_of_regions': Region(**the_boss.reduction.bkg_kwargs)
            }
        elif 'width' in the_boss.reduction.bkg_kwargs:
            the_boss.reduction.bkg_kwargs = {
                'list_of_regions': Region.from_dict(region_dict=the_boss.reduction.bkg_kwargs)
            }
    else:
        print("COULD NOT SUBTRACT BACKGROUND. SKIPPING...")
    if the_boss.reduction.bkg_function is not None:
        refl.bkg_sub(the_boss.reduction.bkg_function,
                      **the_boss.reduction.bkg_kwargs)
        the_boss.reduction.data_state.background = 'corrected'



    log_processing_stage("Performing data corrections...")
    if the_boss.reduction.dcd_normalisation is not None:
        log_processing_stage("DCD normalisation")
        itp = corrections.get_interpolator(
            the_boss.reduction.dcd_normalisation, i07_dat_to_dict_dataframe)
        refl.qdcd_normalisation(itp)
        the_boss.reduction.data_state.dcd = 'normalised'
    


    log_processing_stage("Footprint correction.")
    refl.footprint_correction(
        the_boss.reduction.beam_width, the_boss.reduction.sample_size)
    



    log_processing_stage("Transmission normalisation.")
    if the_boss.reduction.overwrite_transmission is not None:
        overwrite_transmissions=the_boss.reduction.overwrite_transmission
    else:
        overwrite_transmissions=None

    refl.transmission_normalisation(overwrite_transmissions)
    the_boss.reduction.data_state.transmission = 'normalised'
    refl.concatenate()


    if q_subsample_dicts is not None:
        log_processing_stage(
            "Bounding q-vectors.")
        # We'll need to subsample a subset of our scans.
        for q_subsample_dict in q_subsample_dicts:
            refl.subsample_q(**q_subsample_dict)
        debug.log("Limited q-range on specified scans.")
    


    # Rebin the data, if the user requested this.
    if the_boss.data.rebin:
        log_processing_stage("Rebinning the data.")
        if the_boss.data.q_min is None:
            debug.log("Linearly rebinning data into " +
                      str(the_boss.data.n_qvectors) + " uniformly spaced " +
                      "points in q-space.", unimportance=2)
            refl.rebin(number_of_q_vectors=the_boss.data.n_qvectors)
        else:
            if the_boss.data.q_shape == 'linear':
                debug.log("Rebinning data linearly.", unimportance=2)
                spacing = np.linspace
            elif the_boss.data.q_shape == 'log':
                debug.log("Rebinning data logarithmically", unimportance=2)
                spacing = np.logspace
            debug.log(
                f"Spacing generated from {refl.q_vectors.min()}Å to " +
                f"{refl.q_vectors.max()}Å.", unimportance=2
            )
            refl.rebin(new_q=spacing(refl.q_vectors.min(), refl.q_vectors.max(),
                                      the_boss.data.q_step))
        the_boss.reduction.data_state.rebinned = the_boss.data.q_shape

    the_boss.data_source.experiment.measurement.q_range = [
        str(refl.q_vectors.min()), str(refl.q_vectors.max())]
    the_boss.data.n_qvectors = str(len(refl.reflectivity))



    # Prepare the data array.
    if the_boss.reduction.normalisation==True:
        data = np.array([refl.q_vectors, refl.reflectivity, refl.reflectivity_e]).T
    elif the_boss.reduction.normalisation==False:
        data = np.array([refl.q_vectors, refl.reflectivity_nonorm, refl.reflectivity_e_nonorm]).T
    debug.log("XRR reduction completed.", unimportance=2)

    # Work out where to save the file.
    datetime_str = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    run_numbers.sort()
    dat_filename = 'XRR_{}_'.format(
        run_numbers[0]) + yaml_pipeline_name + datetime_str + ".dat"
    if filename is None:
        # Make sure that the processing directory exists.
        processing_path = path.join(the_boss.directory_path, 'processing')
        if not os.path.exists(processing_path):
            os.makedirs(processing_path)
        # Now prepare the full path to the file
        filename = (processing_path + dat_filename)
    if str(filename).endswith('processed'):
        if not os.path.exists(str(filename)):
            os.makedirs(str(filename)+'/')
    if os.path.isdir(str(filename)):
        # It's possible we were given a directory in which to save the created
        # file. In this case, use the filename variable as a directory and add
        # our auto generated filename to it.
        filename = os.path.join(str(filename), dat_filename)

    # Write the data.
    np.savetxt(
        filename, data, header=f"{dump(vars(the_boss))}\n Q(1/Å)\tR\tR_error"
    )

    debug.log("-" * 10)
    debug.log(f"Reduced data stored at {filename}", unimportance=0)
    debug.log("-" * 10)
