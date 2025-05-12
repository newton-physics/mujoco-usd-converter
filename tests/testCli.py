# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest
from unittest.mock import patch

from mjc_usd_converter import run


class TestCli(unittest.TestCase):
    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def test_run(self):
        with patch("sys.argv", ["mjc_usd_converter", "tests/data/worldgeom.xml", "tests/output/worldgeom"]):
            self.assertEqual(run(), 0)
        self.assertTrue(pathlib.Path("tests/output/worldgeom/worldgeom.usda").exists())
