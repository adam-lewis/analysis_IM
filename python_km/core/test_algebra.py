#! /usr/bin/python
"""Unit tests for algebra.py."""

import os
import unittest
import copy

import scipy as sp
import numpy.lib.format as npfor

import algebra
import kiyopy.custom_exceptions as ce

class TestMatTypes(unittest.TestCase) :
    
    def test_from_memory(self) :
        # Works if constructed from array.
        data = sp.empty((5, 6, 6))
        data[:] = 4.0
        Mat = algebra.info_array(data, {'a' : 'b'})
        self.assertEqual(Mat.shape, (5, 6, 6))
        self.assertEqual(Mat.info['a'], 'b')
        self.assertTrue(sp.allclose(Mat, 4.0))
        # Check that the dictionary is there and empty if uninitialized.
        Mat4 = algebra.info_array(data)
        self.assertEqual(Mat4.info, {})
        # Works if constructed from a slice.
        Mat2 = Mat[1:2, :, :]
        self.assertEqual(Mat2.shape, (1, 6, 6))
        self.assertEqual(Mat2.info['a'], 'b')
        # Works if constructed from a view.
        Mat3 = data.view(algebra.info_array)
        self.assertEqual(Mat3.shape, (5, 6, 6))
        Mat3.info['a'] = 'b'

    def test_from_memmap(self) :
        # Works if constructed from array.
        data = npfor.open_memmap('temp.npy', mode='w+', shape=(4,3,3))
        data[:] = 5.0
        Mat = algebra.info_memmap(data, {'a': 'b'})
        Mat.flush()
        self.assertEqual(Mat.shape, (4, 3, 3))
        self.assertEqual(Mat.info['a'], 'b')
        self.assertTrue(sp.allclose(Mat, 5.0))
        self.assertTrue(isinstance(Mat,  sp.memmap))
        del Mat
        os.remove('temp.npy')

    def test_fails_if_not_memmap(self) :
        data = sp.empty((5, 7, 7))
        self.assertRaises(TypeError, algebra.info_memmap, data)

    def test_assert_info(self) :
        """Test the assert_info function."""
        # info_memaps should pass.
        data = npfor.open_memmap('temp.npy', mode='w+', shape=(4,3,3))
        data[:] = 5.0
        Mat = algebra.info_memmap(data)
        algebra.assert_info(Mat)
        del Mat
        os.remove('temp.npy')
        # info_arrays should pass.
        data = sp.empty((5, 6, 6))
        data[:] = 4.0
        Mat = algebra.info_array(data)
        algebra.assert_info(Mat)
        # arrays should fail.
        self.assertRaises(TypeError, algebra.assert_info, data)

class TestLoadSave(unittest.TestCase) :
    
    def setUp(self) :
        info = { 'a' : 42, 'b' : 'a string', 'c' : 3.14159 }
        data = sp.arange(80).reshape((2,8,5))
        self.Mat = algebra.info_array(data, info)

    def test_runs_filename(self) :
        algebra.save('temp.npy', self.Mat)
        self.assertTrue('temp.npy' in os.listdir('./'))
        self.assertTrue('temp.npy.meta' in os.listdir('./'))

    def test_runs_fid(self) :
        fid = open('temp.npy', 'w')
        algebra.save(fid, self.Mat)
        self.assertTrue('temp.npy' in os.listdir('./'))
        self.assertTrue('temp.npy.meta' in os.listdir('./'))

    def test_checks_dict_executable(self) :
        self.Mat.info['un_readable_object'] = sp.arange(100000)
        self.assertRaises(ce.DataError, algebra.save, 'temp.npy', self.Mat)

    def test_loads(self) :
        algebra.save('temp.npy', self.Mat)
        Loaded = algebra.load('temp.npy')
        self.assertTrue(isinstance(Loaded, sp.ndarray))
        self.assertTrue(isinstance(Loaded, algebra.info_array))
        self.assertTrue(sp.allclose(Loaded, self.Mat))
        self.assertEqual(Loaded.info['a'], self.Mat.info['a'])
        self.assertEqual(Loaded.info['b'], self.Mat.info['b'])
        self.assertAlmostEqual(Loaded.info['c'], self.Mat.info['c'])

    def test_memmap_read(self) :
        algebra.save('temp.npy', self.Mat)
        marray = algebra.open_memmap('temp.npy', mode="r")
        self.assertTrue(isinstance(marray, sp.ndarray))
        self.assertTrue(isinstance(marray, algebra.info_memmap))
        self.assertTrue(sp.allclose(marray, self.Mat))
        self.assertEqual(marray.info['a'], self.Mat.info['a'])

    def test_memmap_write(self) :
        marray = algebra.open_memmap('temp.npy', mode="w+",
                                     shape=self.Mat.shape,
                                     dtype=self.Mat.dtype,
                                     )
        marray[:] = self.Mat[:]
        marray.info = self.Mat.info
        del marray
        marray = None
        Loaded = algebra.load('temp.npy')
        self.assertTrue(isinstance(Loaded, sp.ndarray))
        self.assertTrue(isinstance(Loaded, algebra.info_array))
        self.assertTrue(sp.allclose(Loaded, self.Mat))
        self.assertEqual(Loaded.info['a'], self.Mat.info['a'])


    def tearDown(self) :
        del self.Mat
        if 'temp.npy' in os.listdir('./') :
            os.remove('temp.npy')
        if 'temp.npy.meta' in os.listdir('./') :
            os.remove('temp.npy.meta')

class TestMakeAlgebra(unittest.TestCase) :
    
    def setUp(self) :
        data = sp.arange(60, dtype=float)
        data.shape = (2, 5, 6)
        self.array = algebra.info_array(data)

    def test_make_vector(self) :
        self.array = algebra.vect_array(self.array)
        self.assertEqual(self.array.info['type'], 'vect')
        self.assertEqual(self.array.axes, (None, None, None))
        self.assertTrue(isinstance(self.array, algebra.vect))
        self.assertTrue(isinstance(self.array, algebra.info_array))

    def test_make_vector_named(self) :
        self.array = algebra.vect_array(self.array, ('freq', None, 'ra'))
        self.assertEqual(self.array.info['axes'], ('freq', None, 'ra'))
        self.assertEqual(self.array.axes, ('freq', None, 'ra'))

    def test_make_vector_raises(self) :
        self.assertRaises(TypeError, algebra.vect_array, self.array, (1,2,3))
        self.assertRaises(ValueError, algebra.vect_array, self.array, 
                          ('a','b'))

    def test_make_mat(self) :
        self.array = algebra.mat_array(self.array, row_axes=(0,1), 
                                       col_axes=(0,2))
        self.assertEqual(self.array.info['type'], 'mat')
        self.assertEqual(self.array.axes, (None, None, None))
        self.assertEqual(self.array.rows, (0,1))
        self.assertEqual(self.array.cols, (0,2))
        self.assertTrue(isinstance(self.array, algebra.mat))

    def test_make_mat_raises(self) :
        self.assertRaises(ValueError, algebra.mat_array, self.array, (1,), (2,))
        self.assertRaises(ValueError, algebra.mat_array, self.array, (0,1,'a'), 
                          (2,))
        self.assertRaises(ValueError, algebra.mat_array, self.array, (0,1), 
                          (3,))

class TestMatVectFromArray(unittest.TestCase) :
    
    def setUp(self) :
        self.data = sp.arange(80).reshape((2,8,5))
        self.memmap_data = npfor.open_memmap('temp.npy', mode='w+',
                                             shape=(2,8,5))
        self.memmap_data[:,:,:] = sp.arange(80).reshape(2,8,5)

    def test_vect(self) :
        vect_arr = algebra.make_vect(self.data)
        vect_mem = algebra.make_vect(self.memmap_data)
        self.assertTrue(sp.allclose(vect_arr, vect_mem))
        self.assertTrue(isinstance(vect_arr, algebra.info_array))
        self.assertTrue(isinstance(vect_arr, algebra.vect))
        self.assertTrue(isinstance(vect_mem, algebra.info_memmap))
        self.assertTrue(isinstance(vect_mem, algebra.vect))
    
    def test_mat(self) :
        mat_arr = algebra.make_mat(self.data, (0,1), (0,2))
        mat_mem = algebra.make_mat(self.memmap_data, (0,1), (0,2))
        self.assertTrue(sp.allclose(mat_arr, mat_mem))
        self.assertTrue(isinstance(mat_arr, algebra.info_array))
        self.assertTrue(isinstance(mat_arr, algebra.mat))
        self.assertTrue(isinstance(mat_mem, algebra.info_memmap))
        self.assertTrue(isinstance(mat_mem, algebra.mat))

    def test_from_info(self) :
        arr = algebra.info_array(self.data)
        mat_arr = algebra.make_mat(arr, (0,1), (0,2))
        self.assertTrue(isinstance(mat_arr, algebra.mat))
        mem = algebra.info_memmap(self.memmap_data)
        vect_mem = algebra.make_vect(mem)
        self.assertTrue(isinstance(vect_mem, algebra.vect))

    def tearDown(self) :
        del self.memmap_data
        os.remove('temp.npy')

class TestMatUtils(unittest.TestCase) :
    
    def setUp(self) :
        data = sp.arange(30)
        data.shape = (5, 2, 3)
        self.vect = algebra.info_array(data)
        self.vect = algebra.vect_array(self.vect, 
                                       axis_names=('freq', 'a', 'b'))
        data = sp.arange(120)
        self.mat = algebra.info_array(data)
        self.mat.shape = (5, 4, 6)
        self.mat = algebra.mat_array(self.mat, row_axes=(0,1), col_axes=(0,2), 
                                      axis_names=('freq', 'mode', 'mode'))

    def test_invalid_assignments(self) :
        self.assertRaises(TypeError, self.vect.__setattr__, 'axes', 
                          (None, 5, 'a'))
        self.assertRaises(ValueError, self.vect.__setattr__, 'axes', 
                          (None, 'a'))
        self.assertRaises(ValueError, self.mat.__setattr__, 'cols', 
                          (None, 'a'))
        self.assertRaises(ValueError, self.mat.__setattr__, 'rows', 
                          (0, 7))

    def test_mat_shape(self) :
        """ Check basic functionality."""
        self.assertEqual(self.vect.mat_shape, (30,))
        self.assertEqual(self.mat.mat_shape, (20, 30))
        # Check that it fails if I mess with stuff.
        self.vect.info['axes'] = (None, 5, 'a')
        self.assertRaises(TypeError, self.vect.__getattr__, 'mat_shape')
        self.vect.info['axes'] = (None, 'a')
        self.assertRaises(ValueError, self.vect.__getattr__, 'mat_shape')
        self.mat.info['rows'] = (0,)
        self.assertRaises(ValueError, self.mat.__getattr__, 'mat_shape')
        self.mat.info['rows'] = (0,1,4)
        self.assertRaises(ValueError, self.mat.__getattr__, 'mat_shape')

    def test_another_mat_shape(self) :
        self.mat.shape = (5, 4, 2, 3)
        self.mat.axes = ('freq', 'mode', 'a', 'b')
        self.mat.cols = (0, 2, 3)
        self.mat.rows = (0, 1)
        self.assertEqual(self.mat.mat_shape, (5*4, 5*2*3))

    def test_assert_axes_ordered(self) :
        self.mat.assert_axes_ordered()
        self.mat.cols = (2,)
        self.mat.assert_axes_ordered()
        self.mat.cols = (0,2)
        self.mat.rows = (1,0)
        self.assertRaises(NotImplementedError, self.mat.assert_axes_ordered)
        self.mat.rows = (0,2)
        self.mat.cols = (0,1)
        self.assertRaises(NotImplementedError, self.mat.assert_axes_ordered)

    def test_expand_mat(self) :
        expanded = self.mat.expand()
        self.assertEqual(expanded.shape, self.mat.mat_shape)
        self.assertTrue(sp.allclose(self.mat[0,:,:], expanded[0:4, 0:6]))
    
    def test_flat_view(self) :
        view = self.vect.flat_view()
        self.assertEqual(view.shape, (5*2*3, ))
        self.assertEqual(self.vect.shape, (5, 2, 3))
        view[0] = 42
        self.assertAlmostEqual(self.vect[0,0,0], 42)

    def test_dot_mat_vect(self) :
        self.mat.shape = (5, 4, 2, 3)
        self.mat.cols = (0, 2, 3)
        self.mat.axes = ('freq', 'mode', 'a', 'b')
        prod = algebra.dot(self.mat, self.vect)
        self.assertEqual(prod.mat_shape, (20,))
        self.assertEqual(prod.shape, (5, 4))
        self.assertEqual(prod.info['axes'], ('freq', 'mode'))
        self.assertTrue(sp.allclose(prod.flatten(),
                        sp.dot(self.mat.expand(),
                        self.vect.flatten())))
        # Make sure it checks that the inner axis names match.
        self.mat.axes = ('freq', 'mode', 'c', 'b')
        algebra.dot(self.mat, self.vect, check_inner_axes=False)
        self.assertRaises(ce.DataError, algebra.dot, self.mat, self.vect)
        # Make sure that is checks that the inner axes lengths match.
        self.mat.shape = (5, 4, 6)
        self.mat.cols = (0, 2)
        self.mat.axes = ('freq', 'mode', 'a')
        algebra.dot(self.mat, self.vect, check_inner_axes=False)
        self.assertRaises(ce.DataError, algebra.dot, self.mat, self.vect)

    def test_dot_mat_checks_dims(self) :
        """ Make sure that it checks that marticies have compatible dimensions 
        for matrix multiplication."""
        self.mat.shape = (5, 4, 2, 3)
        self.mat.cols = (0, 2, 3)
        self.mat.axes = ('freq', 'mode', 'a', 'b')
        self.assertRaises(ValueError, algebra.dot, self.vect, self.mat)
        # Matrix-Matrix multiplication not written yet.
        mat2 = sp.arange(120)
        mat2.shape = (5, 2, 3, 4)
        mat2 = algebra.make_mat(mat2, (0, 1, 2), (0, 3))
        self.assertRaises(NotImplementedError, algebra.dot, self.mat, mat2)
    
    def test_to_from_file(self) :
        """Test that vects and mats can be written to and from file and have
        all thier properties preserved."""
        # For vectors.
        algebra.save('temp.npy', self.vect)
        new_vect = algebra.vect_array(algebra.load('temp.npy'))
        self.assertTrue(sp.allclose(self.vect, new_vect))
        self.assertEqual(self.vect.axes, new_vect.axes)
        # For matricies.
        algebra.save('temp.npy', self.mat)
        new_mat = algebra.mat_array(algebra.load('temp.npy'))
        self.assertTrue(sp.allclose(self.mat, new_mat))
        self.assertEqual(self.mat.axes, new_mat.axes)
        # Messing with stuf should raise exceptions.
        new_mat = algebra.load('temp.npy')
        new_mat.info['cols'] = (0,3)
        self.assertRaises(ValueError, algebra.mat_array, new_mat)
        # Clean up
        os.remove('temp.npy')
        os.remove('temp.npy.meta')

if __name__ == '__main__' :
    unittest.main()

