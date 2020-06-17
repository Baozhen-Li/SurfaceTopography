SurfaceTopography
=================

*Read and analyze surface topographies with Python.* This code implements basic classes for handling uniform and
nonuniform surface topography data. It contains a rich set of import filters for experimental surface topography data.
Surface topographies can be easily analyzed using standard (rms height, power spectrum, ...) and some special purpose
(autocorrelation function, variable bandwidth analysis, ...) statistical techniques. 

If you use this code, please cite:
[Jacobs, Junge, Pastewka, Surf. Topogr. Metrol. Prop. 1, 013001 (2017)](https://doi.org/10.1088/2051-672X/aa51f8)

Build status
------------

The following badge should say _build passing_. This means that all automated tests completed successfully for the master branch.

[![Build Status](https://travis-ci.org/ComputationalMechanics/SurfaceTopography.svg?branch=master)](https://travis-ci.org/github/ComputationalMechanics/SurfaceTopography)

Documentation
-------------

[Sphinx](https://www.sphinx-doc.org/)-generated documentation can be found [here](https://computationalmechanics.github.io/SurfaceTopography/).

Dependencies
------------

The package requires :
- **numpy** - https://www.numpy.org/
- **NuMPI** - https://github.com/imtek-simulation/numpi
- **muFFT** - https://gitlab.com/muspectre/muspectre

Optional dependencies:
- **runtests** - https://github.com/bccp/runtests
