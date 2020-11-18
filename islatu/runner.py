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
                'guassian_2d': background.fit_gaussian_2d,
                'i07': io.i07_dat_parser,
                'crop': cropping.crop_2d,
                'crop_peak': cropping.crop_around_peak_2d,
                }

metadata = {'creator': {'name': 'Unknown',
                        'affiliation': 'Unknown',
                        'time': 000000},
            'data source': {'origin': {'local contact': 'Unknown',
                                       'facility': 'Diamond Light Source',
                                       'experiment ID': 000000,
                                       'experiment date': 000000,
                                       'title': 'Unknown'},
                            'experiment': {'instrument': 'i07',
                                           'probe': 'xray',
                                           'energy': 12.5,
                                           'measurement': {'scheme': 'q-dispersive',
                                                           'q range': 'Unknown'},
                                           'sample': 'Unknown'}
                            },
            'reduction': {'software': {'name': 'islatu',
                                       'link': 'https://islatu.readthedocs.io',
                                       'version': __version__},
                          'yaml': 'Unknown',
                          'input files': {'datafiles': []},
                          'data state': {}},
            'data': {}
            }

class Foreperson:
    def __init__(self, metadata):
        self.parser = None
        self.year = datetime.datetime.now().year
        self.directory_path = None
        self.crop_function = function_map['crop_peak']
        self.crop_kwargs = None
        self.bkg_function = function_map['gaussian_1d']
        self.bkg_kwargs = None
        self.dcd_normalisation = None
        self.sample_size = None
        self.beam_width = None
        self.n_qvectors = 50
        self.q_min = None
        self.q_max = None
        self.q_step = None
        self.q_shape = 'linear'
        self.n_columns = 3
        self.theta_axis_name = "dcdtheta"
        self.q_axis_name = "qdcd"
        self.transpose = False
        self.qz_dimension = 1
        self.qxy_dimension = 0
        self.pixel_max = 1e6
        self.hot_pixel_max = 1e5
        self.metadata = metadata

    def ready(self, directory):
        directory_path = directory.format(self.metadata['data source']['experiment']['instrument'], self.year, self.metadata['data source']['origin']['experiment ID'])
        if path.isdir(directory_path):
            self.directory_path = directory_path
        else:
            raise FileNotFoundError("The experiment directory cannot be found.")

def reduce(run_numbers, yaml_file, directory='/dls/{}/data/{}/{}/', metadata=metadata, title='Unknown'):
    """
    The runner that parses the yaml file and performs the data reduction.

    run_numbers (:py:attr:`list` of :py:attr:`int`): Reflectometry scans that
        make up the profile.
    yaml_file (:py:attr:`str`): File path to instruction set.
    metadata (:py:attr:`dict`): If metadata should be included in the outpuit
        file, pass this as a :py:attr:`dict`.
    title (:py:attr:`str`): A title for the experiment.
    """
    the_boss = Foreperson(metadata)
    y_file = open(yaml_file, 'r')
    recipe = load(y_file, Loader=Loader)
    y_file.close()
    the_boss.metadata['data source']['origin']['local contact'] = recipe['visit']['local contact']
    the_boss.metadata['data source']['origin']['experiment date'] = str(datetime.datetime.now().date())
    the_boss.metadata['data source']['origin']['title'] = title
    the_boss.metadata['creator']['name'] = recipe['visit']['user']
    the_boss.metadata['creator']['affiliation'] = recipe['visit']['user affiliation']
    the_boss.metadata['reduction']['yaml'] = yaml_file
    the_boss.metadata['reduction']['input files']['datafile'] = [self.directory_path + str(r) for r in run_numbers]
    keys = recipe.keys()
    if 'instrument' in keys:
        the_boss.metadata['data source']['experiment']['instrument'] = recipe['instrument']
        the_boss.parser = function_map[recipe['instrument']]
    else:
        raise ValueError("No instrument given in {}.".format(yaml_file))
    if 'visit' in keys:
        the_boss.metadata['data source']['origin']['experiment ID'] = recipe['visit']['visit id']
        if 'year' in recipe['visit'].keys():
            the_boss.year = recipe['visit']['year']
    else:
        raise ValueError("No visit given in {}.".format(yaml_file))
    if 'crop' in keys:
        the_boss.crop_function = function_map[recipe['crop']['method']]
        if 'kwargs' in recipe['crop']:
            the_boss.crop_kwargs = recipe['crop']['kwargs']
    if 'background' in keys:
        the_boss.bkg_function = function_map[recipe['background']['method']]
        if 'kwargs' in recipe['background']:
            the_boss.bkg_kwargs = recipe['background']['kwargs']
    if 'setup' in keys:
        if 'dcd normalisation' in recipe['setup'].keys():
            the_boss.dcd_normalisation = recipe['setup']['dcd normalisation']
            the_boss.metadata['data source']['links'] = {'instrument reference': 'doi:10.1107/S0909049512009272'}
        if 'sample size' in recipe['setup'].keys():
            the_boss.sample_size = make_tuple(recipe['setup']['sample size'])
            try:
                _ = len(the_boss.sample_size)
                the_boss.sample_size = ufloat(the_boss.sample_size[0], the_boss.sample_size[1])
            except TypeError:
                pass
        else:
            raise ValueError("No sample size given in setup of {}.".format(yaml_file))
        if 'beam width' in recipe['setup'].keys():
            the_boss.beam_width = make_tuple(recipe['setup']['beam width'])
            try:
                _ = len(the_boss.beam_width)
                the_boss.beam_width = ufloat(the_boss.sample_size[0], the_boss.sample_size[1])
            except TypeError:
                pass
        else:
            raise ValueError("No beam width given in setup of {}.".format(yaml_file))
        if 'theta_axis' in recipe['setup'].keys():
            the_boss.theta_axis_name = recipe['setup']['theta_axis']
        if 'q axis' in recipe['setup'].keys():
            the_boss.q_axis_name = recipe['setup']['q axis']
        if 'transpose' in recipe['setup'].keys():
            the_boss.transpose = recipe['setup']['transpose']
            if the_boss.transpose:
                the_boss.qz_dimension = 0
                the_boss.qxy_dimension = 1
        if 'pixel_max' in recipe['setup'].keys():
            the_boss.pixel_max = recipe['setup']['pixel_max']
        if 'hot_pixel_max' in recipe['setup'].keys():
            the_boss.hot_pixel_max = recipe['setup']['hot_pixel_max']
    else:
        raise ValueError("No setup given in {}.".format(yaml_file))
    if 'rebin' in keys:
        if 'n qvectors' in recipe['rebin'].keys():
            the_boss.n_qvectors = recipe['rebin']['n qvectors']
        elif 'min' in recipe['rebin'].keys() and 'max' in recipe['rebin'].keys() and 'step' in recipe['rebin'].keys():
            the_boss.q_min = recipe['rebin']['min']
            the_boss.q_max = recipe['rebin']['max']
            the_boss.q_step = recipe['rebin']['step']
            if 'shape' in recipe['rebin'].keys():
                the_boss.q_shape = recipe['rebin']['shape']
        else:
            raise ValueError("Please define parameters of rebin in {}.".format(yaml_file))
    if 'output_columns' in keys:
        the_boss.output_columns = recipe['output_columns']

    the_boss.ready(directory)

    files_to_reduce = []
    for f in run_numbers:
        files_to_reduce.append(the_boss.directory_path + f + '.dat')


    print("-" * 10)
    print('File Parsing')
    print("-" * 10)
    refl = refl_data.Profile(files_to_reduce, the_boss.parser, the_boss.q_axis_name,
                             the_boss.theta_axis_name, None, 0, the_boss.pixel_max,
                             the_boss.hot_pixel_max, the_boss.transpose)
    print("-" * 10)
    print('Cropping')
    print("-" * 10)
    refl.crop(the_boss.crop_function, the_boss.crop_kwargs)

    print("-" * 10)
    print('Background Subtraction')
    print("-" * 10)
    refl.bkg_sub(the_boss.bkg_function, the_boss.bkg_kwargs)
    the_boss.metadata['reduction']['data state']['background'] = 'corrected'

    print("-" * 10)
    print('Estimating Resolution Function')
    print("-" * 10)
    refl.resolution_function(the_boss.qz_dimension, progress=True)
    the_boss.metadata['reduction']['data state']['resolution'] = 'estimated'

    print("-" * 10)
    print('Performing Data Corrections')
    print("-" * 10)
    if the_boss.dcd_normalisation is not None:
        itp = corrections.get_interpolator(the_boss.dcd_normalisation, the_boss.parser)
        refl.qdcd_normalisation(itp)
        the_boss.metadata['reduction']['data state']['dcd'] = 'normalised'
    refl.footprint_correction(the_boss.beam_width, the_boss.sample_size)
    refl.transmission_normalisation()
    the_boss.metadata['reduction']['data state']['transmission'] = 'normalised'
    refl.concatenate()
    refl.normalise_ter()
    the_boss.metadata['reduction']['data state']['intensity'] = 'normalised'

    print("-" * 10)
    print('Rebinning')
    print("-" * 10)
    if the_boss.q_min is None:
        refl.rebin(number_of_q_vectors=the_boss.n_qvectors)
    else:
        if the_boss.q_space == 'linear':
            spacing = np.linspace
        elif the_boss.q_space == 'log':
            spacing = np.logspace
        refl.rebin(new_q=spacing(the_boss.q_min, the_boss.q_max, the_boss.q_step))
    the_boss.metadata['reduction']['data state']['rebinned'] = the_boss.q_shape

    the_boss.metadata['data source']['experiment']['measurement']['q range'] = [str(refl.q.min()), str(refl.q.max())]
    the_boss.metadata['data']['column 1'] = 'Qz / Aa^-1'
    the_boss.metadata['data']['column 2'] = 'RQz'
    the_boss.metadata['data']['column 3'] = 'sigma RQz, standard deviation'
    if the_boss.output_columns == 3:
        data = np.array([refl.q, refl.R, refl.dR]).T
        np.savetxt(the_boss.directory_path + '/processing/XRR_' + run_numbers[0] + '.dat', data, header='{}\n 1 2 3'.format(dump(the_boss.metadata)))
    elif the_boss.output_columns == 4:
        data = np.array([refl.q, refl.R, refl.dR, refl.dq]).T
        the_boss.metadata['data']['column 4'] = 'sigma Qz / Aa^-1, standard deviation'
        np.savetxt(the_boss.directory_path + '/processing/XRR_' + run_numbers[0] + '.dat', data, header='{}\n 1 2 3 4'.format(dump(the_boss.metadata)))
    print("-" * 10)
    print('Reduced Data Stored in Processing Directory')
    print("-" * 10)
