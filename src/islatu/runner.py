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


try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from yaml import load, dump
import numpy as np

import islatu
from islatu import background
from islatu import corrections
from islatu import cropping
from islatu import io
from islatu.region import Region
from islatu.io import i07_dat_to_dict_dataframe
from islatu.refl_profile import Profile
from islatu.debug import debug


# This could be done by reflection, but it feels slightly less arcane to use
# this kind of function map. It also gives these scripts a little more
# flexibility.
function_map = {
    'roi_subtraction': background.roi_subtraction,
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


class Reduction:
    """
    This class contains all of the information pertaining to data reduction
    carried out on this reflectometry data.
    """

    def __init__(self, software=Software(), input_files=None,
                 data_state=DataState(), parser=io.i07_nxs_parser,
                 crop_function=cropping.crop_to_region, crop_kwargs=None,
                 bkg_function=background.fit_gaussian_1d, bkg_kwargs=None,
                 dcd_normalisation=None, sample_size=None, beam_width=None):
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
            if recipe['output columns'] == 3:
                self.data = Data(
                    columns=[
                        'Qz / Aa^-1', 'RQz', 'sigma RQz, standard deviation'])
            if recipe['output columns'] == 34:
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
              title='Unknown', filename=None,
              q_subsample_dicts=None):
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
    if not str(directory).endswith("/"):
        directory = directory + "/"
    the_boss = Foreperson(run_numbers, yaml_file, directory, title)

    # Necessary to distnguish the same data processed by different pipelines.
    yaml_pipeline_name = yaml_file.split("/")[-1][:-5]

    files_to_reduce = the_boss.reduction.input_files

    log_processing_stage("File parsing")
    refl = Profile.fromfilenames(files_to_reduce, the_boss.reduction.parser)

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
    else:
        the_boss.reduction.crop_kwargs = {
            'region': Region(**the_boss.reduction.crop_kwargs)
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
        else:
            the_boss.reduction.bkg_kwargs = {
                'list_of_regions': Region(**the_boss.reduction.bkg_kwargs)
            }
    else:
        raise NotImplementedError(
            "Tried to subtract background using not implemented method."
        )
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
    refl.transmission_normalisation()
    the_boss.reduction.data_state.transmission = 'normalised'
    refl.concatenate()

    if q_subsample_dicts is not None:
        log_processing_stage(
            "Doctoring data.\nSorry, I mean: Bounding q-vectors.")
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
    data = np.array([refl.q_vectors, refl.reflectivity, refl.reflectivity_e]).T
    debug.log("XRR reduction completed.", unimportance=2)

    # Work out where to save the file.
    datetime_str = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    dat_filename = 'XRR_{}_'.format(
        run_numbers[0]) + yaml_pipeline_name + datetime_str + ".dat"
    if filename is None:
        # Make sure that the processing directory exists.
        processing_path = the_boss.directory_path + 'processing/'
        if not os.path.exists(processing_path):
            os.makedirs(processing_path)
        # Now prepare the full path to the file
        filename = (processing_path + dat_filename)
    elif os.path.isdir(filename):
        # It's possible we were given a directory in which to save the created
        # file. In this case, use the filename variable as a directory and add
        # our auto generated filename to it.
        filename = os.path.join(filename, dat_filename)

    # Write the data.
    np.savetxt(
        filename, data, header=f"{dump(vars(the_boss))}\n Q(1/Å) R R_error"
    )

    debug.log("-" * 10)
    debug.log(f"Reduced data stored at {filename}", unimportance=0)
    debug.log("-" * 10)
