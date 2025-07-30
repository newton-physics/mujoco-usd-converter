# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib

from pxr import Gf, Sdf, Usd, UsdGeom

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestFrames(ConverterTestCase):
    def assert_rotation_almost_equal(self, rot1, rot2, tolerance):
        self.assertTrue(Gf.IsClose(rot1.GetAxis(), rot2.GetAxis(), tolerance))
        self.assertTrue(Gf.IsClose(rot1.GetAngle(), rot2.GetAngle(), tolerance))

    def test_frames(self):
        tolerance = 1e-6
        model = pathlib.Path("./tests/data/frames.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        geom: Usd.Prim = stage.GetPrimAtPath("/frames/Geometry/mainBody/framedBody/ObjBox")
        geom_mesh = UsdGeom.Mesh(geom)
        self.assertTrue(geom_mesh)

        transform = Gf.Transform(geom_mesh.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))

        self.assertTrue(Gf.IsClose(transform.GetTranslation(), Gf.Vec3d(-pow(2, 0.5) / 2, -pow(2, 0.5) / 2, 0), tolerance))
        self.assert_rotation_almost_equal(transform.GetRotation(), Gf.Rotation(Gf.Vec3d(0, 0, 1), 90), 1e-4)
        self.assertTrue(Gf.IsClose(transform.GetScale(), Gf.Vec3d(0.2, 0.2, 0.8), tolerance))

        geom: Usd.Prim = stage.GetPrimAtPath("/frames/Geometry/mainBody/framedGeom")
        geom_cube = UsdGeom.Cube(geom)
        self.assertTrue(geom_cube)

        transform = Gf.Transform(geom_cube.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))

        self.assertTrue(Gf.IsClose(transform.GetTranslation(), Gf.Vec3d(pow(2, 0.5) / 2, -pow(2, 0.5) / 2, 0), tolerance))
        self.assert_rotation_almost_equal(transform.GetRotation(), Gf.Rotation(Gf.Vec3d(0, 0, 1), 90), 1e-4)
        self.assertTrue(Gf.IsClose(transform.GetScale(), Gf.Vec3d(0.1, 0.1, 0.4), tolerance))
