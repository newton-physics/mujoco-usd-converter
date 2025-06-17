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

    def assert_rotation_almost_equal(self, rot1: Gf.Rotation, rot2: Gf.Rotation, tolerance: float):
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
