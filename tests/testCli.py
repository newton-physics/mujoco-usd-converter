# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest
from unittest.mock import patch

# workaround for Windows not locating the USD libs, because of the way plugInfo.json in usdex is structured
import usdex.core  # noqa: F401
from pxr import Sdf

from mjc_usd_converter import run


class TestCli(unittest.TestCase):
    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def test_run(self):
        for model in pathlib.Path("tests/data").glob("*.xml"):
            model_name = model.stem
            with patch("sys.argv", ["mjc_usd_converter", str(model), f"tests/output/{model_name}"]):
                self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/{model_name}.usda").exists())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/payload").is_dir())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/payload/Contents.usda").is_file())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/payload/Geometry.usda").is_file())

    def test_flatten(self):
        model = "tests/data/meshes.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mjc_usd_converter", model, f"tests/output/{model_name}", "--flatten"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertFalse(pathlib.Path(f"tests/output/{model_name}/payload").exists())
            self.assertFalse(pathlib.Path(f"tests/output/{model_name}/{model_name}.usda").exists())
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/{model_name}.usdc").exists())

    def test_comment(self):
        model = "tests/data/worldgeom.xml"
        model_name = pathlib.Path(model).stem
        with patch("sys.argv", ["mjc_usd_converter", model, f"tests/output/{model_name}", "--comment", "from the unittests"]):
            self.assertEqual(run(), 0, f"Failed to convert {model}")
            self.assertTrue(pathlib.Path(f"tests/output/{model_name}/{model_name}.usda").exists())
            layer = Sdf.Layer.FindOrOpen(f"tests/output/{model_name}/{model_name}.usda")
            self.assertEqual(layer.comment, "from the unittests")

    def test_invalid_input(self):
        with patch("sys.argv", ["mjc_usd_converter", "tests/data/invalid.xml", "tests/output/invalid"]):
            self.assertEqual(run(), 1, "Expected non-zero exit code for invalid input")

    def test_invalid_output(self):
        # create a file that is not a directory
        pathlib.Path("tests/output").mkdir(parents=True, exist_ok=True)
        pathlib.Path("tests/output/invalid").touch()
        with patch("sys.argv", ["mjc_usd_converter", "tests/data/worldgeom.xml", "tests/output/invalid"]):
            self.assertEqual(run(), 1, "Expected non-zero exit code for invalid output")
