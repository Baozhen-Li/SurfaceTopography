#
# Copyright 2019-2020 Lars Pastewka
#           2019-2020 Antoine Sanner
#           2019-2020 Michael Röttger
#           2019 Kai Haase
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import abc
import warnings

import numpy as np


class ChannelInfo:
    """
    Information on topography channels contained within a file. The interface
    is identical to :obj:`HeightContainer` and subclasses.
    """

    def __init__(self, reader, index, name=None, dim=None, nb_grid_pts=None,
                 physical_sizes=None, periodic=None,
                 info={}):
        """
        Initialize the channel. Use as many information from the file as
        possible by passing it in the keyword arguments.

        Arguments
        ---------
        reader: ReaderBase
            Reader instance this channel is coming from.
        index: int
            Index of channel in the file, where zero is the first channel.
        name: str
            Name of the channel. If no name is given, "channel <index>" will
            be used, where "<index>" is replaced with the index.
        dim: int
            Number of dimensions.
        nb_grid_pts: tuple of ints
            Number grid points in each dimension.
        physical_sizes: tuple of floats
            Physical dimensions.
        periodic: bool
            Wether the SurfaceTopography should be interpreted as one period of
            a periodic surface. This will affect the PSD and autocorrelation
            calculations (windowing).
        info: dict
            Meta data found in the file.
        """
        self._reader = reader
        self._index = int(index)
        self._name = "channel {}".format(self._index) \
            if name is None else str(name)
        self._dim = dim
        self._nb_grid_pts = None \
            if nb_grid_pts is None else tuple(np.ravel(nb_grid_pts))
        self._physical_sizes = None \
            if physical_sizes is None else tuple(np.ravel(physical_sizes))
        self._periodic = periodic
        self._info = info.copy()

    def topography(self, physical_sizes=None,
                   height_scale_factor=None, info={},
                   periodic=False,
                   subdomain_locations=None, nb_subdomain_grid_pts=None):
        """
        Returns an instance of a subclass of :obj:`HeightContainer` that
        contains the topography data. The method allows to override data
        found in the data file.

        Arguments
        ---------
        physical_sizes : tuple of floats
            Physical size of the topography. It is necessary to specify this
            if no physical size is found in the data file. If there is a
            physical size, then this parameter will override the physical
            size found in the data file.
        height_scale_factor : float
            Override height scale factor found in the data file.
        info : dict
            This dictionary will be appended to the info dictionary returned
            by the reader.
        periodic: bool
            Wether the SurfaceTopography should be interpreted as one period of
            a periodic surface. This will affect the PSD and autocorrelation
            calculations (windowing)
        subdomain_locations : tuple of ints
            Origin (location) of the subdomain handled by the present MPI
            process.
        nb_subdomain_grid_pts : tuple of ints
            Number of grid points within the subdomain handled by the present
            MPI process.

        Returns
        -------
        topography : subclass of :obj:`HeightContainer`
            The object containing the actual topography data.
        """
        return self._reader.topography(
            channel_index=self._index,
            physical_sizes=physical_sizes,
            height_scale_factor=height_scale_factor,
            info=info,
            periodic=periodic,
            subdomain_locations=subdomain_locations,
            nb_subdomain_grid_pts=nb_subdomain_grid_pts)

    @property
    def index(self):
        """Unique integer channel index."""
        return self._index

    @property
    def name(self):
        '''
        Name of the channel.
        Can be used in a UI for identifying a channel.
        '''
        return self._name

    @property
    def dim(self):
        """
        1 for line scans and 2 for topography maps.
        """
        return self._dim

    @property
    def nb_grid_pts(self):
        """
        Number of grid points in each direction, either 1 or 2 elements
        depending on the dimension of the topography.
        """
        return self._nb_grid_pts

    @property
    def physical_sizes(self):
        """
        If the physical size can be determined from the file, a tuple is
        returned. The tuple has 1 or 2 elements (size_x, size_y), depending
        on the dimension of the topography.

        If the physical size can not be determined from the file, then
        None is returned.

        Note that the physical sizes obtained from the file can be
        overwritten by passing a `physical_sizes` argument to the
        `topography` method that returns the topography object.
        """
        return self._physical_sizes

    @property
    def is_periodic(self):
        """
        Return whether the topography is periodically repeated at the
        boundaries.
        """
        return self._periodic

    @property
    def pixel_size(self):
        """
        The pixel size is returned as the phyiscal size divided by the number
        of grid points. If the physical size can be determined from the file,
        a tuple is returned. The tuple has 1 or 2 elements (size_x, size_y),
        depending on the dimension of the topography.

        If the physical size can not be determined from the file, then
        None is returned.

        Note that the physical sizes obtained from the file can be overwritten
        by passing a `physical_sizes` argument to the `topography` method that
        returns the topography object. Overriding the physical size will also
        affect the pixel size.
        """
        if self._physical_sizes is None or self._nb_grid_pts is None:
            return None
        else:
            return tuple(np.array(self._physical_sizes) /
                         np.array(self._nb_grid_pts))

    @property
    def area_per_pt(self):
        """
        The area per point is returned as the product over the pixel size
        tuple. If `pixel_size` returns None, than also `area_per_pt` returns
        None.s
        """
        if self.pixel_size is None:
            return None
        else:
            return np.prod(self.pixel_size)

    @property
    def info(self):
        """
        A dictionary containing additional information (metadata) not used by
        PyCo itself, but required by third-party application.

        Presently, the following entries have been standardized:
        'unit':
            This is the unit of the physical size (if given in the file) and
            the units of the heights.
        'height_scale_factor':
            Factor which was used to scale the raw numbers from file (which
            can be voltages or some other quantity actually acquired in the
            measurement technique) to heights with the given 'unit'.
        """
        return self._info


class ReaderBase(metaclass=abc.ABCMeta):
    """
    Base class for topography readers. These are object that allow to open a
    file (from filename or stream object), inspect its metadata and then
    request to load a topography from it. Metadata is typically extracted
    without reading the full file.
    """

    _format = None
    _name = None
    _description = None

    _default_channel_index = 0

    @classmethod
    def format(cls):
        """
        String identifier for this file format. Identifier must be unique and
        is typically equal to the file extension of this format.
        """
        if cls._format is None:
            raise RuntimeError('Reader does not provide a format string')
        return cls._format

    @classmethod
    def name(cls):
        """
        Short name of this file format.
        """
        if cls._name is None:
            raise RuntimeError('Reader does not provide a name')
        return cls._name

    @classmethod
    def description(cls):
        """
        Long description of this file format. Should be formatted as markdown.
        """
        if cls._description is None:
            raise RuntimeError('Reader does not provide a description string')
        return cls._description

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        pass

    @property
    @abc.abstractmethod
    def channels(self):
        """
        Returns a list of :obj:`ChannelInfo`s describing the available data
        channels.
        """
        raise NotImplementedError

    @property
    def default_channel(self):
        """Return the default channel. This is often the first channel with
        height information."""
        return self.channels[self._default_channel_index]

    @classmethod
    def _check_physical_sizes(self, physical_sizes_from_arg,
                              physical_sizes=None):
        if physical_sizes is None:
            if physical_sizes_from_arg is None:
                raise ValueError("physical_sizes could not be extracted from "
                                 "file, you should provide it")
        else:
            if physical_sizes_from_arg is None:
                physical_sizes_from_arg = physical_sizes
            elif tuple(physical_sizes_from_arg) != tuple(physical_sizes):
                warnings.warn(
                    "A physical size different from the value specified when "
                    "calling the reader was present in the file. We will "
                    "ignore the value given in the file. Specified values: "
                    "{}; Values from file: {}".format(
                        physical_sizes,
                        physical_sizes_from_arg))
        return physical_sizes_from_arg

    @abc.abstractmethod
    def topography(self, channel_index=None, physical_sizes=None,
                   height_scale_factor=None, info={},
                   periodic=False,
                   subdomain_locations=None, nb_subdomain_grid_pts=None):
        """
        Returns an instance of a subclass of :obj:`HeightContainer` that
        contains the topography data. The method allows to override data
        found in the data file.

        Arguments
        ---------
        channel_index : int
            Index of the channel to load. See also `channels` method.
            (Default: None, which load the default channel)
        physical_si""zes : tuple of floats
            Physical size of the topography. It is necessary to specify this
            if no physical size is found in the data file. If there is a
            physical size, then this parameter will override the physical
            size found in the data file.
        height_scale_factor : float
            Override height scale factor found in the data file.
        info : dict
            This dictionary will be appended to the info dictionary returned
            by the reader.
        periodic: bool
            Wether the SurfaceTopography should be interpreted as one period of
            a periodic surface. This will affect the PSD and autocorrelation
            calculations (windowing)
        subdomain_locations : tuple of ints
            Origin (location) of the subdomain handled by the present MPI
            process.
        nb_subdomain_grid_pts : tuple of ints
            Number of grid points within the subdomain handled by the present
            MPI process.

        Returns
        -------
        topography : subclass of :obj:`HeightContainer`
            The object containing the actual topography data.
        """
        raise NotImplementedError


class ReadFileError(Exception):
    pass


class UnknownFileFormatGiven(ReadFileError):
    pass


class CannotDetectFileFormat(ReadFileError):
    """
    Raised when no reader is able to open_topography the file
    """
    pass


class FileFormatMismatch(ReadFileError):
    """
    Raised when the reader cannot interpret the file at all
    (obvious for txt vs binary, but holds also for a header)
    """
    pass


class CorruptFile(ReadFileError):
    """
    Raised when the reader identifies the file format as matching,
    but there is a mistake, for example the number of points doesn't match
    """
    pass
