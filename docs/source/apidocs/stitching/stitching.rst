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
   * - :py:obj:`rebin <stitching.rebin>`
     - .. autodoc2-docstring:: stitching.rebin
          :summary:

API
~~~

.. py:function:: concatenate(scan_list: typing.List[islatu.scan.Scan])
   :canonical: stitching.concatenate

   .. autodoc2-docstring:: stitching.concatenate

.. py:function:: rebin(q_vectors, reflected_intensity, new_q=None, rebin_as='linear', number_of_q_vectors=5000)
   :canonical: stitching.rebin

   .. autodoc2-docstring:: stitching.rebin
