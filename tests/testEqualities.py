# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

from pxr import Sdf, Usd, UsdPhysics

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestEqualities(ConverterTestCase):

    def __has_authored_value(self, property: Usd.Property) -> bool:
        if hasattr(property, "HasAuthoredValue"):
            return property.HasAuthoredValue()
        else:
            return property.HasAuthoredTargets()

    def test_weld_equality_schema(self):
        # Test that weld equality attributes are authored correctly
        model = pathlib.Path("./tests/data/equality_weld_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Custom weld equality should have non-default values authored
        custom_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/custom_weld")
        self.assertTrue(custom_weld.IsValid())
        self.assertTrue(custom_weld.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsEqualityWeldAPI")))

        # Check that all possible MJC properties are authored, weld equalities don't use mjc:target
        not_authored_properties = [
            "mjc:target",
        ]
        for property in custom_weld.GetPropertiesInNamespace("mjc"):
            if property.GetName() in not_authored_properties:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")
            else:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")

        # Check solimp values
        expected_solimp = [0.8, 0.9, 0.002, 0.6, 3]
        actual_solimp = custom_weld.GetAttribute("mjc:solimp").Get()
        self.assertEqual(len(actual_solimp), len(expected_solimp))
        for i in range(5):
            self.assertAlmostEqual(actual_solimp[i], expected_solimp[i])

        # Check solref values
        expected_solref = [0.03, 0.8]
        actual_solref = custom_weld.GetAttribute("mjc:solref").Get()
        self.assertEqual(len(actual_solref), len(expected_solref))
        for i in range(2):
            self.assertAlmostEqual(actual_solref[i], expected_solref[i])

        # Check torqueScale
        self.assertAlmostEqual(custom_weld.GetAttribute("mjc:torqueScale").Get(), 2.5)

        # The weld prim itself is the fixed joint
        self.assertTrue(custom_weld.IsA(UsdPhysics.FixedJoint))
        weld_joint = UsdPhysics.FixedJoint(custom_weld)
        self.assertTrue(weld_joint)

        # Verify the joint connects the correct bodies
        body0_targets = weld_joint.GetBody0Rel().GetTargets()
        body1_targets = weld_joint.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertIn("body0", str(body0_targets[0]))
        self.assertIn("body1", str(body1_targets[0]))

        # Default weld equality should have default values that are NOT authored
        default_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/default_weld")
        self.assertTrue(default_weld.IsValid())
        self.assertTrue(default_weld.IsA(UsdPhysics.FixedJoint))
        self.assertTrue(default_weld.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsEqualityWeldAPI")))

        # Check that default MJC properties are NOT authored
        for property in default_weld.GetPropertiesInNamespace("mjc"):
            self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")

        # Verify the resolved values still match expected defaults
        expected_default_solimp = [0.9, 0.95, 0.001, 0.5, 2]
        actual_default_solimp = default_weld.GetAttribute("mjc:solimp").Get()
        self.assertEqual(len(actual_default_solimp), len(expected_default_solimp))
        for i in range(5):
            self.assertAlmostEqual(actual_default_solimp[i], expected_default_solimp[i])

        expected_default_solref = [0.02, 1]
        actual_default_solref = default_weld.GetAttribute("mjc:solref").Get()
        self.assertEqual(len(actual_default_solref), len(expected_default_solref))
        for i in range(2):
            self.assertAlmostEqual(actual_default_solref[i], expected_default_solref[i])

        self.assertAlmostEqual(default_weld.GetAttribute("mjc:torqueScale").Get(), 1.0)

        # Site-based weld equality should connect the parent bodies of the sites
        site_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/site_weld")
        self.assertTrue(site_weld.IsValid())
        self.assertTrue(site_weld.IsA(UsdPhysics.FixedJoint))
        self.assertTrue(site_weld.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsEqualityWeldAPI")))

        # Check that MJC properties are authored for site weld
        for property in site_weld.GetPropertiesInNamespace("mjc"):
            if property.GetName() in not_authored_properties:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")
            else:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")

        # Check solimp values
        expected_site_solimp = [0.75, 0.85, 0.004, 0.55, 2.5]
        actual_site_solimp = site_weld.GetAttribute("mjc:solimp").Get()
        self.assertEqual(len(actual_site_solimp), len(expected_site_solimp))
        for i in range(5):
            self.assertAlmostEqual(actual_site_solimp[i], expected_site_solimp[i])

        # Check solref values
        expected_site_solref = [0.025, 0.9]
        actual_site_solref = site_weld.GetAttribute("mjc:solref").Get()
        self.assertEqual(len(actual_site_solref), len(expected_site_solref))
        for i in range(2):
            self.assertAlmostEqual(actual_site_solref[i], expected_site_solref[i])

        # Check torqueScale
        self.assertAlmostEqual(site_weld.GetAttribute("mjc:torqueScale").Get(), 1.5)

        # Verify the joint connects the parent bodies of the sites (body4 and body5)
        site_weld_joint = UsdPhysics.FixedJoint(site_weld)
        body0_targets = site_weld_joint.GetBody0Rel().GetTargets()
        body1_targets = site_weld_joint.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertIn("body4", str(body0_targets[0]))
        self.assertIn("body5", str(body1_targets[0]))

    def test_weld_missing_body2(self):
        # When a weld equality has no body2 (name2), MuJoCo uses worldbody; in USD, body1 is the default prim
        model = pathlib.Path("./tests/data/equality_weld_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        weld_to_world: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/weld_to_world")
        self.assertTrue(weld_to_world.IsValid())
        self.assertTrue(weld_to_world.IsA(UsdPhysics.FixedJoint))
        self.assertTrue(weld_to_world.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsEqualityWeldAPI")))

        weld_joint = UsdPhysics.FixedJoint(weld_to_world)
        body0_targets = weld_joint.GetBody0Rel().GetTargets()
        body1_targets = weld_joint.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        # First body is the specified body (body0)
        self.assertIn("body0", str(body0_targets[0]))
        # Second body is world → in USD the default prim
        default_prim = stage.GetDefaultPrim()
        self.assertTrue(default_prim.IsValid())
        self.assertEqual(body1_targets[0], default_prim.GetPath())

    def test_weld_equality_joint_enabled(self):
        # XML active="true" (default) → joint enabled, attr should not be authored when default
        # XML active="false" → joint disabled, physics:jointEnabled must be authored and false
        model = pathlib.Path("./tests/data/equality_weld_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Enabled weld (default): resolved value True, attr should not be authored
        default_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/default_weld")
        self.assertTrue(default_weld.IsValid())
        default_joint = UsdPhysics.FixedJoint(default_weld)
        joint_enabled_attr = default_joint.GetJointEnabledAttr()
        self.assertTrue(joint_enabled_attr.Get(), "Default weld should be enabled")
        self.assertFalse(
            self.__has_authored_value(joint_enabled_attr),
            "physics:jointEnabled should not be authored when it is the default (true)",
        )

        # Disabled weld: attr must be authored and false
        disabled_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/disabled_weld")
        self.assertTrue(disabled_weld.IsValid())
        disabled_joint = UsdPhysics.FixedJoint(disabled_weld)
        disabled_joint_enabled_attr = disabled_joint.GetJointEnabledAttr()
        self.assertTrue(
            self.__has_authored_value(disabled_joint_enabled_attr),
            "physics:jointEnabled should be authored when equality is inactive",
        )
        self.assertFalse(disabled_joint_enabled_attr.Get(), "Disabled weld should have jointEnabled false")

    def test_joint_equality_joint_enabled(self):
        # XML active="true" (default) → joint enabled, attr should not be authored when default
        # XML active="false" → joint disabled, physics:jointEnabled must be authored and false
        model = pathlib.Path("./tests/data/equality_joint_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Enabled joint equality (default): resolved value True, attr should not be authored
        default_joint_prim: Usd.Prim = stage.GetPrimAtPath("/equality_joint_attributes/Geometry/body2/slide0")
        self.assertTrue(default_joint_prim.IsValid())
        default_joint = UsdPhysics.PrismaticJoint(default_joint_prim)
        joint_enabled_attr = default_joint.GetJointEnabledAttr()
        self.assertTrue(joint_enabled_attr.Get(), "Default joint equality should be enabled")
        self.assertFalse(
            self.__has_authored_value(joint_enabled_attr),
            "physics:jointEnabled should not be authored when it is the default (true)",
        )

        # Disabled joint equality: attr must be authored and false (hinge2 has disabled_joint_eq)
        disabled_joint_prim: Usd.Prim = stage.GetPrimAtPath("/equality_joint_attributes/Geometry/body4/hinge2")
        self.assertTrue(disabled_joint_prim.IsValid())
        disabled_joint = UsdPhysics.RevoluteJoint(disabled_joint_prim)
        disabled_joint_enabled_attr = disabled_joint.GetJointEnabledAttr()
        self.assertTrue(
            self.__has_authored_value(disabled_joint_enabled_attr),
            "physics:jointEnabled should be authored when joint equality is inactive",
        )
        self.assertFalse(disabled_joint_enabled_attr.Get(), "Disabled joint equality should have jointEnabled false")

    def test_joint_equality_schema(self):
        # Test that joint equality attributes are authored correctly
        model = pathlib.Path("./tests/data/equality_joint_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Custom joint equality - API applied to the constrained joint (hinge0)
        custom_joint: Usd.Prim = stage.GetPrimAtPath("/equality_joint_attributes/Geometry/body0/hinge0")
        self.assertTrue(custom_joint.IsValid())
        self.assertTrue(custom_joint.IsA(UsdPhysics.RevoluteJoint))
        self.assertTrue(custom_joint.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsEqualityJointAPI")))

        # Check that all MJC equality properties are authored for custom joint
        equality_properties = ["mjc:solimp", "mjc:solref", "mjc:coef0", "mjc:coef1", "mjc:coef2", "mjc:coef3", "mjc:coef4", "mjc:target"]
        for prop_name in equality_properties:
            prop = custom_joint.GetProperty(prop_name)
            self.assertTrue(self.__has_authored_value(prop), f"Property {prop_name} is not authored")

        # Check solimp values
        expected_solimp = [0.85, 0.92, 0.003, 0.7, 4]
        actual_solimp = custom_joint.GetAttribute("mjc:solimp").Get()
        self.assertEqual(len(actual_solimp), len(expected_solimp))
        for i in range(5):
            self.assertAlmostEqual(actual_solimp[i], expected_solimp[i])

        # Check solref values
        expected_solref = [0.01, 0.6]
        actual_solref = custom_joint.GetAttribute("mjc:solref").Get()
        self.assertEqual(len(actual_solref), len(expected_solref))
        for i in range(2):
            self.assertAlmostEqual(actual_solref[i], expected_solref[i])

        # Check polynomial coefficients (polycoef="0.5 1.5 0.1 0.05 0.02")
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:coef0").Get(), 0.5)
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:coef1").Get(), 1.5)
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:coef2").Get(), 0.1)
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:coef3").Get(), 0.05)
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:coef4").Get(), 0.02)

        # Check that the target relationship points to hinge1
        target_rel = custom_joint.GetRelationship("mjc:target")
        targets = target_rel.GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertIn("hinge1", str(targets[0]))

        # Default joint equality - API applied to the constrained joint (slide0)
        default_joint: Usd.Prim = stage.GetPrimAtPath("/equality_joint_attributes/Geometry/body2/slide0")
        self.assertTrue(default_joint.IsValid())
        self.assertTrue(default_joint.IsA(UsdPhysics.PrismaticJoint))
        self.assertTrue(default_joint.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsEqualityJointAPI")))

        # Check that only the target relationship is authored (required), default values are NOT authored
        authored_properties = ["mjc:target"]
        for property in default_joint.GetPropertiesInNamespace("mjc"):
            if property.GetName() in authored_properties:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")
            else:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")

        # Verify the resolved values still match expected defaults
        expected_default_solimp = [0.9, 0.95, 0.001, 0.5, 2]
        actual_default_solimp = default_joint.GetAttribute("mjc:solimp").Get()
        self.assertEqual(len(actual_default_solimp), len(expected_default_solimp))
        for i in range(5):
            self.assertAlmostEqual(actual_default_solimp[i], expected_default_solimp[i])

        expected_default_solref = [0.02, 1]
        actual_default_solref = default_joint.GetAttribute("mjc:solref").Get()
        self.assertEqual(len(actual_default_solref), len(expected_default_solref))
        for i in range(2):
            self.assertAlmostEqual(actual_default_solref[i], expected_default_solref[i])

        # Check default polynomial coefficients (polycoef="0 1 0 0 0")
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:coef0").Get(), 0.0)
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:coef1").Get(), 1.0)
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:coef2").Get(), 0.0)
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:coef3").Get(), 0.0)
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:coef4").Get(), 0.0)

        # Check that the target relationship points to slide1
        target_rel = default_joint.GetRelationship("mjc:target")
        targets = target_rel.GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertIn("slide1", str(targets[0]))
