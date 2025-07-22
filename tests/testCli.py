# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest
from unittest.mock import patch

# workaround for Windows not locating the USD libs, because of the way plugInfo.json in usdex is structured
import usdex.core  # noqa: F401
from pxr import Sdf, Usd

from mujoco_usd_converter import run


class TestCli(unittest.TestCase):
    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def test_run(self):
        for model in pathlib.Path("tests/data").glob("*.xml"):
            model_name = model.stem
            with patch("sys.argv", ["mujoco_usd_converter", str(model), f"tests/output/{model_name}"]):
                self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/{model_name}.usda").exists())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/payload").is_dir())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/payload/Contents.usda").is_file())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/payload/Geometry.usda").is_file())

    def test_no_layer_structure(self):
        model = "tests/data/meshes.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mujoco_usd_converter", model, f"tests/output/{model_name}", "--no-layer-structure"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertFalse(pathlib.Path(f"tests/output/{model_name}/payload").exists())
            self.assertFalse(pathlib.Path(f"tests/output/{model_name}/{model_name}.usda").exists())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/{model_name}.usdc").exists())

    def test_no_physics_scene(self):
        model = "tests/data/scene_attributes.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mujoco_usd_converter", model, f"tests/output/{model_name}", "--no-physics-scene"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/{model_name}.usda").exists())
            stage = Usd.Stage.Open(f"tests/output/{model_name}/{model_name}.usda")
            self.assertFalse(stage.GetPrimAtPath("/PhysicsScene").IsValid())

    def test_comment(self):
        model = "tests/data/worldgeom.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mujoco_usd_converter", model, f"tests/output/{model_name}", "--comment", "from the unittests"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/{model_name}.usda").exists())
            layer = Sdf.Layer.FindOrOpen(f"tests/output/{model_name}/{model_name}.usda")
            self.assertEqual(layer.comment, "from the unittests")

    def test_invalid_input(self):
        with patch("sys.argv", ["mujoco_usd_converter", "tests/data/invalid.xml", "tests/output/invalid"]):
            self.assertEqual(run(), 1, "Expected non-zero exit code for invalid input")

    def test_invalid_output(self):
        # create a file that is not a directory
        pathlib.Path("tests/output").mkdir(parents=True, exist_ok=True)
        pathlib.Path("tests/output/invalid").touch()
        with patch("sys.argv", ["mujoco_usd_converter", "tests/data/worldgeom.xml", "tests/output/invalid"]):
            self.assertEqual(run(), 1, "Expected non-zero exit code for invalid output")

    def test_input_path_is_directory(self):
        # Create a directory as input_file (should fail)
        input_dir = pathlib.Path("tests/data/input_dir")
        input_dir.mkdir(parents=True, exist_ok=True)
        try:
            with patch("sys.argv", ["mujoco_usd_converter", str(input_dir), "tests/output/dir_as_input"]):
                self.assertEqual(run(), 1, "Expected non-zero exit code for input path as directory")
        finally:
            shutil.rmtree(input_dir)

    def test_input_file_not_xml(self):
        # Create a non-xml file as input_file (should fail)
        not_xml = pathlib.Path("tests/data/not_xml.txt")
        not_xml.write_text("dummy content")
        try:
            with patch("sys.argv", ["mujoco_usd_converter", str(not_xml), "tests/output/not_xml"]):
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
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code when output dir cannot be created")

    def test_conversion_returns_none(self):
        # Test the case where converter.convert() returns None/false value
        model = "tests/data/worldgeom.xml"
        with (
            patch("mujoco_usd_converter.convert.Converter.convert", return_value=None),
            patch("sys.argv", ["mujoco_usd_converter", model, "tests/output/conversion_none"]),
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code when conversion returns None")

    def test_conversion_exception_non_verbose(self):
        # Test exception handling when verbose=False (should not re-raise)
        model = "tests/data/worldgeom.xml"
        with (
            patch("mujoco_usd_converter.convert.Converter.convert", side_effect=RuntimeError("Test conversion error")),
            patch("sys.argv", ["mujoco_usd_converter", model, "tests/output/conversion_error"]),
        ):
            self.assertEqual(run(), 1, "Expected non-zero exit code when conversion raises exception")

    def test_conversion_exception_verbose(self):
        # Test exception handling when verbose=True (should re-raise)
        model = "tests/data/worldgeom.xml"
        with (
            patch("mujoco_usd_converter.convert.Converter.convert", side_effect=RuntimeError("Test conversion error")),
            patch("sys.argv", ["mujoco_usd_converter", model, "tests/output/conversion_error_verbose", "--verbose"]),
            self.assertRaises(RuntimeError),
        ):
            run()
