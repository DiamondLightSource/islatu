The command line interface
============================

Introduction
----------------

This page contains some simple instructions on how to use the process_xrr CLI.

Typing `process_xrr.py -h` should give an overview of how it can be used. 


Creating a .yaml file
----------------------

Before
starting, you should create a .yaml file that contains some details pertaining
to your experiment.

An example of the .yaml file could be something like


.. code-block:: yaml 

    instrument: 'i07'
    visit:
      local contact: "Firstname Lastname"
      user: 'Firstname Lastname'
      user affiliation: 'InstitutionName'
      visit id: 'experimentID'
      date: 2021-08-06
    setup:
      # ====(sample_length, sample_width) in m
      # ====...where the "length" direction is parallel to the wavevector of the
      # ====incident light for |q|=0.
      sample size: (200e-3, 10e-3)

      # ====Beam FWHM in m
      beam width: 100e-6

      #==== /path/to/normalization/file  comment this line out if not using dcd normalisation
      #=== Outside of diamond, this might look like, for example:
      # ====/Users/richardbrearton/Documents/Data/si28707-1/404863.dat
      dcd normalisation: /dls/i07/data/2021/si28707-1/404863.dat 

    crop:
      # currently only one cropping method is available
      method: crop
      # comment out kwargs to crop to ROI_1 from nexus data file, as specified in GDA.
      # leave kwargs uncommented  to manually crop to a specified cropping region.
      kwargs: {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}
      
    background:
      # The most reliable method that one can use to subtract background is
      # roi_subtraction. We strongly recommend that this option is used.
      method: roi_subtraction
      # comment out kwargs to use ROI_2 from nexus data file as background region.
      # leave uncommented kwargs to manually select a specified background region.
      kwargs: {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}

    normalisation:
      #choose whether to normalise the final intensity profile by the maximum value
      maxnorm: True
      
    adjustments:
      #use this section to define adjusments needed for specific cases, for example here to instruct islatu to use the delta angle for the theta calculations. 
      new_axis_name: 'diff1delta'
      new_axis_type: 'tth'

    rebin:
      # Number of bins to place q-vectors into. These bins are linearly spaced in q
      # by default.
      n qvectors: 5000


If the roi_subtraction option for background subtraction method is not suitable, more information on the alternative options can be found in the `API documentation`_.

Processing with process_xrr.py
------------------------------------

So, you have your data files stored in /path/.../to/data/ , your .yaml file at /path/.../to/yaml_file.yaml and you want your processed output to live in /path/.../to/xrr_curve.dat . If the directory /path/.../to/data/ contains exclusively the scans used to construct your reflectivity curve, then this reflectivity curve can be constructed using:

.. code-block:: bash

    process_xrr.py -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/xrr_curve.dat

So, after writing -d you need to tell process_xrr where to find your data, after writing -y you need to tell process_xrr where to find your .yaml file, and after writing -o you need to tell process_xrr where to save your data.

If you don't want to come up with a new name for the final processed output each time, then don't worry: the islatu package will generate a name for your .dat file at a directory of your choosing. To do this, simply give the path to a directory as opposed to a file to the -o option. Explicitly, this would look like:

.. code-block:: bash

    process_xrr.py -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/output_directory/

Then your output XRR curve will live in /path/.../to/output_directory/generated_name.dat . These names are generated from your .yaml file and your scan numbers, so will be unique for different analyses.

When processing in diamond, often reflectivity profiles will be constructed from consecutive scans whose scan numbers vary incrementally from a minimum number to a maximum number. By default, these will all be stored in one big directory. The above examples would only work if your directory contained exclusively the scans from which your profile will be constructed, which is clearly not the case here. 

So, if your scan numbers of interest start at lower_number and end at upper_number and are stored in a directory /path/.../to/data/ that contains many other scan numbers, then processing can be carried out using

.. code-block:: bash

    process_xrr.py  -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/output_directory/ -l lower_number -u upper_number`

*Practical example 1*
^^^^^^^^^^^^^^^^^^^^^^^^

Imagine my account name is xrr12345, so ~ aliases to /home/xrr12345. In my documents folder, I have a folder called ~/Documents/Recipes/ for .yaml recipes. I have another folder called ~/Documents/Data/ for reduced XRR curves. I'm interested in some data collected in 2021 using the DCD setup in the experiment si28979-1, and my data is stored in the experiment's root directory on the diamond filesystem. My DCD normalization .dat file is stored in /dls/i07/data/2021/si28979-1/817213.dat , and my XRR curve is constructed from scans number 817220-817229 inclusive.

To begin, I add the above DCD template .yaml file to my recipes folder and name it DCD_si28979_1.yaml (note that this name is completely up to you and has no practical consequences).

Now that I have a generic .yaml file where I want it, I open it up with my favourite text editor and fill out my personal and experimental details. Most importantly, my DCD normalization line reads

**dcd normalisation: /dls/i07/data/2021/si28979-1/817213.dat**

If this field is not filled out correctly, the Islatu package will raise an error, but it should be reasonably uncomplicated to work out what went wrong! Now, to produce my corrected XRR curve I write in a terminal:

.. code-block:: bash

    process_xrr.py -d /dls/i07/data/2021/si28979-1/ -y /home/xrr12345/Documents/Recipes/DCD_si28979_1.yaml -o /home/xrr12345/Documents/Data/ -l 817220 -u 817229`

*Practical example 2*
^^^^^^^^^^^^^^^^^^^^^^

Now, later on in the same experiment you want to process another reflectivity curve, with numbers between 817241 - 817251. But, acquisition of this profile was not so smooth, and scan numbers 817246 and 817249 should not be included in the final XRR profile. In situations like this, where profiles need to be constructed from custom lists of scan numbers, process_xrr can be run as follows:

.. code-block:: bash

    process_xrr.py -d /dls/i07/data/2021/si28979-1/ -y /home/xrr12345/Documents/Recipes/DCD_si28979_1.yaml -o /home/xrr12345/Documents/Data/ -N 817241 817242 817243 817244 817245 817247 817248 817250 817251`

.. _API documentation: ./apidocs/background/background.html