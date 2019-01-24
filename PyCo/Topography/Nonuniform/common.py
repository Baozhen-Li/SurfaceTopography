#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@file   common.py

@author Lars Pastewka <lars.pastewka@imtek.uni-freiburg.de>

@date   11 Dec 2018

@brief  Bin for small common helper function and classes for nonuniform
        topographies.

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


def derivative(topography, n):
    """
    Compute derivative of nonuniform line-scan. Function assumes nonperiodic topographies.

    First derivative: Central differences.
    Second derivative: Expand :math:`h(x+\\Delta x_+)` and :math:`(x-\\Delta x_-)` up to second order in the grid
    spacing :math:`\\Delta x_+` and :math:`\\Delta x_+`. Then
    :math:`\\Delta x_- f(x+\\Delta x_+) + \\Delta x_+ f(x+\\Delta x_-)` yields:

    ..math ::

         \\frac{d^2h}{dx^2} \approx  = 2 \\frac{\\Delta x_-\left[f(x+\\Delta x_+)-f(x)\right] + \\Delta x+-\left[f(x+\\Delta x_-)-f(x)\right]}{\\Delta x_+\\Delta x_-(\\Delta x_++\\Delta x_-)}

    Parameters
    ----------
    topography : Topography or UniformLineScan
        Topography object containing height information.
    n : int
        Number of times the derivative is taken.

    Returns
    -------
    derivative : array
        Array with derivative values. Length of array is reduced by :math:`n` with
        respect to the input array for the :math:`n`th derivative.
    """
    x, h = topography.x_positions_and_heights_array()
    if n == 1:
        return np.diff(h) / np.diff(x)
    elif n == 2:
        dxp = x[2:] - x[1:-1]
        dxm = x[1:-1] - x[:-2]

        return 2 * (dxm * (h[2:] - h[1:-1]) + dxp * (h[0:-2] - h[1:-1])) / (dxp * dxm * (dxp + dxm))
    else:
        raise RuntimeError('Currently only first and second derivatives are supported for nonuniform topographies.')
