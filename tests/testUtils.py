# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import unittest

from pxr import Tf, Usd

from mujoco_usd_converter.utils import set_schema_attribute


class TestSetSchemaAttribute(unittest.TestCase):

    def test_set_unique_value(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI(Usd.SchemaRegistry.GetAPISchemaTypeName("MjcPhysicsJointAPI"))

        # Setting a valid attribute with a non-default value should author the value
        set_schema_attribute(prim, "mjc:armature", 0.5)
        self.assertTrue(prim.GetAttribute("mjc:armature").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:armature").Get(), 0.5)

    def test_set_default_value(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI(Usd.SchemaRegistry.GetAPISchemaTypeName("MjcPhysicsJointAPI"))

        set_schema_attribute(prim, "mjc:armature", 0)  # Default value is 0
        self.assertFalse(prim.GetAttribute("mjc:armature").HasAuthoredValue())  # Should not be authored
        self.assertEqual(prim.GetAttribute("mjc:armature").Get(), 0)  # But should still return default value

    def test_invalid_schema(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        self.assertFalse(prim.HasAPI(Usd.SchemaRegistry.GetAPISchemaTypeName("MjcPhysicsJointAPI")))

        with self.assertRaises(Tf.ErrorException, msg="Attribute mjc:armature is not valid for prim /TestPrim with schemas []"):
            set_schema_attribute(prim, "mjc:armature", 0.5)

    def test_invalid_attribute(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI(Usd.SchemaRegistry.GetAPISchemaTypeName("MjcPhysicsJointAPI"))

        # Setting an invalid attribute should raise a coding error
        with self.assertRaises(Tf.ErrorException):
            set_schema_attribute(prim, "mjc:invalid_attribute", 123)

    def test_invalid_value(self):
        stage: Usd.Stage = Usd.Stage.CreateInMemory()
        prim: Usd.Prim = stage.DefinePrim("/TestPrim")
        prim.ApplyAPI(Usd.SchemaRegistry.GetAPISchemaTypeName("MjcPhysicsJointAPI"))

        with self.assertRaises(Tf.ErrorException):
            set_schema_attribute(prim, "mjc:armature", "wrong type")
