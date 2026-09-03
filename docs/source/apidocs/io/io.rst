:py:mod:`io`
============

.. py:module:: io

.. autodoc2-docstring:: io
   :allowtitles:

Module Contents
---------------

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`i07_dat_to_dict_dataframe <io.i07_dat_to_dict_dataframe>`
     - .. autodoc2-docstring:: io.i07_dat_to_dict_dataframe
          :summary:
   * - :py:obj:`load_ind_image_from_h5 <io.load_ind_image_from_h5>`
     - .. autodoc2-docstring:: io.load_ind_image_from_h5
          :summary:
   * - :py:obj:`check_total_images_in_h5 <io.check_total_images_in_h5>`
     - .. autodoc2-docstring:: io.check_total_images_in_h5
          :summary:
   * - :py:obj:`load_images_from_h5 <io.load_images_from_h5>`
     - .. autodoc2-docstring:: io.load_images_from_h5
          :summary:
   * - :py:obj:`parse_adjustments <io.parse_adjustments>`
     - .. autodoc2-docstring:: io.parse_adjustments
          :summary:
   * - :py:obj:`make_data <io.make_data>`
     - .. autodoc2-docstring:: io.make_data
          :summary:
   * - :py:obj:`i07_nxs_parser_noload <io.i07_nxs_parser_noload>`
     - .. autodoc2-docstring:: io.i07_nxs_parser_noload
          :summary:
   * - :py:obj:`i07_nxs_parser_noload_diff <io.i07_nxs_parser_noload_diff>`
     - .. autodoc2-docstring:: io.i07_nxs_parser_noload_diff
          :summary:
   * - :py:obj:`i07_nxs_parser <io.i07_nxs_parser>`
     - .. autodoc2-docstring:: io.i07_nxs_parser
          :summary:
   * - :py:obj:`_try_to_find_files <io._try_to_find_files>`
     - .. autodoc2-docstring:: io._try_to_find_files
          :summary:

API
~~~

.. py:function:: i07_dat_to_dict_dataframe(file_path)
   :canonical: io.i07_dat_to_dict_dataframe

   .. autodoc2-docstring:: io.i07_dat_to_dict_dataframe

.. py:function:: load_ind_image_from_h5(h5_file_path, datanxfilepath, ind, transpose=False)
   :canonical: io.load_ind_image_from_h5

   .. autodoc2-docstring:: io.load_ind_image_from_h5

.. py:function:: check_total_images_in_h5(h5_file_path, datanxfilepath)
   :canonical: io.check_total_images_in_h5

   .. autodoc2-docstring:: io.check_total_images_in_h5

.. py:function:: load_images_from_h5(h5_file_path, datanxfilepath, transpose=False)
   :canonical: io.load_images_from_h5

   .. autodoc2-docstring:: io.load_images_from_h5

.. py:function:: parse_adjustments(i07_nxs, adjustments)
   :canonical: io.parse_adjustments

   .. autodoc2-docstring:: io.parse_adjustments

.. py:function:: make_data(axis, axis_name, axis_type, shared_vals, q_offset, theta_offset)
   :canonical: io.make_data

   .. autodoc2-docstring:: io.make_data

.. py:function:: i07_nxs_parser_noload(file_path: str, remove_indices=None, adjustments=None)
   :canonical: io.i07_nxs_parser_noload

   .. autodoc2-docstring:: io.i07_nxs_parser_noload

.. py:function:: i07_nxs_parser_noload_diff(file_path: str, remove_indices=None, adjustments=None)
   :canonical: io.i07_nxs_parser_noload_diff

   .. autodoc2-docstring:: io.i07_nxs_parser_noload_diff

.. py:function:: i07_nxs_parser(file_path: str, remove_indices=None, adjustments=None)
   :canonical: io.i07_nxs_parser

   .. autodoc2-docstring:: io.i07_nxs_parser

.. py:function:: _try_to_find_files(filenames: list[str], additional_search_paths: list[str])
   :canonical: io._try_to_find_files

   .. autodoc2-docstring:: io._try_to_find_files
