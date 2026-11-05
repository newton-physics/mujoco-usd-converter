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
        self.assertTrue(Gf.IsClose(self._get_input_value(shader, "diffuseColor"), Gf.Vec3f(0, 0, 1), 1e-6))
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
        self.assertTrue(Gf.IsClose(self._get_input_value(shader, "diffuseColor"), Gf.Vec3f(1, 0, 0), 1e-6))
        # MuJoCo displays emission times the authored sRGB color
        emissive_color = usdex.core.linearToSrgb(self._get_input_value(shader, "emissiveColor"))
        self.assertTrue(Gf.IsClose(emissive_color, Gf.Vec3f(0.5, 0, 0), 1e-6))

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
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(emissive_color), 0.1 * diffuse_color, 1e-6))

        shader = self._get_shader("SkyBlue")
        diffuse_color = self._get_input_value(shader, "diffuseColor")
        diffuse_color = usdex.core.linearToSrgb(diffuse_color)
        self.assertTrue(Gf.IsClose(diffuse_color, Gf.Vec3f(0.3, 0.8, 0.9), 1e-6))
        emissive_color = self._get_input_value(shader, "emissiveColor")
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(emissive_color), 0.2 * diffuse_color, 1e-6))

    def _get_openpbr_input_value(self, material_name: str, input_name: str):
        material_prim = self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/{material_name}")
        shader = usdex.core.computeEffectiveMtlxSurfaceShader(UsdShade.Material(material_prim))
        self.assertEqual(shader.GetShaderId(), "ND_open_pbr_surface_surfaceshader")
        return self._get_input_value(shader, input_name)

    def test_openpbr_material(self):
        """OpenPBR inputs should be driven by the same Material Interface as the UsdPreviewSurface inputs."""
        self.assertTrue(Gf.IsClose(self._get_openpbr_input_value("BlueMetallic", "base_color"), Gf.Vec3f(0, 0, 1), 1e-6))
        self.assertAlmostEqual(self._get_openpbr_input_value("BlueMetallic", "base_metalness"), 0.8)
        self.assertAlmostEqual(self._get_openpbr_input_value("BlueMetallic", "specular_roughness"), 0.7)
        self.assertEqual(self._get_openpbr_input_value("BlueMetallic", "geometry_opacity"), 1)

    def test_openpbr_default_roughness(self):
        """Materials without shininess should keep the UsdPreviewSurface default roughness in both shaders."""
        self.assertAlmostEqual(self._get_input_value(self._get_shader("GreenSpecular"), "roughness"), 0.5)
        self.assertAlmostEqual(self._get_openpbr_input_value("GreenSpecular", "specular_roughness"), 0.5)

    def test_openpbr_emission(self):
        """Emissive colors should drive the OpenPBR emission at the default luminance."""
        emission_color = usdex.core.linearToSrgb(self._get_openpbr_input_value("RedEmissive", "emission_color"))
        self.assertTrue(Gf.IsClose(emission_color, Gf.Vec3f(0.5, 0, 0), 1e-6))
        self.assertAlmostEqual(self._get_openpbr_input_value("RedEmissive", "emission_luminance"), 1000.0)

    def test_openpbr_texture(self):
        """Textures should drive both shaders from the same Material Interface input."""
        material = UsdShade.Material(self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/Grid"))
        self.assertEqual(material.GetInput("ColorTexture").Get().path, "./Textures/grid.png")
        shader = usdex.core.computeEffectiveMtlxSurfaceShader(material)
        source = shader.GetInput("base_color").GetConnectedSource()
        self.assertTrue(source)
        self.assertEqual(UsdShade.Shader(source[0].GetPrim()).GetShaderId(), "ND_tiledimage_color3")


class TestPreviewMaterial(ConverterTestCase):
    """Disabling OpenPBR should author visual materials with only a UsdPreviewSurface shader."""

    def setUp(self):
        super().setUp()
        model_path = pathlib.Path("./tests/data/materials.xml")
        self.model_name = model_path.stem
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*will discard textures at render time")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter(openpbr=False).convert(model_path, self.tmpDir())
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(self.stage)

    def test_preview_only(self):
        """Every material should have a UsdPreviewSurface shader and no MaterialX shader."""
        materials = [UsdShade.Material(prim) for prim in self.stage.GetPrimAtPath(f"/{self.model_name}/Materials").GetChildren()]
        self.assertGreater(len(materials), 0)
        for material in materials:
            self.assertTrue(usdex.core.computeEffectivePreviewSurfaceShader(material), msg=material.GetPath())
            self.assertFalse(material.GetSurfaceOutput("mtlx"), msg=material.GetPath())
            self.assertFalse(material.GetPrim().HasAPI("MaterialXConfigAPI"), msg=material.GetPath())

    def test_preview_values(self):
        """UsdPreviewSurface values should come from the Material Interface."""
        material = UsdShade.Material(self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/RedEmissive"))
        shader = usdex.core.computeEffectivePreviewSurfaceShader(material)
        diffuse = UsdShade.Utils.GetValueProducingAttributes(shader.GetInput("diffuseColor"))[0]
        emissive = UsdShade.Utils.GetValueProducingAttributes(shader.GetInput("emissiveColor"))[0]
        self.assertEqual(diffuse.GetPrim(), material.GetPrim())
        self.assertTrue(Gf.IsClose(diffuse.Get(), Gf.Vec3f(1, 0, 0), 1e-6))
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(emissive.Get()), Gf.Vec3f(0.5, 0, 0), 1e-6))


class TestBrightEmission(ConverterTestCase):
    def test_openpbr_bright_emission(self):
        """Emissive colors brighter than 1.0 should be normalized, with the excess carried by the OpenPBR emission luminance."""
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(pathlib.Path("./tests/data/bright_emission.xml"), self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)
        material = UsdShade.Material(stage.GetPrimAtPath("/bright_emission/Materials/BrightOrange"))
        shader = usdex.core.computeEffectiveMtlxSurfaceShader(material)
        emission_color = UsdShade.Utils.GetValueProducingAttributes(shader.GetInput("emission_color"))[0].Get()
        luminance = UsdShade.Utils.GetValueProducingAttributes(shader.GetInput("emission_luminance"))[0].Get()
        self.assertAlmostEqual(max(emission_color), 1.0, places=6)
        self.assertGreater(luminance, 1000.0)
        expected = usdex.core.sRgbToLinear(2 * Gf.Vec3f(1, 0.5, 0))
        self.assertTrue(Gf.IsClose(emission_color * (luminance / 1000.0), expected, 1e-5))


class TestBuiltinTexture(ConverterTestCase):
    """Only procedural builtin textures are skipped; file backed textures in the same model still convert."""

    def setUp(self):
        super().setUp()
        model_path = pathlib.Path("./tests/data/builtin_textures.xml")
        self.model_name = model_path.stem
        self.output_dir = pathlib.Path(self.tmpDir())
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*Unsupported builtin texture type.*gradient_texture")],
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
        return UsdShade.Utils.GetValueProducingAttributes(shader.GetInput(input_name))[0].Get()

    def _get_diffuse_source_prim(self, material_name: str) -> Usd.Prim:
        # Every preview material connects diffuseColor to its material interface, so the
        # texture is identified by the connected source being a UsdUVTexture reader.
        shader = self._get_shader(material_name)
        connected_source = shader.GetInput("diffuseColor").GetConnectedSource()
        self.assertTrue(connected_source)
        return connected_source[0].GetPrim()

    def test_builtin_texture_is_skipped(self):
        source_prim = self._get_diffuse_source_prim("Gradient")
        self.assertEqual(str(source_prim.GetPath()), f"/{self.model_name}/Materials/Gradient")
        self.assertEqual(source_prim.GetTypeName(), "Material")
        self.assertFalse(self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/Gradient/DiffuseTexture"))

    def test_file_texture_still_converts(self):
        source = UsdShade.Shader(self._get_diffuse_source_prim("Grid"))
        self.assertEqual(source.GetShaderId(), "UsdUVTexture")
        self.assertEqual(self._get_input_value(source, "file").path, "./Textures/grid.png")
        self.assertTrue((self.output_dir / "Payload" / "Textures" / "grid.png").exists())

    def test_only_the_file_texture_is_copied(self):
        textures = sorted(path.name for path in (self.output_dir / "Payload" / "Textures").iterdir())
        self.assertEqual(textures, ["grid.png"])
