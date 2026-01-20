# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import pathlib

import mujoco
import numpy as np
import stl
import tinyobjloader
import usdex.core
from pxr import Tf, Usd, UsdGeom, Vt

from .data import ConversionData, Tokens
from .numpy import convert_vec3f_array
from .utils import set_transform

__all__ = ["convert_meshes"]


def convert_meshes(data: ConversionData):
    if not len(data.spec.meshes):
        return

    data.libraries[Tokens.Geometry] = usdex.core.addAssetLibrary(data.content[Tokens.Contents], Tokens.Geometry, format="usdc")
    data.references[Tokens.Geometry] = {}

    geo_scope = data.libraries[Tokens.Geometry].GetDefaultPrim()
    source_names = [get_mesh_name(x) for x in data.spec.meshes]
    safe_names = data.name_cache.getPrimNames(geo_scope, source_names)
    for mesh, source_name, safe_name in zip(data.spec.meshes, source_names, safe_names):
        mesh_prim: Usd.Prim = usdex.core.defineXform(geo_scope, safe_name).GetPrim()
        data.references[Tokens.Geometry][source_name] = mesh_prim
        # FUTURE: specialize from class
        if source_name != safe_name:
            usdex.core.setDisplayName(mesh_prim, source_name)
        convert_mesh(mesh_prim, mesh, data)

    usdex.core.saveStage(data.libraries[Tokens.Geometry], comment=f"Mesh Library for {data.spec.modelname}. {data.comment}")


def get_mesh_name(mesh: mujoco.MjsMesh) -> str:
    if mesh.name:
        return mesh.name
    elif mesh.file:
        return pathlib.Path(mesh.file).stem
    else:
        return f"Mesh_{mesh.id}"


def convert_mesh(prim: Usd.Prim, mesh: mujoco.MjsMesh, data: ConversionData):
    if not mesh.file:
        # FUTURE: support inline meshes
        raise Tf.RaiseRuntimeError(f"Mesh {mesh.name} has no file")

    mesh_file = pathlib.Path(data.spec.modelfiledir) / pathlib.Path(data.spec.meshdir) / pathlib.Path(mesh.file)
    if not mesh_file.exists():
        raise Tf.RaiseRuntimeError(f"Mesh {mesh.name} file {mesh_file} does not exist")

    if mesh.content_type == "model/stl" or mesh_file.suffix.lower() == ".stl":
        mesh_prim = convert_stl(prim, mesh_file)
    elif mesh.content_type == "model/obj" or mesh_file.suffix.lower() == ".obj":
        mesh_prim = convert_obj(prim, mesh_file)
    else:
        raise Tf.RaiseRuntimeError(
            f"Mesh {mesh.name} from file {mesh_file} has unsupported content_type {mesh.content_type} or extension {mesh_file.suffix}"
        )

    set_transform(mesh_prim, mesh, data.spec)


def convert_stl(prim: Usd.Prim, input_path: pathlib.Path) -> UsdGeom.Mesh:
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


def convert_obj(prim: Usd.Prim, input_path: pathlib.Path) -> UsdGeom.Mesh:
    reader = tinyobjloader.ObjReader()
    if not reader.ParseFromFile(str(input_path)):
        Tf.RaiseRuntimeError(f'Invalid input_path: "{input_path}" could not be parsed. {reader.Error()}')

    shapes = reader.GetShapes()
    if len(shapes) == 0:
        Tf.RaiseRuntimeError(f'Invalid input_path: "{input_path}" contains no meshes')
    elif len(shapes) > 1:
        Tf.Warn(f'"{input_path.name}" contains multiple meshes, only the first one will be converted')

    attrib = reader.GetAttrib()
    obj_mesh = shapes[0].mesh

    face_vertex_counts = Vt.IntArray(obj_mesh.num_face_vertices)
    vertex_indices_in_shape = np.array(obj_mesh.vertex_indices(), dtype=np.int32)
    unique_vertex_indices = np.unique(vertex_indices_in_shape)
    face_vertex_indices = Vt.IntArray.FromNumpy(np.searchsorted(unique_vertex_indices, vertex_indices_in_shape))

    vertices_array = np.array(attrib.vertices, dtype=np.float32).reshape(-1, 3)
    points = Vt.Vec3fArray.FromNumpy(vertices_array[unique_vertex_indices])

    normals = None
    if len(attrib.normals) > 0:
        normal_indices_in_shape = np.array(obj_mesh.normal_indices(), dtype=np.int32)
        unique_normal_indices = np.unique(normal_indices_in_shape)

        normals_array = np.array(attrib.normals, dtype=np.float32).reshape(-1, 3)
        normals_data = normals_array[unique_normal_indices]

        remapped_normal_indices = np.searchsorted(unique_normal_indices, normal_indices_in_shape)
        normals = usdex.core.Vec3fPrimvarData(
            UsdGeom.Tokens.faceVarying,
            Vt.Vec3fArray.FromNumpy(normals_data),
            Vt.IntArray.FromNumpy(remapped_normal_indices),
        )
        normals.index()  # re-index the normals to remove duplicates

    uvs = None
    if len(attrib.texcoords) > 0:
        texcoord_indices_in_shape = np.array(obj_mesh.texcoord_indices(), dtype=np.int32)
        unique_texcoord_indices = np.unique(texcoord_indices_in_shape)

        texcoords_array = np.array(attrib.texcoords, dtype=np.float32).reshape(-1, 2)
        uv_data = texcoords_array[unique_texcoord_indices]

        remapped_texcoord_indices = np.searchsorted(unique_texcoord_indices, texcoord_indices_in_shape)
        uvs = usdex.core.Vec2fPrimvarData(
            UsdGeom.Tokens.faceVarying,
            Vt.Vec2fArray.FromNumpy(uv_data),
            Vt.IntArray.FromNumpy(remapped_texcoord_indices),
        )
        uvs.index()  # re-index the uvs to remove duplicates

    usd_mesh = usdex.core.definePolyMesh(prim, face_vertex_counts, face_vertex_indices, points, normals, uvs)
    if not usd_mesh:
        Tf.RaiseRuntimeError(f'Failed to convert mesh "{prim.GetPath()}" from {input_path}')
    return usd_mesh
