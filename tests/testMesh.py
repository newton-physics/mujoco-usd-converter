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
        self.assertTrue(usd_mesh_obj.GetPointsAttr().HasAuthoredValue())
        self.assertTrue(usd_mesh_obj.GetFaceVertexCountsAttr().HasAuthoredValue())
        self.assertTrue(usd_mesh_obj.GetFaceVertexIndicesAttr().HasAuthoredValue())
        # The sample box.obj has normals and UVs
        normals_primvar: UsdGeom.Primvar = UsdGeom.PrimvarsAPI(usd_mesh_obj).GetPrimvar("normals")
        self.assertTrue(normals_primvar.IsDefined())
        self.assertTrue(normals_primvar.HasAuthoredValue())
        self.assertTrue(normals_primvar.GetIndicesAttr().HasAuthoredValue())
        uvs_primvar: UsdGeom.Primvar = UsdGeom.PrimvarsAPI(usd_mesh_obj).GetPrimvar("st")
        self.assertTrue(uvs_primvar.IsDefined())
        self.assertTrue(uvs_primvar.HasAuthoredValue())
        self.assertTrue(uvs_primvar.GetIndicesAttr().HasAuthoredValue())

        # Test mesh conversion with no name
        mesh_prim: Usd.Prim = stage.GetPrimAtPath(f"/{model_name}/Geometry/body1/body2/box")
        self.assertTrue(mesh_prim)
        # meshes are references to the geometry library layer
        self.assertTrue(mesh_prim.HasAuthoredReferences())
        usd_mesh = UsdGeom.Mesh(mesh_prim)
        self.assertTrue(usd_mesh.GetPointsAttr().HasAuthoredValue())
        self.assertTrue(usd_mesh.GetFaceVertexCountsAttr().HasAuthoredValue())
        self.assertTrue(usd_mesh.GetFaceVertexIndicesAttr().HasAuthoredValue())
