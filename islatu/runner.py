from islatu import background
from islatu import corrections
from islatu import cropping
from islatu import image
from islatu import io
from islatu import refl_data
from islatu import stitching
from yaml import load, CLoader
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

class Foreperson:
    def __init__(self, metadata):
        self.parser = None
        self.visit_id = None
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
        self.theta_axis_name = None
        self.q_axis_name = "qdcd"
        self.transpose = False
        self.qz_dimension = 1
        self.qxy_dimension = 0
        self.pixel_max = 1e6
        self.hot_pixel_max = 1e5
        self.metadata = metadata
        self.creator = {'name': 'Unknown',
                        'affiliation': 'Unknown',
                        'time': datetime.datetime.now().isoformat()}
        self.data_source = {'experiment': {'probe': 'X-rays',
                                           'instrument': 'i07',
                                           'sample': None}}
        self.reduction = {'software': 'islatu', 'yaml': None}
        if self.n_columns == 3
            self.data = {'column 1': 'Qz / Aa^-1', 'column 2': 'RQz', 'column 3': 'sigma RQz , standard deviation'}
        elif self.n_columns == 4:
            self.data = {'column 1': 'Qz / Aa^-1', 'column 2': 'RQz', 'column 3': 'sigma RQz , standard deviation', 'column 4': 'dQz-by-Qz , resolution'}
        if 'creator' in metadata.keys():
            self.creator = metadata['creator']
        if 'data source' in metadata.keys():
            self.data_source = metadata['data source']
        self.header = None


    def ready(self, directory):
        directory_path = directory.format(self.data_source['experiment']['instrument'], self.year, self.visit_id)
        if path.isdir(directory_path):
            self.directory_path = directory_path
        else:
            raise FileNotFoundError("The experiment directory cannot be found.")
        self.header = f' creator:\n   name:{
            self.creator['name']}\n   affiliation:{
            self.creator['affiliation']}\n   time:{
            self.creator['time']}\n data source:\n   experiment:\n     probe:{
            self.data_source['experiment']['probe']}\n     instrument:{
            self.data_source['experiment']['instrument']}\n     sample:{
            self.data_source['experiment']['sample']}\n reduction:\n   software:{
            self.reduction['software']}\n   yaml:{
            self.reduction['yaml']}\n data:\n   column 1:{
            self.data['column 1']}\n   column 2:{
            self.data['column 2']}\n   column 3:{
            self.data['column 3']}'
        if self.n_columns == 4:
            self.header += '\n   column 4:{
            self.data['column 4']}'

def reduce(run_numbers, yaml_file, directory='/dls/{}/data/{}/{}/', metadata=None):
    """
    The runner that parses the yaml file and performs the data reduction.

    run_numbers (:py:attr:`list` of :py:attr:`int`): Reflectometry scans that
        make up the profile.
    yaml_file (:py:attr:`str`): File path to instruction set.
    metadata (:py:attr:`dict`): If metadata should be included in the outpuit
        file, pass this as a :py:attr:`dict`.
    """1
    the_boss = Foreperson(metadata)
    y_file = open(yaml_file, 'r')
    recipe = load(y_file, Loader=CLoader)
    y_file.close()
    the_boss.reduction['yaml'] = yaml_file
    keys = recipe.keys()
    if 'instrument' in keys:
        the_boss.self.data_source['experiment']['instrument'] = recipe['instrument']
        the_boss.parser = function_map[recipe['instrument']]
    else:
        raise ValueError("No instrument given in {}.".format(yaml_file))
    if 'visit' in keys:
        the_boss.visit_id = recipe['visit']['visit_id']
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
        if 'dcd_normalisation' in recipe['setup'].keys():
            the_boss.dcd_normalisation = recipe['setup']['dcd_normalisation']
        if 'sample_size' in recipe['setup'].keys():
            the_boss.sample_size = make_tuple(recipe['setup']['sample_size'])
            try:
                _ = len(the_boss.sample_size)
                the_boss.sample_size = ufloat(the_boss.sample_size[0], the_boss.sample_size[1])
            except TypeError:
                pass
        else:
            raise ValueError("No sample_size given in setup of {}.".format(yaml_file))
        if 'beam_width' in recipe['setup'].keys():
            the_boss.beam_width = make_tuple(recipe['setup']['beam_width'])
            try:
                _ = len(the_boss.beam_width)
                the_boss.beam_width = ufloat(the_boss.sample_size[0], the_boss.sample_size[1])
            except TypeError:
                pass
        else:
            raise ValueError("No beam_width given in setup of {}.".format(yaml_file))
        if 'theta_axis' in recipe['setup'].keys():
            the_boss.theta_axis_name = recipe['setup']['theta_axis']
        if 'q_axis' in recipe['setup'].keys():
            the_boss.q_axis_name = recipe['setup']['theta_axis']
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
        if 'n_qvectors' in recipe['rebin'].keys():
            the_boss.n_qvectors = recipe['rebin']['n_qvectors']
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

    print("-" * 10)
    print('Estimating Resolution Function')
    print("-" * 10)
    refl.resolution_function(the_boss.qz_dimension, progress=True)

    print("-" * 10)
    print('Performing Data Corrections')
    print("-" * 10)
    if the_boss.dcd_normalisation is not None:
        itp = corrections.get_interpolator(the_boss.dcd_normalisation, the_boss.parser)
        refl.qdcd_normalisation(itp)
    refl.footprint_correction(the_boss.beam_width, the_boss.sample_size)
    refl.transmission_normalisation()
    refl.concatenate()
    refl.normalise_ter()

    print("-" * 10)
    print('Rebinning')
    print("-" * 10)
    if the_boss.q_min is None:
        refl.rebin(number_of_q_vectors=the_boss.n_qvectors)
    else:
        if the_boss.q_space is 'linear':
            spacing = np.linspace
        elif the_boss.q_space is 'log':
            spacing = np.logspace
        refl.rebin(new_q=spacing(the_boss.q_min, the_boss.q_max, the_boss.q_step))

    if the_boss.output_columns == 3:
        data = np.array([refl.q, refl.R, refl.dR]).T
        np.savetxt(the_boss.directory_path + '/processing/' + run_numbers[0] + '.dat', data, header='{}'.format(the_boss.header))
    elif the_boss.output_columns == 4:
        data = np.array([refl.q, refl.R, refl.dR, refl.dq]).T
        np.savetxt(the_boss.directory_path + '/processing/' + run_numbers[0] + '.dat', data, header='{}'.format(the_boss.header))
    print("-" * 10)
    print('Reduced Data Stored in Processing Directory')
    print("-" * 10)
