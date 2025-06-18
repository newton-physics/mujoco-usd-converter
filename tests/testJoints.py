# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

from pxr import Gf, Sdf, Usd, UsdPhysics

import mjc_usd_converter


class TestJoints(unittest.TestCase):
    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def assert_rotation_almost_equal(self, rot1: Gf.Rotation, rot2: Gf.Rotation, tolerance: float = 1e-6):
        self.assertTrue(Gf.IsClose(rot1.GetAxis(), rot2.GetAxis(), tolerance))
        self.assertTrue(Gf.IsClose(rot1.GetAngle(), rot2.GetAngle(), tolerance))

    def test_hinge_joints(self):
        model = pathlib.Path("./tests/data/hinge_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

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

        # the expected axis remains x as we always export x-aligned joints and instead manipulate the local rot values
        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertEqual(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint.GetLocalRot0Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0, -0.7071067690849304, 0)))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0, -0.7071067690849304, 0)))
        self.assertAlmostEqual(joint.GetLowerLimitAttr().Get(), -60)
        self.assertAlmostEqual(joint.GetUpperLimitAttr().Get(), 5)

        # it has an extra joint with a 90 degree rotation between body4 and body5
        body5 = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/body5"))
        self.assertTrue(body5)
        self.assertFalse(body5.GetPrim().HasAPI(UsdPhysics.ArticulationRootAPI))

        joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/body5/PhysicsRevoluteJoint"))
        self.assertTrue(joint)

        self.assertEqual(joint.GetBody0Rel().GetTargets(), [body4.GetPrim().GetPath()])
        self.assertEqual(joint.GetBody1Rel().GetTargets(), [body5.GetPrim().GetPath()])

        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertEqual(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(-0.1, 1.1, 0))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assert_rotation_almost_equal(Gf.Rotation(joint.GetLocalRot0Attr().Get()), Gf.Rotation(Gf.Quatf(0.5, Gf.Vec3f(0.5, -0.5, 0.5))))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0, -0.7071067690849304, 0)))
        self.assertAlmostEqual(joint.GetLowerLimitAttr().Get(), -90)
        self.assertAlmostEqual(joint.GetUpperLimitAttr().Get(), 0)

    def test_slide_joints(self):
        model = pathlib.Path("./tests/data/slide_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

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

        self.assertEqual(joint.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertEqual(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0))
        self.assertEqual(joint.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint.GetLocalRot0Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0.0, 0.0, 0.7071067690849304)))
        self.assertEqual(joint.GetLocalRot1Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0.0, 0.0, 0.7071067690849304)))
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
        self.assertEqual(joint2.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertEqual(joint2.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0))
        self.assertEqual(joint2.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint2.GetLocalRot0Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0.0, 0.0, 0.7071067690849304)))
        self.assertEqual(joint2.GetLocalRot1Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0.0, 0.0, 0.7071067690849304)))
        self.assertAlmostEqual(joint2.GetLowerLimitAttr().Get(), 0)
        self.assertAlmostEqual(joint2.GetUpperLimitAttr().Get(), 0.25)

    def test_ball_joints(self):
        model = pathlib.Path("./tests/data/ball_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

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
        self.assertEqual(joint.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0))
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

        self.assertEqual(joint2.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertEqual(joint2.GetLocalPos0Attr().Get(), Gf.Vec3f(0, 0.6, 0))
        self.assertEqual(joint2.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assertEqual(joint2.GetLocalRot0Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0, -0.7071067690849304, 0)))
        self.assertEqual(joint2.GetLocalRot1Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0, -0.7071067690849304, 0)))
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

        self.assertEqual(joint3.GetAxisAttr().Get(), UsdPhysics.Tokens.x)
        self.assertEqual(joint3.GetLocalPos0Attr().Get(), Gf.Vec3f(-0.1, 1.1, 0))
        self.assertEqual(joint3.GetLocalPos1Attr().Get(), Gf.Vec3f(0, 0.1, 0))
        self.assert_rotation_almost_equal(Gf.Rotation(joint3.GetLocalRot0Attr().Get()), Gf.Rotation(Gf.Quatf(0.5, Gf.Vec3f(0.5, -0.5, 0.5))))
        self.assertEqual(joint3.GetLocalRot1Attr().Get(), Gf.Quatf(0.7071067690849304, Gf.Vec3f(0, -0.7071067690849304, 0)))
        self.assertAlmostEqual(joint3.GetConeAngle0LimitAttr().Get(), 90)
        self.assertAlmostEqual(joint3.GetConeAngle1LimitAttr().Get(), 90)

    def test_fixed_and_free_joints(self):
        model = pathlib.Path("./tests/data/fixed_vs_free_joints.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        # A body without an explicit MJC joint has a fixed joint in USD
        body1_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body1")
        body2_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body1/body2")
        joint_prim = stage.GetPrimAtPath("/fixed_vs_free_joints/Geometry/body1/body2/PhysicsFixedJoint")
        self.assertTrue(joint_prim.IsA(UsdPhysics.FixedJoint))
        fixed_joint = UsdPhysics.FixedJoint(joint_prim)
        self.assertEqual(fixed_joint.GetBody0Rel().GetTargets(), [body1_prim.GetPath()])
        self.assertEqual(fixed_joint.GetBody1Rel().GetTargets(), [body2_prim.GetPath()])

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
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        # Check that joint group is authored
        joint0: Usd.Prim = stage.GetPrimAtPath("/hinge_joints/Geometry/body1/body2/PhysicsRevoluteJoint")
        self.assertEqual(joint0.GetAttribute("mjc:group").Get(), 0)
        joint2: Usd.Prim = stage.GetPrimAtPath("/hinge_joints/Geometry/body3/body4/PhysicsRevoluteJoint")
        self.assertEqual(joint2.GetAttribute("mjc:group").Get(), 2)

    def test_auto_limits(self):
        # Test with autolimits="true"
        model = pathlib.Path("./tests/data/joint_limits.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

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
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

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
