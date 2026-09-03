:py:mod:`stitching`
===================

.. py:module:: stitching

.. autodoc2-docstring:: stitching
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`concatenate <stitching.concatenate>`
     - .. autodoc2-docstring:: stitching.concatenate
          :summary:
   * - :py:obj:`match_overlap_resolution <stitching.match_overlap_resolution>`
     - .. autodoc2-docstring:: stitching.match_overlap_resolution
          :summary:
   * - :py:obj:`rebin <stitching.rebin>`
     - .. autodoc2-docstring:: stitching.rebin
          :summary:

API
~~~

.. py:function:: concatenate(scan_list: list[islatu.scan.Scan])
   :canonical: stitching.concatenate

   .. autodoc2-docstring:: stitching.concatenate

.. py:function:: match_overlap_resolution(data_df: pandas.DataFrame)
   :canonical: stitching.match_overlap_resolution

   .. autodoc2-docstring:: stitching.match_overlap_resolution

.. py:function:: rebin(q_vectors, reflected_intensity, new_q=None, rebin_as='linear', number_of_q_vectors=5000)
   :canonical: stitching.rebin

   .. autodoc2-docstring:: stitching.rebin
