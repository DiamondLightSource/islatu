Guide on creating a yaml file for Islatu
===========================================


The yaml file provide details about the expeirmental setup, and the options desired for data analysis. It is made up from multiple sections, which are either a single item and so laid out on one line e.g.

.. code-block:: yaml 

    section_name: section_value

or have multiple subheadings for various related options e.g. 

.. code-block:: yaml 

    section_name:
      subheading1_name: subheading1 value
      subheading2_name: subheading2 value
    

.. important:: 

    make sure to use a double space indent for the subheadings

Below is a list of sections that can be included in your islatu yaml file, and subheadings which are the available options within each section. 

instrument
-----------

This section provides details on the instrument used to record the experimental data. 

    .. confval:: instrument

        which instrument was used to collect your data. Currently the only option is 'i07'


.. code-block:: yaml
    :caption: example instrument section

    instrument: 'i07'

visit
------

This section provides information on the experiment visit at Diamond


    .. confval:: visit id

        id for the diamond experiment, usually in the form of si#####-#  e.g. si28707-1

    .. confval:: local contact (Optional)

    provide the name of the local contact during the experiment

    .. confval:: user (Optional)

        name of user analysing the data

    .. confval:: user affiliation (Optional)

        institution which the user has an affiliation with

    .. confval:: date (Optional)

        date for when the experiment took place

.. code-block:: yaml
    :caption: example visit section
    
    visit:
      local contact: "Firstname Lastname"
      user: 'Firstname Lastname'
      user affiliation: 'InstitutionName'
      visit id: 'experimentID'
      date: 2021-08-06

setup 
------

This section provides details on the setup of the beamline and sample

    .. confval:: sample size

        set the size of the sample in the format (sample_length, sample_width) in m, where the "length" direction is parallel to the wavevector of the incident light for q=0  e.g. (200e-3, 10e-3)

    .. confval:: beam width
        
        The full-width half maximum of the x-ray beam  in m e.g. 100e-6
    
    .. confval:: dcd_normalisation  (Optional)

        The full filepath to the normalisation file 

.. code-block:: yaml
    :caption: example setup section

    setup:
      sample size: (200e-3, 10e-3)
      beam width: 100e-6
      dcd normalisation: /dls/i07/data/2021/si28707-1/404863.dat 

crop
----

This section provides details on selecting a signal region of interest (ROI)

    .. confval:: method

        defines the method to use when creating the ROI, currently only available method is crop

    .. confval:: kwargs (Optional)

        define the region to be used for the signal ROI in the format {'x_start': X_START_PIXEL , 'x_end': X_END_PIXEL, 'y_start': Y_START_PIXEL, 'y_end': Y_END_PIXEL}  e.g. 

        .. code-block:: yaml
        
            {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}
        
        If region is not specified the processing will default to using ROI 1 as set during the expeirent.

.. code-block:: yaml
    :caption: example crop section

    crop:
      method: crop
      kwargs: {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}



background
-----------

This section provides details on how to perform the background subtraction.

    .. confval:: method

        defines the method used for the background subtraction, currently only reliable method is roi_subtraction.  
        If the roi_subtraction option for background subtraction method is not suitable, more information on the alternative options can be found in the `API documentation`_.
    
    .. confval:: kwargs (Optional)

        define the region to be used for the background ROI in the format {'x_start': X_START_PIXEL , 'x_end': X_END_PIXEL, 'y_start': Y_START_PIXEL, 'y_end': Y_END_PIXEL}  e.g. 

        .. code-block:: yaml
        
            {'x_start': 1450, 'x_end': 1550, 'y_start': 190, 'y_end': 211}

        If region is not specified the processing will default to using ROI 2 as set during the expeirent.

.. code-block:: yaml
    :caption: example background section with roi_subtraction

    background:
      method: roi_subtraction
      kwargs: {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}

To skip the background subtraction step  you can set the method to None or none, and or simply comment out the background section of the yaml file

.. code-block:: yaml
    :caption: example background sections for skipping background removal

    background:
      method: None
      kwargs: {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}

    background:
      method: none
      kwargs: {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}

    #background:
    #  method: None
    #  kwargs: {'x_start': 1050, 'x_end': 1150, 'y_start': 190, 'y_end': 211}

adjustments (Optional)
-------------------------

This section provides details on variables which you want to overwrite or change the value of.

    .. confval:: new_axis_name

        redefine which axis is used when calculating the exit angles or q. The value specified here replaces the default axis saved in the nexus file
    
    .. confval:: new_axis_type

        define what type of axis the new_axis is using one of the following options:

        - tth: the new axis is two theta

        - th: the new axis is theta

        - q: the new axis is Q
    
        .. confval:: theta_offset

            set value to offset all calculated values of theta
        
        OR
        
        .. confval:: q_offset
            
            set value to offset all calculated values of q


.. code-block:: yaml
    :caption: example adjustments section

    adjustments:
      new_axis_name: 'diff1delta'
      new_axis_type: 'tth'
      theta_offset: 0.3
      q_offset: 0.1

rebin (Optional)
------------------

    .. confval:: n qvectors

        Integer number of bins to place q-vectors into. These bins are linearly spaced in q by default.


.. code-block:: yaml
    :caption: example rebin section

    rebin:
      n qvectors: 5000


normalisation (Optional)
--------------------------

    .. confval:: maxnorm

        set to True or False depending on whether you want to processed Intensity to be normalised to its maximum value

  

.. code-block:: yaml
    :caption: example normalisation section

    normalisation:
      maxnorm: True


transmission (Optional)
----------------------------

    .. confval:: values

        overwrite transmission values which are contained in the nexus file. 


.. code-block:: yaml
    :caption: example transmission section

    transmission:
      values: [1,1,1.3,1]



.. _API documentation: ./apidocs/background/background.html
