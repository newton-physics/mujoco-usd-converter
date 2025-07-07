# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

import usdex.core
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, Vt

import mjc_usd_converter


class TestGeom(unittest.TestCase):
    def setUp(self):
        model = pathlib.Path("./tests/data/geoms.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"./tests/output/{model_name}"))
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)

    def tearDown(self):
        self.stage = None
        if pathlib.Path("./tests/output").exists():
            shutil.rmtree("./tests/output")

    def test_sphere(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/Sphere")
        sphere: UsdGeom.Sphere = UsdGeom.Sphere(prim)
        self.assertTrue(sphere)
        self.assertEqual(sphere.GetRadiusAttr().Get(), 0.1)

    def test_cylinder(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/Cylinder")
        cylinder: UsdGeom.Cylinder = UsdGeom.Cylinder(prim)
        self.assertTrue(cylinder)
        self.assertEqual(cylinder.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertEqual(cylinder.GetRadiusAttr().Get(), 0.1)
        self.assertEqual(cylinder.GetHeightAttr().Get(), 0.4)

    def test_box(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/Box")
        box: UsdGeom.Cube = UsdGeom.Cube(prim)
        self.assertTrue(box)
        self.assertEqual(box.GetSizeAttr().Get(), 2)
        self.assertTrue(Gf.IsClose(usdex.core.getLocalTransform(box.GetPrim()).GetScale(), (0.1, 0.1, 0.1), 1e-6))

    def test_capsule(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/Capsule")
        capsule: UsdGeom.Capsule = UsdGeom.Capsule(prim)
        self.assertTrue(capsule)
        self.assertEqual(capsule.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertEqual(capsule.GetRadiusAttr().Get(), 0.1)
        self.assertEqual(capsule.GetHeightAttr().Get(), 0.4)

    def test_plane(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/Plane")
        plane: UsdGeom.Plane = UsdGeom.Plane(prim)
        self.assertTrue(plane)
        self.assertEqual(plane.GetAxisAttr().Get(), UsdGeom.Tokens.z)
        self.assertEqual(plane.GetWidthAttr().Get(), 20)
        self.assertEqual(plane.GetLengthAttr().Get(), 20)

    def test_display_color(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual")
        sphere: UsdGeom.Sphere = UsdGeom.Sphere(prim)
        self.assertTrue(sphere)
        self.assertEqual(sphere.GetDisplayColorAttr().Get(), Vt.Vec3fArray([Gf.Vec3f(1.0, 0.0, 0.0)]))
        self.assertEqual(sphere.GetDisplayOpacityAttr().Get(), Vt.FloatArray([0.5]))

    def test_purpose(self):
        default_prim = self.stage.GetPrimAtPath("/geoms/Geometry/default_collider")
        self.assertEqual(UsdGeom.Imageable(default_prim).GetPurposeAttr().Get(), UsdGeom.Tokens.default_)

        visual_prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual")
        self.assertEqual(UsdGeom.Imageable(visual_prim).GetPurposeAttr().Get(), UsdGeom.Tokens.default_)

        guide_prim = self.stage.GetPrimAtPath("/geoms/Geometry/guide_visual")
        self.assertEqual(UsdGeom.Imageable(guide_prim).GetPurposeAttr().Get(), UsdGeom.Tokens.guide)

        guide_mesh_collider_prim = self.stage.GetPrimAtPath("/geoms/Geometry/guide_mesh_collider")
        self.assertEqual(UsdGeom.Imageable(guide_mesh_collider_prim).GetPurposeAttr().Get(), UsdGeom.Tokens.guide)

    def test_default_collider(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/default_collider")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        collider_api = UsdPhysics.CollisionAPI(prim)
        # Enabled by default, so attribute should not be authored
        self.assertFalse(collider_api.GetCollisionEnabledAttr().HasAuthoredValue())
        self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))
        self.assertEqual(UsdGeom.Imageable(prim).GetPurposeAttr().Get(), UsdGeom.Tokens.default_)

    def test_visual_geom(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual")
        self.assertFalse(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertEqual(UsdGeom.Imageable(prim).GetPurposeAttr().Get(), UsdGeom.Tokens.default_)

    def test_visual_with_mass(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual_with_mass")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        collider_api = UsdPhysics.CollisionAPI(prim)
        self.assertFalse(collider_api.GetCollisionEnabledAttr().Get())
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 5.0)
        self.assertFalse(mass_api.GetDensityAttr().HasAuthoredValue())
        self.assertEqual(UsdGeom.Imageable(prim).GetPurposeAttr().Get(), UsdGeom.Tokens.default_)

    def test_visual_with_density(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual_with_density")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        collider_api = UsdPhysics.CollisionAPI(prim)
        self.assertFalse(collider_api.GetCollisionEnabledAttr().Get())
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetDensityAttr().Get(), 2000)
        self.assertFalse(mass_api.GetMassAttr().HasAuthoredValue())
        self.assertEqual(UsdGeom.Imageable(prim).GetPurposeAttr().Get(), UsdGeom.Tokens.default_)

    def test_visual_in_range_no_mass(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual_in_range_no_mass")
        self.assertFalse(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertEqual(UsdGeom.Imageable(prim).GetPurposeAttr().Get(), UsdGeom.Tokens.default_)

    def test_guide_visual(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/guide_visual")
        self.assertFalse(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertEqual(UsdGeom.Imageable(prim).GetPurposeAttr().Get(), UsdGeom.Tokens.guide)

    def test_mesh_collider(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/guide_mesh_collider")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MeshCollisionAPI))
        mesh_collider_api = UsdPhysics.MeshCollisionAPI(prim)
        self.assertEqual(mesh_collider_api.GetApproximationAttr().Get(), UsdPhysics.Tokens.convexHull)
        self.assertEqual(UsdGeom.Imageable(prim).GetPurposeAttr().Get(), UsdGeom.Tokens.guide)

    def test_explicit_mass(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/explicit_mass")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 10.0)
        self.assertFalse(mass_api.GetDensityAttr().HasAuthoredValue())

    def test_explicit_density(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/explicit_density")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetDensityAttr().Get(), 3000)
        self.assertFalse(mass_api.GetMassAttr().HasAuthoredValue())

    def test_mass_and_density(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/mass_and_density")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 15.0)
        self.assertAlmostEqual(mass_api.GetDensityAttr().Get(), 4000)

    def test_shell_inertia(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/shell_inertia")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsCollisionAPI")))
        self.assertTrue(prim.GetAttribute("mjc:shellinertia").HasAuthoredValue())
        self.assertTrue(prim.GetAttribute("mjc:shellinertia").Get())
