#
# Copyright 2019-2020 Lars Pastewka
#           2020 Michael Röttger
#           2019 Antoine Sanner
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

#
# The DI file format is described in detail here:
# http://www.physics.arizona.edu/~smanne/DI/software/fileformats.html
#

import re
from datetime import datetime

import numpy as np

from SurfaceTopography import Topography

from .common import get_unit_conversion_factor, height_units, mangle_height_unit
from .Reader import ReaderBase, ChannelInfo


###

class DIReader(ReaderBase):
    _format = 'di'
    _name = 'Veeco (Digital Instruments) Nanoscope'
    _description = '''
Digitial Instruments Nanoscope files typically have a three-digit number as
the file extension (.001, .002, .003, ...). This format contains information
on the physical size of the topography map as well as its units. The reader
supports V4.3 and later version of the format.
'''

    def __init__(self, fobj):
        """
        Load Digital Instrument's Nanoscope files.

        Arguments
        ---------
        fobj : filename or file object
             File or data stream to open.
        """
        self._fobj = fobj
        close_file = False
        if not hasattr(fobj, 'read'):
            fobj = open(fobj, 'rb')
            close_file = True
        try:
            parameters = []
            section_name = None
            section_dict = {}

            L = fobj.readline().decode('latin-1').strip()
            while L and L.lower() != r'\*file list end':
                if L.startswith('\\*'):
                    if section_name is not None:
                        parameters += [(section_name, section_dict)]
                    new_section_name = L[2:].lower()
                    if section_name is None:
                        if new_section_name != 'file list':
                            raise IOError("Header must start with the "
                                          "'File list' section.")
                    section_name = new_section_name
                    section_dict = {}
                elif L.startswith('\\'):
                    if section_name is None:
                        raise IOError('Encountered key before section '
                                      'header.')
                    s = L[1:].split(': ', 1)
                    try:
                        key, value = s
                    except ValueError:
                        key, = s
                        value = ''
                    section_dict[key.lower()] = value.strip()
                else:
                    raise IOError(
                        "Header line '{}' does not start with a slash."
                        .format(L))
                L = fobj.readline().decode('latin-1').strip()
            if section_name is None:
                raise IOError('No sections found in header.')
            parameters += [(section_name, section_dict)]

            self._channels = []
            self._offsets = []

            scanner = {}
            info = {}
            for n, p in parameters:
                if n == 'file list':
                    if 'date' in p:
                        info['acquisition_time'] = \
                            datetime.strptime(p['date'],
                                              '%I:%M:%S %p %a %b %d %Y')
                elif n == 'scanner list' or n == 'ciao scan list':
                    scanner.update(p)
                elif n == 'ciao image list':
                    image_data_key = re.match(r'^S \[(.*?)\] ',
                                              p['@2:image data']).group(1)

                    nx = int(p['samps/line'])
                    ny = int(p['number of lines'])

                    s = p['scan size'].split(' ', 2)
                    sx = float(s[0])
                    sy = float(s[1])

                    xy_unit = mangle_height_unit(s[2])
                    offset = int(p['data offset'])
                    self._offsets.append(offset)

                    length = int(p['data length'])
                    elsize = int(p['bytes/pixel'])
                    if elsize != 2:
                        raise IOError(
                            "Don't know how to handle {} bytes per pixel "
                            "data.".format(elsize))
                    if nx * ny * elsize != length:
                        raise IOError(
                            'Data block physical_sizes differs from extend '
                            'of surface.')

                    scale_re = re.match(
                        r'^V \[(.*?)\] \(([0-9\.]+) (.*)\/LSB\) (.*) '
                        r'(.*)', p['@2:z scale'])
                    quantity = scale_re.group(1).lower()
                    hard_scale = float(scale_re.group(4)) / 65536
                    hard_unit = scale_re.group(5)

                    s = scanner['@' + quantity].split()
                    if s[0] != 'V' or len(s) < 2:
                        raise ValueError('Malformed Nanoscope DI file.')
                    soft_scale = float(s[1])

                    height_unit = None
                    hard_to_soft = 1.0
                    if len(s) > 2:
                        # Check units
                        height_unit, soft_unit = s[2].split('/')
                        hard_to_soft = get_unit_conversion_factor(hard_unit,
                                                                  soft_unit)
                        if hard_to_soft is None:
                            raise ValueError(
                                "Units for hard (={}) and soft (={}) "
                                "scale differ for '{}'. Don't know how "
                                "to handle this.".format(hard_unit,
                                                         soft_unit,
                                                         image_data_key))
                    if height_unit in height_units:
                        height_unit = mangle_height_unit(height_unit)
                        if xy_unit != height_unit:
                            fac = get_unit_conversion_factor(xy_unit,
                                                             height_unit)
                            sx *= fac
                            sy *= fac
                            xy_unit = height_unit
                        unit = height_unit
                    else:
                        unit = (xy_unit, height_unit)

                    channel_info = info.copy()
                    channel_info.update(dict(
                        unit=unit,
                        height_scale_factor=hard_scale * hard_to_soft *
                        soft_scale))
                    channel = ChannelInfo(self,
                                          len(self._channels),
                                          name=image_data_key,
                                          dim=2,
                                          nb_grid_pts=(nx, ny),
                                          physical_sizes=(sx, sy),
                                          periodic=False,
                                          info=channel_info)
                    self._channels.append(channel)
        finally:
            if close_file:
                fobj.close()

    @property
    def channels(self):
        return self._channels

    def topography(self, channel_index=None, physical_sizes=None,
                   height_scale_factor=None, info={}, periodic=False,
                   subdomain_locations=None, nb_subdomain_grid_pts=None):
        if channel_index is None:
            channel_index = self._default_channel_index

        if subdomain_locations is not None or \
                nb_subdomain_grid_pts is not None:
            raise RuntimeError(
                'This reader does not support MPI parallelization.')
        close_file = False
        if not hasattr(self._fobj, 'read'):
            fobj = open(self._fobj, 'rb')
            close_file = True
        else:
            fobj = self._fobj

        channel = self._channels[channel_index]
        sx, sy = self._check_physical_sizes(physical_sizes,
                                            channel.physical_sizes)

        nx, ny = channel.nb_grid_pts

        offset = self._offsets[channel_index]
        dtype = np.dtype('<i2')

        ###################################

        fobj.seek(offset)
        rawdata = fobj.read(nx * ny * dtype.itemsize)
        unscaleddata = np.frombuffer(rawdata, count=nx * ny,
                                     dtype=dtype).reshape(nx, ny)

        # internal information from file
        _info = dict(unit=channel.info["unit"], data_source=channel.name)
        _info.update(info)
        if 'acquisition_time' in channel.info:
            _info['acquisition_time'] = channel.info['acquisition_time']

        # the orientation of the heights is modified in order to match
        # the image of gwyddion when plotted with imshow(t.heights().T)
        # or pcolormesh(t.heights().T) for origin in lower left and
        # with inverted y axis (cartesian coordinate system)
        surface = Topography(np.fliplr(unscaleddata.T), (sx, sy), info=_info,
                             periodic=periodic)
        if height_scale_factor is None:
            height_scale_factor = channel.info["height_scale_factor"]
        surface = surface.scale(height_scale_factor)

        if close_file:
            fobj.close()

        return surface

    channels.__doc__ = ReaderBase.channels.__doc__
    topography.__doc__ = ReaderBase.topography.__doc__
