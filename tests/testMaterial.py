# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib

import usdex.core
import usdex.test
from pxr import Gf, Sdf, Tf, Usd, UsdShade

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestMaterial(ConverterTestCase):
    def setUp(self):
        super().setUp()
        model_path = pathlib.Path("./tests/data/materials.xml")
        self.model_name = model_path.stem
        self.output_dir = pathlib.Path(self.tmpDir())
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*will discard textures at render time")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model_path, self.output_dir)
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(self.stage)

    def _get_shader(self, material_name: str) -> UsdShade.Shader:
        material_prim = self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/{material_name}")
        self.assertTrue(material_prim)
        return usdex.core.computeEffectivePreviewSurfaceShader(UsdShade.Material(material_prim))

    def _get_input_value(self, shader: UsdShade.Shader, input_name: str):
        value_attrs = UsdShade.Utils.GetValueProducingAttributes(shader.GetInput(input_name))

        # The values are defined in the material interface, not in the shader
        self.assertEqual(value_attrs[0].GetPrim(), shader.GetPrim().GetParent())

        return value_attrs[0].Get()

    def test_metallic_material(self):
        shader = self._get_shader("BlueMetallic")
        self.assertEqual(self._get_input_value(shader, "diffuseColor"), Gf.Vec3f(0, 0, 1))
        self.assertEqual(self._get_input_value(shader, "opacity"), 1)
        self.assertAlmostEqual(self._get_input_value(shader, "roughness"), 0.7)
        self.assertAlmostEqual(self._get_input_value(shader, "metallic"), 0.8)
        self.assertFalse(shader.GetInput("useSpecularWorkflow"))

    def test_specular_material(self):
        # Specular is currently disabled.
        shader = self._get_shader("GreenSpecular")
        self.assertFalse(shader.GetInput("useSpecularWorkflow"))

    def test_emissive_material(self):
        shader = self._get_shader("RedEmissive")
        self.assertEqual(self._get_input_value(shader, "diffuseColor"), Gf.Vec3f(1, 0, 0))
        self.assertEqual(self._get_input_value(shader, "emissiveColor"), Gf.Vec3f(0.5, 0, 0))

    def test_textured_material(self):
        shader = self._get_shader("Grid")
        texture_input: UsdShade.Input = shader.GetInput("diffuseColor")
        self.assertTrue(texture_input.HasConnectedSource())

        # Check that the texture file was copied and is referenced correctly
        texture_path = self.output_dir / "Payload" / "Textures" / "grid.png"
        self.assertTrue(texture_path.exists())

        # Check that the connected source is a relative asset path to the expected texture
        connected_source = texture_input.GetConnectedSource()
        texture_shader = UsdShade.Shader(connected_source[0].GetPrim())
        self.assertEqual(self._get_input_value(texture_shader, "file").path, "./Textures/grid.png")

    def test_material_binding(self):
        textured_box_prim = self.stage.GetPrimAtPath(f"/{self.model_name}/Geometry/TexturedBox")
        self.assertTrue(textured_box_prim)
        material_binding = UsdShade.MaterialBindingAPI(textured_box_prim)
        self.assertTrue(material_binding)
        self.assertTrue(material_binding.GetDirectBindingRel())
        self.assertEqual(len(material_binding.GetDirectBindingRel().GetTargets()), 1)
        bound_material = material_binding.GetDirectBindingRel().GetTargets()[0]
        material = UsdShade.Material(self.stage.GetPrimAtPath(bound_material))
        self.assertTrue(material)
        self.assertEqual(material.GetPrim().GetName(), "Grid")
        self.assertEqual(material.GetPrim().GetParent(), self.stage.GetPrimAtPath(f"/{self.model_name}/Materials"))
        # materials are references to the material library layer
        self.assertTrue(material.GetPrim().HasAuthoredReferences())

    def test_instanceable_material(self):
        shader = self._get_shader("BlueMetallic")
        self.assertTrue(shader)
        material_prim = shader.GetPrim().GetParent()
        self.assertTrue(material_prim)
        self.assertTrue(material_prim.GetPrim().IsInstanceable())
        self.assertTrue(material_prim.GetPrim().IsInstance())
        self.assertTrue(shader.GetPrim().IsInstanceProxy())

    def test_unnamed_texture_material(self):
        shader = self._get_shader("UnnamedTexture")
        self.assertTrue(shader)
        texture_input: UsdShade.Input = shader.GetInput("diffuseColor")
        self.assertTrue(texture_input.HasConnectedSource())

        connected_source = texture_input.GetConnectedSource()
        texture_shader = UsdShade.Shader(connected_source[0].GetPrim())
        self.assertEqual(self._get_input_value(texture_shader, "file").path, "./Textures/grid.png")

    def test_material_color_space(self):
        shader = self._get_shader("Gray")
        diffuse_color = self._get_input_value(shader, "diffuseColor")
        diffuse_color = usdex.core.linearToSrgb(diffuse_color)
        self.assertTrue(Gf.IsClose(diffuse_color, Gf.Vec3f(0.7, 0.7, 0.7), 1e-6))
        self.assertFalse(shader.GetInput("emissiveColor"))

        shader = self._get_shader("DarkGreen")
        diffuse_color = self._get_input_value(shader, "diffuseColor")
        diffuse_color = usdex.core.linearToSrgb(diffuse_color)
        self.assertTrue(Gf.IsClose(diffuse_color, Gf.Vec3f(0.1, 0.7, 0.0), 1e-6))
        emissive_color = self._get_input_value(shader, "emissiveColor")
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(emissive_color / 0.1), diffuse_color, 1e-6))

        shader = self._get_shader("SkyBlue")
        diffuse_color = self._get_input_value(shader, "diffuseColor")
        diffuse_color = usdex.core.linearToSrgb(diffuse_color)
        self.assertTrue(Gf.IsClose(diffuse_color, Gf.Vec3f(0.3, 0.8, 0.9), 1e-6))
        emissive_color = self._get_input_value(shader, "emissiveColor")
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(emissive_color / 0.2), diffuse_color, 1e-6))
