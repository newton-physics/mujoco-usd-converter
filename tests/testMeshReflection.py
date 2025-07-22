# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib
import shutil
import unittest

from pxr import Gf, Sdf, Usd, UsdGeom

import mujoco_usd_converter


class TestMeshReflection(unittest.TestCase):
    def tearDown(self):
        if pathlib.Path("tests/output").exists():
            shutil.rmtree("tests/output")

    def assert_rotation_almost_equal(self, rot1, rot2, tolerance):
        self.assertTrue(Gf.IsClose(rot1.GetAxis(), rot2.GetAxis(), tolerance))
        self.assertTrue(Gf.IsClose(rot1.GetAngle(), rot2.GetAngle(), tolerance))

    def test_mesh_reflection(self):
        tolerance = 1e-6
        rotation_const = 0.57735
        model = pathlib.Path("./tests/data/reflected_meshes.xml")
        model_name = pathlib.Path(model).stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, pathlib.Path(f"tests/output/{model_name}"))
        stage: Usd.Stage = Usd.Stage.Open(asset.path)

        geom: Usd.Prim = stage.GetPrimAtPath("/reflected_meshes/Geometry/body/bodyRegular/complexCube")
        geom_mesh = UsdGeom.Mesh(geom)
        self.assertTrue(geom_mesh)
        transform = Gf.Transform(geom_mesh.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))

        self.assertTrue(Gf.IsClose(transform.GetTranslation(), Gf.Vec3d(0.021, 0.07, 1.1), tolerance))
        self.assert_rotation_almost_equal(transform.GetRotation(), Gf.Rotation(Gf.Vec3d(rotation_const), 120), 1e-4)
        self.assertTrue(Gf.IsClose(transform.GetScale(), Gf.Vec3d(0.1), tolerance))

        geom: Usd.Prim = stage.GetPrimAtPath("/reflected_meshes/Geometry/body/bodyReflected/complexCubeMirror")
        geom_mesh = UsdGeom.Mesh(geom)
        self.assertTrue(geom_mesh)

        transform = Gf.Transform(geom_mesh.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))
        self.assertTrue(Gf.IsClose(transform.GetTranslation(), Gf.Vec3d(0.021, -0.07, 1.1), tolerance))
        self.assert_rotation_almost_equal(transform.GetRotation(), Gf.Rotation(Gf.Vec3d(rotation_const, rotation_const, -rotation_const), 240), 1e-4)
        self.assertTrue(Gf.IsClose(transform.GetScale(), Gf.Vec3d(-0.1), tolerance))
