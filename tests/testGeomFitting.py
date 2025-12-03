# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import omni.asset_validator
import usdex.core
from pxr import Gf, Sdf, Tf, Usd, UsdGeom

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestGeomFitting(ConverterTestCase):
    def setUp(self):
        super().setUp()
        model = pathlib.Path("./tests/data/geoms_fitting.xml")
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Parent body name not found.*"),
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'Ellipsoid'"),
            ],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)
        # the test data contains unwelded meshes, so we disable the weld checker
        self.validationEngine.disable_rule(omni.asset_validator.WeldChecker)
        self.assertIsValidUsd(self.stage)

    def test_geom_fitting_unsupported(self):
        # Check that no unsupported fitting types are specified.
        default_prim = self.stage.GetDefaultPrim()

        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_ellipsoid_no_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Xform))

        # Since type="ellipsoid" should not have been generated, there are two child prims: "complex_cube" and "PhysicsFixedJoint".
        self.assertEqual(len(prim.GetChildren()), 2)

        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_ellipsoid_no_transform/complex_cube"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Mesh))

    def test_no_body_name(self):
        # If the body name is not specified.
        default_prim = self.stage.GetDefaultPrim()

        prim_path = f"{default_prim.GetPath()}/Geometry/tn__/complex_cube"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Mesh))

        prim_path = f"{default_prim.GetPath()}/Geometry/tn__/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

    def test_use_geom_name(self):
        # When specifying a geom name.
        default_prim = self.stage.GetDefaultPrim()

        prim_path = f"{default_prim.GetPath()}/Geometry/use_geom_name/geom_complex_cube"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Mesh))

        prim_path = f"{default_prim.GetPath()}/Geometry/use_geom_name/geom_complex_cube_collision"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

    def test_geom_fitting_box(self):
        default_prim = self.stage.GetDefaultPrim()

        # When not using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_no_transform/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)

        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.47636932, 0.49139905, 0.5194262), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03074589395921, 0.501516571216, -0.02411530172992), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.11115205, 0.86828923, 0.22571543, 0.42751792))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_transform/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.47636932, 0.49139905, 0.5194262), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.13713980789211, 0.012144646664811, 0.001516571216727), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_fitscale/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.5716432, 0.5896788, 0.62331146), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03713980789211, 0.012144646664811, 0.5015165712167), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_scaled_x/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.1, 0.15, 0.6), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0, 0.70710677, 0, 0.70710677))

        # A box scaled non-uniformly in XYZ. Long in the Y direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_scaled_y/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.1, 0.15, 0.6), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.5, 0.5, -0.5, 0.5))

        # A box scaled non-uniformly in XYZ. Long in the Z direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_scaled_z/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.1, 0.15, 0.6), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.70710677, 0, 0, 0.70710677))

    def test_geom_fitting_fitting_sphere(self):
        default_prim = self.stage.GetDefaultPrim()

        # When not using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_no_transform/Sphere"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.4957315243758671, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03074589395921, 0.501516571216, -0.02411530172992), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.11115205, 0.86828923, 0.22571543, 0.42751792))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_transform/Sphere"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.4957315243758671, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.13713980789211, 0.012144646664811, 0.001516571216727), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_fitscale/Sphere"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.5948778292510405, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03713980789211, 0.012144646664811, 0.5015165712167), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_x/Sphere"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.28333333333333327, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0, 0.70710677, 0, 0.70710677))

        # A box scaled non-uniformly in XYZ. Long in the Y direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_y/Sphere"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.28333333333333327, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.5, 0.5, -0.5, 0.5))

        # A box scaled non-uniformly in XYZ. Long in the Z direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_z/Sphere"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.28333333333333327, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.70710677, 0, 0, 0.70710677))

    def test_geom_fitting_cylinder(self):
        default_prim = self.stage.GetDefaultPrim()

        # When not using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_no_transform/Cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.4838841777760525, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.0388524351509925, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03074589395921, 0.501516571216, -0.02411530172992), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.11115205, 0.86828923, 0.22571543, 0.42751792))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_transform/Cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.4838841777760525, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.0388524351509925, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.1371398078921, 0.01214464666481, 0.00151657121672), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_fitscale/Cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.580661013331263, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.2466229221811909, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03713980789211787, 0.012144646664811277, 0.5015165712167277), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_x/Cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.1250000037252903, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.2000000476837158, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0, 0.70710677, 0, 0.70710677))

        # A box scaled non-uniformly in XYZ. Long in the y direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_y/Cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.12499999999999994, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.2, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.5, 0.5, -0.5, 0.5))

        # A box scaled non-uniformly in XYZ. Long in the z direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_z/Cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.12499999999999997, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.2, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.70710677, 0, 0, 0.70710677))

    def test_geom_fitting_capsule(self):
        default_prim = self.stage.GetDefaultPrim()

        # When not using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_no_transform/Capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.4838841777760525, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.5549682573749399, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03074589395921, 0.501516571216, -0.02411530172992), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.11115205, 0.86828923, 0.22571543, 0.42751792))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_with_transform/Capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.4838841777760525, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.5549682573749399, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.13713980789211788, 0.012144646664811277, 0.001516571216727658), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_with_fitscale/Capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.580661013331263, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.6659619088499279, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03713980789211787, 0.012144646664811277, 0.5015165712167277), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_x/Capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.12499999999999994, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 1.075, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0, 0.70710677, 0, 0.70710677))

        # A box scaled non-uniformly in XYZ. Long in the Y direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_y/Capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.12499999999999994, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 1.075, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.5, 0.5, -0.5, 0.5))

        # A box scaled non-uniformly in XYZ. Long in the Z direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_z/Capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.12499999999999997, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 1.075, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.70710677, 0, 0, 0.70710677))
