#
# Copyright 2015-2016, 2019-2020 Lars Pastewka
#           2020 Michael Röttger
#           2019 Antoine Sanner
#           2019 Kai Haase
#           2015-2016 Till Junge
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

import unittest
import os

import pytest
from NuMPI import MPI

from SurfaceTopography.IO.MI import MIReader

pytestmark = pytest.mark.skipif(
    MPI.COMM_WORLD.Get_size() > 1,
    reason="tests only serial funcionalities, please execute with pytest")

DATADIR = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.realpath(__file__))),
    'file_format_examples')


class MISurfaceTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_read_header(self):
        file_path = os.path.join(DATADIR, 'mi1.mi')

        loader = MIReader(file_path)

        # Like in Gwyddion, there should be 4 channels in total
        assert len(loader.channels) == 4
        assert [ch.name for ch in loader.channels] == ['Topography',
                                                       'Deflection',
                                                       'Friction', 'Friction']

        # Check if metadata has been read in correctly
        self.assertEqual(loader.channels[0].dim, 2)
        self.assertEqual(loader.channels[0].nb_grid_pts, (256, 256))
        self.assertEqual(loader.channels[0].physical_sizes, (2e-05, 2e-05))
        self.assertEqual(loader.channels[0].info,
                         {'DisplayOffset': '8.8577270507812517e-004',
                          'DisplayRange': '1.3109436035156252e-002',
                          'acqMode': 'Main',
                          'label': 'Topography',
                          'range': '2.9025000000000003e+000',
                          'unit': 'µm',
                          'direction': 'Trace',
                          'filter': '3rd_order',
                          'name': 'Topography',
                          'trace': 'Trace'})

        self.assertEqual(loader.default_channel.index, 0)
        self.assertEqual(loader.default_channel.nb_grid_pts, (256, 256))

        # Some metadata value
        self.assertEqual(loader.info['biasSample'], 'TRUE')

    def test_topography(self):
        file_path = os.path.join(DATADIR, 'mi1.mi')

        loader = MIReader(file_path)

        topography = loader.topography()

        # Check one height value
        self.assertAlmostEqual(topography._heights[0, 0], -0.4986900329589844,
                               places=9)

        # Check out if metadata from global and the channel are both in the
        # result from channel metadata
        self.assertTrue('direction' in topography.info.keys())
        # From global metadata
        self.assertTrue('zDacRange' in topography.info.keys())

        # Check the value of one of the metadata
        self.assertEqual(topography.info['unit'], 'µm')
