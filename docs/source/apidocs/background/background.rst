:py:mod:`background`
====================

.. py:module:: background

.. autodoc2-docstring:: background
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`FitInfo <background.FitInfo>`
     - .. autodoc2-docstring:: background.FitInfo
          :summary:
   * - :py:obj:`BkgSubInfo <background.BkgSubInfo>`
     - .. autodoc2-docstring:: background.BkgSubInfo
          :summary:

Functions
~~~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`roi_subtraction <background.roi_subtraction>`
     - .. autodoc2-docstring:: background.roi_subtraction
          :summary:
   * - :py:obj:`univariate_normal <background.univariate_normal>`
     - .. autodoc2-docstring:: background.univariate_normal
          :summary:
   * - :py:obj:`fit_gaussian_1d <background.fit_gaussian_1d>`
     - .. autodoc2-docstring:: background.fit_gaussian_1d
          :summary:

API
~~~

.. py:class:: FitInfo
   :canonical: background.FitInfo

   .. autodoc2-docstring:: background.FitInfo

   .. py:attribute:: popt
      :canonical: background.FitInfo.popt
      :type: numpy.ndarray
      :value: None

      .. autodoc2-docstring:: background.FitInfo.popt

   .. py:attribute:: pcov
      :canonical: background.FitInfo.pcov
      :type: numpy.ndarray
      :value: None

      .. autodoc2-docstring:: background.FitInfo.pcov

   .. py:attribute:: fit_function
      :canonical: background.FitInfo.fit_function
      :type: typing.Callable
      :value: None

      .. autodoc2-docstring:: background.FitInfo.fit_function

.. py:class:: BkgSubInfo
   :canonical: background.BkgSubInfo

   .. autodoc2-docstring:: background.BkgSubInfo

   .. py:attribute:: bkg
      :canonical: background.BkgSubInfo.bkg
      :type: float
      :value: None

      .. autodoc2-docstring:: background.BkgSubInfo.bkg

   .. py:attribute:: bkg_e
      :canonical: background.BkgSubInfo.bkg_e
      :type: float
      :value: None

      .. autodoc2-docstring:: background.BkgSubInfo.bkg_e

   .. py:attribute:: bkg_sub_function
      :canonical: background.BkgSubInfo.bkg_sub_function
      :type: typing.Callable
      :value: None

      .. autodoc2-docstring:: background.BkgSubInfo.bkg_sub_function

   .. py:attribute:: fit_info
      :canonical: background.BkgSubInfo.fit_info
      :type: background.FitInfo
      :value: None

      .. autodoc2-docstring:: background.BkgSubInfo.fit_info

.. py:function:: roi_subtraction(image, list_of_regions: typing.List[islatu.region.Region])
   :canonical: background.roi_subtraction

   .. autodoc2-docstring:: background.roi_subtraction

.. py:function:: univariate_normal(data, mean, sigma, offset, factor)
   :canonical: background.univariate_normal

   .. autodoc2-docstring:: background.univariate_normal

.. py:function:: fit_gaussian_1d(image: islatu.image.Image, params_0=None, bounds=None, axis=0)
   :canonical: background.fit_gaussian_1d

   .. autodoc2-docstring:: background.fit_gaussian_1d
