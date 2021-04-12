#
# Copyright 2021 Lars Pastewka
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

import numpy as np
from io import TextIOBase
from struct import unpack
from zipfile import ZipFile

import defusedxml.ElementTree as ElementTree

from .. import Topography
from .Reader import ReaderBase, ChannelInfo

# The files within ZON (zip) files are named using UUIDs. Some of these
# UUIDs are fixed and contain the same information in each of these files.

# This file contains height data
HEIGHT_DATA_UUID = '4cdb0c75-5706-48cc-a9a1-adf395d609ae'

# This contains information on unit conversion
UNIT_UUID = '686613b8-27b5-4a29-8ffc-438c2780873e'

# This contains an inventory of *image* data
INVENTORY_UUID = '772e6d38-40aa-4590-85d3-b041fa243570'


class ZONReader(ReaderBase):
    _format = 'zon'
    _name = 'Keyence ZON'
    _description = '''
This reader open ZON files that are written by some Keyence instruments.
'''

    # Reads in the positions of all the data and metadata
    def __init__(self, file_path):

        # depending from where this function is called, file_path might already
        # be a filestream
        already_open = False
        if not hasattr(file_path, 'read'):
            f = open(file_path, "rb")
        else:
            already_open = True
            if isinstance(file_path, TextIOBase):
                # file was opened without the 'b' option, so read its buffer to
                # get the binary data
                f = file_path.buffer
            else:
                f = file_path

        # ZON files are ZIP files with a header. The header contains a
        # thumbnail of the measurement and we are not really interested
        # in that one. Python's ZipFile automatically skips that header.

        self._channels = []
        try:
            with ZipFile(f, 'r') as z:
                # Parse unit information
                root = ElementTree.parse(z.open(UNIT_UUID)).getroot()
                meter_per_pixel = float(root.find('XYCalibration').find('MeterPerPixel').text)
                meter_per_unit = float(root.find('ZCalibration').find('MeterPerUnit').text)

                # Parse height data information
                # Header consists of four int32, followed by image data
                width, height, element_size = unpack('iii', z.open(HEIGHT_DATA_UUID).read(12))
                assert element_size == 4
                self._channels += [
                    ChannelInfo(self, 0, name='default', dim=2,
                                nb_grid_pts=(width, height),
                                physical_sizes=(width * meter_per_pixel,
                                                height * meter_per_unit),
                                info={'unit': 'm',
                                      'data_uuid': HEIGHT_DATA_UUID,
                                      'meter_per_pixel': meter_per_pixel,
                                      'meter_per_unit': meter_per_unit})]

        finally:
            if not already_open:
                f.close()

        self._file_path = file_path

    @property
    def channels(self):
        return self._channels

    def topography(self, channel_index=None, physical_sizes=None, height_scale_factor=None, info={},
                   periodic=False, subdomain_locations=None, nb_subdomain_grid_pts=None):
        if channel_index is None:
            channel_index = self._default_channel_index

        if subdomain_locations is not None or nb_subdomain_grid_pts is not None:
            raise RuntimeError('This reader does not support MPI parallelization.')

        channel_info = self._channels[channel_index]
        if physical_sizes is None:
            physical_sizes = channel_info.physical_sizes

        info.update(channel_info.info)

        # depending from where this function is called, file_path might already
        # be a filestream
        already_open = False
        if not hasattr(self._file_path, 'read'):
            f = open(self._file_path, "rb")
        else:
            already_open = True
            if isinstance(self._file_path, TextIOBase):
                # file was opened without the 'b' option, so read its buffer to
                # get the binary data
                f = self._file_path.buffer
            else:
                f = self._file_path

        try:
            # Read image data
            nx, ny = channel_info.nb_grid_pts
            with ZipFile(f, 'r') as z:
                with z.open(channel_info.info['data_uuid']) as f:
                    f.read(16)  # skip header
                    height_data = np.frombuffer(f.read(4 * nx * ny), np.dtype('i4'))
                    height_data.shape = (nx, ny)
        finally:
            if not already_open:
                f.close()

        topo = Topography(height_data, physical_sizes, info=info, periodic=periodic)

        meter_per_unit = channel_info.info['meter_per_unit']
        if height_scale_factor is not None:
            return topo.scale(height_scale_factor * meter_per_unit)
        else:
            return topo.scale(meter_per_unit)

        return topo
