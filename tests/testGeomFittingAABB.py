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
        self.assertTrue(Gf.IsClose(scale, (0.8559072, 0.7781741, 0.70797443), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.005380221417930632, 0.4999997998975669, -0.004139026615141719), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.11115205, 0.86828923, 0.22571543, 0.42751792))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_transform/box_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.8559072, 0.7781741, 0.70797443), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.10647141846274108, 0.0020491624891415972, -2.0010243301227248e-7), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_fitscale/box_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1.0270886, 0.93380886, 0.8495693), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.006471418462741075, 0.0020491624891415972, 0.499999799897567), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

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
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.8559072194762076, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.005380221417930632, 0.4999997998975669, -0.004139026615141719), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.11115205, 0.86828923, 0.22571543, 0.42751792))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_transform/sphere_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.8559072194762076, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.10647141846274108, 0.0020491624891415972, -2.0010243301227248e-7), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_fitscale/sphere_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 1.027088663371449, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.006471418462741075, 0.0020491624891415972, 0.499999799897567), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

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
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.8559072194762076, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.4159488607901767, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.005380221417930632, 0.4999997998975669, -0.004139026615141719), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.11115205, 0.86828923, 0.22571543, 0.42751792))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_transform/cylinder_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.8559072194762076, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.4159488607901767, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.10647141846274108, 0.0020491624891415972, -2.0010243301227248e-7), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_fitscale/cylinder_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 1.027088663371449, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.6991386329482119, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.006471418462741075, 0.0020491624891415972, 0.499999799897567), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.44702968, 0.65726686, -0.26079687, 0.54785925))

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

    # TODO: When fitaabb="true", the capsule causes a compile-time error (MuJoCo 3.5.0).
    # We have not yet included tests for the capsule case here.
