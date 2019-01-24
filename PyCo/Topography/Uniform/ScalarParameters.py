#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@file   ScalarParameters.py

@author Till Junge <till.junge@kit.edu>

@date   11 Feb 2015

@brief  Functions computing scalar roughness parameters

@section LICENCE

Copyright 2015-2018 Till Junge, Lars Pastewka

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np


def rms_height(topography, kind='Sq'):
    """
    Compute the root mean square height amplitude of a topography or
    line scan stored on a uniform grid.

    Parameters
    ----------
    topography : Topography or UniformLineScan
        Topography object containing height information.

    Returns
    -------
    rms_height : float
        Root mean square height value.
    """
    profile = topography.heights()
    if kind == 'Sq':
        return np.sqrt(((profile-profile.mean())**2).mean())
    elif kind == 'Rq':
        return np.sqrt(((profile-profile.mean(axis=0))**2).mean())
    else:
        raise RuntimeError("Unknown rms height kind '{}'.".format(kind))


def rms_slope(topography):
    """
    Compute the root mean square amplitude of the height gradient of a
    topography or line scan stored on a uniform grid.

    Parameters
    ----------
    topography : Topography or UniformLineScan
        Topography object containing height information.

    Returns
    -------
    rms_slope : float
        Root mean square slope value.
    """
    diff = topography.derivative(1)
    return np.sqrt((diff[0]**2).mean()+(diff[1]**2).mean())


def rms_Laplacian(topography):
    """
    Compute the root mean square Laplacian of the height gradient of a
    topography or line scan stored on a uniform grid. The rms curvature
    is half of the value returned here.

    Parameters
    ----------
    topography : Topography or UniformLineScan
        Topography object containing height information.

    Returns
    -------
    rms_laplacian : float
        Root mean square Laplacian value.
    """
    curv = topography.derivative(2)
    return np.sqrt(((curv[0][:, 1:-1]+curv[1][1:-1, :])**2).mean())

