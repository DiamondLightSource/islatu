Practical examples of using the command line interface 
========================================================



*Practical example 1*
------------------------------

Imagine my account name is xrr12345, so ~ aliases to /home/xrr12345. In my documents folder, I have a folder called ~/Documents/Recipes/ for .yaml recipes. I have another folder called ~/Documents/Data/ for reduced XRR curves. I'm interested in some data collected in 2021 using the DCD setup in the experiment si28979-1, and my data is stored in the experiment's root directory on the diamond filesystem. My DCD normalization .dat file is stored in /dls/i07/data/2021/si28979-1/817213.dat , and my XRR curve is constructed from scans number 817220-817229 inclusive.

To begin, I add the above DCD template .yaml file to my recipes folder and name it DCD_si28979_1.yaml (note that this name is completely up to you and has no practical consequences).

Now that I have a generic .yaml file where I want it, I open it up with my favourite text editor and fill out my personal and experimental details. Most importantly, my DCD normalization line reads

**dcd normalisation: /dls/i07/data/2021/si28979-1/817213.dat**

If this field is not filled out correctly, the Islatu package will raise an error, but it should be reasonably uncomplicated to work out what went wrong! Now, to produce my corrected XRR curve I write in a terminal:

.. code-block:: bash

    process_xrr -d /dls/i07/data/2021/si28979-1/ -y /home/xrr12345/Documents/Recipes/DCD_si28979_1.yaml -o /home/xrr12345/Documents/Data/ -l 817220 -u 817229`

*Practical example 2*
--------------------------

Now, later on in the same experiment you want to process another reflectivity curve, with numbers between 817241 - 817251. But, acquisition of this profile was not so smooth, and scan numbers 817246 and 817249 should not be included in the final XRR profile. In situations like this, where profiles need to be constructed from custom lists of scan numbers, process_xrr can be run as follows:

.. code-block:: bash

    process_xrr -d /dls/i07/data/2021/si28979-1/ -y /home/xrr12345/Documents/Recipes/DCD_si28979_1.yaml -o /home/xrr12345/Documents/Data/ -N 817241 817242 817243 817244 817245 817247 817248 817250 817251`



