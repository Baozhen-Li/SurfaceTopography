#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
@file   HeightContainer.py

@author Lars Pastewka <lars.pastewka@imtek.uni-freiburg.de>

@date   09 Dec 2018

@brief  Support for uniform topogography descriptions

@section LICENCE

Copyright 2015-2017 Till Junge, Lars Pastewka

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

import abc

import numpy as np

from .HeightContainer import AbstractHeightContainer, UniformTopographyInterface, DecoratedTopography
from .Uniform.Detrending import tilt_from_height, tilt_and_curvature


class UniformLineScan(AbstractHeightContainer, UniformTopographyInterface):
    """
    Line scan that lives on a uniform one-dimensional grid.
    """

    _functions = {}

    def __init__(self, heights, size, periodic=False, info={}):
        """
        Parameters
        ----------
        profile : array_like
            Data containing the height information. Needs to be a
            one-dimensional array.
        size : tuple of floats
            Physical size of the topography map
        periodic : bool
            Flag setting the periodicity of the surface
        """
        heights = np.asarray(heights)

        if heights.ndim != 1:
            raise ValueError('Heights array must be one-dimensional.')

        super().__init__(info=info)

        # Automatically turn this into a masked array if there is data missing
        if np.sum(np.logical_not(np.isfinite(heights))) > 0:
            heights = np.ma.masked_where(np.logical_not(np.isfinite(heights)), heights)
        self._heights = heights
        self._size = size
        self._periodic = periodic

    def __getstate__(self):
        state = super().__getstate__(), self._heights, self._size, self._periodic
        return state

    def __setstate__(self, state):
        superstate, self._heights, self._size, self._periodic = state
        super().__setstate__(superstate)

    # Implement abstract methods of AbstractHeightContainer

    @property
    def dim(self):
        return 1

    @property
    def size(self):
        return self._size,

    @size.setter
    def size(self, new_size):
        self._size = new_size

    @property
    def is_periodic(self):
        return self._periodic

    @property
    def is_uniform(self):
        return True

    # Implement uniform line scan interface

    @property
    def resolution(self):
        return len(self._heights),

    @property
    def pixel_size(self):
        return (s / r for s, r in zip(self.size, self.resolution))

    @property
    def area_per_pt(self):
        return self.pixel_size

    @property
    def has_undefined_data(self):
        return np.ma.getmask(self._heights) is not np.ma.nomask

    def positions(self):
        r, = self.resolution
        p, = self.pixel_size
        return np.arange(r) * p

    def heights(self):
        return self._heights

    def save(self, fname, compress=True):
        """ saves the topography as a NumpyTxtTopography. Warning: This only saves
            the profile; the size is not contained in the file
        """
        if compress:
            if not fname.endswith('.gz'):
                fname = fname + ".gz"
        np.savetxt(fname, self.array())


class UniformlyInterpolatedLineScan(DecoratedTopography, UniformTopographyInterface):
    """
    Interpolate a topography onto a uniform grid.
    """

    def __init__(self, topography, nb_points, padding, info={}):
        """
        Parameters
        ----------
        topography : Topography
            Topography to interpolate.
        nb_points : int
            Number of equidistant grid points.
        padding : int
            Number of padding grid points, zeros appended to the data.
        """
        super().__init__(topography, info=info)
        self.nb_points = nb_points
        self.padding = padding

        # This is populated with functions from the nonuniform topography, but this is a uniform topography
        self._functions = UniformLineScan._functions

    def __getstate__(self):
        """ is called and the returned object is pickled as the contents for
            the instance
        """
        state = super().__getstate__(), self.nb_points, self.padding
        return state

    def __setstate__(self, state):
        """ Upon unpickling, it is called with the unpickled state
        Keyword Arguments:
        state -- result of __getstate__
        """
        superstate, self.nb_points, self.padding = state
        super().__setstate__(superstate)

    # Implement abstract methods of AbstractHeightContainer

    @property
    def dim(self):
        return 1

    @property
    def size(self):
        s, = self.parent_topography.size
        return s * (self.nb_points + self.padding) / self.nb_points,

    @property
    def is_periodic(self):
        return self.parent_topography.is_periodic

    @property
    def is_uniform(self):
        return True

    # Implement uniform line scan interface

    @property
    def resolution(self):
        """Return resolution, i.e. number of pixels, of the topography."""
        return self.nb_points + self.padding,

    @property
    def pixel_size(self):
        return (s / r for s, r in zip(self.size, self.resolution))

    @property
    def area_per_pt(self):
        return self.pixel_size

    @property
    def has_undefined_data(self):
        return False

    def positions(self):
        left, right = self.parent_topography.x_range
        size = right - left
        return np.linspace(left - size * self.padding / (2 * self.nb_points),
                           right + size * self.padding / (2 * self.nb_points),
                           self.nb_points + self.padding)

    def heights(self):
        """ Computes the rescaled profile.
        """
        x = self.positions()
        return np.interp(x, *self.parent_topography.positions_and_heights())


class Topography(AbstractHeightContainer, UniformTopographyInterface):
    """
    Topography that lives on a uniform two-dimensional grid, i.e. a topography
    map.
    """

    _functions = {}

    def __init__(self, heights, size, periodic=False, info={}):
        """
        Parameters
        ----------
        profile : array_like
            Data containing the height information. Needs to be a
            two-dimensional array.
        size : tuple of floats
            Physical size of the topography map
        periodic : bool
            Flag setting the periodicity of the surface
        """
        heights = np.asarray(heights)

        if heights.ndim != 2:
            raise ValueError('Heights array must be two-dimensional.')

        super().__init__(info=info)

        # Automatically turn this into a masked array if there is data missing
        if np.sum(np.logical_not(np.isfinite(heights))) > 0:
            heights = np.ma.masked_where(np.logical_not(np.isfinite(heights)), heights)
        self._heights = heights
        self._size = size
        self._periodic = periodic

    def __getstate__(self):
        state = super().__getstate__(), self._heights, self._size, self._periodic
        return state

    def __setstate__(self, state):
        superstate, self._heights, self._size, self._periodic = state
        super().__setstate__(superstate)

    # Implement abstract methods of AbstractHeightContainer

    @property
    def dim(self):
        return 2

    @property
    def is_periodic(self):
        return self._periodic

    @property
    def is_uniform(self):
        return True

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, new_size):
        self._size = new_size

    @property
    def resolution(self, ):
        """ needs to be testable to make sure that geometry and halfspace are
            compatible
        """
        return self._heights.shape

    # Implement topography interface

    @property
    def pixel_size(self):
        return np.asarray(self.size) / np.asarray(self.resolution)

    @property
    def area_per_pt(self):
        return np.prod(self.pixel_size)

    @property
    def has_undefined_data(self):
        return np.ma.getmask(self._heights) is not np.ma.nomask

    def positions(self):
        # FIXME: Write test for this method
        nx, ny = self.resolution
        sx, sy = self.size
        return np.meshgrid(np.arange(nx) * sx/nx, np.arange(ny) * sy/ny, indexing='ij')

    def heights(self):
        return self._heights

    def positions_and_heights(self):
        x, y = self.positions()
        return x, y, self.heights()

    def save(self, fname, compress=True):
        """ saves the topography as a NumpyTxtTopography. Warning: This only saves
            the profile; the size is not contained in the file
        """
        if compress:
            if not fname.endswith('.gz'):
                fname = fname + ".gz"
        np.savetxt(fname, self.heights())


class DecoratedUniformTopography(DecoratedTopography, UniformTopographyInterface):
    @property
    def has_undefined_data(self):
        return self.parent_topography.has_undefined_data

    @property
    def is_periodic(self):
        return self.parent_topography.is_periodic

    @property
    def dim(self):
        return self.parent_topography.dim

    @property
    def pixel_size(self):
        return self.parent_topography.pixel_size

    @property
    def size(self):
        return self.parent_topography.size

    @size.setter
    def size(self, new_size):
        self.parent_topography.size = new_size

    @property
    def resolution(self):
        return self.parent_topography.resolution

    @property
    def area_per_pt(self):
        return self.parent_topography.area_per_pt

    def positions(self):
        return self.parent_topography.positions()

    def positions_and_heights(self):
        return (*self.positions(), self.heights())

    def squeeze(self):
        if self.dim == 1:
            return UniformLineScan(self.heights(), self.size, periodic=self.is_periodic, info=self.info)
        else:
            return Topography(self.heights(), self.size, periodic=self.is_periodic, info=self.info)


class ScaledUniformTopography(DecoratedUniformTopography):
    """ used when geometries are scaled
    """

    def __init__(self, topography, coeff, info={}):
        """
        Keyword Arguments:
        topography  -- Topography to scale
        coeff -- Scaling factor
        """
        super().__init__(topography, info=info)
        self.coeff = float(coeff)

    def __getstate__(self):
        """ is called and the returned object is pickled as the contents for
            the instance
        """
        state = super().__getstate__(), self.coeff
        return state

    def __setstate__(self, state):
        """ Upon unpickling, it is called with the unpickled state
        Keyword Arguments:
        state -- result of __getstate__
        """
        superstate, self.coeff = state
        super().__setstate__(superstate)

    def heights(self):
        """ Computes the rescaled profile.
        """
        return self.coeff * self.parent_topography.heights()


class DetrendedUniformTopography(DecoratedUniformTopography):
    """
    Remove trends from a topography. This is achieved by fitting polynomials
    to the topography data to extract trend lines. The resulting topography
    is then detrended by substracting these trend lines.
    """

    def __init__(self, topography, detrend_mode='height', info={}):
        """
        Parameters
        ----------
        topography : Topography
            Topography to be detrended.
        detrend_mode : str
            'center': center the topography, no trend correction.
            'height': adjust slope such that rms height is minimized.
            'slope': adjust slope such that rms slope is minimized.
            'curvature': adjust slope and curvature such that rms height is minimized.
            (Default: 'height')
        """
        super().__init__(topography, info=info)
        self._detrend_mode = detrend_mode
        self._detrend()

    def _detrend(self):
        if self.dim == 1:
            if self._detrend_mode == 'center':
                self._coeffs = (self.parent_topography.mean(),)
            elif self._detrend_mode == 'height':
                x, y = self.parent_topography.positions_and_heights()
                self._coeffs = polyfit(x / self.parent_topography.size, y, 1)
            elif self._detrend_mode == 'slope':
                sl = self.parent_topography.derivative().mean()
                self._coeffs = [self.parent_topography.mean(), sl]
            elif self._detrend_mode == 'curvature':
                x, y = self.parent_topography.positions_and_heights()
                self._coeffs = polyfit(x / self.parent_topography.size, y, 2)
            else:
                raise ValueError("Unsupported detrend mode '{}' for line scans." \
                                 .format(self._detrend_mode))
        else:  # self.dim == 2
            if self._detrend_mode is None or self._detrend_mode == 'center':
                self._coeffs = [self.parent_topography.mean()]
            elif self._detrend_mode == 'height':
                self._coeffs = [s for s in tilt_from_height(self.parent_topography)]
            elif self._detrend_mode == 'slope':
                slx, sly = self.parent_topography.derivative(1)
                slx = slx.mean()
                sly = sly.mean()
                nx, ny = self.resolution
                sx, sy = self.size
                self._coeffs = [slx * sx, sly * sy,
                                self.parent_topography.mean() - slx * sx * (nx - 1) / (2 * nx) - sly * sy * (ny - 1) / (
                                            2 * ny)]
            elif self._detrend_mode == 'curvature':
                self._coeffs = [s for s in tilt_and_curvature(self.parent_topography)]
            else:
                raise ValueError("Unsupported detrend mode '{}' for 2D topographies." \
                                 .format(self._detrend_mode))

    def __getstate__(self):
        """ is called and the returned object is pickled as the contents for
            the instance
        """
        state = super().__getstate__(), self._detrend_mode, self._coeffs
        return state

    def __setstate__(self, state):
        """ Upon unpickling, it is called with the unpickled state
        Keyword Arguments:
        state -- result of __getstate__
        """
        superstate, self._detrend_mode, self._coeffs = state
        super().__setstate__(superstate)

    @property
    def coeffs(self, ):
        return self._coeffs

    @property
    def detrend_mode(self, ):
        return self._detrend_mode

    @detrend_mode.setter
    def detrend_mode(self, detrend_mode):
        self._detrend_mode = detrend_mode
        self._detrend()

    @property
    def is_periodic(self):
        """A detrended surface is never periodic"""
        return False

    def heights(self):
        """ Computes the combined profile.
        """
        if len(self._coeffs) == 1:
            a0, = self._coeffs
            return self.parent_topography.heights() - a0
        elif self.dim == 1:
            x = np.arange(n) / self.resolution[0]
            if len(self._coeffs) == 2:
                a0, a1 = self._coeffs
                return self.parent_topography.heights() - a0 - a1 * x
            elif len(self._coeffs) == 3:
                a0, a1, a2 = self._coeffs
                return self.parent_topography.heights() - a0 - a1 * x - a2 * x * x
            else:
                raise RuntimeError('Unknown size of coefficients tuple for line scans.')
        else:  # self.dim == 2
            x, y = np.meshgrid(*(np.arange(n) / n for n in self.resolution), indexing='ij')
            if len(self._coeffs) == 3:
                a1x, a1y, a0 = self._coeffs
                return self.parent_topography.heights() - a0 - a1x * x - a1y * y
            elif len(self._coeffs) == 6:
                m, n, mm, nn, mn, h0 = self._coeffs
                xx = x * x
                yy = y * y
                xy = x * y
                return self.parent_topography.heights() - h0 - m * x - n * y - mm * xx - nn * yy - mn * xy
            else:
                raise RuntimeError('Unknown size of coefficients tuple for 2D topographies.')

    def stringify_plane(self, fmt=lambda x: str(x)):
        str_coeffs = [fmt(x) for x in self._coeffs]
        if self.dim == 1:
            if len(self._coeffs) == 1:
                h0, = str_coeffs
                return h0
            elif len(self._coeffs) == 2:
                return '{0} + {1} x'.format(*str_coeffs)
            elif len(self._coeffs) == 3:
                return '{0} + {1} x + {2} x^2'.format(*str_coeffs)
            else:
                raise RuntimeError('Unknown size of coefficients tuple.')
        else:
            if len(self._coeffs) == 1:
                h0, = str_coeffs
                return h0
            elif len(self._coeffs) == 3:
                return '{2} + {0} x + {1} y'.format(*str_coeffs)
            elif len(self._coeffs) == 6:
                return '{5} + {0} x + {1} y + {2} x^2 + {3} y^2 + {4} xy'.format(*str_coeffs)
            else:
                raise RuntimeError('Unknown size of coefficients tuple.')


class TranslatedTopography(DecoratedUniformTopography):
    """ used when geometries are translated
    """
    name = 'translated_topography'

    def __init__(self, topography, offset=(0, 0), info={}):
        """
        Keyword Arguments:
        topography  -- Topography to translate
        offset -- Translation offset in number of grid points
        """
        super().__init__(topography, info=info)
        assert isinstance(topography, Topography)
        self._offset = offset

    @property
    def offset(self, ):
        return self._offset

    @offset.setter
    def offset(self, offset, offsety=None):
        if offsety is None:
            self.offset = offset
        else:
            self.offset = (offset, offsety)

    def heights(self):
        """ Computes the translated profile.
        """
        offsetx, offsety = self.offset
        return np.roll(np.roll(self.parent_topography.heights(), offsetx, axis=0), offsety, axis=1)


class CompoundTopography(DecoratedUniformTopography):
    """ used when geometries are combined
    """
    name = 'compound_topography'

    def __init__(self, topography_a, topography_b):
        """ Behaves like a topography that is a sum of two Topographies
        Keyword Arguments:
        topography_a   -- first topography of the compound
        topography_b   -- second topography of the compound
        """
        super().__init__()

        def combined_val(prop_a, prop_b, propname):
            """
            topographies can have a fixed or dynamic, adaptive resolution (or other
            attributes). This function assures that -- if this function is
            called for two topographies with fixed resolutions -- the resolutions
            are identical
            Parameters:
            prop_a   -- field of one topography
            prop_b   -- field of other topography
            propname -- field identifier (for error messages only)
            """
            if prop_a is None:
                return prop_b
            else:
                if prop_b is not None:
                    assert prop_a == prop_b, \
                        "{} incompatible:{} <-> {}".format(
                            propname, prop_a, prop_b)
                return prop_a

        self._dim = combined_val(topography_a.dim, topography_b.dim, 'dim')
        self._resolution = combined_val(topography_a.resolution, topography_b.resolution, 'resolution')
        self._size = combined_val(topography_a.size, topography_b.size, 'size')
        self.parent_topography_a = topography_a
        self.parent_topography_b = topography_b

    def array(self):
        """ Computes the combined profile
        """
        return (self.parent_topography_a.heights() +
                self.parent_topography_b.heights())


### Register analysis functions from this module

Topography.register_function('mean', lambda this: this.heights().mean())
UniformLineScan.register_function('mean', lambda this: this.heights().mean())


### Register pipeline functions from this module

Topography.register_function('scale', ScaledUniformTopography)
Topography.register_function('detrend', DetrendedUniformTopography)

UniformLineScan.register_function('scale', ScaledUniformTopography)
UniformLineScan.register_function('detrend', DetrendedUniformTopography)
