# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import omni.asset_validator
from pxr import Gf, Sdf, Usd, UsdGeom

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestMeshReflection(ConverterTestCase):
    def test_mesh_reflection(self):
        tolerance = 1e-6
        rotation_const = 0.57735
        model = pathlib.Path("./tests/data/reflected_meshes.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        # the test data contains unwelded meshes, so we disable the weld checker
        self.validationEngine.disable_rule(omni.asset_validator.WeldChecker)
        self.assertIsValidUsd(stage)

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
