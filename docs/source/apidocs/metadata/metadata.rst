:py:mod:`metadata`
==================

.. py:module:: metadata

.. autodoc2-docstring:: metadata
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Metadata <metadata.Metadata>`
     - .. autodoc2-docstring:: metadata.Metadata
          :summary:

API
~~~

.. py:class:: Metadata(local_path)
   :canonical: metadata.Metadata

   .. autodoc2-docstring:: metadata.Metadata

   .. rubric:: Initialization

   .. autodoc2-docstring:: metadata.Metadata.__init__

   .. py:property:: probe_energy
      :canonical: metadata.Metadata.probe_energy
      :abstractmethod:

      .. autodoc2-docstring:: metadata.Metadata.probe_energy

   .. py:property:: default_axis
      :canonical: metadata.Metadata.default_axis
      :abstractmethod:
      :type: numpy.ndarray

      .. autodoc2-docstring:: metadata.Metadata.default_axis

   .. py:property:: default_axis_name
      :canonical: metadata.Metadata.default_axis_name
      :abstractmethod:
      :type: str

      .. autodoc2-docstring:: metadata.Metadata.default_axis_name

   .. py:property:: default_axis_type
      :canonical: metadata.Metadata.default_axis_type
      :abstractmethod:
      :type: str

      .. autodoc2-docstring:: metadata.Metadata.default_axis_type

   .. py:property:: transmission
      :canonical: metadata.Metadata.transmission
      :abstractmethod:

      .. autodoc2-docstring:: metadata.Metadata.transmission

   .. py:property:: detector_distance
      :canonical: metadata.Metadata.detector_distance
      :abstractmethod:

      .. autodoc2-docstring:: metadata.Metadata.detector_distance
