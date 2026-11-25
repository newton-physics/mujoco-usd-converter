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
        diffuse_color = usdex.core.linearToSrgb(self._get_input_value(shader, "diffuseColor"))
        self.assertTrue(Gf.IsClose(diffuse_color, Gf.Vec3f(0.8, 0.2, 0.1), 1e-6))
        # MuJoCo displays emission times the authored sRGB color
        emissive_color = usdex.core.linearToSrgb(self._get_input_value(shader, "emissiveColor"))
        self.assertTrue(Gf.IsClose(emissive_color, Gf.Vec3f(0.4, 0.1, 0.05), 1e-6))

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
        self.assertTrue(Gf.IsClose(emission_color, Gf.Vec3f(0.4, 0.1, 0.05), 1e-6))
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
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(diffuse.Get()), Gf.Vec3f(0.8, 0.2, 0.1), 1e-6))
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(emissive.Get()), Gf.Vec3f(0.4, 0.1, 0.05), 1e-6))


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
        expected = usdex.core.sRgbToLinear(2 * Gf.Vec3f(0.8, 0.4, 0.2))
        self.assertTrue(Gf.IsClose(emission_color * (luminance / 1000.0), expected, 1e-5))


class TestOutOfRangeMaterial(ConverterTestCase):
    """Out-of-range material values should be clamped with a warning rather than aborting or passing through."""

    openpbr = True

    # The checker matches diagnostics in order, so these follow the material order of the MJCF, and the attribute order within a material:
    # rgba (r, g, b, a), shininess, metallic, emission. Any other warning, such as one for an in-range material, fails the test.
    _SHININESS_NOTE = r".*multiplied by 128.*OpenGL.*1 - shininess.*"
    _EXPECTED_WARNINGS = (
        r".*'HighShininess': shininess=1.5 .*clamped to 1\..*" + _SHININESS_NOTE,
        r".*'LowShininess': shininess=-0.3 .*clamped to 0\..*" + _SHININESS_NOTE,
        r".*'HighMetallic': metallic=1.5 .*clamped to 1\.",
        r".*'LowMetallic': metallic=-0.5 .*clamped to 0\.",
        r".*'HighOpacity': rgba\.a \(opacity\)=1.4 .*clamped to 1\.",
        r".*'LowOpacity': rgba\.a \(opacity\)=-0.2 .*clamped to 0\.",
        r".*'HighRed': rgba\.r=1.5 .*clamped to 1\.",
        r".*'HighGreen': rgba\.g=1.5 .*clamped to 1\.",
        r".*'HighBlue': rgba\.b=1.5 .*clamped to 1\.",
        r".*'LowRed': rgba\.r=-0.5 .*clamped to 0\.",
        r".*'LowGreen': rgba\.g=-0.5 .*clamped to 0\.",
        r".*'LowBlue': rgba\.b=-0.5 .*clamped to 0\.",
        r".*'NegativeEmission': emission=-1 is outside the valid range.*ignored\.",
        r".*'ClampedEmission': rgba\.r=1.5 .*clamped to 1\.",
        r".*'AllOutOfRange': rgba\.r=1.5 .*clamped to 1\.",
        r".*'AllOutOfRange': rgba\.g=-0.5 .*clamped to 0\.",
        r".*'AllOutOfRange': rgba\.b=2 .*clamped to 1\.",
        r".*'AllOutOfRange': rgba\.a \(opacity\)=1.4 .*clamped to 1\.",
        r".*'AllOutOfRange': shininess=2 .*clamped to 1\..*" + _SHININESS_NOTE,
        r".*'AllOutOfRange': metallic=-2 .*clamped to 0\.",
        r".*'AllOutOfRange': emission=-3 is outside the valid range.*ignored\.",
        # the MJCF name is reported even though the USD prim name had to be made safe
        r".*'my material\.1': shininess=1.5 .*clamped to 1\..*" + _SHININESS_NOTE,
    )

    def setUp(self):
        super().setUp()
        model_path = pathlib.Path("./tests/data/out_of_range_materials.xml")
        self.model_name = model_path.stem
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, pattern) for pattern in self._EXPECTED_WARNINGS],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter(openpbr=self.openpbr).convert(model_path, self.tmpDir())
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(self.stage)

    def _get_shader(self, material_name: str) -> UsdShade.Shader:
        material_prim = self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/{material_name}")
        self.assertTrue(material_prim, msg=material_name)
        return usdex.core.computeEffectivePreviewSurfaceShader(UsdShade.Material(material_prim))

    def _get_input_value(self, material_name: str, input_name: str):
        shader = self._get_shader(material_name)
        return UsdShade.Utils.GetValueProducingAttributes(shader.GetInput(input_name))[0].Get()

    def _get_srgb_color(self, material_name: str) -> Gf.Vec3f:
        return usdex.core.linearToSrgb(self._get_input_value(material_name, "diffuseColor"))

    def _assert_color(self, material_name: str, expected: Gf.Vec3f):
        self.assertTrue(Gf.IsClose(self._get_srgb_color(material_name), expected, 1e-5), msg=material_name)

    def test_shininess_is_clamped(self):
        self.assertAlmostEqual(self._get_input_value("HighShininess", "roughness"), 0.0)
        self.assertAlmostEqual(self._get_input_value("LowShininess", "roughness"), 1.0)

    def test_metallic_is_clamped(self):
        self.assertAlmostEqual(self._get_input_value("HighMetallic", "metallic"), 1.0)
        self.assertAlmostEqual(self._get_input_value("LowMetallic", "metallic"), 0.0)

    def test_opacity_is_clamped(self):
        self.assertAlmostEqual(self._get_input_value("HighOpacity", "opacity"), 1.0)
        self.assertAlmostEqual(self._get_input_value("LowOpacity", "opacity"), 0.0)

    def test_color_is_clamped(self):
        # each channel is clamped independently, on both sides, leaving the others untouched
        self._assert_color("HighRed", Gf.Vec3f(1.0, 0.2, 0.2))
        self._assert_color("HighGreen", Gf.Vec3f(0.2, 1.0, 0.2))
        self._assert_color("HighBlue", Gf.Vec3f(0.2, 0.2, 1.0))
        self._assert_color("LowRed", Gf.Vec3f(0.0, 0.2, 0.2))
        self._assert_color("LowGreen", Gf.Vec3f(0.2, 0.0, 0.2))
        self._assert_color("LowBlue", Gf.Vec3f(0.2, 0.2, 0.0))

    def test_invalid_emission_is_ignored(self):
        for material_name in ("NegativeEmission", "AllOutOfRange"):
            self.assertFalse(self._get_shader(material_name).GetInput("emissiveColor"), msg=material_name)

    def test_emission_uses_clamped_color(self):
        # MuJoCo emits emission times the color, so the clamped color 1.0 * 0.5 is used rather than the authored 1.5 * 0.5
        emissive_color = usdex.core.linearToSrgb(self._get_input_value("ClampedEmission", "emissiveColor"))
        self.assertTrue(Gf.IsClose(emissive_color, Gf.Vec3f(0.5, 0.1, 0.1), 1e-5))

    def test_all_attributes_are_clamped_together(self):
        self._assert_color("AllOutOfRange", Gf.Vec3f(1.0, 0.0, 1.0))
        self.assertAlmostEqual(self._get_input_value("AllOutOfRange", "opacity"), 1.0)
        self.assertAlmostEqual(self._get_input_value("AllOutOfRange", "roughness"), 0.0)
        self.assertAlmostEqual(self._get_input_value("AllOutOfRange", "metallic"), 0.0)

    def test_unsafe_material_name(self):
        # the material still converts when its name is not a valid prim name
        materials = self.stage.GetPrimAtPath(f"/{self.model_name}/Materials").GetChildren()
        displayed = [usdex.core.getDisplayName(prim) for prim in materials]
        self.assertIn("my material.1", displayed)

    def test_bounds_are_valid(self):
        # the bounds are inclusive, so these convert unchanged without a warning (any warning fails setUp)
        self._assert_color("LowerBounds", Gf.Vec3f(0.0, 0.0, 0.0))
        self.assertAlmostEqual(self._get_input_value("LowerBounds", "opacity"), 0.0)
        self.assertAlmostEqual(self._get_input_value("LowerBounds", "roughness"), 1.0)
        self.assertAlmostEqual(self._get_input_value("LowerBounds", "metallic"), 0.0)
        self.assertFalse(self._get_shader("LowerBounds").GetInput("emissiveColor"))

        self._assert_color("UpperBounds", Gf.Vec3f(1.0, 1.0, 1.0))
        self.assertAlmostEqual(self._get_input_value("UpperBounds", "opacity"), 1.0)
        self.assertAlmostEqual(self._get_input_value("UpperBounds", "roughness"), 0.0)
        self.assertAlmostEqual(self._get_input_value("UpperBounds", "metallic"), 1.0)

    def test_unset_values_are_valid(self):
        # MuJoCo's -1 sentinels for shininess & metallic are not out of range
        self._assert_color("Defaults", Gf.Vec3f(1.0, 1.0, 1.0))
        self.assertAlmostEqual(self._get_input_value("Defaults", "opacity"), 1.0)
        self.assertAlmostEqual(self._get_input_value("Defaults", "roughness"), 0.5)

    def test_valid_values_are_unchanged(self):
        self.assertAlmostEqual(self._get_input_value("Valid", "roughness"), 0.75)
        self.assertAlmostEqual(self._get_input_value("Valid", "metallic"), 1.0)

    def test_openpbr_values_are_clamped(self):
        """The OpenPBR inputs share the Material Interface, so they hold the clamped values too."""
        if not self.openpbr:
            self.skipTest("OpenPBR is disabled")
        material = UsdShade.Material(self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/AllOutOfRange"))
        shader = usdex.core.computeEffectiveMtlxSurfaceShader(material)

        def value(input_name: str):
            return UsdShade.Utils.GetValueProducingAttributes(shader.GetInput(input_name))[0].Get()

        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(value("base_color")), Gf.Vec3f(1.0, 0.0, 1.0), 1e-5))
        self.assertAlmostEqual(value("geometry_opacity"), 1.0)
        self.assertAlmostEqual(value("specular_roughness"), 0.0)
        self.assertAlmostEqual(value("base_metalness"), 0.0)

    def test_openpbr_emission_uses_clamped_color(self):
        if not self.openpbr:
            self.skipTest("OpenPBR is disabled")
        material = UsdShade.Material(self.stage.GetPrimAtPath(f"/{self.model_name}/Materials/ClampedEmission"))
        shader = usdex.core.computeEffectiveMtlxSurfaceShader(material)
        emission_color = UsdShade.Utils.GetValueProducingAttributes(shader.GetInput("emission_color"))[0].Get()
        self.assertTrue(Gf.IsClose(usdex.core.linearToSrgb(emission_color), Gf.Vec3f(0.5, 0.1, 0.1), 1e-5))


class TestOutOfRangePreviewMaterial(TestOutOfRangeMaterial):
    """The UsdPreviewSurface only path (openpbr=False) uses different usd-exchange helpers, so it must clamp identically."""

    openpbr = False


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
