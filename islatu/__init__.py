"""
Structure of the module:

Profile(MeasurementBase):
    List<Scan> scans

Scan(MeasurementBase):
    Metadata metadata

Scan2D(Scan):
    List<Image> images
    ... and various image manipulation methods and suitable method overrides

MeasurementBase:
    Data data
    ... and convenience methods for the manipulation of the data

Metadata:
    Dict<string, PyObject> _scraped_metadata
    float probe_energy
    string detector_name
    bool is_2d_detector
    bool is_point_detector
    bool probe_mass
    bool detector_distance
    List<float> roi_maxvals
    string data_files
    ... and more (TBD)

Data:
    Array<float> q_vectors
    Array<float> theta
    Array<float> 2_theta
    Array<float> intensity


Workflow:

    profile = Profile(file_paths, parser)

    parser returns a Scan
"""

MAJOR = 0
MINOR = 0
MICRO = 60
__version__ = '%d.%d.%d' % (MAJOR, MINOR, MICRO)
