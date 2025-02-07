.. islatu documentation master file, created by
   sphinx-quickstart on Fri Jan 17 18:56:48 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.
   


X-ray reflectometry reduction in Python
=======================================

:py:mod:`islatu` is an open-source pacakge for the reduction of x-ray reflectometry datasets.
Currently, :py:mod:`islatu` is developed at and supports data from `Diamond Light Source`_, however we are happy to work with others to enable data from other sources (including neutron sources).

These webpages include `API-level documentation`_ and information about some `workflows`_ that can be used for data reduction. There is also documentation on a `command line interface`_ that can be used to process reflectivity data without any python programming.

Searching
----------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Contributing
------------
As with any coding project, there are many ways to contribue. To report a bug or suggest a feature, `open an issue on the github repository`_. If you would like to contribute code, we would recommend that you first `raise an issue`_ before diving into writing code, so we can let you know if we are working on something similar already. To e.g. fix typos in documentation or in the code, or for other minor changes, feel free to make pull requests directly.

Test section
----------------
.. collapse:: Click to Open
    
    This section will be visible when the page load
    test content block

Contact us
----------------
If you need to contact the developers about anything, please either `raise an issue on the github repository`_ if appropriate, or send an email to philip.mousley@diamond.ac.uk.

Contributors
------------
- `Philip Mousley`_
- `Richard Brearton`_
- `Andrew R. McCluskey`_

Acknowledgements
----------------

We acknowledge the support of the Ada Lovelace Centre – a joint initiative between the Science and Technology Facilities Council (as part of UK Research and Innovation), Diamond Light Source, and the UK Atomic Energy Authority, in the development of this software.

.. _Diamond Light Source: https://www.diamond.ac.uk
.. _open an issue on the github repository: https://github.com/DiamondLightSource/islatu/issues
.. _raise an issue: https://github.com/DiamondLightSource/islatu/issues
.. _raise an issue on the github repository: https://github.com/DiamondLightSource/islatu/issues
.. _API-level documentation: ./modules.html
.. _workflows: ./workflows.html
.. _command line interface: ./process_xrr.ipynb
.. _Andrew R. McCluskey: https://www.armccluskey.com
.. _Richard Brearton: https://scholar.google.com/citations?user=fD9zp0YAAAAJ&hl=en
.. _Philip Mousley: https://orcid.org/0000-0002-3666-3768 
.. toctree::
   :hidden:
   :maxdepth: 2

   installation
   workflows
   process_xrr
   modules


