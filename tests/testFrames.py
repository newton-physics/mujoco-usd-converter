# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import usdex.core
import usdex.test
from pxr import Gf, Sdf, Tf, Usd, UsdGeom

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestFrames(ConverterTestCase):
    def test_frames(self):
        model = pathlib.Path("./tests/data/frames.xml")
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        geom: Usd.Prim = stage.GetPrimAtPath("/frames/Geometry/mainBody/framedBody/ObjBox")
        geom_mesh = UsdGeom.Mesh(geom)
        self.assertTrue(geom_mesh)

        transform = Gf.Transform(geom_mesh.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))

        self.assertTrue(Gf.IsClose(transform.GetTranslation(), Gf.Vec3d(-pow(2, 0.5) / 2, -pow(2, 0.5) / 2, 0), 1e-6))
        self.assertRotationsAlmostEqual(transform.GetRotation(), Gf.Rotation(Gf.Vec3d(0, 0, 1), 90), 1e-4)
        self.assertTrue(Gf.IsClose(transform.GetScale(), Gf.Vec3d(0.2, 0.2, 0.8), 1e-6))

        geom: Usd.Prim = stage.GetPrimAtPath("/frames/Geometry/mainBody/framedGeom")
        geom_cube = UsdGeom.Cube(geom)
        self.assertTrue(geom_cube)

        transform = Gf.Transform(geom_cube.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))

        self.assertTrue(Gf.IsClose(transform.GetTranslation(), Gf.Vec3d(pow(2, 0.5) / 2, -pow(2, 0.5) / 2, 0), 1e-6))
        self.assertRotationsAlmostEqual(transform.GetRotation(), Gf.Rotation(Gf.Vec3d(0, 0, 1), 90), 1e-4)
        self.assertTrue(Gf.IsClose(transform.GetScale(), Gf.Vec3d(0.1, 0.1, 0.4), 1e-6))

    def test_frame_scale_warns(self):
        # MuJoCo scales frame contents at compile time, which the converter does not represent
        self.__assert_frame_scale_warns(pathlib.Path("./tests/data/frames_scale.xml"))

    def test_frame_massscale_warns(self):
        self.__assert_frame_scale_warns(pathlib.Path("./tests/data/frames_massscale.xml"))

    def __assert_frame_scale_warns(self, model: pathlib.Path):
        with usdex.test.ScopedDiagnosticChecker(
            self,
            [(Tf.TF_DIAGNOSTIC_WARNING_TYPE, ".*frame scale is not supported.*")],
            level=usdex.core.DiagnosticsLevel.eWarning,
        ):
            asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model, self.tmpDir())
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)
