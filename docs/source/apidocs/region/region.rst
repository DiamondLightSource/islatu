:py:mod:`region`
================

.. py:module:: region

.. autodoc2-docstring:: region
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Region <region.Region>`
     - .. autodoc2-docstring:: region.Region
          :summary:

API
~~~

.. py:class:: Region(x_start, x_end, y_start, y_end)
   :canonical: region.Region

   .. autodoc2-docstring:: region.Region

   .. rubric:: Initialization

   .. autodoc2-docstring:: region.Region.__init__

   .. py:property:: x_length
      :canonical: region.Region.x_length

      .. autodoc2-docstring:: region.Region.x_length

   .. py:property:: y_length
      :canonical: region.Region.y_length

      .. autodoc2-docstring:: region.Region.y_length

   .. py:property:: num_pixels
      :canonical: region.Region.num_pixels

      .. autodoc2-docstring:: region.Region.num_pixels

   .. py:method:: from_dict(region_dict: dict)
      :canonical: region.Region.from_dict
      :classmethod:

      .. autodoc2-docstring:: region.Region.from_dict

   .. py:method:: __eq__(other)
      :canonical: region.Region.__eq__

      .. autodoc2-docstring:: region.Region.__eq__

   .. py:method:: __str__()
      :canonical: region.Region.__str__
