The command line interface
============================

Introduction
----------------

This page contains some simple instructions on how to use the Islatu command line interface (CLI).

Typing the following help command will give an overview of how to interact with the CLI. 

.. code-block:: bash
  
  process_xrr -h` 


The first step is to create a .yaml file containing important information about your experiental setup and data processing options.
Following the yaml creation guide below for instructions on making a yaml file.


.. toctree::
   :maxdepth: 1

   yaml_creation


Processing with process_xrr.py
------------------------------------

So, you have your data files stored in /path/.../to/data/ , your .yaml file at /path/.../to/yaml_file.yaml and you want your processed output to live in /path/.../to/xrr_curve.dat . If the directory /path/.../to/data/ contains exclusively the scans used to construct your reflectivity curve, then this reflectivity curve can be constructed using:

.. code-block:: bash

    process_xrr -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/xrr_curve.dat

So, after writing -d you need to tell process_xrr where to find your data, after writing -y you need to tell process_xrr where to find your .yaml file, and after writing -o you need to tell process_xrr where to save your data.

If you don't want to come up with a new name for the final processed output each time, then don't worry: the islatu package will generate a name for your .dat file at a directory of your choosing. To do this, simply give the path to a directory as opposed to a file to the -o option. Explicitly, this would look like:

.. code-block:: bash

    process_xrr -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/output_directory/

Then your output XRR curve will live in /path/.../to/output_directory/generated_name.dat . These names are generated from your .yaml file and your scan numbers, so will be unique for different analyses.

When processing in diamond, often reflectivity profiles will be constructed from consecutive scans whose scan numbers vary incrementally from a minimum number to a maximum number. By default, these will all be stored in one big directory. The above examples would only work if your directory contained exclusively the scans from which your profile will be constructed, which is clearly not the case here. 

So, if your scan numbers of interest start at lower_number and end at upper_number and are stored in a directory /path/.../to/data/ that contains many other scan numbers, then processing can be carried out using

.. code-block:: bash

    process_xrr  -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/output_directory/ -l lower_number -u upper_number`

*Practical example 1*
^^^^^^^^^^^^^^^^^^^^^^^^

Imagine my account name is xrr12345, so ~ aliases to /home/xrr12345. In my documents folder, I have a folder called ~/Documents/Recipes/ for .yaml recipes. I have another folder called ~/Documents/Data/ for reduced XRR curves. I'm interested in some data collected in 2021 using the DCD setup in the experiment si28979-1, and my data is stored in the experiment's root directory on the diamond filesystem. My DCD normalization .dat file is stored in /dls/i07/data/2021/si28979-1/817213.dat , and my XRR curve is constructed from scans number 817220-817229 inclusive.

To begin, I add the above DCD template .yaml file to my recipes folder and name it DCD_si28979_1.yaml (note that this name is completely up to you and has no practical consequences).

Now that I have a generic .yaml file where I want it, I open it up with my favourite text editor and fill out my personal and experimental details. Most importantly, my DCD normalization line reads

**dcd normalisation: /dls/i07/data/2021/si28979-1/817213.dat**

If this field is not filled out correctly, the Islatu package will raise an error, but it should be reasonably uncomplicated to work out what went wrong! Now, to produce my corrected XRR curve I write in a terminal:

.. code-block:: bash

    process_xrr -d /dls/i07/data/2021/si28979-1/ -y /home/xrr12345/Documents/Recipes/DCD_si28979_1.yaml -o /home/xrr12345/Documents/Data/ -l 817220 -u 817229`

*Practical example 2*
^^^^^^^^^^^^^^^^^^^^^^

Now, later on in the same experiment you want to process another reflectivity curve, with numbers between 817241 - 817251. But, acquisition of this profile was not so smooth, and scan numbers 817246 and 817249 should not be included in the final XRR profile. In situations like this, where profiles need to be constructed from custom lists of scan numbers, process_xrr can be run as follows:

.. code-block:: bash

    process_xrr -d /dls/i07/data/2021/si28979-1/ -y /home/xrr12345/Documents/Recipes/DCD_si28979_1.yaml -o /home/xrr12345/Documents/Data/ -N 817241 817242 817243 817244 817245 817247 817248 817250 817251`



.. _how to create a yaml file: ./yaml_creation.html

