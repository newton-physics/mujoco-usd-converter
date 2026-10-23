# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import mujoco
import numpy as np
import omni.asset_validator
import usdex.core
from pxr import Gf, Sdf, Usd, UsdGeom

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestMeshRefPose(ConverterTestCase):
    def setUp(self):
        super().setUp()
        # the test data contains unwelded meshes, so we disable the weld checker
        self.validationEngine.disable_rule(omni.asset_validator.WeldChecker)

    def __convert(self, model_path: pathlib.Path) -> Usd.Stage:
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model_path, pathlib.Path(self.tmpDir()) / model_path.stem)
        stage: Usd.Stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)
        return stage

    def __get_mesh(self, stage: Usd.Stage, name: str) -> UsdGeom.Mesh:
        mesh = UsdGeom.Mesh(stage.GetPrimAtPath(f"{stage.GetDefaultPrim().GetPath()}/Geometry/body/{name}"))
        self.assertTrue(mesh, name)
        return mesh

    def test_world_points_match_mujoco(self):
        model_path = pathlib.Path("./tests/data/mesh_ref_pose.xml")
        stage = self.__convert(model_path)
        model = mujoco.MjModel.from_xml_path(str(model_path))
        data = mujoco.MjData(model)
        mujoco.mj_kinematics(model, data)
        for geom_id in range(model.ngeom):
            name = model.geom(geom_id).name
            with self.subTest(geom=name):
                mesh_id = model.geom_dataid[geom_id]
                start = model.mesh_vertadr[mesh_id]
                vertices = model.mesh_vert[start : start + model.mesh_vertnum[mesh_id]]
                expected = vertices @ data.geom_xmat[geom_id].reshape(3, 3).T + data.geom_xpos[geom_id]

                mesh = self.__get_mesh(stage, name)
                world = np.array(mesh.ComputeLocalToWorldTransform(Usd.TimeCode.Default()))
                actual = np.array(mesh.GetPointsAttr().Get()) @ world[:3, :3] + world[3, :3]

                # MuJoCo may reorder or merge vertices, so compare against the closest point in each direction
                distances = np.linalg.norm(expected[:, None] - actual[None], axis=-1)
                self.assertLess(distances.min(axis=1).max(), 1e-5)
                self.assertLess(distances.min(axis=0).max(), 1e-5)

    def test_unsheared_ref_pose_is_authored_as_transform(self):
        stage = self.__convert(pathlib.Path("./tests/data/mesh_ref_pose.xml"))
        source_points = self.__get_mesh(stage, "plainGeom").GetPointsAttr().Get()
        for name in ("refPosGeom", "refQuatGeom", "refPoseGeom"):
            with self.subTest(geom=name):
                self.assertEqual(self.__get_mesh(stage, name).GetPointsAttr().Get(), source_points)

        # the geom has an identity pose, so its transform is the mesh transform
        pos, _, orient, scale = usdex.core.getLocalTransformComponentsQuat(self.__get_mesh(stage, "refPoseGeom").GetPrim())
        self.assertTrue(Gf.IsClose(pos, Gf.Vec3d(-0.01, -0.06, 0.06), 1e-6))
        self.assertRotationsAlmostEqual(Gf.Rotation(orient), Gf.Rotation(Gf.Vec3d(1, 0, 0), 270), 1e-4)
        self.assertTrue(Gf.IsClose(scale, Gf.Vec3f(0.1, 0.3, 0.2), 1e-6))

    def test_sheared_ref_pose_is_baked_into_points(self):
        quat = np.array([0.9, 0.3, 0.1, 0.2])
        rotation = np.empty(9)
        mujoco.mju_quat2Mat(rotation, quat / np.linalg.norm(quat))
        rotation = rotation.reshape(3, 3)
        refpos = np.array([0.1, 0.2, 0.3])

        # MuJoCo cannot compile the ASCII STL test asset, so it is converted separately
        for model_path in (pathlib.Path("./tests/data/mesh_ref_pose.xml"), pathlib.Path("./tests/data/mesh_ref_pose_stl.xml")):
            with self.subTest(model=model_path.stem):
                stage = self.__convert(model_path)
                mesh = self.__get_mesh(stage, "shearedGeom")
                source = self.__get_mesh(stage, "plainGeom")

                expected_points = (np.array(source.GetPointsAttr().Get()) - refpos) @ rotation
                np.testing.assert_allclose(np.array(mesh.GetPointsAttr().Get()), expected_points, atol=1e-6)
                self.assertEqual(mesh.GetExtentAttr().Get(), UsdGeom.PointBased.ComputeExtent(mesh.GetPointsAttr().Get()))

                normals = UsdGeom.PrimvarsAPI(mesh).GetPrimvar(UsdGeom.Tokens.normals)
                source_normals = UsdGeom.PrimvarsAPI(source).GetPrimvar(UsdGeom.Tokens.normals)
                np.testing.assert_allclose(np.array(normals.Get()), np.array(source_normals.Get()) @ rotation, atol=1e-6)
                self.assertEqual(normals.GetIndices(), source_normals.GetIndices())

                # only the scale remains, as an unrotated scale cannot shear
                pos, _, orient, scale = usdex.core.getLocalTransformComponentsQuat(mesh.GetPrim())
                self.assertTrue(Gf.IsClose(pos, Gf.Vec3d(0), 1e-6))
                self.assertRotationsAlmostEqual(Gf.Rotation(orient), Gf.Rotation(Gf.Quatd.GetIdentity()), 1e-4)
                self.assertTrue(Gf.IsClose(scale, Gf.Vec3f(0.1, 0.2, 0.3), 1e-6))
