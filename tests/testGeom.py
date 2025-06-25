# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

import usdex.core
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade

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

    def test_physics_materials(self):
        model = pathlib.Path("./tests/data/physics_materials.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"./tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        prim1 = stage.GetPrimAtPath("/physics_materials/Geometry/custom_friction_1")
        prim2 = stage.GetPrimAtPath("/physics_materials/Geometry/custom_friction_2")
        prim3 = stage.GetPrimAtPath("/physics_materials/Geometry/different_friction")
        prim4 = stage.GetPrimAtPath("/physics_materials/Geometry/default_friction")

        # Get material bindings
        binding_api_1 = UsdShade.MaterialBindingAPI(prim1)
        binding_api_2 = UsdShade.MaterialBindingAPI(prim2)
        binding_api_3 = UsdShade.MaterialBindingAPI(prim3)
        binding_api_4 = UsdShade.MaterialBindingAPI(prim4)

        # Check Physics Bindings
        phys_binding_1 = binding_api_1.GetDirectBinding(materialPurpose="physics")
        phys_binding_2 = binding_api_2.GetDirectBinding(materialPurpose="physics")
        phys_binding_3 = binding_api_3.GetDirectBinding(materialPurpose="physics")
        phys_binding_4 = binding_api_4.GetDirectBinding(materialPurpose="physics")

        # Assert that geoms with same friction reuse the same material
        self.assertEqual(phys_binding_1.GetMaterialPath(), phys_binding_2.GetMaterialPath())
        self.assertNotEqual(phys_binding_1.GetMaterialPath(), phys_binding_3.GetMaterialPath())
        self.assertTrue(stage.GetPrimAtPath(phys_binding_4.GetMaterialPath()).IsValid())

        # Check Visual Bindings
        vis_binding_1 = binding_api_1.GetDirectBinding()
        vis_binding_2 = binding_api_2.GetDirectBinding()
        vis_binding_3 = binding_api_3.GetDirectBinding()
        vis_binding_4 = binding_api_4.GetDirectBinding()  # Should be empty

        self.assertTrue(stage.GetPrimAtPath(vis_binding_1.GetMaterialPath()).IsValid())
        self.assertEqual(vis_binding_1.GetMaterialPath(), vis_binding_2.GetMaterialPath())
        self.assertNotEqual(vis_binding_1.GetMaterialPath(), vis_binding_3.GetMaterialPath())
        self.assertFalse(stage.GetPrimAtPath(vis_binding_4.GetMaterialPath()).IsValid())

        # Assert that the visual and physics materials are distinct
        self.assertNotEqual(phys_binding_1.GetMaterialPath(), vis_binding_1.GetMaterialPath())

        # Assert values on the first custom physics material
        material_1_prim = stage.GetPrimAtPath(phys_binding_1.GetMaterialPath())
        phys_mat_1 = UsdPhysics.MaterialAPI(material_1_prim)
        self.assertAlmostEqual(phys_mat_1.GetDynamicFrictionAttr().Get(), 0.8)
        self.assertAlmostEqual(phys_mat_1.GetPrim().GetAttribute("mjc:friction:torsional").Get(), 0.1)
        self.assertAlmostEqual(phys_mat_1.GetPrim().GetAttribute("mjc:friction:rolling").Get(), 0.05)

        # Assert there are the correct number of materials in the dedicated scope
        materials_scope = stage.GetPrimAtPath("/physics_materials/Materials")
        # 2 visual materials + 3 physics materials
        self.assertEqual(len(materials_scope.GetChildren()), 5)

        # Assert that the physics materials are in the physics layer
        physics_layer_path = pathlib.Path(f"./tests/output/{model_name}/payload/Physics.usda").absolute()
        self.assertTrue(physics_layer_path.exists(), msg=f"Physics layer not found at {physics_layer_path}")
        physics_stage: Usd.Stage = Usd.Stage.Open(physics_layer_path.as_posix())
        physics_materials_scope = physics_stage.GetPrimAtPath("/physics_materials/Materials")
        self.assertEqual(len(physics_materials_scope.GetChildren()), 3)

        # Assert that the visual materials are in the materials layer
        materials_layer_path = pathlib.Path(f"./tests/output/{model_name}/payload/Materials.usda").absolute()
        self.assertTrue(materials_layer_path.exists(), msg=f"Materials layer not found at {materials_layer_path}")
        materials_stage: Usd.Stage = Usd.Stage.Open(materials_layer_path.as_posix())
        visual_materials_scope = materials_stage.GetPrimAtPath("/physics_materials/Materials")
        self.assertEqual(len(visual_materials_scope.GetChildren()), 2)
