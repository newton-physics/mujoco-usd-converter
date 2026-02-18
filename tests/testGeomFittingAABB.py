# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import omni.asset_validator
import usdex.core
from pxr import Gf, Sdf, Tf, Usd, UsdGeom

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestGeomFittingAABB(ConverterTestCase):
    def setUp(self):
        super().setUp()
        model = pathlib.Path("./tests/data/geoms_fitting_aabb.xml")
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Parent body name not found.*"),
                (Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Unsupported or unknown geom type mjtGeom.mjGEOM_ELLIPSOID for geom 'ellipsoid'"),
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

        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_ellipsoid_no_transform/ellipsoid_visual"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Mesh))

    def test_no_body_name(self):
        # If the body name is not specified.
        default_prim = self.stage.GetDefaultPrim()

        prim_path = f"{default_prim.GetPath()}/Geometry/Body/complex_cube"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Mesh))

        prim_path = f"{default_prim.GetPath()}/Geometry/Body/Box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

    def test_use_geom_name(self):
        # When specifying a geom name.
        default_prim = self.stage.GetDefaultPrim()

        prim_path = f"{default_prim.GetPath()}/Geometry/use_geom_name/geom_complex_cube_visual"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Mesh))

        prim_path = f"{default_prim.GetPath()}/Geometry/use_geom_name/geom_complex_cube"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

    def test_geom_fitting_box(self):
        default_prim = self.stage.GetDefaultPrim()

        # When not using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_no_transform/box"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)

        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.7532054, 0.75478935, 0.76835316), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04823722128442205, 0.4989525530226528, -0.006278505815367666), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_transform/box_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.7532054, 0.75478935, 0.76835316), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14747536245281256, -0.010599014694299781, -0.0010474469773470996), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_fitscale/box_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.9038465, 0.9057472, 0.9220238), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04747536245281256, -0.010599014694299781, 0.4989525530226529), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_scaled_x/box_scaled_x"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_scaled_y/box_scaled_y"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_scaled_z/box_scaled_z"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_no_transform/sphere"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.7683531441266045, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04823722128442205, 0.4989525530226528, -0.006278505815367666), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_transform/sphere_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.7683531441266045, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14747536245281256, -0.010599014694299781, -0.0010474469773470996), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_fitscale/sphere_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.9220237729519254, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04747536245281256, -0.010599014694299781, 0.4989525530226529), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_x/sphere_scaled_x"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.6000000000000024, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0, 0.70710677, 0, 0.70710677))

        # A box scaled non-uniformly in XYZ. Long in the Y direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_y/sphere_scaled_y"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.6000000000000015, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.5, 0.5, -0.5, 0.5))

        # A box scaled non-uniformly in XYZ. Long in the Z direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_z/sphere_scaled_z"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.6000000000000008, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.70710677, 0, 0, 0.70710677))

    def test_geom_fitting_cylinder(self):
        default_prim = self.stage.GetDefaultPrim()

        # When not using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_no_transform/cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.7547893248064179, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.536706288253209, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04823722128442205, 0.4989525530226528, -0.006278505815367666), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_transform/cylinder_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.7547893248064179, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.536706288253209, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14747536245281256, -0.010599014694299781, -0.0010474469773470996), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_fitscale/cylinder_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.9057471897677014, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.8440475459038508, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04747536245281256, -0.010599014694299781, 0.4989525530226529), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_x/cylinder_scaled_x"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.1500000000000006, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.2000000000000048, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0, 0.70710677, 0, 0.70710677))

        # A box scaled non-uniformly in XYZ. Long in the y direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_y/cylinder_scaled_y"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.15000000000000038, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.200000000000003, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.5, 0.5, -0.5, 0.5))

        # A box scaled non-uniformly in XYZ. Long in the z direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_z/cylinder_scaled_z"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.1500000000000002, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.2000000000000015, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.70710677, 0, 0, 0.70710677))

    def test_geom_fitting_capsule(self):
        default_prim = self.stage.GetDefaultPrim()

        # When not using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_no_transform/capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.7547893248064179, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.027127638640373153, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04823722128442205, 0.4989525530226528, -0.006278505815367666), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_with_transform/capsule_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.7547893248064179, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.027127638640373153, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14747536245281256, -0.010599014694299781, -0.0010474469773470996), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_with_fitscale/capsule_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.9057471897677014, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.03255316636844778, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.04747536245281256, -0.010599014694299781, 0.4989525530226529), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_x/capsule_scaled_x"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.1500000000000006, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.9000000000000037, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0, 0.70710677, 0, 0.70710677))

        # A box scaled non-uniformly in XYZ. Long in the Y direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_y/capsule_scaled_y"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.15000000000000038, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.9000000000000024, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.5, 0.5, -0.5, 0.5))

        # A box scaled non-uniformly in XYZ. Long in the Z direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_z/capsule_scaled_z"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.1500000000000002, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.9000000000000011, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0, 0, 0), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.70710677, 0, 0, 0.70710677))
