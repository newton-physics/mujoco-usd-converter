# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib

from pxr import Gf, Sdf, Usd, UsdPhysics

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestJoints(ConverterTestCase):

    def setUp(self):
        super().setUp()
        self.tolerance = 1e-6

    def test_hinge_joints(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # first hinge is aligned with the x-axis
        body1 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/hinge_joints/Geometry/body1"))
        self.assertTrue(body1)
        self.assertTrue(body1.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        body2 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/hinge_joints/Geometry/body1/body2"))
        self.assertTrue(body2)
        self.assertFalse(body2.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/hinge_joints/Geometry/body1/body2/PhysicsRevoluteJoint"))
        self.assertTrue(joint)

        self.assertEqual(joint.GetBody0Rel().GetTargets(), [body1.GetPrim().GetPath()])
        self.assertEqual(joint.GetBody1Rel().GetTargets(), [body2.GetPrim().GetPath()])

        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertEqual(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertAlmostEqual(joint.GetLowerLimitAttr().Get(), -90)
        self.assertAlmostEqual(joint.GetUpperLimitAttr().Get(), 10)

        # second hinge is aligned with the y-axis
        body3 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/hinge_joints/Geometry/body3"))
        self.assertTrue(body3)
        self.assertTrue(body3.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        body4 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4"))
        self.assertTrue(body4)
        self.assertFalse(body4.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/PhysicsRevoluteJoint"))
        self.assertTrue(joint)

        self.assertEqual(joint.GetBody0Rel().GetTargets(), [body3.GetPrim().GetPath()])
        self.assertEqual(joint.GetBody1Rel().GetTargets(), [body4.GetPrim().GetPath()])

        # the expected axis is z, with a 180 degree local rotation as the -z axis on the mjc joint needs to be realigned for the limits to make sense
        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.z)
        self.assertTrue(Gf.IsClose(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0), self.tolerance))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint.GetLocalRot0Attr().Get(), Gf.Quatf(0.0, Gf.Vec3f(-1.0, 0.0, 0.0)))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(0.0, Gf.Vec3f(-1.0, 0.0, 0.0)))
        self.assertAlmostEqual(joint.GetLowerLimitAttr().Get(), -5)
        self.assertAlmostEqual(joint.GetUpperLimitAttr().Get(), 60)

        # it has an extra joint with a 90 degree rotation between body4 and body5
        body5 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/body5"))
        self.assertTrue(body5)
        self.assertFalse(body5.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/body5/PhysicsRevoluteJoint"))
        self.assertTrue(joint)

        self.assertEqual(joint.GetBody0Rel().GetTargets(), [body4.GetPrim().GetPath()])
        self.assertEqual(joint.GetBody1Rel().GetTargets(), [body5.GetPrim().GetPath()])

        # the expected axis remains z to respect the axis alignment of the mjc joint
        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.z)
        self.assertTrue(Gf.IsClose(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(-0.1, 1.1, 0), self.tolerance))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assert_rotation_almost_equal(Gf.Rotation(joint.GetLocalRot0Attr().Get()), Gf.Rotation(Gf.Quatf(0.7071068, Gf.Vec3f(0, 0, 0.7071067))))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertAlmostEqual(joint.GetLowerLimitAttr().Get(), -90)
        self.assertAlmostEqual(joint.GetUpperLimitAttr().Get(), 0)

        # it has an extra joint with an off-axis rotation
        body6 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/body6"))
        self.assertTrue(body6)
        self.assertFalse(body6.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/body6/PhysicsRevoluteJoint"))
        self.assertTrue(joint)

        self.assertEqual(joint.GetBody0Rel().GetTargets(), [body4.GetPrim().GetPath()])
        self.assertEqual(joint.GetBody1Rel().GetTargets(), [body6.GetPrim().GetPath()])

        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertTrue(Gf.IsClose(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 1.1, 0.1), self.tolerance))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assert_rotation_almost_equal(
            Gf.Rotation(joint.GetLocalRot0Attr().Get()),
            Gf.Rotation(Gf.Quatf(0.37174803, Gf.Vec3f(0.37174803, 0.6015009, 0.6015009))),
        )
        self.assert_rotation_almost_equal(
            Gf.Rotation(joint.GetLocalRot1Attr().Get()),
            Gf.Rotation(Gf.Quatf(0.97324896, Gf.Vec3f(0, 0.22975293, 0))),
        )
        self.assertAlmostEqual(joint.GetLowerLimitAttr().Get(), 0)
        self.assertAlmostEqual(joint.GetUpperLimitAttr().Get(), 90)

    def test_slide_joints(self):
        model = pathlib.Path("./tests/data/slide_joints.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # first slide is aligned with the x-axis
        body1 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/slide_joints/Geometry/body1"))
        self.assertTrue(body1)
        self.assertTrue(body1.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        body2 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/slide_joints/Geometry/body1/body2"))
        self.assertTrue(body2)
        self.assertFalse(body2.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint = UsdPhysics.PrismaticJoint(stage.GetPrimAtPath("/slide_joints/Geometry/body1/body2/PhysicsPrismaticJoint"))
        self.assertTrue(joint)

        self.assertEqual(joint.GetBody0Rel().GetTargets(), [body1.GetPrim().GetPath()])
        self.assertEqual(joint.GetBody1Rel().GetTargets(), [body2.GetPrim().GetPath()])

        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.y)
        self.assertTrue(Gf.IsClose(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0), self.tolerance))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0.0, 0.0, 0)))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0.0, 0.0, 0)))
        self.assertAlmostEqual(joint.GetLowerLimitAttr().Get(), 0)
        self.assertAlmostEqual(joint.GetUpperLimitAttr().Get(), 0.5)

        # second hinge is aligned with the y-axis
        body3 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/slide_joints/Geometry/body3"))
        self.assertTrue(body3)
        self.assertTrue(body3.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        body4 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/slide_joints/Geometry/body3/body4"))
        self.assertTrue(body4)
        self.assertFalse(body4.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint2 = UsdPhysics.PrismaticJoint(stage.GetPrimAtPath("/slide_joints/Geometry/body3/body4/slide2"))
        self.assertTrue(joint2)

        self.assertEqual(joint2.GetBody0Rel().GetTargets(), [body3.GetPrim().GetPath()])
        self.assertEqual(joint2.GetBody1Rel().GetTargets(), [body4.GetPrim().GetPath()])

        # the expected axis remains x as we always export x-aligned joints and instead manipulate the local rot values
        self.assertEqual(joint2.GetAxisAttr().Get(), UsdPhysics.Tokens.y)
        self.assertTrue(Gf.IsClose(joint2.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0), self.tolerance))
        self.assertEqual(joint2.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint2.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0.0, 0.0, 0)))
        self.assertEqual(joint2.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0.0, 0.0, 0)))
        self.assertAlmostEqual(joint2.GetLowerLimitAttr().Get(), 0)
        self.assertAlmostEqual(joint2.GetUpperLimitAttr().Get(), 0.25)

        # it has an extra joint with a 90 degree rotation between body4 and body5
        body5 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/slide_joints/Geometry/body3/body4/body5"))
        self.assertTrue(body5)
        self.assertFalse(body5.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint3 = UsdPhysics.PrismaticJoint(stage.GetPrimAtPath("/slide_joints/Geometry/body3/body4/body5/PhysicsPrismaticJoint"))
        self.assertTrue(joint3)

        self.assertEqual(joint3.GetBody0Rel().GetTargets(), [body4.GetPrim().GetPath()])
        self.assertEqual(joint3.GetBody1Rel().GetTargets(), [body5.GetPrim().GetPath()])

        self.assertEqual(joint3.GetAxisAttr().Get(), UsdPhysics.Tokens.z)
        self.assertTrue(Gf.IsClose(joint3.GetLocalPos0Attr().Get(), Gf.Vec3f(-0.1, 1.1, 0), self.tolerance))
        self.assertEqual(joint3.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assert_rotation_almost_equal(Gf.Rotation(joint3.GetLocalRot0Attr().Get()), Gf.Rotation(Gf.Quatf(0.7071068, Gf.Vec3f(0, 0, 0.7071067))))
        self.assertEqual(joint3.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertAlmostEqual(joint3.GetLowerLimitAttr().Get(), 0)
        self.assertAlmostEqual(joint3.GetUpperLimitAttr().Get(), 0.25)

    def test_ball_joints(self):
        model = pathlib.Path("./tests/data/ball_joints.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # first ball joint is aligned with the x-axis
        body1 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/ball_joints/Geometry/body1"))
        self.assertTrue(body1)
        self.assertTrue(body1.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        body2 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/ball_joints/Geometry/body1/body2"))
        self.assertTrue(body2)
        self.assertFalse(body2.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint = UsdPhysics.SphericalJoint(stage.GetPrimAtPath("/ball_joints/Geometry/body1/body2/PhysicsSphericalJoint"))
        self.assertTrue(joint)

        self.assertEqual(joint.GetBody0Rel().GetTargets(), [body1.GetPrim().GetPath()])
        self.assertEqual(joint.GetBody1Rel().GetTargets(), [body2.GetPrim().GetPath()])

        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertTrue(Gf.IsClose(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0), self.tolerance))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertAlmostEqual(joint.GetConeAngle0LimitAttr().Get(), 90)
        self.assertAlmostEqual(joint.GetConeAngle1LimitAttr().Get(), 90)

        # second ball joint is aligned with the y-axis
        body3 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/ball_joints/Geometry/body3"))
        self.assertTrue(body3)
        self.assertTrue(body3.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        body4 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/ball_joints/Geometry/body3/body4"))
        self.assertTrue(body4)
        self.assertFalse(body4.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint2 = UsdPhysics.SphericalJoint(stage.GetPrimAtPath("/ball_joints/Geometry/body3/body4/PhysicsSphericalJoint"))
        self.assertTrue(joint2)

        self.assertEqual(joint2.GetBody0Rel().GetTargets(), [body3.GetPrim().GetPath()])
        self.assertEqual(joint2.GetBody1Rel().GetTargets(), [body4.GetPrim().GetPath()])

        self.assertEqual(joint2.GetAxisAttr().Get(), UsdPhysics.Tokens.z)
        self.assertTrue(Gf.IsClose(joint2.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0), self.tolerance))
        self.assertEqual(joint2.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint2.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertEqual(joint2.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertAlmostEqual(joint2.GetConeAngle0LimitAttr().Get(), 45)
        self.assertAlmostEqual(joint2.GetConeAngle1LimitAttr().Get(), 45)

        # it has an extra joint with a 90 degree rotation between body4 and body5
        body5 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/ball_joints/Geometry/body3/body4/body5"))
        self.assertTrue(body5)
        self.assertFalse(body5.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint3 = UsdPhysics.SphericalJoint(stage.GetPrimAtPath("/ball_joints/Geometry/body3/body4/body5/PhysicsSphericalJoint"))
        self.assertTrue(joint3)

        self.assertEqual(joint3.GetBody0Rel().GetTargets(), [body4.GetPrim().GetPath()])
        self.assertEqual(joint3.GetBody1Rel().GetTargets(), [body5.GetPrim().GetPath()])

        self.assertEqual(joint3.GetAxisAttr().Get(), UsdPhysics.Tokens.z)
        self.assertTrue(Gf.IsClose(joint3.GetLocalPos0Attr().Get(), Gf.Vec3f(-0.1, 1.1, 0), self.tolerance))
        self.assertEqual(joint3.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assert_rotation_almost_equal(Gf.Rotation(joint3.GetLocalRot0Attr().Get()), Gf.Rotation(Gf.Quatf(0.7071068, Gf.Vec3f(0, 0, 0.7071067))))
        self.assertEqual(joint3.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertAlmostEqual(joint3.GetConeAngle0LimitAttr().Get(), 90)
        self.assertAlmostEqual(joint3.GetConeAngle1LimitAttr().Get(), 90)

    def test_fixed_and_free_joints(self):
        model = pathlib.Path("./tests/data/fixed_vs_free_joints.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # A body without an explicit MJC joint has a fixed joint in USD
        body1_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body1")
        body2_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body1/body2")
        joint_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body1/body2/PhysicsFixedJoint")
        self.assertTrue(joint_prim.IsA(UsdPhysics.FixedJoint))
        fixed_joint = UsdPhysics.FixedJoint(joint_prim)
        self.assertEqual(fixed_joint.GetBody0Rel().GetTargets(), [body1_prim.GetPath()])
        self.assertEqual(fixed_joint.GetBody1Rel().GetTargets(), [body2_prim.GetPath()])
        self.assertEqual(fixed_joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.5, 0))
        self.assertEqual(fixed_joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0))
        self.assertEqual(fixed_joint.GetLocalRot0Attr().Get(), Gf.Quatf(0.7071068286895752, Gf.Vec3f(0.0, 0.0, 0.7071067094802856)))
        self.assertEqual(fixed_joint.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))

        # A free floating body has no joint in USD
        body3_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body3")
        for child in body3_prim.GetChildren():
            self.assertFalse(child.IsA(UsdPhysics.Joint))

        # Its child is still fixed to the parent
        body4_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body3/body4")
        joint_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body3/body4/PhysicsFixedJoint")
        self.assertTrue(joint_prim.IsA(UsdPhysics.FixedJoint))
        fixed_joint = UsdPhysics.FixedJoint(joint_prim)
        self.assertEqual(fixed_joint.GetBody0Rel().GetTargets(), [body3_prim.GetPath()])
        self.assertEqual(fixed_joint.GetBody1Rel().GetTargets(), [body4_prim.GetPath()])

    def test_joint_group(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Check that joint group is authored
        joint0: Usd.Prim = stage.GetPrimAtPath("/hinge_joints/Geometry/body1/body2/PhysicsRevoluteJoint")
        self.assertEqual(joint0.GetAttribute("mjc:group").Get(), 0)
        joint2: Usd.Prim = stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/PhysicsRevoluteJoint")
        self.assertEqual(joint2.GetAttribute("mjc:group").Get(), 2)

    def test_auto_limits(self):
        # Test with autolimits="true"
        model = pathlib.Path("./tests/data/joint_limits.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Explicitly unlimited joint should not have limits
        unlimited_joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/joint_limits/Geometry/body3/body4/unlimited_joint"))
        self.assertFalse(unlimited_joint.GetLowerLimitAttr().HasAuthoredValue())
        self.assertFalse(unlimited_joint.GetUpperLimitAttr().HasAuthoredValue())

        # Auto-limited joint should have limits
        auto_limited_joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/joint_limits/Geometry/body5/body6/auto_limited_joint"))
        self.assertTrue(auto_limited_joint.GetLowerLimitAttr().HasAuthoredValue())
        self.assertTrue(auto_limited_joint.GetUpperLimitAttr().HasAuthoredValue())
        self.assertAlmostEqual(auto_limited_joint.GetLowerLimitAttr().Get(), -30)
        self.assertAlmostEqual(auto_limited_joint.GetUpperLimitAttr().Get(), 30)

        # Auto-limited joint with same range should be unlimited
        auto_unlimited_same_range = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/joint_limits/Geometry/body7/body8/auto_unlimited_same_range"))
        self.assertFalse(auto_unlimited_same_range.GetLowerLimitAttr().HasAuthoredValue())
        self.assertFalse(auto_unlimited_same_range.GetUpperLimitAttr().HasAuthoredValue())

    def test_no_autolimits(self):
        # Test with autolimits="false"
        model = pathlib.Path("./tests/data/joint_limits_no_autolimits.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Explicitly limited joint should have limits
        limited_joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/joint_limits_no_autolimits/Geometry/body1/body2/limited_joint"))
        self.assertTrue(limited_joint.GetLowerLimitAttr().HasAuthoredValue())
        self.assertTrue(limited_joint.GetUpperLimitAttr().HasAuthoredValue())
        self.assertAlmostEqual(limited_joint.GetLowerLimitAttr().Get(), -45)
        self.assertAlmostEqual(limited_joint.GetUpperLimitAttr().Get(), 45)

        # Explicitly unlimited joint should not have limits
        unlimited_joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/joint_limits_no_autolimits/Geometry/body3/body4/unlimited_joint"))
        self.assertFalse(unlimited_joint.GetLowerLimitAttr().HasAuthoredValue())
        self.assertFalse(unlimited_joint.GetUpperLimitAttr().HasAuthoredValue())

    def test_mjc_schema(self):
        # Test that all joint attributes are authored correctly
        model = pathlib.Path("./tests/data/joint_attributes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # A joints attributes are authored to USD if they are set to non-default values
        custom_joint: Usd.Prim = stage.GetPrimAtPath("/joint_attributes/Geometry/body1/custom_joint")
        self.assertTrue(custom_joint.IsValid())
        self.assertTrue(custom_joint.IsA(UsdPhysics.RevoluteJoint))
        self.assertTrue(custom_joint.HasAPI(Usd.SchemaRegistry.GetAPISchemaTypeName("MjcPhysicsJointAPI")))

        # Check that all MJC properties are authored
        for property in custom_joint.GetPropertiesInNamespace("mjc"):
            self.assertTrue(property.HasAuthoredValue(), f"Property {property.GetName()} is not authored")

        # Check that all attributes are authored correctly
        self.assertTrue(custom_joint.GetAttribute("mjc:actuatorfrclimited").HasAuthoredValue())
        self.assertEqual(custom_joint.GetAttribute("mjc:actuatorfrclimited").Get(), "true")
        self.assertTrue(custom_joint.GetAttribute("mjc:actuatorfrcrange:min").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:actuatorfrcrange:min").Get(), -10)
        self.assertTrue(custom_joint.GetAttribute("mjc:actuatorfrcrange:max").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:actuatorfrcrange:max").Get(), 10)
        self.assertTrue(custom_joint.GetAttribute("mjc:actuatorgravcomp").HasAuthoredValue())
        self.assertEqual(custom_joint.GetAttribute("mjc:actuatorgravcomp").Get(), True)
        self.assertTrue(custom_joint.GetAttribute("mjc:armature").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:armature").Get(), 0.1)
        self.assertTrue(custom_joint.GetAttribute("mjc:damping").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:damping").Get(), 0.5)
        self.assertTrue(custom_joint.GetAttribute("mjc:frictionloss").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:frictionloss").Get(), 0.2)
        self.assertTrue(custom_joint.GetAttribute("mjc:margin").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:margin").Get(), 0.01)
        self.assertTrue(custom_joint.GetAttribute("mjc:ref").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:ref").Get(), 0.1)
        self.assertTrue(custom_joint.GetAttribute("mjc:solimplimit").HasAuthoredValue())
        expected_solimplimit = [0.8, 0.9, 0.002, 0.6, 3]
        actual_solimplimit = custom_joint.GetAttribute("mjc:solimplimit").Get()
        for i in range(5):
            self.assertAlmostEqual(actual_solimplimit[i], expected_solimplimit[i], places=5)
        self.assertTrue(custom_joint.GetAttribute("mjc:solreflimit").HasAuthoredValue())
        expected_solreflimit = [0.01, 0.5]
        actual_solreflimit = custom_joint.GetAttribute("mjc:solreflimit").Get()
        for i in range(2):
            self.assertAlmostEqual(actual_solreflimit[i], expected_solreflimit[i], places=5)
        self.assertTrue(custom_joint.GetAttribute("mjc:solimpfriction").HasAuthoredValue())
        expected_solimpfriction = [0.7, 0.8, 0.001, 0.4, 2]
        actual_solimpfriction = custom_joint.GetAttribute("mjc:solimpfriction").Get()
        for i in range(5):
            self.assertAlmostEqual(actual_solimpfriction[i], expected_solimpfriction[i], places=5)
        self.assertTrue(custom_joint.GetAttribute("mjc:solreffriction").HasAuthoredValue())
        expected_solreffriction = [0.015, 0.8]
        actual_solreffriction = custom_joint.GetAttribute("mjc:solreffriction").Get()
        for i in range(2):
            self.assertAlmostEqual(actual_solreffriction[i], expected_solreffriction[i], places=5)
        self.assertTrue(custom_joint.GetAttribute("mjc:springdamper").HasAuthoredValue())
        expected_springdamper = [0.5, 0.3]
        actual_springdamper = custom_joint.GetAttribute("mjc:springdamper").Get()
        for i in range(2):
            self.assertAlmostEqual(actual_springdamper[i], expected_springdamper[i], places=5)
        self.assertTrue(custom_joint.GetAttribute("mjc:springref").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:springref").Get(), 0.2)
        self.assertTrue(custom_joint.GetAttribute("mjc:stiffness").HasAuthoredValue())
        self.assertAlmostEqual(custom_joint.GetAttribute("mjc:stiffness").Get(), 100)

        # A joint with explicitly authored default values in MJC does not need to author any values in USD
        default_joint: Usd.Prim = stage.GetPrimAtPath("/joint_attributes/Geometry/body2/default_joint")
        self.assertTrue(default_joint.IsValid())
        self.assertTrue(default_joint.IsA(UsdPhysics.PrismaticJoint))
        self.assertTrue(default_joint.HasAPI(Usd.SchemaRegistry.GetAPISchemaTypeName("MjcPhysicsJointAPI")))
        self.assertFalse(default_joint.GetAttribute("mjc:actuatorfrclimited").HasAuthoredValue())
        self.assertEqual(default_joint.GetAttribute("mjc:actuatorfrclimited").Get(), "auto")
        self.assertFalse(default_joint.GetAttribute("mjc:actuatorfrcrange:min").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:actuatorfrcrange:min").Get(), 0)
        self.assertFalse(default_joint.GetAttribute("mjc:actuatorfrcrange:max").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:actuatorfrcrange:max").Get(), 0)
        self.assertFalse(default_joint.GetAttribute("mjc:actuatorgravcomp").HasAuthoredValue())
        self.assertEqual(default_joint.GetAttribute("mjc:actuatorgravcomp").Get(), False)
        self.assertFalse(default_joint.GetAttribute("mjc:armature").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:armature").Get(), 0.0)
        self.assertFalse(default_joint.GetAttribute("mjc:damping").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:damping").Get(), 0.0)
        self.assertFalse(default_joint.GetAttribute("mjc:frictionloss").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:frictionloss").Get(), 0.0)
        self.assertFalse(default_joint.GetAttribute("mjc:margin").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:margin").Get(), 0.0)
        self.assertFalse(default_joint.GetAttribute("mjc:ref").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:ref").Get(), 0.0)
        self.assertFalse(default_joint.GetAttribute("mjc:springref").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:springref").Get(), 0.0)
        self.assertFalse(default_joint.GetAttribute("mjc:stiffness").HasAuthoredValue())
        self.assertAlmostEqual(default_joint.GetAttribute("mjc:stiffness").Get(), 0)

    def test_joint_to_worldbody(self):
        model = pathlib.Path("./tests/data/simple_actuator.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # A joint to the worldbody should be authored as a fixed joint
        joint_prim: UsdPhysics.RevoluteJoint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/simple_actuator/Geometry/body/hinge"))
        self.assertTrue(joint_prim)
        self.assertEqual(joint_prim.GetBody0Rel().GetTargets(), [stage.GetDefaultPrim().GetPath()])
        self.assertEqual(joint_prim.GetBody1Rel().GetTargets(), [stage.GetPrimAtPath("/simple_actuator/Geometry/body").GetPath()])
        self.assertEqual(joint_prim.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0, 0))
        self.assertEqual(joint_prim.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0, 0))
        self.assertEqual(joint_prim.GetLocalRot0Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertEqual(joint_prim.GetLocalRot1Attr().Get(), Gf.Quatf(1, Gf.Vec3f(0, 0, 0)))
        self.assertEqual(joint_prim.GetAxisAttr().Get(), UsdPhysics.Tokens.y)
        self.assertEqual(joint_prim.GetLowerLimitAttr().Get(), 0)
        self.assertEqual(joint_prim.GetUpperLimitAttr().Get(), 90)
