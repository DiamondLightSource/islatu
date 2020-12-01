from islatu import background
from islatu import corrections
from islatu import cropping
from islatu import image
from islatu import io
from islatu import refl_data
from islatu import stitching
from islatu import __version__
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import datetime
from os import path
from ast import literal_eval as make_tuple
from uncertainties import ufloat
import numpy as np

function_map = {'gaussian_1d': background.fit_gaussian_1d,
                'gaussian_2d': background.fit_gaussian_2d,
                'area': None,
                'i07': io.i07_dat_parser,
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
                 data_state=DataState(), parser=io.i07_dat_parser,
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
        if columns=='both':
            self.both = True
            self.column_4 = columns[3]
        self.rebin = True
        self.n_qvectors = n_qvectors
        self.q_step = q_step
        self.q_shape = 'linear'

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
                "The experiment directory cannot be found.")

        self.reduction.input_files = [
            self.directory_path + str(r) + '.dat' for r in run_numbers]


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
                "No visit given in {}. "\
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
                    self.reduction.sample_size = ufloat(
                        self.reduction.sample_size[0],
                        self.reduction.sample_size[1])
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
                    self.reduction.beam_width = ufloat(
                        self.reduction.beam_width[0],
                        self.reduction.beam_width[1])
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
                raise ValueError("Please define parameters of "\
                                 "rebin in {}.".format(yaml_file))
        else:
            self.data.rebin=False


def i07reduce(run_numbers, yaml_file, directory='/dls/{}/data/{}/{}/',
              title='Unknown'):
    """
    The runner that parses the yaml file and performs the data reduction.

    run_numbers (:py:attr:`list` of :py:attr:`int`): Reflectometry scans that
        make up the profile.
    yaml_file (:py:attr:`str`): File path to instruction set.
    directory (:py:attr:`str`): Outline for directory path.
    title (:py:attr:`str`): A title for the experiment.
    """
    the_boss = Foreperson(run_numbers, yaml_file, directory, title)

    files_to_reduce = the_boss.reduction.input_files


    print("-" * 10)
    print('File Parsing')
    print("-" * 10)
    refl = refl_data.Profile(files_to_reduce, the_boss.reduction.parser,
         the_boss.data_source.experiment.measurement.q_axis_name,
         the_boss.data_source.experiment.measurement.theta_axis_name,
         None, 0, the_boss.data_source.experiment.measurement.pixel_max,
         the_boss.data_source.experiment.measurement.hot_pixel_max,
         the_boss.data_source.experiment.measurement.transpose)

    print("-" * 10)
    print('Cropping')
    print("-" * 10)
    refl.crop(the_boss.reduction.crop_function, the_boss.reduction.crop_kwargs)

    print("-" * 10)
    print('Background Subtraction')
    print("-" * 10)
    refl.bkg_sub(the_boss.reduction.bkg_function,
                 the_boss.reduction.bkg_kwargs)
    the_boss.reduction.data_state.background = 'corrected'

    print("-" * 10)
    print('Estimating Resolution Function')
    print("-" * 10)
    refl.resolution_function(
        the_boss.data_source.experiment.measurement.qz_dimension,
        progress=True)
    the_boss.reduction.data_state.resolution = 'estimated'

    print("-" * 10)
    print('Performing Data Corrections')
    print("-" * 10)
    if the_boss.reduction.dcd_normalisation is not None:
        itp = corrections.get_interpolator(
            the_boss.reduction.dcd_normalisation, the_boss.reduction.parser)
        refl.qdcd_normalisation(itp)
        the_boss.reduction.data_state.dcd = 'normalised'
    refl.footprint_correction(
        the_boss.reduction.beam_width, the_boss.reduction.sample_size)
    refl.transmission_normalisation()
    the_boss.reduction.data_state.transmission = 'normalised'
    refl.concatenate()
    refl.normalise_ter()
    the_boss.reduction.data_state.intensity = 'normalised'

    if the_boss.data.rebin:
        print("-" * 10)
        print('Rebinning')
        print("-" * 10)
        if the_boss.data.q_min is None:
            refl.rebin(number_of_q_vectors=the_boss.data.n_qvectors)
        else:
            if the_boss.data.q_space == 'linear':
                spacing = np.linspace
            elif the_boss.data.q_space == 'log':
                spacing = np.logspace
            refl.rebin(new_q=spacing(refl.q.min(), refl.q.max(),
                                     the_boss.data.q_step))
        the_boss.reduction.data_state.rebinned = the_boss.data.q_shape

    the_boss.data_source.experiment.measurement.q_range = [
        str(refl.q.min()), str(refl.q.max())]
    the_boss.data.n_qvectors = str(len(refl.R))
    try:
        _ = the_boss.data.column_4
        data = np.array([refl.q, refl.R, refl.dR, refl.dq]).T
        np.savetxt(
            (the_boss.directory_path + '/processing/XRR_{}.dat'.format(
                run_numbers[0])), data,
             header='{}\n 1 2 3 4'.format(dump(vars(the_boss))))
        if the_boss.data.both:
            data = np.array([refl.q, refl.R, refl.dR]).T
            np.savetxt(
                (the_boss.directory_path + '/processing/XRR_{}_3col.dat'.format(
                    run_numbers[0])), data,
                 header='{}\n 1 2 3'.format(dump(vars(the_boss))))
    except:
        data = np.array([refl.q, refl.R, refl.dR]).T
        np.savetxt(
            (the_boss.directory_path + '/processing/XRR_{}.dat'.format(
                run_numbers[0])), data,
             header='{}\n 1 2 3'.format(dump(vars(the_boss))))

    print("-" * 10)
    print('Reduced Data Stored in Processing Directory')
    print("-" * 10)
