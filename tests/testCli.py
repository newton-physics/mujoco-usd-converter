# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
from unittest.mock import patch

import usdex.core
import usdex.test
from pxr import Sdf, Tf, Usd

from mujoco_usd_converter._impl.cli import run
from tests.util.ConverterTestCase import ConverterTestCase


class TestCli(ConverterTestCase):

    def test_run(self):
        model = "tests/data/geoms.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mujoco_usd_converter", str(model), self.tmpDir()]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
        self.assertTrue((pathlib.Path(self.tmpDir()) / f"{model_name}.usda").exists())

    def test_no_layer_structure(self):
        model = "tests/data/meshes.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mujoco_usd_converter", model, self.tmpDir(), "--no-layer-structure"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertFalse((pathlib.Path(self.tmpDir()) / "Payload").exists())
            self.assertFalse((pathlib.Path(self.tmpDir()) / f"{model_name}.usda").exists())
            self.assertTrue((pathlib.Path(self.tmpDir()) / f"{model_name}.usdc").exists())

    def test_no_physics_scene(self):
        model = "tests/data/scene_attributes.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mujoco_usd_converter", model, self.tmpDir(), "--no-physics-scene"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertTrue((pathlib.Path(self.tmpDir()) / f"{model_name}.usda").exists())
            stage = Usd.Stage.Open((pathlib.Path(self.tmpDir()) / f"{model_name}.usda").as_posix())
            self.assertFalse(stage.GetPrimAtPath("/PhysicsScene").IsValid())

    def test_comment(self):
        model = "tests/data/worldgeom.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mujoco_usd_converter", model, self.tmpDir(), "--comment", "from the unittests"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertTrue((pathlib.Path(self.tmpDir()) / f"{model_name}.usda").exists())
            layer = Sdf.Layer.FindOrOpen((pathlib.Path(self.tmpDir()) / f"{model_name}.usda").as_posix())
            self.assertEqual(layer.comment, "from the unittests")

    def test_invalid_input(self):
        with (
            patch("sys.argv", ["mujoco_usd_converter", "tests/data/invalid.xml", self.tmpDir()]),
            usdex.test.ScopedDiagnosticChecker(self, [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Input file does not exist.*")]),
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code for invalid input")

    def test_invalid_output(self):
        # create a file that is not a directory
        pathlib.Path("tests/output").mkdir(parents=True, exist_ok=True)
        pathlib.Path("tests/output/invalid").touch()
        with (
            patch("sys.argv", ["mujoco_usd_converter", "tests/data/worldgeom.xml", "tests/output/invalid"]),
            usdex.test.ScopedDiagnosticChecker(self, [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Output path exists but is not a directory.*")]),
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code for invalid output")

    def test_input_path_is_directory(self):
        # Create a directory as input_file (should fail)
        input_dir = pathlib.Path("tests/data/input_dir")
        input_dir.mkdir(parents=True, exist_ok=True)
        try:
            with (
                patch("sys.argv", ["mujoco_usd_converter", str(input_dir), self.tmpDir()]),
                usdex.test.ScopedDiagnosticChecker(self, [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Input path is not a file.*")]),
            ):
                self.assertEqual(run(), 1, "Expected non-zero exit code for input path as directory")
        finally:
            shutil.rmtree(input_dir)

    def test_input_file_not_xml(self):
        # Create a non-xml file as input_file (should fail)
        not_xml = pathlib.Path("tests/data/not_xml.txt")
        not_xml.write_text("dummy content")
        try:
            with (
                patch("sys.argv", ["mujoco_usd_converter", str(not_xml), self.tmpDir()]),
                usdex.test.ScopedDiagnosticChecker(self, [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Only MJCF.*are supported as input.*")]),
            ):
                self.assertEqual(run(), 1, "Expected non-zero exit code for non-xml input file")
        finally:
            not_xml.unlink()

    def test_output_dir_cannot_create(self):
        # Simulate output_dir.mkdir raising an exception (should fail)
        model = "tests/data/worldgeom.xml"
        output_dir = pathlib.Path("tests/output/cannot_create")
        with (
            patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")),
            patch("sys.argv", ["mujoco_usd_converter", model, str(output_dir)]),
            usdex.test.ScopedDiagnosticChecker(self, [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Failed to create output directory.*")]),
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code when output dir cannot be created")

    def test_conversion_returns_none(self):
        # Test the case where converter.convert() returns None/false value
        model = "tests/data/worldgeom.xml"
        with (
            patch("mujoco_usd_converter.Converter.convert", return_value=None),
            patch("sys.argv", ["mujoco_usd_converter", model, self.tmpDir()]),
            usdex.test.ScopedDiagnosticChecker(
                self,
                [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Conversion failed for unknown reason.*")],
                level=usdex.core.DiagnosticsLevel.eWarning,
            ),
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code when conversion returns None")

    def test_conversion_exception_non_verbose(self):
        # Test exception handling when verbose=False (should not re-raise)
        model = "tests/data/worldgeom.xml"
        with (
            patch("mujoco_usd_converter.Converter.convert", side_effect=RuntimeError("Test conversion error")),
            patch("sys.argv", ["mujoco_usd_converter", model, self.tmpDir()]),
            usdex.test.ScopedDiagnosticChecker(
                self,
                [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, "Conversion failed: Test conversion error.*")],
                level=usdex.core.DiagnosticsLevel.eWarning,
            ),
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code when conversion raises exception")

    def test_conversion_exception_verbose(self):
        # Test exception handling when verbose=True (should re-raise)
        model = "tests/data/worldgeom.xml"
        with (
            patch("mujoco_usd_converter.Converter.convert", side_effect=RuntimeError("Test conversion error")),
            patch("sys.argv", ["mujoco_usd_converter", model, self.tmpDir(), "--verbose"]),
            self.assertRaises(RuntimeError),
            usdex.test.ScopedDiagnosticChecker(self, [], level=usdex.core.DiagnosticsLevel.eWarning),
        ):
            run()
