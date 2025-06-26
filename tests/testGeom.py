# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

from pxr import Sdf, Usd, UsdPhysics

import mjc_usd_converter


class TestGeom(unittest.TestCase):
    def setUp(self):
        model = pathlib.Path("./tests/data/geoms.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"./tests/output/{model_name}"))
        self.stage: Usd.Stage = Usd.Stage.Open(asset.path)

    def tearDown(self):
        self.stage = None
        if pathlib.Path("./tests/output").exists():
            shutil.rmtree("./tests/output")

    def test_default_collider(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/default_collider")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        collider_api = UsdPhysics.CollisionAPI(prim)
        # Enabled by default, so attribute should not be authored
        self.assertFalse(collider_api.GetCollisionEnabledAttr().HasAuthoredValue())
        self.assertFalse(prim.HasAPI(UsdPhysics.MassAPI))

    def test_visual_geom(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual")
        self.assertFalse(prim.HasAPI(UsdPhysics.CollisionAPI))

    def test_visual_with_mass(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual_with_mass")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        collider_api = UsdPhysics.CollisionAPI(prim)
        self.assertFalse(collider_api.GetCollisionEnabledAttr().Get())
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 5.0)
        self.assertFalse(mass_api.GetDensityAttr().HasAuthoredValue())

    def test_visual_with_density(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual_with_density")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        collider_api = UsdPhysics.CollisionAPI(prim)
        self.assertFalse(collider_api.GetCollisionEnabledAttr().Get())
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetDensityAttr().Get(), 2000)
        self.assertFalse(mass_api.GetMassAttr().HasAuthoredValue())

    def test_visual_in_range_no_mass(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/visual_in_range_no_mass")
        self.assertFalse(prim.HasAPI(UsdPhysics.CollisionAPI))

    def test_mesh_collider(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/mesh_collider")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MeshCollisionAPI))
        mesh_collider_api = UsdPhysics.MeshCollisionAPI(prim)
        self.assertEqual(mesh_collider_api.GetApproximationAttr().Get(), UsdPhysics.Tokens.convexHull)

    def test_explicit_mass(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/explicit_mass")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 10.0)
        self.assertFalse(mass_api.GetDensityAttr().HasAuthoredValue())

    def test_explicit_density(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/explicit_density")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetDensityAttr().Get(), 3000)
        self.assertFalse(mass_api.GetMassAttr().HasAuthoredValue())

    def test_mass_and_density(self):
        prim: Usd.Prim = self.stage.GetPrimAtPath("/geoms/Geometry/mass_and_density")
        self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
        self.assertTrue(prim.HasAPI(UsdPhysics.MassAPI))
        mass_api = UsdPhysics.MassAPI(prim)
        self.assertAlmostEqual(mass_api.GetMassAttr().Get(), 15.0)
        self.assertAlmostEqual(mass_api.GetDensityAttr().Get(), 4000)
