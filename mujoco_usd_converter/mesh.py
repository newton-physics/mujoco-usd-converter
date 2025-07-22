# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import pathlib

import mujoco
import stl
import tinyobjloader
import usdex.core
from pxr import Gf, Tf, Usd, UsdGeom, Vt

from ._future import Tokens, addLibraryLayer
from .data import ConversionData
from .numpy import convert_vec3f_array
from .utils import set_transform

__all__ = ["convert_meshes"]


def convert_meshes(data: ConversionData):
    if not len(data.spec.meshes):
        return

    data.libraries[Tokens.Geometry] = addLibraryLayer(data.content[Tokens.Contents], Tokens.Geometry, format="usdc")
    data.references[Tokens.Geometry] = {}

    geo_scope = data.libraries[Tokens.Geometry].GetDefaultPrim()
    source_names = [__get_mesh_name(x) for x in data.spec.meshes]
    safe_names = data.name_cache.getPrimNames(geo_scope, source_names)
    for mesh, source_name, safe_name in zip(data.spec.meshes, source_names, safe_names):
        mesh_prim: Usd.Prim = usdex.core.defineXform(geo_scope, safe_name).GetPrim()
        data.references[Tokens.Geometry][source_name] = mesh_prim
        # FUTURE: specialize from class
        if source_name != safe_name:
            usdex.core.setDisplayName(mesh_prim, source_name)
        __convert_mesh(mesh_prim, mesh, data)

    usdex.core.saveStage(data.libraries[Tokens.Geometry], comment=f"Mesh Library for {data.spec.modelname}. {data.comment}")


def __get_mesh_name(mesh: mujoco.MjsMesh) -> str:
    if mesh.name:
        return mesh.name
    elif mesh.file:
        return pathlib.Path(mesh.file).stem
    else:
        return f"Mesh_{mesh.id}"


def __convert_mesh(prim: Usd.Prim, mesh: mujoco.MjsMesh, data: ConversionData):
    if not mesh.file:
        # FUTURE: support inline meshes
        raise Tf.RaiseRuntimeError(f"Mesh {mesh.name} has no file")

    mesh_file = pathlib.Path(data.spec.modelfiledir) / pathlib.Path(data.spec.meshdir) / pathlib.Path(mesh.file)
    if not mesh_file.exists():
        raise Tf.RaiseRuntimeError(f"Mesh {mesh.name} file {mesh_file} does not exist")

    if mesh.content_type == "model/stl" or mesh_file.suffix.lower() == ".stl":
        mesh_prim = __convert_stl(prim, mesh_file)
    elif mesh.content_type == "model/obj" or mesh_file.suffix.lower() == ".obj":
        mesh_prim = __convert_obj(prim, mesh_file)
    else:
        raise Tf.RaiseRuntimeError(
            f"Mesh {mesh.name} from file {mesh_file} has unsupported content_type {mesh.content_type} or extension {mesh_file.suffix}"
        )

    set_transform(mesh_prim, mesh, data.spec)


def __convert_stl(prim: Usd.Prim, input_path: pathlib.Path) -> UsdGeom.Mesh:
    stl_mesh = stl.Mesh.from_file(input_path, calculate_normals=False)

    points = usdex.core.Vec3fPrimvarData(UsdGeom.Tokens.vertex, convert_vec3f_array(stl_mesh.points))
    points.index()
    face_vertex_indices = points.indices()
    face_vertex_counts = [3] * stl_mesh.points.shape[0]

    normals = None
    if stl_mesh.normals.any():
        normals = usdex.core.Vec3fPrimvarData(UsdGeom.Tokens.uniform, convert_vec3f_array(stl_mesh.normals))
        normals.index()

    usd_mesh = usdex.core.definePolyMesh(
        prim.GetParent(),
        prim.GetName(),
        faceVertexCounts=Vt.IntArray(face_vertex_counts),
        faceVertexIndices=Vt.IntArray(face_vertex_indices),
        points=points.values(),
        normals=normals,
    )
    if not usd_mesh:
        Tf.RaiseRuntimeError(f'Failed to convert mesh "{prim.GetPath()}" from {input_path}')
    return usd_mesh


def __convert_obj(prim: Usd.Prim, input_path: pathlib.Path) -> UsdGeom.Mesh:
    reader = tinyobjloader.ObjReader()
    if not reader.ParseFromFile(str(input_path)):
        Tf.RaiseRuntimeError(f'Invalid input_path: "{input_path}" could not be parsed. {reader.Error()}')

    shapes = reader.GetShapes()
    if len(shapes) == 0:
        Tf.RaiseRuntimeError(f'Invalid input_path: "{input_path}" contains no meshes')
    elif len(shapes) > 1:
        Tf.Warn(f'"{input_path}" contains multiple meshes, only the first one will be converted')

    attrib = reader.GetAttrib()
    obj_mesh = shapes[0].mesh

    vertices = attrib.vertices
    face_vertex_counts = obj_mesh.num_face_vertices
    face_vertex_indices = obj_mesh.vertex_indices()

    points = [Gf.Vec3f(vertices[i], vertices[i + 1], vertices[i + 2]) for i in range(0, len(vertices), 3)]

    normals = None
    source_normals = attrib.normals
    if len(source_normals) > 0:
        normals_data = [Gf.Vec3f(source_normals[i], source_normals[i + 1], source_normals[i + 2]) for i in range(0, len(source_normals), 3)]
        normals = usdex.core.Vec3fPrimvarData(UsdGeom.Tokens.faceVarying, Vt.Vec3fArray(normals_data), Vt.IntArray(obj_mesh.normal_indices()))
        normals.index()  # re-index the normals to remove duplicates

    uvs = None
    source_uvs = attrib.texcoords
    if len(source_uvs) > 0:
        uv_data = [Gf.Vec2f(source_uvs[i], source_uvs[i + 1]) for i in range(0, len(source_uvs), 2)]
        uvs = usdex.core.Vec2fPrimvarData(UsdGeom.Tokens.faceVarying, Vt.Vec2fArray(uv_data), Vt.IntArray(obj_mesh.texcoord_indices()))
        uvs.index()  # re-index the uvs to remove duplicates

    usd_mesh = usdex.core.definePolyMesh(
        prim.GetParent(),
        prim.GetName(),
        faceVertexCounts=Vt.IntArray(face_vertex_counts),
        faceVertexIndices=Vt.IntArray(face_vertex_indices),
        points=Vt.Vec3fArray(points),
        normals=normals,
        uvs=uvs,
    )
    if not usd_mesh:
        Tf.RaiseRuntimeError(f'Failed to convert mesh "{prim.GetPath()}" from {input_path}')
    return usd_mesh
