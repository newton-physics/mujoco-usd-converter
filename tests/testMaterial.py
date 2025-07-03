# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pathlib
import shutil
import unittest

import usdex.core
from pxr import Gf, Sdf, Usd, UsdShade

import mjc_usd_converter


class TestMaterial(unittest.TestCase):
    def setUp(self):
        model_path = pathlib.Path("./tests/data/materials.xml")
        self.model_name = model_path.stem
        self.output_dir = pathlib.Path(f"tests/output/{self.model_name}")
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model_path, self.output_dir)
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)

    def tearDown(self):
        self.stage = None
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    def _get_shader(self, material_name: str) -> UsdShade.Shader:
        material_prim = self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/{material_name}")
        self.assertTrue(material_prim)
        return usdex.core.computeEffectivePreviewSurfaceShader(UsdShade.Material(material_prim))

    def test_metallic_material(self):
        shader = self._get_shader("BlueMetallic")
        self.assertEqual(shader.GetInput("diffuseColor").Get(), Gf.Vec3f(0, 0, 1))
        self.assertEqual(shader.GetInput("opacity").Get(), 1)
        self.assertAlmostEqual(shader.GetInput("roughness").Get(), 0.7)
        self.assertAlmostEqual(shader.GetInput("metallic").Get(), 0.8)
        self.assertFalse(shader.GetInput("useSpecularWorkflow"))

    def test_specular_material(self):
        shader = self._get_shader("GreenSpecular")
        self.assertEqual(shader.GetInput("useSpecularWorkflow").Get(), 1)
        self.assertAlmostEqual(shader.GetInput("specularColor").Get(), Gf.Vec3f(0.8))

    def test_emissive_material(self):
        shader = self._get_shader("RedEmissive")
        self.assertEqual(shader.GetInput("emissiveColor").Get(), Gf.Vec3f(0.5))

    def test_textured_material(self):
        shader = self._get_shader("Grid")
        texture_input: UsdShade.Input = shader.GetInput("diffuseColor")
        self.assertTrue(texture_input.HasConnectedSource())

        # Check that the texture file was copied and is referenced correctly
        texture_path = self.output_dir / "payload" / "Textures" / "grid.png"
        self.assertTrue(texture_path.exists())

        # Check that the connected source is a relative asset path to the expected texture
        connected_source = texture_input.GetConnectedSource()
        texture_prim = connected_source[0].GetPrim()
        texture_file_attr = texture_prim.GetAttribute("inputs:file")
        self.assertEqual(texture_file_attr.Get().path, "./Textures/grid.png")

    def test_material_binding(self):
        textured_box_prim = self.stage.GetPrimAtPath(f"/{self.model_name}/Geometry/TexturedBox")
        self.assertTrue(textured_box_prim)
        material_binding = UsdShade.MaterialBindingAPI(textured_box_prim)
        self.assertEqual(len(material_binding.GetDirectBindingRel().GetTargets()), 1)
        bound_material = material_binding.GetDirectBindingRel().GetTargets()[0]
        material = UsdShade.Material(self.stage.GetPrimAtPath(bound_material))
        self.assertTrue(material)
        self.assertEqual(material.GetPrim().GetName(), "Grid")
        self.assertEqual(material.GetPrim().GetParent(), self.stage.GetPrimAtPath(f"/{self.model_name}/Materials"))
        # materials are references to the material library layer
        self.assertTrue(material.GetPrim().GetReferences())
