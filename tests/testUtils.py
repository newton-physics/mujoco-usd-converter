# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import mujoco
import numpy as np
from pxr import Gf, Tf, Usd, UsdGeom

from mujoco_usd_converter._impl.utils import set_schema_attribute, set_transform
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

    def test_small_rotation_is_preserved(self):
        # A 1e-4 rad rotation is representable as a Quatf, but its real component rounds to 1 in float precision
        angle = 1e-4
        quat = [np.cos(angle / 2), 0, 0, np.sin(angle / 2)]
        for orientation in ("body", "frame", "fromto"):
            with self.subTest(orientation=orientation):
                spec = mujoco.MjSpec()
                if orientation == "body":
                    mjc_object = spec.worldbody.add_body(quat=quat)
                elif orientation == "frame":
                    mjc_object = spec.worldbody.add_frame(quat=quat).add_body()
                else:
                    # a capsule along +z tilted by angle about the x axis
                    mjc_object = spec.worldbody.add_geom(
                        type=mujoco.mjtGeom.mjGEOM_CAPSULE, size=[0.01, 0, 0], fromto=[0, 0, 0, 0, -np.sin(angle), np.cos(angle)]
                    )
                stage = Usd.Stage.CreateInMemory()
                prim = UsdGeom.Xform.Define(stage, "/Prim")
                set_transform(prim, mjc_object, spec)
                orient = prim.GetPrim().GetAttribute("xformOp:orient").Get()
                self.assertIsInstance(orient, Gf.Quatf)
                # measure the angle with atan2, since acos of the float real component cannot resolve it
                authored_angle = 2 * np.arctan2(orient.GetImaginary().GetLength(), orient.GetReal())
                self.assertAlmostEqual(authored_angle, angle, delta=1e-9)
