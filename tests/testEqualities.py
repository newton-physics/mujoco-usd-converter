# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import usdex.test
from pxr import Gf, Sdf, Tf, Usd, UsdPhysics

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
        custom_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/tn__customweld_aF")
        self.assertTrue(custom_weld.IsValid())
        self.assertTrue(custom_weld.HasAPI("MjcEqualityWeldAPI"))

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
        self.assertEqual("/equality_weld_attributes/Geometry/body0", str(body0_targets[0]))
        self.assertEqual("/equality_weld_attributes/Geometry/body1", str(body1_targets[0]))

        # Default weld equality should have default values that are NOT authored
        default_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/default_weld")
        self.assertTrue(default_weld.IsValid())
        self.assertTrue(default_weld.IsA(UsdPhysics.FixedJoint))
        self.assertTrue(default_weld.HasAPI("MjcEqualityWeldAPI"))

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
        self.assertTrue(site_weld.HasAPI("MjcEqualityWeldAPI"))

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
        self.assertEqual("/equality_weld_attributes/Geometry/body4/site4", str(body0_targets[0]))
        self.assertEqual("/equality_weld_attributes/Geometry/body5/site5", str(body1_targets[0]))
        self.assertTrue(site_weld_joint.GetExcludeFromArticulationAttr().Get())

    def test_weld_missing_body2(self):
        # When a weld equality has no body2 (name2), MuJoCo uses worldbody; in USD, body1 is the default prim
        model = pathlib.Path("./tests/data/equality_weld_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        weld_to_world: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/weld_to_world")
        self.assertTrue(weld_to_world.IsValid())
        self.assertTrue(weld_to_world.IsA(UsdPhysics.FixedJoint))
        self.assertTrue(weld_to_world.HasAPI("MjcEqualityWeldAPI"))

        weld_joint = UsdPhysics.FixedJoint(weld_to_world)
        body0_targets = weld_joint.GetBody0Rel().GetTargets()
        body1_targets = weld_joint.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        # First body is the specified body (body0)
        self.assertEqual("/equality_weld_attributes/Geometry/body0", str(body0_targets[0]))
        # Second body is world - in USD the default prim
        default_prim = stage.GetDefaultPrim()
        self.assertTrue(default_prim.IsValid())
        self.assertEqual(body1_targets[0], default_prim.GetPath())

    def test_weld_equality_joint_enabled(self):
        # XML active="true" (default) - joint enabled, attr should not be authored when default
        # XML active="false" - joint disabled, physics:jointEnabled must be authored and false
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

        # Disabled weld: attr must be authored and false (also autonamed to Equality)
        disabled_weld: Usd.Prim = stage.GetPrimAtPath("/equality_weld_attributes/Physics/Equality")
        self.assertTrue(disabled_weld.IsValid())
        disabled_joint = UsdPhysics.FixedJoint(disabled_weld)
        disabled_joint_enabled_attr = disabled_joint.GetJointEnabledAttr()
        self.assertTrue(
            self.__has_authored_value(disabled_joint_enabled_attr),
            "physics:jointEnabled should be authored when equality is inactive",
        )
        self.assertFalse(disabled_joint_enabled_attr.Get(), "Disabled weld should have jointEnabled false")

    def test_weld_with_sites(self):
        # Verify that weld equalities with sites are converted correctly
        model = pathlib.Path("./tests/data/equality_weld_with_sites.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        weld_sites: Usd.Prim = stage.GetPrimAtPath("/equality_weld_with_sites/Physics/sites")
        self.assertTrue(weld_sites.IsValid())
        joint_weld_sites = UsdPhysics.FixedJoint(weld_sites)
        body0_targets = joint_weld_sites.GetBody0Rel().GetTargets()
        body1_targets = joint_weld_sites.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_weld_with_sites/Geometry/box1/box1_site", str(body0_targets[0]))
        self.assertEqual("/equality_weld_with_sites/Geometry/box2/box2_site", str(body1_targets[0]))
        self.assertTrue(Gf.IsClose(joint_weld_sites.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_weld_sites.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_weld_sites.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_weld_sites.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertTrue(joint_weld_sites.GetJointEnabledAttr().Get())

        weld_sites_separated: Usd.Prim = stage.GetPrimAtPath("/equality_weld_with_sites/Physics/sites_separated")
        self.assertTrue(weld_sites_separated.IsValid())
        joint_weld_sites_separated = UsdPhysics.FixedJoint(weld_sites_separated)
        body0_targets = joint_weld_sites_separated.GetBody0Rel().GetTargets()
        body1_targets = joint_weld_sites_separated.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_weld_with_sites/Geometry/box3/box3_site", str(body0_targets[0]))
        self.assertEqual("/equality_weld_with_sites/Geometry/box4/box4_site", str(body1_targets[0]))
        self.assertTrue(Gf.IsClose(joint_weld_sites_separated.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_weld_sites_separated.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_weld_sites_separated.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_weld_sites_separated.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertTrue(joint_weld_sites_separated.GetJointEnabledAttr().Get())

    def test_joint_equality_joint_enabled(self):
        # XML active="true" (default) - joint enabled, attr should not be authored when default
        # XML active="false" - joint disabled, physics:jointEnabled must be authored and false
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

        self.assertTrue(default_joint_prim.HasAPI("NewtonMimicAPI"))
        self.assertTrue(default_joint_prim.GetAttribute("newton:mimicEnabled").Get())

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

        self.assertTrue(disabled_joint_prim.HasAPI("NewtonMimicAPI"))
        self.assertFalse(disabled_joint_prim.GetAttribute("newton:mimicEnabled").Get())

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
        self.assertTrue(custom_joint.HasAPI("MjcEqualityJointAPI"))

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
        targets = custom_joint.GetRelationship("mjc:target").GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual("/equality_joint_attributes/Geometry/body0/body1/hinge1", str(targets[0]))

        # Check NewtonMimicAPI attributes
        self.assertTrue(custom_joint.HasAPI("NewtonMimicAPI"))
        self.assertAlmostEqual(custom_joint.GetAttribute("newton:mimicCoef0").Get(), 0.5)
        self.assertAlmostEqual(custom_joint.GetAttribute("newton:mimicCoef1").Get(), 1.5)
        targets = custom_joint.GetRelationship("newton:mimicJoint").GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual("/equality_joint_attributes/Geometry/body0/body1/hinge1", str(targets[0]))
        self.assertTrue(custom_joint.GetAttribute("newton:mimicEnabled").Get())

        # Default joint equality - API applied to the constrained joint (slide0)
        default_joint: Usd.Prim = stage.GetPrimAtPath("/equality_joint_attributes/Geometry/body2/slide0")
        self.assertTrue(default_joint.IsValid())
        self.assertTrue(default_joint.IsA(UsdPhysics.PrismaticJoint))
        self.assertTrue(default_joint.HasAPI("MjcEqualityJointAPI"))

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
        targets = default_joint.GetRelationship("mjc:target").GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual("/equality_joint_attributes/Geometry/body2/body3/slide1", str(targets[0]))

        # Check NewtonMimicAPI attributes
        self.assertTrue(default_joint.HasAPI("NewtonMimicAPI"))
        self.assertAlmostEqual(default_joint.GetAttribute("newton:mimicCoef0").Get(), 0.0)
        self.assertAlmostEqual(default_joint.GetAttribute("newton:mimicCoef1").Get(), 1.0)
        targets = default_joint.GetRelationship("newton:mimicJoint").GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual("/equality_joint_attributes/Geometry/body2/body3/slide1", str(targets[0]))
        self.assertTrue(default_joint.GetAttribute("newton:mimicEnabled").Get())

        # Check that only the target relationship is authored (required), default values are NOT authored
        authored_properties = ["newton:mimicJoint"]
        for property in default_joint.GetPropertiesInNamespace("newton"):
            if property.GetName() in authored_properties:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")
            else:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")

    def test_connect_equality_schema(self):
        # Test that connect equality attributes are authored correctly
        model = pathlib.Path("./tests/data/equality_connect_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Custom connect equality should have non-default values authored
        custom_connect: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/custom_connect")
        self.assertTrue(custom_connect.IsValid())
        self.assertTrue(custom_connect.HasAPI("MjcEqualityConnectAPI"))

        # Connect equalities only have solimp and solref (no mjc:target, no torqueScale)
        not_authored_properties = ["mjc:target", "mjc:torqueScale"]
        for property in custom_connect.GetPropertiesInNamespace("mjc"):
            if property.GetName() in not_authored_properties:
                self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")
            else:
                self.assertTrue(self.__has_authored_value(property), f"Property {property.GetName()} is not authored")

        # Check solimp values (custom_connect has solimp="0.8 0.9 0.002 0.6 3")
        expected_solimp = [0.8, 0.9, 0.002, 0.6, 3]
        actual_solimp = custom_connect.GetAttribute("mjc:solimp").Get()
        self.assertEqual(len(actual_solimp), len(expected_solimp))
        for i in range(5):
            self.assertAlmostEqual(actual_solimp[i], expected_solimp[i])

        # Check solref values (custom_connect has solref="0.03 0.8")
        expected_solref = [0.03, 0.8]
        actual_solref = custom_connect.GetAttribute("mjc:solref").Get()
        self.assertEqual(len(actual_solref), len(expected_solref))
        for i in range(2):
            self.assertAlmostEqual(actual_solref[i], expected_solref[i])

        # Connect equality is a spherical joint
        self.assertTrue(custom_connect.IsA(UsdPhysics.SphericalJoint))
        connect_joint = UsdPhysics.SphericalJoint(custom_connect)
        self.assertTrue(connect_joint)

        body0_targets = connect_joint.GetBody0Rel().GetTargets()
        body1_targets = connect_joint.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_connect_attributes/Geometry/body0", str(body0_targets[0]))
        self.assertEqual("/equality_connect_attributes/Geometry/body1", str(body1_targets[0]))

        self.assertTrue(Gf.IsClose(connect_joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0.05, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(connect_joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0.2), 1e-5))
        self.assertRotationsAlmostEqual(connect_joint.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertRotationsAlmostEqual(connect_joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))

        # Default connect equality should have default values that are NOT authored
        default_connect: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/default_connect")
        self.assertTrue(default_connect.IsValid())
        self.assertTrue(default_connect.IsA(UsdPhysics.SphericalJoint))
        self.assertTrue(default_connect.HasAPI("MjcEqualityConnectAPI"))

        # Check that default MJC properties are NOT authored
        for property in default_connect.GetPropertiesInNamespace("mjc"):
            self.assertFalse(self.__has_authored_value(property), f"Property {property.GetName()} is authored")

        # Verify the resolved values still match expected defaults
        expected_default_solimp = [0.9, 0.95, 0.001, 0.5, 2]
        actual_default_solimp = default_connect.GetAttribute("mjc:solimp").Get()
        self.assertEqual(len(actual_default_solimp), len(expected_default_solimp))
        for i in range(5):
            self.assertAlmostEqual(actual_default_solimp[i], expected_default_solimp[i])

        expected_default_solref = [0.02, 1]
        actual_default_solref = default_connect.GetAttribute("mjc:solref").Get()
        self.assertEqual(len(actual_default_solref), len(expected_default_solref))
        for i in range(2):
            self.assertAlmostEqual(actual_default_solref[i], expected_default_solref[i])

        default_joint = UsdPhysics.SphericalJoint(default_connect)
        self.assertTrue(Gf.IsClose(default_joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(default_joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0.2), 1e-5))
        self.assertRotationsAlmostEqual(default_joint.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertRotationsAlmostEqual(default_joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))

        site_connect: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/site_connect")
        self.assertTrue(site_connect.IsValid())
        self.assertTrue(site_connect.IsA(UsdPhysics.SphericalJoint))
        self.assertTrue(site_connect.HasAPI("MjcEqualityConnectAPI"))

        site_connect_joint = UsdPhysics.SphericalJoint(site_connect)
        body0_targets = site_connect_joint.GetBody0Rel().GetTargets()
        body1_targets = site_connect_joint.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_connect_attributes/Geometry/body4/site4", str(body0_targets[0]))
        self.assertEqual("/equality_connect_attributes/Geometry/body5/site5", str(body1_targets[0]))
        self.assertRotationsAlmostEqual(site_connect_joint.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertRotationsAlmostEqual(site_connect_joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertTrue(site_connect_joint.GetExcludeFromArticulationAttr().Get())

    def test_connect_equality_joint_positions_and_rotations(self):
        # Verify spherical joint localPos0, localPos1, localRot0, localRot1 match anchor-based semantics
        model = pathlib.Path("./tests/data/equality_connect_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        connect_a: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/connect_anchor_a")
        self.assertTrue(connect_a.IsValid())
        joint_a = UsdPhysics.SphericalJoint(connect_a)
        self.assertTrue(Gf.IsClose(joint_a.GetLocalPos0Attr().Get(), Gf.Vec3f(0.1, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_a.GetLocalPos1Attr().Get(), Gf.Vec3f(-0.4, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_a.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_a.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())

        connect_b: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/connect_anchor_b")
        self.assertTrue(connect_b.IsValid())
        joint_b = UsdPhysics.SphericalJoint(connect_b)
        self.assertTrue(Gf.IsClose(joint_b.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.15, 0.02), 1e-5))
        self.assertTrue(Gf.IsClose(joint_b.GetLocalPos1Attr().Get(), Gf.Vec3f(-0.5, 0.15, 0.02), 1e-5))
        self.assertRotationsAlmostEqual(joint_b.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_b.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())

        connect_world: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/connect_to_world")
        self.assertTrue(connect_world.IsValid())
        joint_world = UsdPhysics.SphericalJoint(connect_world)
        self.assertTrue(Gf.IsClose(joint_world.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_world.GetLocalPos1Attr().Get(), Gf.Vec3f(3, 0, 0.9), 1e-5))
        self.assertRotationsAlmostEqual(joint_world.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_world.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())

    def test_connect_equality_enabled(self):
        # XML active="true" (default) - joint enabled, attr should not be authored when default
        # XML active="false" - joint disabled, physics:jointEnabled must be authored and false
        model = pathlib.Path("./tests/data/equality_connect_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Enabled connect (default): resolved value True, attr should not be authored
        default_connect: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/default_connect")
        self.assertTrue(default_connect.IsValid())
        default_joint = UsdPhysics.SphericalJoint(default_connect)
        joint_enabled_attr = default_joint.GetJointEnabledAttr()
        self.assertTrue(joint_enabled_attr.Get(), "Default connect should be enabled")
        self.assertFalse(
            self.__has_authored_value(joint_enabled_attr),
            "physics:jointEnabled should not be authored when it is the default (true)",
        )

        # Disabled connect: attr must be authored and false
        disabled_connect: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/disabled_connect")
        self.assertTrue(disabled_connect.IsValid())
        disabled_joint = UsdPhysics.SphericalJoint(disabled_connect)
        disabled_joint_enabled_attr = disabled_joint.GetJointEnabledAttr()
        self.assertTrue(
            self.__has_authored_value(disabled_joint_enabled_attr),
            "physics:jointEnabled should be authored when equality is inactive",
        )
        self.assertFalse(disabled_joint_enabled_attr.Get(), "Disabled connect should have jointEnabled false")

    def test_connect_missing_body2(self):
        # When a connect equality has no body2, MuJoCo uses worldbody; in USD, body1 is the default prim
        model = pathlib.Path("./tests/data/equality_connect_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        connect_to_world: Usd.Prim = stage.GetPrimAtPath("/equality_connect_attributes/Physics/connect_to_world")
        self.assertTrue(connect_to_world.IsValid())
        self.assertTrue(connect_to_world.IsA(UsdPhysics.SphericalJoint))
        self.assertTrue(connect_to_world.HasAPI("MjcEqualityConnectAPI"))

        connect_joint = UsdPhysics.SphericalJoint(connect_to_world)
        body0_targets = connect_joint.GetBody0Rel().GetTargets()
        body1_targets = connect_joint.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        # First body is the specified body (body6)
        self.assertEqual("/equality_connect_attributes/Geometry/body6", str(body0_targets[0]))
        # Second body is world - in USD the default prim
        default_prim = stage.GetDefaultPrim()
        self.assertTrue(default_prim.IsValid())
        self.assertEqual(body1_targets[0], default_prim.GetPath())

    def test_connect_equality_anchor_positions(self):
        # Verify anchor positions are correctly converted from XML anchor values
        model = pathlib.Path("./tests/data/equality_connect.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        world_to_body: Usd.Prim = stage.GetPrimAtPath("/equality_connect/Physics/world_to_body")
        self.assertTrue(world_to_body.IsValid())
        joint_world_to_body = UsdPhysics.SphericalJoint(world_to_body)
        self.assertTrue(Gf.IsClose(joint_world_to_body.GetLocalPos0Attr().Get(), Gf.Vec3f(0.5, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_world_to_body.GetLocalPos1Attr().Get(), Gf.Vec3f(-2.5, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_world_to_body.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_world_to_body.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())

        bodies: Usd.Prim = stage.GetPrimAtPath("/equality_connect/Physics/bodies")
        self.assertTrue(bodies.IsValid())
        joint_bodies = UsdPhysics.SphericalJoint(bodies)
        self.assertTrue(Gf.IsClose(joint_bodies.GetLocalPos0Attr().Get(), Gf.Vec3f(0.5, 0.1, 0.5), 1e-5))
        self.assertTrue(Gf.IsClose(joint_bodies.GetLocalPos1Attr().Get(), Gf.Vec3f(0.5, 0.1, 0.5), 1e-5))
        self.assertRotationsAlmostEqual(joint_bodies.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_bodies.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())

        sites: Usd.Prim = stage.GetPrimAtPath("/equality_connect/Physics/sites")
        self.assertTrue(sites.IsValid())
        joint_sites = UsdPhysics.SphericalJoint(sites)
        self.assertTrue(Gf.IsClose(joint_sites.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_sites.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_sites.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_sites.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())

    def test_connects_vs_welds(self):
        # Verify that connect and weld constraints are equivalent when defined with sites and bodies
        model = pathlib.Path("./tests/data/equality_connect_vs_weld.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Connect constraints should be equivalent to weld constraints with the same anchor positions
        connect_site: Usd.Prim = stage.GetPrimAtPath("/equality_connect_vs_weld/Physics/connect_site")
        self.assertTrue(connect_site.IsValid())
        joint_connect_site = UsdPhysics.SphericalJoint(connect_site)
        body0_targets = joint_connect_site.GetBody0Rel().GetTargets()
        body1_targets = joint_connect_site.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_connect_vs_weld/Geometry/a1", str(body0_targets[0]))
        self.assertEqual("/equality_connect_vs_weld/Geometry/a/a2", str(body1_targets[0]))
        self.assertTrue(Gf.IsClose(joint_connect_site.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_connect_site.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_connect_site.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_connect_site.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertTrue(joint_connect_site.GetJointEnabledAttr().Get())

        weld_site: Usd.Prim = stage.GetPrimAtPath("/equality_connect_vs_weld/Physics/weld_site")
        self.assertTrue(weld_site.IsValid())
        joint_weld_site = UsdPhysics.FixedJoint(weld_site)
        body0_targets = joint_weld_site.GetBody0Rel().GetTargets()
        body1_targets = joint_weld_site.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_connect_vs_weld/Geometry/b1", str(body0_targets[0]))
        self.assertEqual("/equality_connect_vs_weld/Geometry/b/b2", str(body1_targets[0]))
        self.assertTrue(Gf.IsClose(joint_weld_site.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_weld_site.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_weld_site.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_weld_site.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertTrue(joint_weld_site.GetJointEnabledAttr().Get())

        connect_body: Usd.Prim = stage.GetPrimAtPath("/equality_connect_vs_weld/Physics/connect_body")
        self.assertTrue(connect_body.IsValid())
        joint_connect_body = UsdPhysics.SphericalJoint(connect_body)
        body0_targets = joint_connect_body.GetBody0Rel().GetTargets()
        body1_targets = joint_connect_body.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_connect_vs_weld/Geometry/a", str(body0_targets[0]))
        self.assertEqual("/equality_connect_vs_weld", str(body1_targets[0]))
        self.assertTrue(Gf.IsClose(joint_connect_body.GetLocalPos0Attr().Get(), Gf.Vec3f(0, -1, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_connect_body.GetLocalPos1Attr().Get(), Gf.Vec3f(-2, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_connect_body.GetLocalRot0Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertRotationsAlmostEqual(joint_connect_body.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertFalse(joint_connect_body.GetJointEnabledAttr().Get())

        weld_body: Usd.Prim = stage.GetPrimAtPath("/equality_connect_vs_weld/Physics/weld_body")
        self.assertTrue(weld_body.IsValid())
        joint_weld_body = UsdPhysics.FixedJoint(weld_body)
        body0_targets = joint_weld_body.GetBody0Rel().GetTargets()
        body1_targets = joint_weld_body.GetBody1Rel().GetTargets()
        self.assertEqual(len(body0_targets), 1)
        self.assertEqual(len(body1_targets), 1)
        self.assertEqual("/equality_connect_vs_weld/Geometry/b", str(body0_targets[0]))
        self.assertEqual("/equality_connect_vs_weld", str(body1_targets[0]))
        self.assertTrue(Gf.IsClose(joint_weld_body.GetLocalPos0Attr().Get(), Gf.Vec3f(0, -1, 0), 1e-5))
        self.assertTrue(Gf.IsClose(joint_weld_body.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0), 1e-5))
        self.assertRotationsAlmostEqual(joint_weld_body.GetLocalRot0Attr().Get(), Gf.Quatf(0.70710678, 0.70710678, 0, 0))
        self.assertRotationsAlmostEqual(joint_weld_body.GetLocalRot1Attr().Get(), Gf.Quatf.GetIdentity())
        self.assertFalse(joint_weld_body.GetJointEnabledAttr().Get(), "Weld body should be disabled")

    def test_invalid_names(self):
        model = pathlib.Path("./tests/data/equality_invalid_names.xml")

        with usdex.test.ScopedDiagnosticChecker(
            self,
            [
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*Body 'world' not found for equality 'connect_body'"),
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*Body 'world' not found for equality 'weld_body'"),
            ],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())

        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        # Check that the equalities are invalid prims
        connect_body: Usd.Prim = stage.GetPrimAtPath("/equality_invalid_names/Physics/connect_body")
        self.assertFalse(connect_body.IsValid())
        weld_body: Usd.Prim = stage.GetPrimAtPath("/equality_invalid_names/Physics/weld_body")
        self.assertFalse(weld_body.IsValid())
