---
title: "islatu: A Python package for the reduction of reflectometry data"
tags:
  - Python
  - reflectometry
  - synchrotron radiation
  - condensed matter
authors:
  - name: Richard Brearton
    orcid: 0000-0002-8204-3674
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Andrew McCluskey
    orcid: 0000-0003-3381-5911
    affiliation: 3
  - name: Tim Snow
    orcid: 0000-0001-7146-6885
    affiliation: "1, 4"
affiliations:
  - name: Diamond Light Source Ltd, Diamond House, Harwell Campus, Didcot, Oxfordshire, OX11 0DE, United Kingdom
    index: 1
  - name: Department of Physics, Clarendon Laboratory, University of Oxford, Oxford, Oxfordshire, OX1 3PU, United Kingdom
    index: 2
  - name: European Spallation Source ERIC, P.O. Box 176, SE-221 00, Lund, Sweden
    index: 3
  - name: School of Chemistry, University of Bristol, Bristol, BS8 1TS, UK
    index: 4
date: 03 March 2022
bibliography: paper.bib
---

# Summary

The interaction between light and matter provides a sensitive probe of the
electronic structure of materials, on length scales determined by the difference
between the incident and outgoing wavevector of the light. Reflectometry
techniques involve scattering off the surface of a material, placing a detector
at a point such that any light reaching the detector must scatter through a
vector approximately parallel to the material's surface normal. Typically, for
various experiment-specific reasons, the raw data recorded by a detector will
not be proportional to the quantity of interest: the modulus squared of the
scattering matrix element
${\langle \vec{k}'\rvert}\hat{V}\lvert \vec{k} \rangle$. This is particularly
true when the length of the scattering vector
$|\vec{Q}| = |\vec{k} - \vec{k}'|$
is small, as is the case in reflectivity experiments. Then, in addition to
corrections that must be applied in any scattering experiment, the finite
size of the sample will affect the intensity of the
reflected beam, and it is often necessary to also correct for manual changes
to the beam's attenuation. For the above reasons, all reflectivity experiments
need at least some form of data reduction, with the exact requirements being
experiment specific and often numerous. `islatu` provides a simple, performant
and rigorously tested library and command-line interface for carrying out these
correction steps, which aims to substantially simplify the process of converting
instrument data to a reflectivity curve. This curve can then be analysed using
one of the many widely available reflectivity fitting tools, such as
[@bjorck2007genx], [@nelson2019refnx] and [@nelson2006co].

# Statement of need

`islatu` [@islatu_doi] is a Python package that simplifies the process of
reducing raw reflectometry data to data that has scientific value. This package
is designed to serve three purposes. Firstly, it provides an interface that can
be used to easily script custom reflectometry reduction pipelines. As the
fitting of reduced reflectivity data is an ill-posed problem, it is often
challenging to fit reflectivity curves, even with significant a-priori knowledge
of the structure of the material of interest. In some cases, this could be
related to errors made at data reduction time. `islatu` gives users the
ability to script data reduction at analysis time. This can be particularly
important when combining data sets with very different statistical uncertainties
(as would be the case when comparing neutron and x-ray reflectivity curves), as
errors are computed at data reduction time.

The second purpose of `islatu` is to provide a simple command-line interface,
that can be used in conjunction with a configuration file, to make reflectivity
reduction as automatic as possible. For example, at large-scale facilities, to
make the most of valuable beamtime, it is imperative that feedback on scans is
given to users as quickly as possible after a scan has been performed.

The final purpose of `islatu` is to simplify the handling of uncertainties.
In `islatu`, statistical errors are automatically calculated and efficiently
propagated from the raw data to the reduced dataset using optimized
`numpy` [@harris2020array] routines. Despite their fundamental simplicity,
the propagation of uncertainties is error prone. The assurance provided by
unit tested error propagation gives scientists more time to focus on data
analysis and less time spent worrying about re-implementing standard routines.

Conversion of raw instrument data to a meaningful reflectivity curve is not
desirable, but an absolute requirement.
Cutting corners or making mistakes at this stage in the data analysis process
would result in physically incorrect values of roughnesses and thicknesses being
derived from measurements.
`islatu` needed to be written to address the demand for a lightweight,
rigorously tested package that can carry out the above-described functions.

# Overview

There are a multitude of instruments around the world capable of recording
reflectivity data. `islatu` has been designed with this in mind, with a focus on
directly supporting international standard file formats (including the NeXus
[@konnecke2015nexus] and ORSO file formats) for the initial release,
making `islatu` compatible with most
modern synchrotrons. Thanks to `islatu`'s modular design, it is a
straightforward task to extend this functionality to other data sources; only
one parsing function needs to be added per supported file type.

As there are many instruments worldwide being used to record reflectometry data,
other packages exist that reduce reflectivity profiles. However, these packages
tend to be specific to a technique or instrument and are often closed source.
For example, the reduction of neutron reflectivity data is possible with
`Mantid` [@arnold2014mantid], but it is an enormous piece of software designed to
work specifically with neutron and muon-based techniques. In the x-ray world,
manufacturers of laboratory x-ray sources typically develop their own
closed-source solutions, such as Bruker's DIFFRAC.XRR package and Rigaku's
x-ray reflectivity software [@yasaka2010x]. Open source alternatives to
`islatu` do exist, but tend to not share `islatu`'s focus of being highly
scriptable (either on the command line or through python).
`Reductus` [@maranville2018reductus], for example, is an excellent web-based
reflectometry reduction tool, but its focus is on reducing neutron data via
a graphical user interface.

`islatu` was designed for use with two-dimensional detectors, but support for
point detectors is complete and all reduction steps can be carried out with
identical syntax. To give an overview of `islatu`'s Python API, the first step
in any data reduction with `islatu` is to instantiate a `Profile` object. A full
reflectivity profile can generally be made up of more than one
$|\vec{Q}|$
scan, where $\vec{Q}$ is the probe particle's
scattering vector. To instantiate a `Profile` object, all that needs to be
provided is a list of source files and a function that can be used to parse
them. Once the profile has been instantiated, reduction takes place by calling
the `Profile` object's methods. For example, for an instance of `Profile`
named `my_profile` representing data acquired when a beam with a full width at
half maximum of 100 µm was incident on a sample of length 10 mm, our
reflectometry profile can be footprint-corrected by calling
`my_profile.footprint_correction(beam_width=100e-6, sample_size=10e-3)`.
The footprint correction is
exact for Gaussian beam profiles, and, along with all other reduction methods
available to `Profile` objects, propagates errors optimally (such that the
number of mathematical operations required to propagate the errors is
minimized). The other reduction methods can be used in entirely analogous ways,
taking arguments where necessary, and using metadata scraped from the raw data
files wherever possible.

An example of `islatu` being used to carry out corrections on a profile can be
found in \autoref{fig:corrections}. In \autoref{fig:corrections}(a), the raw
instrument data can be seen (the only analysis that was carried out prior to
plotting was that $|\vec{Q}|$ was calculated for each image in the profile).
The result of using `islatu` to apply corrections to the profile shown in
\autoref{fig:corrections}(a) can be seen in \autoref{fig:corrections}(b) - this
could now be analysed using a piece of fitting software.

<center>
  ![Visualization of the results of the reflectivity reduction process.
  (a) The reflectivity profile associated with the raw data.
  (b) The same data as in (a), after all relevant corrections have been applied.
  \label{fig:corrections}](figures/corrections.png){ width=98% }
</center>

As well as the above-described Python API, `islatu` also features a command-line
interface. This application is used at the I07 beamline at Diamond
[@nicklin2016diamond]
to process reflectivity data immediately after acquisition. The command-line
interface runs a typical `islatu` processing script, where the arguments taken
by the various data reduction methods in the script are extracted from a combination
of a .yml configuration file and command-line arguments. The program outputs a
human-readable metadata-rich .dat file, which at present aims to comply with the
ORSO .ort file format definition, and will be converted to comply exactly with
the .ort file format at such a time as the ORSO file format specification is
finalized.

# Acknowledgements

We acknowledge the support given to this project by the Ada Lovelace centre who
funded this work under the grant number 103318.

# References
