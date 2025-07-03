# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

from pxr import Sdf, Usd, UsdPhysics, UsdShade

import mjc_usd_converter


class TestPhysicsMaterials(unittest.TestCase):
    def tearDown(self):
        if pathlib.Path("./tests/output").exists():
            shutil.rmtree("./tests/output")

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
        self.assertEqual(
            set(phys_mat_1.GetPrim().GetAuthoredPropertyNames()),
            {"physics:dynamicFriction", "mjc:friction:rolling", "mjc:friction:torsional"},
        )
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
