# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from pxr import Gf, Vt

from mujoco_usd_converter._impl.numpy import (
    convert_color,
    convert_quatd,
    convert_quatf,
    convert_vec3d,
    convert_vec3f,
    convert_vec3f_array,
)
from tests.util.ConverterTestCase import ConverterTestCase


class TestConvertVec3d(ConverterTestCase):

    def test_convert_vec3d_basic(self):
        source = np.array([1.0, 2.0, 3.0])
        result = convert_vec3d(source)

        self.assertIsInstance(result, Gf.Vec3d)
        self.assertEqual(result, Gf.Vec3d(1.0, 2.0, 3.0))

    def test_convert_vec3d_negative_values(self):
        source = np.array([-1.5, -2.5, -3.5])
        result = convert_vec3d(source)

        self.assertEqual(result, Gf.Vec3d(-1.5, -2.5, -3.5))

    def test_convert_vec3d_zero_values(self):
        source = np.array([0.0, 0.0, 0.0])
        result = convert_vec3d(source)

        self.assertEqual(result, Gf.Vec3d(0.0, 0.0, 0.0))

    def test_convert_vec3d_integer_array(self):
        source = np.array([1, 2, 3])
        result = convert_vec3d(source)

        self.assertEqual(result, Gf.Vec3d(1.0, 2.0, 3.0))

    def test_convert_vec3d_wrong_shape(self):
        with self.assertRaises(AssertionError):
            convert_vec3d(np.array([1.0, 2.0]))  # Too few elements

        with self.assertRaises(AssertionError):
            convert_vec3d(np.array([1.0, 2.0, 3.0, 4.0]))  # Too many elements

        with self.assertRaises(AssertionError):
            convert_vec3d(np.array([[1.0, 2.0, 3.0]]))  # Wrong dimensions


class TestConvertVec3f(ConverterTestCase):

    def test_convert_vec3f_basic(self):
        source = np.array([1.0, 2.0, 3.0])
        result = convert_vec3f(source)

        self.assertIsInstance(result, Gf.Vec3f)
        self.assertEqual(result, Gf.Vec3f(1.0, 2.0, 3.0))

    def test_convert_vec3f_precision_loss(self):
        source = np.array([1.123456789, 2.987654321, 3.555555555])
        result = convert_vec3f(source)

        # Vec3f has single precision, so we check with lower precision
        expected = Gf.Vec3f(1.123456789, 2.987654321, 3.555555555)
        self.assertTrue(Gf.IsClose(result, expected, 1e-5))

    def test_convert_vec3f_integer_array(self):
        source = np.array([1, 2, 3])
        result = convert_vec3f(source)

        self.assertIsInstance(result, Gf.Vec3f)
        self.assertEqual(result, Gf.Vec3f(1.0, 2.0, 3.0))

    def test_convert_vec3f_wrong_shape(self):
        with self.assertRaises(AssertionError):
            convert_vec3f(np.array([1.0, 2.0]))  # Too few elements

        with self.assertRaises(AssertionError):
            convert_vec3f(np.array([1.0, 2.0, 3.0, 4.0]))  # Too many elements


class TestConvertQuatd(ConverterTestCase):

    def test_convert_quatd_basic(self):
        # Identity quaternion: w=1, x=0, y=0, z=0
        source = np.array([1.0, 0.0, 0.0, 0.0])
        result = convert_quatd(source)

        self.assertIsInstance(result, Gf.Quatd)
        self.assertEqual(result, Gf.Quatd(1.0, Gf.Vec3d(0.0, 0.0, 0.0)))

    def test_convert_quatd_rotation(self):
        # 90 degree rotation around Z-axis: w=0.707, x=0, y=0, z=0.707
        source = np.array([0.7071067811865476, 0.0, 0.0, 0.7071067811865476])
        result = convert_quatd(source)

        expected = Gf.Quatd(0.7071067811865476, Gf.Vec3d(0.0, 0.0, 0.7071067811865476))
        self.assertTrue(Gf.IsClose(result.GetReal(), expected.GetReal(), 1e-10))
        self.assertTrue(Gf.IsClose(result.GetImaginary(), expected.GetImaginary(), 1e-10))

    def test_convert_quatd_normalized(self):
        # Non-normalized input that should still work
        source = np.array([2.0, 0.0, 0.0, 0.0])
        result = convert_quatd(source)

        self.assertEqual(result, Gf.Quatd(2.0, Gf.Vec3d(0.0, 0.0, 0.0)))

    def test_convert_quatd_integer_array(self):
        source = np.array([1, 0, 0, 0])
        result = convert_quatd(source)
        self.assertIsInstance(result, Gf.Quatd)
        self.assertEqual(result, Gf.Quatd(1.0, Gf.Vec3d(0.0, 0.0, 0.0)))

    def test_convert_quatd_wrong_shape(self):
        with self.assertRaises(AssertionError):
            convert_quatd(np.array([1.0, 0.0, 0.0]))  # Too few elements

        with self.assertRaises(AssertionError):
            convert_quatd(np.array([1.0, 0.0, 0.0, 0.0, 0.0]))  # Too many elements


class TestConvertQuatf(ConverterTestCase):

    def test_convert_quatf_basic(self):
        # Identity quaternion: w=1, x=0, y=0, z=0
        source = np.array([1.0, 0.0, 0.0, 0.0])
        result = convert_quatf(source)

        self.assertIsInstance(result, Gf.Quatf)
        self.assertEqual(result, Gf.Quatf(1.0, Gf.Vec3f(0.0, 0.0, 0.0)))

    def test_convert_quatf_rotation(self):
        # 90 degree rotation around X-axis: w=0.707, x=0.707, y=0, z=0
        source = np.array([0.7071067811865476, 0.7071067811865476, 0.0, 0.0])
        result = convert_quatf(source)

        expected = Gf.Quatf(0.7071067811865476, Gf.Vec3f(0.7071067811865476, 0.0, 0.0))
        self.assertTrue(Gf.IsClose(result.GetReal(), expected.GetReal(), 1e-6))
        self.assertTrue(Gf.IsClose(result.GetImaginary(), expected.GetImaginary(), 1e-6))

    def test_convert_quatf_integer_array(self):
        source = np.array([1, 0, 0, 0])
        result = convert_quatf(source)

        self.assertIsInstance(result, Gf.Quatf)
        self.assertEqual(result, Gf.Quatf(1.0, Gf.Vec3f(0.0, 0.0, 0.0)))

    def test_convert_quatf_wrong_shape(self):
        with self.assertRaises(AssertionError):
            convert_quatf(np.array([1.0, 0.0, 0.0]))  # Too few elements

        with self.assertRaises(AssertionError):
            convert_quatf(np.array([1.0, 0.0, 0.0, 0.0, 0.0]))  # Too many elements


class TestConvertColor(ConverterTestCase):

    def test_convert_color_basic(self):
        source = np.array([0.5, 0.6, 0.7, 0.8])
        color, opacity = convert_color(source)

        self.assertIsInstance(color, Gf.Vec3f)
        self.assertIsInstance(opacity, float)

        self.assertEqual(color, Gf.Vec3f(0.5, 0.6, 0.7))
        self.assertAlmostEqual(opacity, 0.8, places=6)

    def test_convert_color_full_opacity(self):
        source = np.array([1.0, 0.0, 0.0, 1.0])  # Red with full opacity
        color, opacity = convert_color(source)

        self.assertEqual(color, Gf.Vec3f(1.0, 0.0, 0.0))
        self.assertAlmostEqual(opacity, 1.0, places=6)

    def test_convert_color_transparent(self):
        source = np.array([0.2, 0.4, 0.6, 0.0])  # Transparent
        color, opacity = convert_color(source)

        self.assertEqual(color, Gf.Vec3f(0.2, 0.4, 0.6))
        self.assertAlmostEqual(opacity, 0.0, places=6)

    def test_convert_color_out_of_range(self):
        source = np.array([-0.1, 1.5, 0.5, 2.0])
        color, opacity = convert_color(source)

        # The function doesn't clamp values, so they should be preserved
        self.assertEqual(color, Gf.Vec3f(-0.1, 1.5, 0.5))
        self.assertAlmostEqual(opacity, 2.0, places=6)

    def test_convert_color_integer_array(self):
        source = np.array([0, 1, 0, 1])  # Green with full opacity
        color, opacity = convert_color(source)

        self.assertIsInstance(color, Gf.Vec3f)
        self.assertIsInstance(opacity, float)
        self.assertEqual(color, Gf.Vec3f(0.0, 1.0, 0.0))
        self.assertAlmostEqual(opacity, 1.0, places=6)

    def test_convert_color_wrong_shape(self):
        with self.assertRaises(AssertionError):
            convert_color(np.array([1.0, 0.0, 0.0]))  # RGB without alpha

        with self.assertRaises(AssertionError):
            convert_color(np.array([1.0, 0.0, 0.0, 1.0, 0.5]))  # Too many elements


class TestConvertVec3fArray(ConverterTestCase):

    def test_convert_vec3f_array_single_vector(self):
        source = np.array([[1.0, 2.0, 3.0]])  # 1 element with 3 components
        result = convert_vec3f_array(source)

        self.assertIsInstance(result, Vt.Vec3fArray)
        self.assertEqual(len(result), 1)

        self.assertEqual(result[0], Gf.Vec3f(1.0, 2.0, 3.0))

    def test_convert_vec3f_array_multiple_vectors(self):
        source = np.array(
            [
                [1.0, 2.0, 3.0],
                [4.0, 5.0, 6.0],
                [7.0, 8.0, 9.0],
            ]
        )  # 3 elements with 3 components each
        result = convert_vec3f_array(source)

        self.assertEqual(len(result), 3)

        # Check vectors
        self.assertEqual(result[0], Gf.Vec3f(1.0, 2.0, 3.0))
        self.assertEqual(result[1], Gf.Vec3f(4.0, 5.0, 6.0))
        self.assertEqual(result[2], Gf.Vec3f(7.0, 8.0, 9.0))

    def test_convert_vec3f_array_multiple_vectors_per_element(self):
        source = np.array(
            [
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                [7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
            ]  # 2 vectors: [1,2,3] and [4,5,6]  # 2 vectors: [7,8,9] and [10,11,12]
        )  # 2 elements with 6 components each (2 vectors per element)
        result = convert_vec3f_array(source)

        self.assertEqual(len(result), 4)  # 2 elements * 2 vectors each = 4 vectors

        # Check vectors from both elements
        self.assertEqual(result[0], Gf.Vec3f(1.0, 2.0, 3.0))
        self.assertEqual(result[1], Gf.Vec3f(4.0, 5.0, 6.0))
        self.assertEqual(result[2], Gf.Vec3f(7.0, 8.0, 9.0))
        self.assertEqual(result[3], Gf.Vec3f(10.0, 11.0, 12.0))

    def test_convert_vec3f_array_empty(self):
        source = np.array([]).reshape(0, 3)  # 0 elements with 3 components each
        result = convert_vec3f_array(source)

        self.assertEqual(len(result), 0)

    def test_convert_vec3f_array_integer_array(self):
        source = np.array([[1, 2, 3], [4, 5, 6]])  # Integer input
        result = convert_vec3f_array(source)

        self.assertIsInstance(result, Vt.Vec3fArray)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], Gf.Vec3f(1.0, 2.0, 3.0))
        self.assertEqual(result[1], Gf.Vec3f(4.0, 5.0, 6.0))

    def test_convert_vec3f_array_wrong_shape(self):
        with self.assertRaises(AssertionError):
            # 4 components (not divisible by 3)
            convert_vec3f_array(np.array([[1.0, 2.0, 3.0, 4.0]]))

        with self.assertRaises(AssertionError):
            # 5 components (not divisible by 3)
            convert_vec3f_array(np.array([[1.0, 2.0, 3.0, 4.0, 5.0]]))

    def test_convert_vec3f_array_zero_components(self):
        source = np.array([]).reshape(2, 0)  # 2 elements with 0 components each
        result = convert_vec3f_array(source)
        self.assertEqual(len(result), 0)
