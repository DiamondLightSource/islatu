I07 YAML
========

A custom YAML input has been designed to enable the automated use of islatu at the I07 beamline.
Here we document all of the options that are available in this interface.

.. code-block:: yaml

   # This is the beamline being used (optional, default i07)
   instrument: i07
   visit:
     # The visit id
     visit id: siXXXXX-1
     # The name or names of the users (optional, default Unknown)
     user: A User & Their Friend
     # Where the user has come from (optional, default Unknown)
     user affiliation: Some University
     # The instrument scientist name (optional, default My Local Contact)
     local contact: A Local Contact
     # The current date (or starting date of the beamtime) (optional, default today)
     date: 2020-XX-XX
   setup:
     # Size of the sample if a tuple is passed these are taken as the value and uncertainty
     sample size: (9e-3, 1e-3)
     # Beam width at half maximum
     beam width: 180e-6
     # Full path to dcd normalisation file (required for dcd normalisation)
     dcd normalisation: /dls/i07/data/2020/si24357-1/380396.dat
     # Name of the theta axis (optional, defaults dcdtheta)
     theta axis: dcdtheta
     # Name of the q axis (optional, defaults qdcd)
     q axis: qdcd
     # If detector should be rotated 90 degrees (optional, defaults False)
     transpose: False
     # The maximum single pixel intensity (optional, defaults 1e6)
     pixel max: 1e6
     # The threshold for something to be investigated as a hot pixel (optional, 1e5)
     hot pixel max: 1e5
   crop:
     # The cropping method to be used (either crop_peak or 'rop)
     # (optional, default crop_peak)
     method: crop
     # Kwargs as a dict (optional, default 'None')
     # An example if crop is used the pixel numbers are given
     kwargs: {'x_start': 200, 'x_end':220, 'y_start': 70, 'y_end': 105}
   background:
     # How the background subtraction should be performed
     # (either gaussian_1d, gaussian_2d, or area)
     # (optional, default gaussian_1d)
     method: gaussian_1d
     # The kwargs for the background method (optional, default 'None')
     # If 'area' then kwargs should be x_start, etc (as with 'crop' above).
     # If 'gaussian_1d', kwargs should be the qxy axis (either 0 or 1)
     kwargs: {'axis': 0}
   # If rebin is not present the data will not be rebinned at all
   rebin:
     # Number of q vectors to be used (optional, default 50)
     n qvectors: 50
     # Alternatively a step size can be given (only used if n qvectors
     # not given)
     step: None
     # A shape of binning can be set (either linear or log)
     # (optional, default log)
     shape: log
   # The number of columns to be output (optional, default 4)
   output columns: 4
