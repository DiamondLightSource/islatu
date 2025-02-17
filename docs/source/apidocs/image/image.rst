:py:mod:`image`
===============

.. py:module:: image

.. autodoc2-docstring:: image
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Image <image.Image>`
     - .. autodoc2-docstring:: image.Image
          :summary:

API
~~~

.. py:class:: Image(array: numpy.ndarray, transpose: bool = False)
   :canonical: image.Image

   .. autodoc2-docstring:: image.Image

   .. rubric:: Initialization

   .. autodoc2-docstring:: image.Image.__init__

   .. py:property:: nominal_values
      :canonical: image.Image.nominal_values

      .. autodoc2-docstring:: image.Image.nominal_values

   .. py:property:: initial_std_devs
      :canonical: image.Image.initial_std_devs

      .. autodoc2-docstring:: image.Image.initial_std_devs

   .. py:property:: shape
      :canonical: image.Image.shape

      .. autodoc2-docstring:: image.Image.shape

   .. py:method:: __repr__()
      :canonical: image.Image.__repr__

      .. autodoc2-docstring:: image.Image.__repr__

   .. py:method:: __str__()
      :canonical: image.Image.__str__

      .. autodoc2-docstring:: image.Image.__str__

   .. py:method:: crop(crop_function, **kwargs)
      :canonical: image.Image.crop

      .. autodoc2-docstring:: image.Image.crop

   .. py:method:: background_subtraction(background_subtraction_function, **kwargs)
      :canonical: image.Image.background_subtraction

      .. autodoc2-docstring:: image.Image.background_subtraction

   .. py:method:: sum()
      :canonical: image.Image.sum

      .. autodoc2-docstring:: image.Image.sum
