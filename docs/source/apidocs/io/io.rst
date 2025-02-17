:py:mod:`io`
============

.. py:module:: io

.. autodoc2-docstring:: io
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`NexusBase <io.NexusBase>`
     - .. autodoc2-docstring:: io.NexusBase
          :summary:
   * - :py:obj:`I07Nexus <io.I07Nexus>`
     - .. autodoc2-docstring:: io.I07Nexus
          :summary:

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`i07_dat_to_dict_dataframe <io.i07_dat_to_dict_dataframe>`
     - .. autodoc2-docstring:: io.i07_dat_to_dict_dataframe
          :summary:
   * - :py:obj:`load_images_from_h5 <io.load_images_from_h5>`
     - .. autodoc2-docstring:: io.load_images_from_h5
          :summary:
   * - :py:obj:`i07_nxs_parser <io.i07_nxs_parser>`
     - .. autodoc2-docstring:: io.i07_nxs_parser
          :summary:
   * - :py:obj:`_try_to_find_files <io._try_to_find_files>`
     - .. autodoc2-docstring:: io._try_to_find_files
          :summary:

API
~~~

.. py:class:: NexusBase(local_path: str)
   :canonical: io.NexusBase

   Bases: :py:obj:`islatu.metadata.Metadata`

   .. autodoc2-docstring:: io.NexusBase

   .. rubric:: Initialization

   .. autodoc2-docstring:: io.NexusBase.__init__

   .. py:property:: src_path
      :canonical: io.NexusBase.src_path

      .. autodoc2-docstring:: io.NexusBase.src_path

   .. py:property:: detector
      :canonical: io.NexusBase.detector

      .. autodoc2-docstring:: io.NexusBase.detector

   .. py:property:: instrument
      :canonical: io.NexusBase.instrument

      .. autodoc2-docstring:: io.NexusBase.instrument

   .. py:property:: entry
      :canonical: io.NexusBase.entry
      :type: nexusformat.nexus.tree.NXentry

      .. autodoc2-docstring:: io.NexusBase.entry

   .. py:property:: default_signal
      :canonical: io.NexusBase.default_signal
      :type: numpy.ndarray

      .. autodoc2-docstring:: io.NexusBase.default_signal

   .. py:property:: default_axis
      :canonical: io.NexusBase.default_axis
      :type: numpy.ndarray

      .. autodoc2-docstring:: io.NexusBase.default_axis

   .. py:property:: default_signal_name
      :canonical: io.NexusBase.default_signal_name

      .. autodoc2-docstring:: io.NexusBase.default_signal_name

   .. py:property:: default_axis_name
      :canonical: io.NexusBase.default_axis_name
      :type: str

      .. autodoc2-docstring:: io.NexusBase.default_axis_name

   .. py:property:: default_nxdata_name
      :canonical: io.NexusBase.default_nxdata_name

      .. autodoc2-docstring:: io.NexusBase.default_nxdata_name

   .. py:property:: default_nxdata
      :canonical: io.NexusBase.default_nxdata
      :type: numpy.ndarray

      .. autodoc2-docstring:: io.NexusBase.default_nxdata

   .. py:property:: default_axis_type
      :canonical: io.NexusBase.default_axis_type
      :abstractmethod:
      :type: str

      .. autodoc2-docstring:: io.NexusBase.default_axis_type

.. py:class:: I07Nexus(local_path: str)
   :canonical: io.I07Nexus

   Bases: :py:obj:`io.NexusBase`

   .. autodoc2-docstring:: io.I07Nexus

   .. rubric:: Initialization

   .. autodoc2-docstring:: io.I07Nexus.__init__

   .. py:attribute:: excalibur_detector_2021
      :canonical: io.I07Nexus.excalibur_detector_2021
      :value: 'excroi'

      .. autodoc2-docstring:: io.I07Nexus.excalibur_detector_2021

   .. py:attribute:: excalibur_04_2022
      :canonical: io.I07Nexus.excalibur_04_2022
      :value: 'exr'

      .. autodoc2-docstring:: io.I07Nexus.excalibur_04_2022

   .. py:attribute:: pilatus_02_2024
      :canonical: io.I07Nexus.pilatus_02_2024
      :value: 'PILATUS'

      .. autodoc2-docstring:: io.I07Nexus.pilatus_02_2024

   .. py:attribute:: excalibur_08_2024
      :canonical: io.I07Nexus.excalibur_08_2024
      :value: 'EXCALIBUR'

      .. autodoc2-docstring:: io.I07Nexus.excalibur_08_2024

   .. py:property:: local_data_path
      :canonical: io.I07Nexus.local_data_path
      :type: str

      .. autodoc2-docstring:: io.I07Nexus.local_data_path

   .. py:property:: detector_name
      :canonical: io.I07Nexus.detector_name
      :type: str

      .. autodoc2-docstring:: io.I07Nexus.detector_name

   .. py:property:: default_axis_name
      :canonical: io.I07Nexus.default_axis_name
      :type: str

      .. autodoc2-docstring:: io.I07Nexus.default_axis_name

   .. py:property:: default_axis_type
      :canonical: io.I07Nexus.default_axis_type
      :type: str

      .. autodoc2-docstring:: io.I07Nexus.default_axis_type

   .. py:method:: _get_ith_region(i: int)
      :canonical: io.I07Nexus._get_ith_region

      .. autodoc2-docstring:: io.I07Nexus._get_ith_region

   .. py:property:: signal_regions
      :canonical: io.I07Nexus.signal_regions
      :type: typing.List[islatu.region.Region]

      .. autodoc2-docstring:: io.I07Nexus.signal_regions

   .. py:property:: background_regions
      :canonical: io.I07Nexus.background_regions
      :type: typing.List[islatu.region.Region]

      .. autodoc2-docstring:: io.I07Nexus.background_regions

   .. py:property:: probe_energy
      :canonical: io.I07Nexus.probe_energy

      .. autodoc2-docstring:: io.I07Nexus.probe_energy

   .. py:property:: transmission
      :canonical: io.I07Nexus.transmission

      .. autodoc2-docstring:: io.I07Nexus.transmission

   .. py:property:: detector_distance
      :canonical: io.I07Nexus.detector_distance

      .. autodoc2-docstring:: io.I07Nexus.detector_distance

   .. py:property:: _src_data_path
      :canonical: io.I07Nexus._src_data_path

      .. autodoc2-docstring:: io.I07Nexus._src_data_path

   .. py:property:: _region_keys
      :canonical: io.I07Nexus._region_keys
      :type: typing.List[str]

      .. autodoc2-docstring:: io.I07Nexus._region_keys

   .. py:property:: _number_of_regions
      :canonical: io.I07Nexus._number_of_regions
      :type: int

      .. autodoc2-docstring:: io.I07Nexus._number_of_regions

   .. py:method:: _get_region_bounds_key(region_no: int, kind: str) -> typing.List[str]
      :canonical: io.I07Nexus._get_region_bounds_key

      .. autodoc2-docstring:: io.I07Nexus._get_region_bounds_key

.. py:function:: i07_dat_to_dict_dataframe(file_path)
   :canonical: io.i07_dat_to_dict_dataframe

   .. autodoc2-docstring:: io.i07_dat_to_dict_dataframe

.. py:function:: load_images_from_h5(h5_file_path, datanxfilepath, transpose=False)
   :canonical: io.load_images_from_h5

   .. autodoc2-docstring:: io.load_images_from_h5

.. py:function:: i07_nxs_parser(file_path: str, remove_indices=None, new_axis_info=None)
   :canonical: io.i07_nxs_parser

   .. autodoc2-docstring:: io.i07_nxs_parser

.. py:function:: _try_to_find_files(filenames: typing.List[str], additional_search_paths: typing.List[str])
   :canonical: io._try_to_find_files

   .. autodoc2-docstring:: io._try_to_find_files
