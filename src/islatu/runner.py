from islatu import background
from islatu import corrections
from islatu import cropping
from islatu import image
from islatu import io
from islatu.io import i07_dat_to_dict_dataframe
from islatu.refl_profile import Profile
from islatu import stitching
from islatu import __version__
from islatu.debug import Debug
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import datetime
import os
from os import path
from ast import literal_eval as make_tuple
import numpy as np

function_map = {'gaussian_1d': background.fit_gaussian_1d,
                'roi_subtraction': None,
                'area': None,
                'i07': io.i07_nxs_parser,
                'crop': cropping.crop_2d,
                'crop_peak': cropping.crop_around_peak_2d,
                }


class Creator:
    def __init__(self, name='Unknown', affiliation='Unknown'):
        self.name = name
        self.affiliation = affiliation
        self.time = datetime.datetime.now()


class Origin:
    def __init__(self, contact='My Local Contact', facility='Diamond Light Source', id=None,
                 title=None, directory_path=None):
        self.contact = contact
        self.facility = facility
        self.id = id
        self.date = str(datetime.datetime.now())
        self.year = None
        self.title = title
        self.directory_path = directory_path


class Measurement:
    def __init__(self, scheme='q-dispersive',
                 q_range=[str(-np.inf), str(np.inf)],
                 theta_axis_name='dcdtheta', q_axis_name='qdcd',
                 transpose=False, qz_dimension=1, qxy_dimension=0,
                 pixel_max=1e6, hot_pixel_max=1e5):
        self.scheme = scheme
        self.q_range = q_range
        self.theta_axis_name = theta_axis_name
        self.q_axis_name = q_axis_name
        self.transpose = transpose
        self.qz_dimension = qz_dimension
        self.qxy_dimension = qxy_dimension
        self.pixel_max = pixel_max
        self.hot_pixel_max = hot_pixel_max


class Experiment:
    def __init__(self, instrument='i07', probe='xray', energy=12.5,
                 measurement=Measurement(), sample=None):
        self.instrument = instrument
        self.probe = probe
        self.energy = energy
        self.measurement = measurement
        self.sample = sample


class DataSource:
    def __init__(self, title, origin=Origin(), experiment=Experiment(),
                 links=None):
        self.origin = origin
        self.origin.title = title
        self.experiment = experiment
        self.links = links


class Software:
    def __init__(self, name='islatu', link='https://islatu.readthedocs.io',
                 version=__version__):
        self.name = name
        self.link = link
        self.version = version


class DataState:
    def __init__(self):
        self.background = None
        self.resolution = None
        self.dcd = None
        self.transmission = None
        self.intensity = None
        self.rebinned = None


class Reduction:
    def __init__(self, software=Software(), input_files=[],
                 data_state=DataState(), parser=io.i07_nxs_parser,
                 crop_function=cropping.crop_around_peak_2d, crop_kwargs=None,
                 bkg_function=background.fit_gaussian_1d, bkg_kwargs=None,
                 dcd_normalisation=None, sample_size=None, beam_width=None):
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
        self.beam_width = None


class Data:
    def __init__(self,
                 columns=['Qz / Aa^-1', 'RQz', 'sigma RQz, standard deviation',
                          'sigma Qz / Aa^-1, standard deviation'],
                 n_qvectors=50, q_min=None, q_max=None, q_step=None,
                 q_shape='log'):
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
    def __init__(self, run_numbers, yaml_file, directory, title):
        self.creator = Creator()
        self.data_source = DataSource(title)
        self.reduction = Reduction()
        self.data = Data()
        y_file = open(yaml_file, 'r')
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
        keys = recipe.keys()
        # Populate information from the visit section
        if 'visit' in keys:
            self.data_source.origin.id = recipe['visit']['visit id']
            if 'date' in recipe['visit'].keys():
                self.data_source.origin.date = datetime.datetime.strptime(
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
                "No visit given in {}. "
                "You must at least give a visit id".format(yaml_file))
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
                    yaml_file))
            if 'beam width' in recipe['setup'].keys():
                self.reduction.beam_width = make_tuple(recipe[
                    'setup']['beam width'])
                try:
                    _ = len(self.reduction.beam_width)
                    self.reduction.beam_width = self.reduction.beam_width[0]
                except TypeError:
                    pass
            else:
                raise ValueError("No beam width given in setup of {}.".format(
                    yaml_file))
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
            raise ValueError("No setup given in {}.".format(yaml_file))
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
                raise ValueError("Please define parameters of "
                                 "rebin in {}.".format(yaml_file))
        else:
            self.data.rebin = False


def i07reduce(run_numbers, yaml_file, directory='/dls/{}/data/{}/{}/',
              title='Unknown', log_lvl=1, filename=None,
              q_subsample_dicts=None):
    """
    The runner that parses the yaml file and performs the data reduction.

    run_numbers (:py:attr:`list` of :py:attr:`int`): 
        Reflectometry scans that make up the profile.
    yaml_file (:py:attr:`str`): 
        File path to instruction set.
    directory (:py:attr:`str`): 
        Outline for directory path.
    title (:py:attr:`str`): 
        A title for the experiment.
    log_lvl: 
        Degree of verbosity of logging requested.
    q_subsample_dicts: 
        A list of dictionaries, which takes the form:
            [{'scan_ID': ID, 'q_min': q_min, 'q_max': q_max},...]
        where type(ID) = str, type(q_min)=float, type(q_max)=float.
    """
    # First prepare our logger.
    debug = Debug(log_lvl)

    # Make sure the directory is properly formatted.
    if not str(directory).endswith("/"):
        directory = directory + "/"
    the_boss = Foreperson(run_numbers, yaml_file, directory, title)

    # Necessary to distnguish the same data processed by different pipelines.
    yaml_pipeline_name = yaml_file.split("/")[-1][:-5]

    files_to_reduce = the_boss.reduction.input_files

    debug.log("-" * 10)
    debug.log('File Parsing', unimportance=0)
    debug.log("-" * 10)
    refl = Profile.fromfilenames(files_to_reduce, the_boss.reduction.parser,
                                 log_lvl=log_lvl)

    debug.log("-" * 10)
    debug.log('Cropping', unimportance=0)
    debug.log("-" * 10)
    # Check to see if we should default to the ROI cropping regions
    if ((the_boss.reduction.crop_function is cropping.crop_2d) and
            the_boss.reduction.crop_kwargs is None):
        the_boss.reduction.crop_kwargs = {
            'x_start': refl.scans[0].metadata.roi_1_x1,
            'x_end': refl.scans[0].metadata.roi_1_x2,
            'y_start': refl.scans[0].metadata.roi_1_y1,
            'y_end': refl.scans[0].metadata.roi_1_y2
        }
        debug.log(
            "Crop region of interest (ROI) generated from excalibur's ROI.",
            unimportance=2)
        debug.log("Generated cropping kwargs:" +
                  str(the_boss.reduction.crop_kwargs), unimportance=2)
    refl.crop(the_boss.reduction.crop_function,
              the_boss.reduction.crop_kwargs)

    debug.log("-" * 10)
    debug.log('Subtracting Background', unimportance=0)
    debug.log("-" * 10)
    # Before subtracting background, make sure that, by default, we're at least
    # trying to subtract background from roi_2.
    if ((the_boss.reduction.bkg_function is None) and
            (the_boss.reduction.bkg_kwargs is None)):
        bkg_sub_kwargs = {
            'x_start': refl.scans[0].metadata.roi_2_x1,
            'x_end': refl.scans[0].metadata.roi_2_x2,
            'y_start': refl.scans[0].metadata.roi_2_y1,
            'y_end': refl.scans[0].metadata.roi_2_y2
        }
        the_boss.reduction.bkg_kwargs = bkg_sub_kwargs

    refl.bkg_sub(the_boss.reduction.bkg_function,
                 the_boss.reduction.bkg_kwargs)
    the_boss.reduction.data_state.background = 'corrected'

    debug.log("-" * 10)
    debug.log('Performing Data Corrections', unimportance=0)
    debug.log("-" * 10)
    if the_boss.reduction.dcd_normalisation is not None:
        itp = corrections.get_interpolator(
            the_boss.reduction.dcd_normalisation, i07_dat_to_dict_dataframe)
        refl.qdcd_normalisation(itp)
        the_boss.reduction.data_state.dcd = 'normalised'
        debug.log("Carried out DCD intensity normalization")
    refl.footprint_correction(
        the_boss.reduction.beam_width, the_boss.reduction.sample_size)
    debug.log("Carried out footprint correction")
    refl.transmission_normalisation()
    debug.log("Corrected for changes in beam attenuation")
    the_boss.reduction.data_state.transmission = 'normalised'
    refl.concatenate()
    if q_subsample_dicts is not None:
        # We'll need to subsample a subset of our scans.
        for q_subsample_dict in q_subsample_dicts:
            refl.subsample_q(**q_subsample_dict)
        debug.log("Limited q-range on specified scans.")

    debug.log("All correction steps completed for q-range: {}Å-{}Å.".format(
        np.min(refl.q), np.max(refl.q)
    ), unimportance=2)

    if the_boss.data.rebin:
        debug.log("-" * 10)
        debug.log('Rebinning the data.', unimportance=0)
        debug.log("-" * 10)
        if the_boss.data.q_min is None:
            debug.log("Linearly rebinning data into " +
                      str(the_boss.data.n_qvectors) + " uniformly spaced " +
                      "points in q-space.", unimportance=2)
            refl.rebin(number_of_q_vectors=the_boss.data.n_qvectors)
        else:
            if the_boss.data.q_space == 'linear':
                debug.log("Rebinning data linearly.", unimportance=2)
                spacing = np.linspace
            elif the_boss.data.q_space == 'log':
                debug.log("Rebinning data logarithmically", unimportance=2)
                spacing = np.logspace
            debug.log(
                "Spacing generated from " + str(refl.q.min()) + "Å to " +
                str(refl.q.max()) + "Å.", unimportance=2
            )
            refl.rebin(new_q=spacing(refl.q.min(), refl.q.max(),
                                     the_boss.data.q_step))
        the_boss.reduction.data_state.rebinned = the_boss.data.q_shape

    the_boss.data_source.experiment.measurement.q_range = [
        str(refl.q.min()), str(refl.q.max())]
    the_boss.data.n_qvectors = str(len(refl.R))

    # Prepare the data array.
    data = np.array([refl.q, refl.R, refl.R_e]).T
    debug.log("XRR reduction completed. q-range: {}Å-{}Å.".format(
        np.min(refl.q), np.max(refl.q)
    ), unimportance=2)

    # Work out where to save the file.
    datetime_str = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
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
        filename, data,
        header='{}\n Q(1/Å) R R_error'.format(dump(vars(the_boss))))

    debug.log("-" * 10)
    debug.log('Reduced Data Stored at {}'.format(filename), unimportance=0)
    debug.log("-" * 10)