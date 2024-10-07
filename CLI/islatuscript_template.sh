#!/bin/bash
#SBATCH --partition cs05r 
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --mem-per-cpu=2000 
#SBATCH --job-name=isaltu
 
/dls_sw/apps/islatu/testing/conda_env/bin/python ${save_path}