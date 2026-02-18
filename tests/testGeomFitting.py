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
        self.assertTrue(Gf.IsClose(scale, (0.48377457, 0.49567172, 0.6591854), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03996189659229483, 0.5015098822207877, -0.02410985048867517), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_transform/box_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.48377457, 0.49567172, 0.6591854), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14579810132345178, 0.008987323573032321, 0.0015098822207878504), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_box_with_fitscale/box_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cube))

        cube = UsdGeom.Cube(prim)
        self.assertEqual(cube.GetSizeAttr().Get(), 2)
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (0.58052945, 0.5948061, 0.79102254), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.045798101323451766, 0.008987323573032321, 0.5015098822207879), 1e-6))
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
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.5462105768323134, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03996189659229483, 0.5015098822207877, -0.02410985048867517), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_transform/sphere_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.5462105768323134, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14579810132345178, 0.008987323573032321, 0.0015098822207878504), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_with_fitscale/sphere_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Sphere))

        sphere = UsdGeom.Sphere(prim)
        self.assertTrue(Gf.IsClose(sphere.GetRadiusAttr().Get(), 0.6554526921987761, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.045798101323451766, 0.008987323573032321, 0.5015098822207879), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_x/sphere_scaled_x"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_y/sphere_scaled_y"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_sphere_scaled_z/sphere_scaled_z"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_no_transform/cylinder"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.4897231473880021, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.318370871441872, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03996189659229483, 0.5015098822207877, -0.02410985048867517), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_transform/cylinder_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.4897231473880021, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.318370871441872, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14579810132345178, 0.008987323573032321, 0.0015098822207878504), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_with_fitscale/cylinder_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Cylinder))

        cylinder = UsdGeom.Cylinder(prim)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(cylinder.GetRadiusAttr().Get(), 0.5876677768656025, 1e-6))
        self.assertTrue(Gf.IsClose(cylinder.GetHeightAttr().Get(), 1.5820450457302464, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.045798101323451766, 0.008987323573032321, 0.5015098822207879), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_x/cylinder_scaled_x"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_y/cylinder_scaled_y"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_cylinder_scaled_z/cylinder_scaled_z"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_no_transform/capsule"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.4897231473880021, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.8286477240538699, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.03996189659229483, 0.5015098822207877, -0.02410985048867517), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(0.31025994, 0.6706377, 0.3387701, 0.58242476))

        # When using transform(pos, quat) in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_with_transform/capsule_with_transform"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.4897231473880021, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.8286477240538699, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.14579810132345178, 0.008987323573032321, 0.0015098822207878504), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # When using transform(quat) and fitscale in geom.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_with_fitscale/capsule_with_fitscale"
        prim = self.stage.GetPrimAtPath(prim_path)
        self.assertTrue(prim)
        self.assertTrue(prim.IsA(UsdGeom.Capsule))

        capsule = UsdGeom.Capsule(prim)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertTrue(Gf.IsClose(capsule.GetRadiusAttr().Get(), 0.5876677768656025, 1e-6))
        self.assertTrue(Gf.IsClose(capsule.GetHeightAttr().Get(), 0.9943772688646438, 1e-6))
        translation, pivot, quat, scale = usdex.core.getLocalTransformComponentsQuat(prim)
        self.assertTrue(Gf.IsClose(scale, (1, 1, 1), 1e-6))
        self.assertTrue(Gf.IsClose(translation, (0.045798101323451766, 0.008987323573032321, 0.5015098822207879), 1e-6))
        self.assertRotationsAlmostEqual(quat, Gf.Quatf(-0.1378371, 0.65314186, -0.29012004, 0.68573827))

        # A box scaled non-uniformly in XYZ. Long in the X direction.
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_x/capsule_scaled_x"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_y/capsule_scaled_y"
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
        prim_path = f"{default_prim.GetPath()}/Geometry/fitting_capsule_scaled_z/capsule_scaled_z"
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
