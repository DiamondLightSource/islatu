:py:mod:`refl_profile`
======================

.. py:module:: refl_profile

.. autodoc2-docstring:: refl_profile
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Profile <refl_profile.Profile>`
     - .. autodoc2-docstring:: refl_profile.Profile
          :summary:

API
~~~

.. py:class:: Profile(data: islatu.data.Data, scans: typing.List[islatu.scan.Scan])
   :canonical: refl_profile.Profile

   Bases: :py:obj:`islatu.data.Data`

   .. autodoc2-docstring:: refl_profile.Profile

   .. rubric:: Initialization

   .. autodoc2-docstring:: refl_profile.Profile.__init__

   .. py:method:: fromfilenames(filenames, parser, new_axis=None)
      :canonical: refl_profile.Profile.fromfilenames
      :classmethod:

      .. autodoc2-docstring:: refl_profile.Profile.fromfilenames

   .. py:method:: crop(crop_function, **kwargs)
      :canonical: refl_profile.Profile.crop

      .. autodoc2-docstring:: refl_profile.Profile.crop

   .. py:method:: bkg_sub(bkg_sub_function, **kwargs)
      :canonical: refl_profile.Profile.bkg_sub

      .. autodoc2-docstring:: refl_profile.Profile.bkg_sub

   .. py:method:: subsample_q(scan_identifier, q_min=0, q_max=float('inf'))
      :canonical: refl_profile.Profile.subsample_q

      .. autodoc2-docstring:: refl_profile.Profile.subsample_q

   .. py:method:: footprint_correction(beam_width, sample_size)
      :canonical: refl_profile.Profile.footprint_correction

      .. autodoc2-docstring:: refl_profile.Profile.footprint_correction

   .. py:method:: transmission_normalisation(overwrite_transmissions=None)
      :canonical: refl_profile.Profile.transmission_normalisation

      .. autodoc2-docstring:: refl_profile.Profile.transmission_normalisation

   .. py:method:: qdcd_normalisation(itp)
      :canonical: refl_profile.Profile.qdcd_normalisation

      .. autodoc2-docstring:: refl_profile.Profile.qdcd_normalisation

   .. py:method:: concatenate()
      :canonical: refl_profile.Profile.concatenate

      .. autodoc2-docstring:: refl_profile.Profile.concatenate

   .. py:method:: rebin(new_q=None, rebin_as='linear', number_of_q_vectors=5000)
      :canonical: refl_profile.Profile.rebin

      .. autodoc2-docstring:: refl_profile.Profile.rebin
