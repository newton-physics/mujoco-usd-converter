# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

import usdex.core
from pxr import Gf, Sdf, Usd, UsdGeom

import mjc_usd_converter


class TestSites(unittest.TestCase):
    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def test_sites(self):
        model = pathlib.Path("./tests/data/sites.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        geom: Usd.Prim = stage.GetPrimAtPath("/sites/Geometry/body/geom")
        geom_sphere = UsdGeom.Sphere(geom)
        self.assertTrue(geom_sphere)
        self.assertEqual(geom_sphere.GetRadiusAttr().Get(), 0.1)
        self.assertEqual(geom_sphere.GetPurposeAttr().Get(), UsdGeom.Tokens.default_)
        self.assertEqual(geom.GetAttribute("mjc:group").Get(), 0)

        site: Usd.Prim = stage.GetPrimAtPath("/sites/Geometry/body/site")
        box = UsdGeom.Cube(site)
        self.assertTrue(box)
        # box size is still 2, boxes are scaled via XformOps
        self.assertEqual(box.GetSizeAttr().Get(), 2)
        self.assertTrue(Gf.IsClose(usdex.core.getLocalTransform(site).GetScale(), Gf.Vec3d(0.1, 0.2, 0.3), 1e-6))
        self.assertEqual(box.GetPurposeAttr().Get(), UsdGeom.Tokens.guide)
        self.assertTrue(site.GetPrim().HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsSiteAPI")))
        self.assertEqual(site.GetAttribute("mjc:group").Get(), 0)

        world_site: Usd.Prim = stage.GetPrimAtPath("/sites/Geometry/worldsite")
        world_sphere = UsdGeom.Sphere(world_site)
        self.assertTrue(world_sphere)
        # default size for sites is 0.005
        self.assertEqual(world_sphere.GetRadiusAttr().Get(), 0.005)
        self.assertEqual(world_sphere.GetPurposeAttr().Get(), UsdGeom.Tokens.guide)
        self.assertTrue(world_site.GetPrim().HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsSiteAPI")))
        self.assertEqual(world_site.GetAttribute("mjc:group").Get(), 1)

    def test_sites_in_physics_layer(self):
        model = pathlib.Path("./tests/data/sites.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mjc_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        site: Usd.Prim = stage.GetPrimAtPath("/sites/Geometry/body/site")
        world_site: Usd.Prim = stage.GetPrimAtPath("/sites/Geometry/worldsite")
        box = UsdGeom.Cube(site)
        self.assertTrue(box)
        world_sphere = UsdGeom.Sphere(world_site)
        self.assertTrue(world_sphere)

        # there are no physics properties on the site prims
        for prop_name in site.GetAuthoredPropertyNames():
            self.assertFalse(prop_name.startswith("physics:"))

        prim_specs: list[Sdf.PrimSpec] = site.GetPrimStack()
        self.assertEqual(len(prim_specs), 2)
        self.assertTrue("Physics" in prim_specs[0].layer.identifier)

        for prop_name in world_site.GetAuthoredPropertyNames():
            self.assertFalse(prop_name.startswith("physics:"))

        prim_specs: list[Sdf.PrimSpec] = world_site.GetPrimStack()
        self.assertEqual(len(prim_specs), 2)
        self.assertTrue("Physics" in prim_specs[0].layer.identifier)

        # site prims are in the physics layer with the MJC schemas applied
        physics_layer_path = pathlib.Path(f"./tests/output/{model_name}/payload/Physics.usda").absolute()
        self.assertTrue(physics_layer_path.exists(), msg=f"Physics layer not found at {physics_layer_path}")
        physics_stage: Usd.Stage = Usd.Stage.Open(physics_layer_path.as_posix())
        site_over: Usd.Prim = physics_stage.GetPrimAtPath("/sites/Geometry/body/site")
        self.assertTrue(site_over.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsSiteAPI")))

        world_site_over: Usd.Prim = physics_stage.GetPrimAtPath("/sites/Geometry/worldsite")
        self.assertTrue(world_site_over.HasAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsSiteAPI")))
