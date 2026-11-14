# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import math
import pathlib

import usdex.core
from pxr import Gf, Sdf, Tf, Usd

import mujoco_usd_converter
from mujoco_usd_converter._impl.utils import set_schema_attribute
from tests.util.ConverterTestCase import ConverterTestCase


class TestSetSchemaAttribute(ConverterTestCase):

    def test_set_unique_value(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI("MjcJointAPI")

        # Setting a valid attribute with a non-default value should author the value
        set_schema_attribute(prim, "mjc:armature", 0.5)
        self.assertTrue(prim.GetAttribute("mjc:armature").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:armature").Get(), 0.5)

    def test_set_default_value(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI("MjcJointAPI")

        set_schema_attribute(prim, "mjc:armature", 0)  # Default value is 0
        self.assertFalse(prim.GetAttribute("mjc:armature").HasAuthoredValue())  # Should not be authored
        self.assertEqual(prim.GetAttribute("mjc:armature").Get(), 0)  # But should still return default value

    def test_invalid_schema(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        self.assertFalse(prim.HasAPI("MjcJointAPI"))

        with self.assertRaises(Tf.ErrorException, msg="Attribute mjc:armature is not valid for prim /TestPrim with schemas []"):
            set_schema_attribute(prim, "mjc:armature", 0.5)

    def test_invalid_attribute(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI("MjcJointAPI")

        # Setting an invalid attribute should raise a coding error
        with self.assertRaises(Tf.ErrorException):
            set_schema_attribute(prim, "mjc:invalid_attribute", 123)

    def test_invalid_value(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI("MjcJointAPI")

        with self.assertRaises(Tf.ErrorException):
            set_schema_attribute(prim, "mjc:armature", "wrong type")


class TestSetTransform(ConverterTestCase):

    def test_small_rotations_are_preserved(self):
        # a 1e-4 rad rotation is representable as a Quatf, but its real component rounds to 1 in single precision
        model = pathlib.Path("./tests/data/small_rotations.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        expected = {
            "quatBody": Gf.Quatd(1, 0, 0, 0.00005).GetNormalized(),
            "framedBody": Gf.Quatd(1, 0, 0, 0.00005).GetNormalized(),
            "fromtoBody/fromtoGeom": Gf.Rotation(Gf.Vec3d.XAxis(), math.degrees(math.atan(0.0001))).GetQuat(),
        }
        for name, quat in expected.items():
            with self.subTest(prim=name):
                prim = stage.GetPrimAtPath(f"/small_rotations/Geometry/{name}")
                _, _, orient, _ = usdex.core.getLocalTransformComponentsQuat(prim)
                self.assertRotationsAlmostEqual(orient, Gf.Quatf(quat), 1e-9)
