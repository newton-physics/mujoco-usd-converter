# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib

import usdex.core
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, Vt

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestGeom(ConverterTestCase):
    def setUp(self):
        super().setUp()
        model = pathlib.Path("./tests/data/geoms.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(self.stage)

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

    def test_group(self):
        default_prim = self.stage.GetPrimAtPath("/geoms/Geometry/default_collider")
        self.assertFalse(default_prim.HasAPI("MjcImageableAPI"))
        self.assertTrue(default_prim.HasAPI("MjcCollisionAPI"))
        self.assertEqual(default_prim.GetAttribute("mjc:group").HasAuthoredValue(), False)
        self.assertEqual(default_prim.GetAttribute("mjc:group").Get(), 0)

        visual_prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual")
        self.assertTrue(visual_prim.HasAPI("MjcImageableAPI"))
        self.assertFalse(visual_prim.HasAPI("MjcCollisionAPI"))
        self.assertEqual(visual_prim.GetAttribute("mjc:group").Get(), 1)

        guide_prim = self.stage.GetPrimAtPath("/geoms/Geometry/guide_visual")
        self.assertTrue(guide_prim.HasAPI("MjcImageableAPI"))
        self.assertFalse(guide_prim.HasAPI("MjcCollisionAPI"))
        self.assertEqual(guide_prim.GetAttribute("mjc:group").Get(), 3)

        guide_mesh_collider_prim = self.stage.GetPrimAtPath("/geoms/Geometry/guide_mesh_collider")
        self.assertFalse(guide_mesh_collider_prim.HasAPI("MjcImageableAPI"))
        self.assertTrue(guide_mesh_collider_prim.HasAPI("MjcCollisionAPI"))
        self.assertEqual(guide_mesh_collider_prim.GetAttribute("mjc:group").Get(), 3)

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

    def test_mjc_mesh_collision_schema(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/all_mesh_collision_properties")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MeshCollisionAPI))
        self.assertTrue(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMeshCollisionAPI")))

        # Check that mjc:inertia attribute is authored and has the correct value
        self.assertTrue(prim.GetAttribute("mjc:inertia").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:inertia").Get(), "convex")

        # Check that mjc:maxhullvert attribute is authored and has the correct value
        self.assertTrue(prim.GetAttribute("mjc:maxhullvert").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:maxhullvert").Get(), 100)

        # Check that all MJC properties are authored
        for property in prim.GetPropertiesInNamespace("mjc"):
            # skip shellinertia as it is not applicable to mesh colliders
            if property.GetName() == "mjc:shellinertia":
                self.assertFalse(property.HasAuthoredValue(), f"Property {property.GetName()} should not be authored")
            else:
                self.assertTrue(property.HasAuthoredValue(), f"Property {property.GetName()} is not authored")

        # Check that the mesh collision properties are not applied when at default values
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/guide_mesh_collider")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MeshCollisionAPI))
        self.assertFalse(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMeshCollisionAPI")))

        # Check partial collision properties do apply the schema
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/partial_mesh_collision_properties")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MeshCollisionAPI))
        self.assertTrue(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMeshCollisionAPI")))
        self.assertTrue(prim.GetAttribute("mjc:inertia").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:inertia").Get(), "exact")
        self.assertFalse(prim.GetAttribute("mjc:maxhullvert").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:maxhullvert").Get(), -1)
        self.assertTrue(prim.GetAttribute("mjc:condim").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:condim").Get(), 4)
        self.assertTrue(prim.GetAttribute("mjc:gap").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:gap").Get(), 0.02)

        # Check default collision properties do not apply the schema
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/default_mesh_collision_properties")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MeshCollisionAPI))
        self.assertFalse(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMeshCollisionAPI")))

        # Check shell inertia properties do apply the schema
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/shell_mesh_collision_properties")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MeshCollisionAPI))
        self.assertTrue(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsMeshCollisionAPI")))
        self.assertTrue(prim.GetAttribute("mjc:inertia").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:inertia").Get(), "shell")
        self.assertFalse(prim.GetAttribute("mjc:maxhullvert").HasAuthoredValue())
        self.assertEqual(prim.GetAttribute("mjc:maxhullvert").Get(), -1)
        self.assertFalse(prim.GetAttribute("mjc:shellinertia").HasAuthoredValue())

    def test_mjc_collision_schema_defaults(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/default_collider")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsCollisionAPI")))

        # Check that no MJC properties are authored
        for property in prim.GetPropertiesInNamespace("mjc"):
            self.assertFalse(property.HasAuthoredValue(), f"Property {property.GetName()} should not be authored")

        # Check that all MJC properties have default values
        self.assertEqual(prim.GetAttribute("mjc:condim").Get(), 3)
        self.assertEqual(prim.GetAttribute("mjc:gap").Get(), 0.0)
        self.assertEqual(prim.GetAttribute("mjc:group").Get(), 0)
        self.assertEqual(prim.GetAttribute("mjc:margin").Get(), 0.0)
        self.assertEqual(prim.GetAttribute("mjc:priority").Get(), 0)
        self.assertEqual(prim.GetAttribute("mjc:shellinertia").Get(), False)
        self.assertEqual(prim.GetAttribute("mjc:solimp").Get(), [0.9, 0.95, 0.001, 0.5, 2.0])
        self.assertEqual(prim.GetAttribute("mjc:solmix").Get(), 1.0)
        self.assertEqual(prim.GetAttribute("mjc:solref").Get(), [0.02, 1.0])

    def test_mjc_collision_schema_authored(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/all_collision_properties")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsCollisionAPI")))

        # Check that all MJC properties are authored
        for property in prim.GetPropertiesInNamespace("mjc"):
            self.assertTrue(property.HasAuthoredValue(), f"Property {property.GetName()} is not authored")

        # Check that all MJC properties have the correct values
        self.assertEqual(prim.GetAttribute("mjc:condim").Get(), 4)
        self.assertEqual(prim.GetAttribute("mjc:gap").Get(), 0.02)
        self.assertEqual(prim.GetAttribute("mjc:group").Get(), 1)
        self.assertEqual(prim.GetAttribute("mjc:margin").Get(), 0.01)
        self.assertEqual(prim.GetAttribute("mjc:priority").Get(), 2)
        self.assertEqual(prim.GetAttribute("mjc:shellinertia").Get(), True)
        self.assertEqual(prim.GetAttribute("mjc:solimp").Get(), [0.95, 0.99, 0.001, 0.5, 2.0])
        self.assertEqual(prim.GetAttribute("mjc:solmix").Get(), 0.9)
        self.assertEqual(prim.GetAttribute("mjc:solref").Get(), [0.05, 1.0])
