import pathlib
import unittest
import site

import mujoco
import usdex.core
from pxr import Usd

import mjc_usd_converter


class DependencyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._site = [x for x in site.getsitepackages() if x.endswith("site-packages")][-1]

    def test_local_mjc_usd_converter(self):
        self.assertEqual(pathlib.Path(mjc_usd_converter.__file__).relative_to(self._site), pathlib.Path("mjc_usd_converter/__init__.py"))

    def test_local_mujoco(self):
        self.assertEqual(pathlib.Path(mujoco.__file__).relative_to(self._site), pathlib.Path("mujoco/__init__.py"))

    def test_local_usd(self):
        self.assertEqual(pathlib.Path(Usd.__file__).relative_to(self._site), pathlib.Path("pxr/Usd/__init__.py"))

    def test_local_usdex(self):
        self.assertEqual(pathlib.Path(usdex.core.__file__).relative_to(self._site), pathlib.Path("usdex/core/__init__.py"))
