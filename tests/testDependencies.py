# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import site
import unittest

import mujoco
import usdex.core
from pxr import Usd


class TestDependencies(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._site = [x for x in site.getsitepackages() if x.endswith("site-packages")][-1]

    def test_local_mujoco(self):
        self.assertEqual(pathlib.Path(mujoco.__file__).relative_to(self._site), pathlib.Path("mujoco/__init__.py"))

    def test_local_usd(self):
        self.assertEqual(pathlib.Path(Usd.__file__).relative_to(self._site), pathlib.Path("pxr/Usd/__init__.py"))

    def test_local_usdex(self):
        self.assertEqual(pathlib.Path(usdex.core.__file__).relative_to(self._site), pathlib.Path("usdex/core/__init__.py"))
