Processing Diamond data
============================

The first step is to create a **.yaml file** containing important information about your experiental setup and data processing options.
Following the yaml creation guide below for instructions on making a yaml file.

.. toctree::
   :maxdepth: 1

   yaml_creation



Working from command line interface (process_xrr) on Diamond system
-----------------------------------------------------------------------
-------------------------------------------------------------------------
   
   To load the islatu  module for x-ray reflectivity processing on a diamond linux machine, open a terminal and type:

   .. code-block:: bash 

      module load islatu
 
   if you require the use the testing version use:

   .. code-block:: bash 

      module load islatu/testing

   to view a list of possible inputs into the processing type

   .. code-block:: bash 

      process_xrr -h

Processing with process_xrr
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

   Some practical examples are shown here 
   
   .. toctree::
      :maxdepth: 1
      
      process_xrr



Using HPC cluster for calculations
-----------------------------------

   If analysing data on the Diamond systems, there is the option to submit your analysis job to a HPC cluster on-site. To submit a job to the cluster you will need to make sure you can connect to wilson SLURM submitter using 'ssh wilson'. To set this up contact a member of the beamline staff or the data analysis contact. 

   Once you can ssh onto wilson, you can then simply add a '-c' to the end of your command to submit the job to the cluster e.g. 

   .. code-block:: bash
      
      process_xrr  -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/output_directory/ -l lower_number -u upper_number -c

   **batch script from bash command line**

      The section of code below is an example of the format which can be saved into a .sh file, or ran by pasting directly into a terminal. 

      .. code-block:: bash  

         PYTHON_SCRIPT='process_xrr.py'
         SCANLIST=(540283 5400 540284)
         DATADIR=/dls/i07/data/2024/si37592-1/
         YAMLPATH=/dls/i07/data/2024/si37592-1/processing/00l/00l.yaml
         OUTPATH=/dls/science/groups/das/ExampleData/i07/islatu_example_data/tests
         
         for scan in  "${SCANLIST[@]}"; do
            echo "Starting processing for scan: $scan"
            python $PYTHON_SCRIPT -d $DATADIR -y $YAMLPATH -o  $OUTPATH -N $scan -c
            exit_code=$?
            echo "Python script for scan $scan exited with code $exit_code" || true
            if [ $exit_code -ne 0 ]; then
               echo "Error processing scan $scan, continuing with next scan"
            fi
            echo "Finished processing scan: $scan"
         done
         
         echo "All scans processed"
      
      
         #alternative method of creating a sequence of scan numbers
         SCANLIST=$(seq 1000 2 1018)


Setting up XRR autoprocessing at Diamond
----------------------------------------------
---------------------------------------------------

There is now the option to setup processing jobs to happen exactly after your scans have finished collecting. 
To do this you will need to edit your data collection macro to include the autoprocessing commands as detailed in the following example macro:

.. code-block:: python

   #define the yaml file for the XRR autoprocessing with islatu
   yaml_file='/dls/science/groups/das/ExampleData/i07/islatu_example_data/yamls/cm37245.yaml' 

   #======scan group 1 - to be processed together
   #use xrr_start to setup a new scanlist and XRR autoprocessing scannable
   scanlist,ps = xrr_start()

   #collect scans that make up the map, using append(currentScan) to add scans to list
   for i in range (1,4,1):
      scan testMotor1 1 1 1
      scanlist.append(currentscan())

   #use xrr_end to send off scans   
   xrr_end(scanlist,ps,yaml_file)

   #======scan group 2 - to be processed together
   #use xrr_start to setup a new scanlist and XRR autoprocessing scannable
   scanlist,ps = xrr_start()

   #collect scans that make up the map, using append(currentScan) to add scans to list
   for i in range (8,12,1):
      scan testMotor1 1 1 1
      scanlist.append(currentscan())

   #use xrr_end to send off scans 
   xrr_end(scanlist,ps,yaml_file)

.. _practicals: ./process_xrr


