**Processing Diamond data**
============================

Working from a jupyter notebook on any system
---------------------------------------------------

--------------------------------------------------------------------------

   The notebook linked below shows a typical data reduction workflow from a notebook handled by :py:mod:`islatu`  : 

   .. toctree::
      :maxdepth: 1

      i07_reflectivity

.. _CLI: ./process_xrr.ipynb




Working from command line interface (process_xrr.py) on Diamond system
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

      process_xrr.py -h

   To start you will need to create a **.yaml file** that contains some details pertaining to your experiment.

   See the `CLI`_ section for information on creating a yaml file and using the command line interface



   **Using HPC cluster for calculations**

   If analysing data on the Diamond systems, there is the option to submit your analysis job to a HPC cluster on-site. To submit a job to the cluster you will need to make sure you can connect to wilson SLURM submitter using 'ssh wilson'. To set this up contact a member of the beamline staff or the data analysis contact. 

   Once you can ssh onto wilson, you can then simply add a '-c' to the end of your command to submit the job to the cluster e.g. 

   .. code-block:: bash
      
      process_xrr.py  -d /path/.../to/data/ -y /path/.../to/yaml_file.yaml -o /path/.../to/output_directory/ -l lower_number -u upper_number -c



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



