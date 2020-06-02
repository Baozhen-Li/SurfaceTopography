#
# Copyright 2018, 2020 Lars Pastewka
#           2019 Michael Röttger
#           2018-2019 Antoine Sanner
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
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import pytest
import unittest
import numpy as np


from SurfaceTopography import Topography, NonuniformLineScan, UniformLineScan

from NuMPI import MPI

from muFFT import FFT

@pytest.fixture
def sinewave2D(comm):
    n = 256
    X, Y = np.mgrid[slice(0,n),slice(0,n)]

    fftengine = FFT((n, n), fft="mpi", communicator=comm)

    hm = 0.1
    L = float(n)
    sinsurf = np.sin(2 * np.pi / L * X) * np.sin(2 * np.pi / L * Y) * hm
    size= (L, L)

    top = Topography(sinsurf, decomposition='domain',
                     nb_subdomain_grid_pts=fftengine.nb_subdomain_grid_pts,
                     subdomain_locations=fftengine.subdomain_locations,
                     physical_sizes=size, communicator=comm)

    return (L, hm, top)

@pytest.mark.skipif(MPI.COMM_WORLD.Get_size()> 1,
        reason="tests only serial functionalities, please execute with pytest")
def test_rms_curvature(sinewave2D):
    L, hm, top = sinewave2D
    numerical = top.rms_curvature()
    analytical = np.sqrt(4 * (16*np.pi**4 / L**4) *hm**2 /4 /4 )
    #                 rms(∆)^2 = (qx^2 + qy^2)^2 * hm^2 / 4
    #print(numerical-analytical)
    np.testing.assert_almost_equal(numerical, analytical, 5)

@pytest.mark.skipif(MPI.COMM_WORLD.Get_size()> 1,
        reason="tests only serial functionalities, please execute with pytest")
def test_rms_slope(sinewave2D):
    L, hm, top = sinewave2D
    numerical = top.rms_slope()
    analytical = np.sqrt(2*np.pi ** 2 * hm**2 / L**2)
    # print(numerical-analytical)
    np.testing.assert_almost_equal(numerical, analytical, 5)

def test_rms_height(comm, sinewave2D):
    L, hm, top = sinewave2D
    numerical = top.rms_height()
    analytical = np.sqrt(hm**2 / 4)

    assert numerical == analytical

@pytest.mark.skipif(MPI.COMM_WORLD.Get_size()> 1,
        reason="tests only serial functionalities, please execute with pytest")
@pytest.mark.parametrize("periodic", [False, True])
def test_rms_curvature_sinewave_2D(periodic):
    precision = 5

    n = 256
    X, Y = np.mgrid[slice(0, n), slice(0, n)]
    hm = 0.3
    L = float(n)
    size=(L,L)

    surf = Topography(np.sin(2 * np.pi / L * X) *hm, physical_sizes=size, periodic=periodic)
    numerical_lapl = surf.rms_laplacian()
    analytical_lapl = np.sqrt((2 * np.pi / L )**4 *hm**2 /2)
    #print(numerical-analytical)
    np.testing.assert_almost_equal(numerical_lapl, analytical_lapl,precision)

    np.testing.assert_almost_equal(surf.rms_curvature(), analytical_lapl / 2  , precision)

@pytest.mark.skipif(MPI.COMM_WORLD.Get_size()> 1,
        reason="tests only serial functionalities, please execute with pytest")
def test_rms_curvature_paraboloid_uniform_1D():
    n = 16
    x = np.arange(n)
    curvature = 0.1
    heights = 0.5 * curvature * x**2

    surf = UniformLineScan(heights, physical_sizes=(n,),
                      periodic=False)
    # central finite differences are second order and so exact for the parabola
    assert abs((surf.rms_curvature() - curvature) / curvature) < 1e-15

@pytest.mark.skipif(MPI.COMM_WORLD.Get_size()> 1,
        reason="tests only serial functionalities, please execute with pytest")
def test_rms_curvature_paraboloid_uniform_2D():
    n = 16
    X, Y = np.mgrid[slice(0, n), slice(0, n)]
    curvature = 0.1
    heights = 0.5 * curvature * (X**2 + Y**2)
    surf = Topography(heights, physical_sizes=(n,n), periodic=False)
    # central finite differences are second order and so exact for the paraboloid
    assert abs((surf.rms_curvature() - curvature) / curvature)  < 1e-15

@unittest.skipIf(MPI.COMM_WORLD.Get_size()> 1,
        reason="tests only serial functionalities, please execute with pytest")
class SinewaveTestNonuniform(unittest.TestCase):
    def setUp(self):
        n = 256

        self.hm = 0.1
        self.L = n
        self.X = np.arange(n+1)  # n+1 because we need the endpoint
        self.sinsurf = np.sin(2 * np.pi * self.X / self.L) * self.hm

        self.precision = 5

#    def test_rms_curvature(self):
#        numerical = Nonuniform.rms_curvature(self.X, self.sinsurf)
#        analytical = np.sqrt(16*np.pi**4 *self.hm**2 / self.L**4 )
#        #print(numerical-analytical)
#        self.assertAlmostEqual(numerical,analytical,self.precision)

    def test_rms_slope(self):
        numerical = NonuniformLineScan(self.X, self.sinsurf).rms_slope()
        analytical = np.sqrt(2*np.pi ** 2 * self.hm**2 / self.L**2)
        # print(numerical-analytical)
        self.assertAlmostEqual(numerical, analytical, self.precision)

    def test_rms_height(self):
        numerical = NonuniformLineScan(self.X, self.sinsurf).rms_height()
        analytical = np.sqrt(self.hm**2 / 2)
        #numerical = np.sqrt(np.trapz(self.sinsurf**2, self.X))

        self.assertAlmostEqual(numerical, analytical, self.precision)

if __name__ == '__main__':
    unittest.main()
