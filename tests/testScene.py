# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib

from pxr import Gf, Sdf, Usd, UsdPhysics

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestScene(ConverterTestCase):

    def test_gravity(self):
        model = pathlib.Path("./tests/data/scene_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        scene: UsdPhysics.Scene = UsdPhysics.Scene(stage.GetPseudoRoot().GetChild("PhysicsScene"))
        self.assertTrue(scene)

        self.assertEqual(scene.GetGravityDirectionAttr().Get(), Gf.Vec3f(0, 0, -1))
        self.assertEqual(scene.GetGravityMagnitudeAttr().Get(), 5)

    def test_scene_attributes_non_default(self):
        # Test with non-default scene options and flags
        model = pathlib.Path("./tests/data/scene_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        scene: Usd.Prim = stage.GetPseudoRoot().GetChild("PhysicsScene")
        self.assertTrue(scene.IsA(UsdPhysics.Scene))
        self.assertTrue(scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(scene.HasAPI("MjcSceneAPI"))

        # Check that Newton scene attributes are authored as expected
        self.assertTrue(scene.GetAttribute("newton:maxSolverIterations").HasAuthoredValue())
        self.assertEqual(scene.GetAttribute("newton:maxSolverIterations").Get(), 200)
        self.assertTrue(scene.GetAttribute("newton:timeStepsPerSecond").HasAuthoredValue())
        self.assertEqual(scene.GetAttribute("newton:timeStepsPerSecond").Get(), 100)
        self.assertTrue(scene.GetAttribute("newton:gravityEnabled").HasAuthoredValue())
        self.assertEqual(scene.GetAttribute("newton:gravityEnabled").Get(), False)

        # Check that all MJC properties are authored
        for property in scene.GetPropertiesInNamespace("mjc"):
            self.assertTrue(property.HasAuthoredValue(), f"Property {property.GetName()} is not authored")

        # Test all flag attributes have been authored and have expected values
        # Disable flags (defaults to enabled=1, we set them to disabled=0)
        flag_attrs = [
            "mjc:flag:actuation",
            "mjc:flag:autoreset",
            "mjc:flag:clampctrl",
            "mjc:flag:constraint",
            "mjc:flag:contact",
            "mjc:flag:damper",
            "mjc:flag:equality",
            "mjc:flag:eulerdamp",
            "mjc:flag:filterparent",
            "mjc:flag:frictionloss",
            "mjc:flag:gravity",
            "mjc:flag:island",
            "mjc:flag:limit",
            "mjc:flag:midphase",
            "mjc:flag:nativeccd",
            "mjc:flag:refsafe",
            "mjc:flag:sensor",
            "mjc:flag:spring",
            "mjc:flag:warmstart",
        ]

        for attr_name in flag_attrs:
            attr: Usd.Attribute = scene.GetAttribute(attr_name)
            self.assertEqual(attr.Get(), False, f"Attribute {attr_name} should be False")

        # Enable flags (defaults to disabled=0, we set them to enabled=1)
        enable_flag_attrs = [
            "mjc:flag:energy",
            "mjc:flag:fwdinv",
            "mjc:flag:invdiscrete",
            "mjc:flag:multiccd",
            "mjc:flag:override",
        ]

        for attr_name in enable_flag_attrs:
            attr = scene.GetAttribute(attr_name)
            self.assertEqual(attr.Get(), True, f"Attribute {attr_name} should be True")

        self.assertEqual(list(scene.GetAttribute("mjc:option:actuatorgroupdisable").Get()), [1, 3, 5])

        self.assertEqual(scene.GetAttribute("mjc:option:ccd_iterations").Get(), 100)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:ccd_tolerance").Get(), 0.00001)
        self.assertEqual(scene.GetAttribute("mjc:option:cone").Get(), "elliptic")
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:density").Get(), 1.5)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:impratio").Get(), 0.5)
        self.assertEqual(scene.GetAttribute("mjc:option:integrator").Get(), "rk4")
        self.assertEqual(scene.GetAttribute("mjc:option:jacobian").Get(), "sparse")
        self.assertEqual(scene.GetAttribute("mjc:option:iterations").Get(), 200)
        self.assertEqual(scene.GetAttribute("mjc:option:ls_iterations").Get(), 100)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:ls_tolerance").Get(), 0.02)
        self.assertTrue(Gf.IsClose(scene.GetAttribute("mjc:option:magnetic").Get(), Gf.Vec3d(0.1, 0.2, 0.3), 1e-6))
        self.assertEqual(scene.GetAttribute("mjc:option:noslip_iterations").Get(), 10)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:noslip_tolerance").Get(), 0.00001)
        self.assertAlmostEqual(list(scene.GetAttribute("mjc:option:o_friction").Get()), [0.8, 0.8, 0.01, 0.0002, 0.0002])
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:o_margin").Get(), 0.001)
        self.assertAlmostEqual(list(scene.GetAttribute("mjc:option:o_solimp").Get()), [0.7, 0.8, 0.002, 0.3, 1])
        self.assertAlmostEqual(list(scene.GetAttribute("mjc:option:o_solref").Get()), [0.01, 0.8])
        self.assertEqual(scene.GetAttribute("mjc:option:sdf_initpoints").Get(), 60)
        self.assertEqual(scene.GetAttribute("mjc:option:sdf_iterations").Get(), 20)
        self.assertEqual(scene.GetAttribute("mjc:option:solver").Get(), "cg")
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:timestep").Get(), 0.01)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:tolerance").Get(), 1e-6)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:viscosity").Get(), 0.1)
        self.assertTrue(Gf.IsClose(scene.GetAttribute("mjc:option:wind").Get(), Gf.Vec3d(1, 2, 3), 1e-6))

        # Test compiler attributes
        self.assertEqual(scene.GetAttribute("mjc:compiler:alignFree").Get(), True)
        self.assertEqual(scene.GetAttribute("mjc:compiler:angle").Get(), "radian")
        self.assertEqual(scene.GetAttribute("mjc:compiler:autoLimits").Get(), False)
        self.assertEqual(scene.GetAttribute("mjc:compiler:balanceInertia").Get(), True)
        self.assertAlmostEqual(scene.GetAttribute("mjc:compiler:boundInertia").Get(), 0.1)
        self.assertAlmostEqual(scene.GetAttribute("mjc:compiler:boundMass").Get(), 0.05)
        self.assertEqual(scene.GetAttribute("mjc:compiler:fitAABB").Get(), True)
        self.assertEqual(scene.GetAttribute("mjc:compiler:fuseStatic").Get(), True)
        self.assertEqual(scene.GetAttribute("mjc:compiler:inertiaFromGeom").Get(), "true")
        self.assertEqual(scene.GetAttribute("mjc:compiler:inertiaGroupRange:max").Get(), 3)
        self.assertEqual(scene.GetAttribute("mjc:compiler:inertiaGroupRange:min").Get(), 1)
        self.assertEqual(scene.GetAttribute("mjc:compiler:saveInertial").Get(), True)
        self.assertAlmostEqual(scene.GetAttribute("mjc:compiler:setTotalMass").Get(), 10.5)
        self.assertEqual(scene.GetAttribute("mjc:compiler:useThread").Get(), False)

    def test_scene_default_values(self):
        model = pathlib.Path("./tests/data/bodies.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        scene: Usd.Prim = stage.GetPseudoRoot().GetChild("PhysicsScene")
        self.assertTrue(scene.IsA(UsdPhysics.Scene))
        self.assertTrue(scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(scene.HasAPI("MjcSceneAPI"))

        # Newton scene attributes are authored as expected
        self.assertTrue(scene.GetAttribute("newton:maxSolverIterations").HasAuthoredValue())
        self.assertEqual(scene.GetAttribute("newton:maxSolverIterations").Get(), 100)
        self.assertTrue(scene.GetAttribute("newton:timeStepsPerSecond").HasAuthoredValue())
        self.assertEqual(scene.GetAttribute("newton:timeStepsPerSecond").Get(), 500)
        self.assertFalse(scene.GetAttribute("newton:gravityEnabled").HasAuthoredValue())
        self.assertEqual(scene.GetAttribute("newton:gravityEnabled").Get(), True)

        physics_scene: UsdPhysics.Scene = UsdPhysics.Scene(scene)
        # authored because this is a Z-up scene & the USD default is Y-up
        self.assertTrue(physics_scene.GetGravityDirectionAttr().HasAuthoredValue())
        self.assertEqual(physics_scene.GetGravityDirectionAttr().Get(), Gf.Vec3f(0, 0, -1))
        self.assertTrue(physics_scene.GetGravityMagnitudeAttr().HasAuthoredValue())
        self.assertAlmostEqual(physics_scene.GetGravityMagnitudeAttr().Get(), 9.81, 5)

        # Check that only MJC properties without a default value are authored
        for property in scene.GetPropertiesInNamespace("mjc"):
            self.assertFalse(property.HasAuthoredValue(), f"Property {property.GetName()} should not be authored")

        # Test that default values are not authored but still available via schema defaults
        # Most flag attributes should not be authored since they match schema defaults
        default_enabled_flags = [
            "mjc:flag:actuation",
            "mjc:flag:autoreset",
            "mjc:flag:clampctrl",
            "mjc:flag:constraint",
            "mjc:flag:contact",
            "mjc:flag:damper",
            "mjc:flag:equality",
            "mjc:flag:eulerdamp",
            "mjc:flag:filterparent",
            "mjc:flag:frictionloss",
            "mjc:flag:gravity",
            "mjc:flag:island",
            "mjc:flag:limit",
            "mjc:flag:midphase",
            "mjc:flag:nativeccd",
            "mjc:flag:refsafe",
            "mjc:flag:sensor",
            "mjc:flag:spring",
            "mjc:flag:warmstart",
        ]

        for attr_name in default_enabled_flags:
            attr: Usd.Attribute = scene.GetAttribute(attr_name)
            self.assertEqual(attr.Get(), True, f"Default attribute {attr_name} should still return True via schema default")

        default_disabled_flags = [
            "mjc:flag:energy",
            "mjc:flag:fwdinv",
            "mjc:flag:invdiscrete",
            "mjc:flag:multiccd",
            "mjc:flag:override",
        ]

        for attr_name in default_disabled_flags:
            attr: Usd.Attribute = scene.GetAttribute(attr_name)
            self.assertEqual(attr.Get(), False, f"Default attribute {attr_name} should still return False via schema default")

        # Test that default values are accessible via schema defaults
        self.assertEqual(list(scene.GetAttribute("mjc:option:actuatorgroupdisable").Get()), [])
        self.assertEqual(scene.GetAttribute("mjc:option:ccd_iterations").Get(), 35)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:ccd_tolerance").Get(), 0.000001)
        self.assertEqual(scene.GetAttribute("mjc:option:cone").Get(), "pyramidal")
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:density").Get(), 0)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:impratio").Get(), 1)
        self.assertEqual(scene.GetAttribute("mjc:option:integrator").Get(), "euler")
        self.assertEqual(scene.GetAttribute("mjc:option:iterations").Get(), 100)
        self.assertEqual(scene.GetAttribute("mjc:option:jacobian").Get(), "auto")
        self.assertEqual(scene.GetAttribute("mjc:option:ls_iterations").Get(), 50)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:ls_tolerance").Get(), 0.01)
        self.assertTrue(Gf.IsClose(scene.GetAttribute("mjc:option:magnetic").Get(), Gf.Vec3d(0, -0.5, 0), 1e-6))
        self.assertEqual(scene.GetAttribute("mjc:option:noslip_iterations").Get(), 0)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:noslip_tolerance").Get(), 0.000001)
        self.assertAlmostEqual(list(scene.GetAttribute("mjc:option:o_friction").Get()), [1, 1, 0.005, 0.0001, 0.0001])
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:o_margin").Get(), 0)
        self.assertAlmostEqual(list(scene.GetAttribute("mjc:option:o_solimp").Get()), [0.9, 0.95, 0.001, 0.5, 2])
        self.assertAlmostEqual(list(scene.GetAttribute("mjc:option:o_solref").Get()), [0.02, 1])
        self.assertEqual(scene.GetAttribute("mjc:option:sdf_initpoints").Get(), 40)
        self.assertEqual(scene.GetAttribute("mjc:option:sdf_iterations").Get(), 10)
        self.assertEqual(scene.GetAttribute("mjc:option:solver").Get(), "newton")
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:timestep").Get(), 0.002)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:tolerance").Get(), 1e-8)
        self.assertAlmostEqual(scene.GetAttribute("mjc:option:viscosity").Get(), 0)
        self.assertTrue(Gf.IsClose(scene.GetAttribute("mjc:option:wind").Get(), Gf.Vec3d(0, 0, 0), 1e-6))

        # Test that default compiler values are accessible via schema defaults
        self.assertEqual(scene.GetAttribute("mjc:compiler:alignFree").Get(), False)
        self.assertEqual(scene.GetAttribute("mjc:compiler:angle").Get(), "degree")
        self.assertEqual(scene.GetAttribute("mjc:compiler:autoLimits").Get(), True)
        self.assertEqual(scene.GetAttribute("mjc:compiler:balanceInertia").Get(), False)
        self.assertAlmostEqual(scene.GetAttribute("mjc:compiler:boundInertia").Get(), 0)
        self.assertAlmostEqual(scene.GetAttribute("mjc:compiler:boundMass").Get(), 0)
        self.assertEqual(scene.GetAttribute("mjc:compiler:fitAABB").Get(), False)
        self.assertEqual(scene.GetAttribute("mjc:compiler:fuseStatic").Get(), False)
        self.assertEqual(scene.GetAttribute("mjc:compiler:inertiaFromGeom").Get(), "auto")
        self.assertEqual(scene.GetAttribute("mjc:compiler:inertiaGroupRange:max").Get(), 5)
        self.assertEqual(scene.GetAttribute("mjc:compiler:inertiaGroupRange:min").Get(), 0)
        self.assertEqual(scene.GetAttribute("mjc:compiler:saveInertial").Get(), False)
        self.assertAlmostEqual(scene.GetAttribute("mjc:compiler:setTotalMass").Get(), -1)
        self.assertEqual(scene.GetAttribute("mjc:compiler:useThread").Get(), True)

    def test_scene_disabled(self):
        model = pathlib.Path("./tests/data/scene_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter(scene=False).convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        scene: Usd.Prim = stage.GetPseudoRoot().GetChild("PhysicsScene")
        self.assertFalse(scene.IsValid())
