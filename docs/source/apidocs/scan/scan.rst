:py:mod:`scan`
==============

.. py:module:: scan

.. autodoc2-docstring:: scan
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Scan <scan.Scan>`
     - .. autodoc2-docstring:: scan.Scan
          :summary:
   * - :py:obj:`Scan2D_noload_diff <scan.Scan2D_noload_diff>`
     - .. autodoc2-docstring:: scan.Scan2D_noload_diff
          :summary:
   * - :py:obj:`Scan2D_noload <scan.Scan2D_noload>`
     - .. autodoc2-docstring:: scan.Scan2D_noload
          :summary:
   * - :py:obj:`Scan2D <scan.Scan2D>`
     - .. autodoc2-docstring:: scan.Scan2D
          :summary:

API
~~~

.. py:class:: Scan(data: islatu.data.Data, metadata: islatu.metadata.Metadata)
   :canonical: scan.Scan

   Bases: :py:obj:`islatu.data.MeasurementBase`

   .. autodoc2-docstring:: scan.Scan

   .. rubric:: Initialization

   .. autodoc2-docstring:: scan.Scan.__init__

   .. py:method:: subsample_q(q_min=0, q_max=float('inf'))
      :canonical: scan.Scan.subsample_q

      .. autodoc2-docstring:: scan.Scan.subsample_q

   .. py:method:: transmission_normalisation(overwrite_transmission=None)
      :canonical: scan.Scan.transmission_normalisation

      .. autodoc2-docstring:: scan.Scan.transmission_normalisation

   .. py:method:: qdcd_normalisation(itp)
      :canonical: scan.Scan.qdcd_normalisation

      .. autodoc2-docstring:: scan.Scan.qdcd_normalisation

   .. py:method:: footprint_correction(beam_width, sample_size)
      :canonical: scan.Scan.footprint_correction

      .. autodoc2-docstring:: scan.Scan.footprint_correction

.. py:class:: Scan2D_noload_diff(data: islatu.data.Data, metadata: diffraction_utils.io.I07Nexus, image_paths=list, remove_indices=None)
   :canonical: scan.Scan2D_noload_diff

   Bases: :py:obj:`scan.Scan`

   .. autodoc2-docstring:: scan.Scan2D_noload_diff

   .. rubric:: Initialization

   .. autodoc2-docstring:: scan.Scan2D_noload_diff.__init__

   .. py:method:: background_and_crop(crop_function, crop_kwargs, bkg_sub_function, bkg_kwargs)
      :canonical: scan.Scan2D_noload_diff.background_and_crop

      .. autodoc2-docstring:: scan.Scan2D_noload_diff.background_and_crop

   .. py:method:: crop(crop_function, **kwargs)
      :canonical: scan.Scan2D_noload_diff.crop

      .. autodoc2-docstring:: scan.Scan2D_noload_diff.crop

   .. py:method:: bkg_sub(bkg_sub_function, **kwargs)
      :canonical: scan.Scan2D_noload_diff.bkg_sub

      .. autodoc2-docstring:: scan.Scan2D_noload_diff.bkg_sub

   .. py:method:: remove_data_points(indices)
      :canonical: scan.Scan2D_noload_diff.remove_data_points

      .. autodoc2-docstring:: scan.Scan2D_noload_diff.remove_data_points

.. py:class:: Scan2D_noload(data: islatu.data.Data, metadata: islatu.metadata.Metadata, image_paths=list, remove_indices=None)
   :canonical: scan.Scan2D_noload

   Bases: :py:obj:`scan.Scan`

   .. autodoc2-docstring:: scan.Scan2D_noload

   .. rubric:: Initialization

   .. autodoc2-docstring:: scan.Scan2D_noload.__init__

   .. py:method:: background_and_crop(crop_function, crop_kwargs, bkg_sub_function, bkg_kwargs)
      :canonical: scan.Scan2D_noload.background_and_crop

      .. autodoc2-docstring:: scan.Scan2D_noload.background_and_crop

   .. py:method:: crop(crop_function, **kwargs)
      :canonical: scan.Scan2D_noload.crop

      .. autodoc2-docstring:: scan.Scan2D_noload.crop

   .. py:method:: bkg_sub(bkg_sub_function, **kwargs)
      :canonical: scan.Scan2D_noload.bkg_sub

      .. autodoc2-docstring:: scan.Scan2D_noload.bkg_sub

   .. py:method:: remove_data_points(indices)
      :canonical: scan.Scan2D_noload.remove_data_points

      .. autodoc2-docstring:: scan.Scan2D_noload.remove_data_points

.. py:class:: Scan2D(data: islatu.data.Data, metadata: islatu.metadata.Metadata, images: list[islatu.image.Image], remove_indices=None)
   :canonical: scan.Scan2D

   Bases: :py:obj:`scan.Scan`

   .. autodoc2-docstring:: scan.Scan2D

   .. rubric:: Initialization

   .. autodoc2-docstring:: scan.Scan2D.__init__

   .. py:method:: crop(crop_function, **kwargs)
      :canonical: scan.Scan2D.crop

      .. autodoc2-docstring:: scan.Scan2D.crop

   .. py:method:: bkg_sub(bkg_sub_function, **kwargs)
      :canonical: scan.Scan2D.bkg_sub

      .. autodoc2-docstring:: scan.Scan2D.bkg_sub

   .. py:method:: remove_data_points(indices)
      :canonical: scan.Scan2D.remove_data_points

      .. autodoc2-docstring:: scan.Scan2D.remove_data_points
