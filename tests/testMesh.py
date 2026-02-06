# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib

from pxr import Sdf, Usd, UsdGeom

import mujoco_usd_converter
from tests.util.ConverterTestCase import ConverterTestCase


class TestMesh(ConverterTestCase):

    def test_mesh_conversion(self):
        model_path = pathlib.Path("./tests/data/meshes.xml")
        model_name = model_path.stem
        asset: Sdf.AssetPath = mujoco_usd_converter.Converter().convert(model_path, self.tmpDir())
        stage = Usd.Stage.Open(asset.path)
        self.assertIsValidUsd(stage)

        # Test STL mesh conversion
        stl_mesh_prim: Usd.Prim = stage.GetPrimAtPath(f"/{model_name}/Geometry/body1/StlBox")
        self.assertTrue(stl_mesh_prim)
        # meshes are references to the geometry library layer
        self.assertTrue(stl_mesh_prim.HasAuthoredReferences())
        usd_mesh_stl = UsdGeom.Mesh(stl_mesh_prim)
        self.assertTrue(usd_mesh_stl.GetPointsAttr().HasAuthoredValue())
        self.assertTrue(usd_mesh_stl.GetFaceVertexCountsAttr().HasAuthoredValue())
        self.assertTrue(usd_mesh_stl.GetFaceVertexIndicesAttr().HasAuthoredValue())
        # The sample box.stl has normals and they are authored as a primvar
        self.assertFalse(usd_mesh_stl.GetNormalsAttr().HasAuthoredValue())
        normals_primvar: UsdGeom.Primvar = UsdGeom.PrimvarsAPI(usd_mesh_stl).GetPrimvar("normals")
        self.assertTrue(normals_primvar.IsDefined())
        self.assertTrue(normals_primvar.HasAuthoredValue())
        self.assertTrue(normals_primvar.GetIndicesAttr().HasAuthoredValue())

        # Test OBJ mesh conversion
        obj_mesh_prim: Usd.Prim = stage.GetPrimAtPath(f"/{model_name}/Geometry/body1/body2/ObjBox")
        self.assertTrue(obj_mesh_prim)
        # meshes are references to the geometry library layer
        self.assertTrue(obj_mesh_prim.HasAuthoredReferences())
        usd_mesh_obj = UsdGeom.Mesh(obj_mesh_prim)
        self.assertEqual(len(usd_mesh_obj.GetPointsAttr().Get()), 8)
        face_vertex_counts = usd_mesh_obj.GetFaceVertexCountsAttr().Get()
        self.assertEqual(len(face_vertex_counts), 6)
        self.assertTrue(all(c == 4 for c in face_vertex_counts))
        face_vertex_indices = usd_mesh_obj.GetFaceVertexIndicesAttr().Get()
        self.assertEqual(len(face_vertex_indices), 24)

        # The sample box.obj has normals and UVs
        normals_primvar: UsdGeom.Primvar = UsdGeom.PrimvarsAPI(usd_mesh_obj).GetPrimvar("normals")
        self.assertTrue(normals_primvar.IsDefined())
        self.assertEqual(len(normals_primvar.GetAttr().Get()), 6)
        self.assertEqual(len(normals_primvar.GetIndicesAttr().Get()), 24)
        uvs_primvar: UsdGeom.Primvar = UsdGeom.PrimvarsAPI(usd_mesh_obj).GetPrimvar("st")
        self.assertTrue(uvs_primvar.IsDefined())
        self.assertEqual(len(uvs_primvar.GetAttr().Get()), 4)
        self.assertEqual(len(uvs_primvar.GetIndicesAttr().Get()), 24)

        # Test mesh conversion with no name
        mesh_prim: Usd.Prim = stage.GetPrimAtPath(f"/{model_name}/Geometry/body1/body2/box")
        self.assertTrue(mesh_prim)
        # meshes are references to the geometry library layer
        self.assertTrue(mesh_prim.HasAuthoredReferences())
        usd_mesh = UsdGeom.Mesh(mesh_prim)
        self.assertEqual(len(usd_mesh.GetPointsAttr().Get()), 8)
        face_vertex_counts = usd_mesh.GetFaceVertexCountsAttr().Get()
        self.assertEqual(len(face_vertex_counts), 6)
        self.assertTrue(all(c == 4 for c in face_vertex_counts))
        face_vertex_indices = usd_mesh.GetFaceVertexIndicesAttr().Get()
        self.assertEqual(len(face_vertex_indices), 24)

        # The sample box.obj has normals and UVs
        normals_primvar: UsdGeom.Primvar = UsdGeom.PrimvarsAPI(usd_mesh).GetPrimvar("normals")
        self.assertTrue(normals_primvar.IsDefined())
        self.assertEqual(len(normals_primvar.GetAttr().Get()), 6)
        self.assertEqual(len(normals_primvar.GetIndicesAttr().Get()), 24)
        uvs_primvar: UsdGeom.Primvar = UsdGeom.PrimvarsAPI(usd_mesh).GetPrimvar("st")
        self.assertTrue(uvs_primvar.IsDefined())
        self.assertEqual(len(uvs_primvar.GetAttr().Get()), 4)
        self.assertEqual(len(uvs_primvar.GetIndicesAttr().Get()), 24)
