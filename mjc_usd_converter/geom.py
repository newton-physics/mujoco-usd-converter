# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import mujoco
import numpy as np
import usdex.core
from pxr import Gf, Tf, Usd, UsdGeom, UsdShade, Vt

from ._future import Tokens, defineRelativeReference
from .data import ConversionData
from .numpy import convert_color
from .utils import get_fromto_vectors, set_purpose, set_transform

__all__ = ["convert_geom", "get_geom_name"]


def get_geom_name(geom: mujoco.MjsGeom) -> str:
    if geom.name:
        return geom.name

    if geom.type == mujoco.mjtGeom.mjGEOM_MESH:
        return geom.meshname or UsdGeom.Tokens.Mesh
    elif geom.type == mujoco.mjtGeom.mjGEOM_PLANE:
        return UsdGeom.Tokens.Plane
    elif geom.type == mujoco.mjtGeom.mjGEOM_SPHERE:
        return UsdGeom.Tokens.Sphere
    elif geom.type == mujoco.mjtGeom.mjGEOM_BOX:
        return "Box"  # USD uses Cube
    elif geom.type == mujoco.mjtGeom.mjGEOM_CYLINDER:
        return UsdGeom.Tokens.Cylinder
    elif geom.type == mujoco.mjtGeom.mjGEOM_CAPSULE:
        return UsdGeom.Tokens.Capsule
    elif geom.type == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
        return "Ellipsoid"
    elif geom.type == mujoco.mjtGeom.mjGEOM_HFIELD:
        return "HField"
    elif geom.type == mujoco.mjtGeom.mjGEOM_SDF:
        return "SDF"
    else:
        Tf.Warn(f"Unsupported or unknown geom type {geom.type}")
        return ""


def convert_geom(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Gprim:
    source_name = get_geom_name(geom)
    if geom.type == mujoco.mjtGeom.mjGEOM_MESH:
        geom_prim = __convert_mesh(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_PLANE:
        geom_prim = __convert_plane(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_SPHERE:
        geom_prim = __convert_sphere(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_BOX:
        geom_prim = __convert_box(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_CYLINDER:
        geom_prim = __convert_cylinder(parent, name, geom, data)
    elif geom.type == mujoco.mjtGeom.mjGEOM_CAPSULE:
        geom_prim = __convert_capsule(parent, name, geom, data)
    else:
        Tf.Warn(f"Unsupported or unknown geom type {geom.type} for geom '{source_name}'")
        return Usd.Prim()

    # FUTURE: specialize from class (asset: spot (type, group, scale, pos), shadow_hand (type, material, group, scale), barkour (rgba))

    set_purpose(geom_prim, geom.group)
    set_transform(geom_prim, geom, data.spec)
    if source_name and geom_prim.GetPrim().GetName() != source_name:
        usdex.core.setDisplayName(geom_prim.GetPrim(), source_name)

    if geom.material:
        __bind_material(geom_prim, geom.material, data)

    # set color and opacity primvars when they are not the default
    if not np.array_equal(geom.rgba, data.spec.default.geom.rgba):
        color, opacity = convert_color(geom.rgba)
        usdex.core.Vec3fPrimvarData(UsdGeom.Tokens.constant, Vt.Vec3fArray([color])).setPrimvar(geom_prim.CreateDisplayColorPrimvar())
        usdex.core.FloatPrimvarData(UsdGeom.Tokens.constant, Vt.FloatArray([opacity])).setPrimvar(geom_prim.CreateDisplayOpacityPrimvar())

    # FUTURE: physics

    return geom_prim


def __convert_mesh(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Mesh:
    ref_mesh: Usd.Prim = data.references[Tokens.Geometry].get(geom.meshname)
    if not ref_mesh:
        Tf.RaiseRuntimeError(f"Mesh '{geom.meshname}' not found in Geometry Library {data.libraries[Tokens.Geometry].GetRootLayer().identifier}")
    prim = defineRelativeReference(parent, ref_mesh, name)
    # the reference mesh may have an invalid source name, and thus a display name
    # however, the prim name may already be valid and override this, in which case
    # we need to block the referenced display name
    if prim.GetPrim().GetName() != ref_mesh.GetPrim().GetName():
        usdex.core.blockDisplayName(prim.GetPrim())
    return UsdGeom.Mesh(prim)


def __convert_plane(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Plane:
    plane: UsdGeom.Plane = UsdGeom.Plane.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    half_width = geom.size[0]
    half_length = geom.size[1]
    # special case for infinite plane in MuJoCo, we need to set a reasonable width and length for USD
    # note that for UsdPhysics the plane is treated as infinite regardless, this is just for visualization
    if half_width == 0:
        half_width = UsdGeom.GetStageMetersPerUnit(parent.GetStage()) * 10
    if half_length == 0:
        half_length = UsdGeom.GetStageMetersPerUnit(parent.GetStage()) * 10
    plane.GetWidthAttr().Set(half_width * 2)
    plane.GetLengthAttr().Set(half_length * 2)
    plane.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(plane, Usd.TimeCode.Default()))
    return plane


def __convert_sphere(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Sphere:
    sphere: UsdGeom.Sphere = UsdGeom.Sphere.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    sphere.GetRadiusAttr().Set(geom.size[0])
    sphere.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(sphere, Usd.TimeCode.Default()))
    # FUTURE: mesh/fitscale
    return sphere


def __convert_box(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Cube:
    start, end = get_fromto_vectors(geom)
    # FUTURE: mesh/fitscale
    if start is not None and end is not None:
        width = length = geom.size[0]
        height = (end - start).GetLength() / 2.0
    else:
        width = geom.size[0]
        length = geom.size[1]
        height = geom.size[2]

    cube: UsdGeom.Cube = UsdGeom.Cube.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    cube.GetSizeAttr().Set(2)  # author the default explicitly
    scale_op = cube.AddScaleOp()
    scale_op.Set(Gf.Vec3f(width, length, height))
    cube.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(cube, Usd.TimeCode.Default()))
    return cube


def __convert_cylinder(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Cylinder:
    radius = geom.size[0]
    start, end = get_fromto_vectors(geom)
    # FUTURE: mesh/fitscale
    if start is not None and end is not None:  # noqa: SIM108
        height = (end - start).GetLength()
    else:
        height = geom.size[1] * 2

    cylinder: UsdGeom.Cylinder = UsdGeom.Cylinder.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    cylinder.GetAxisAttr().Set(UsdGeom.Tokens.z)
    cylinder.GetRadiusAttr().Set(radius)
    cylinder.GetHeightAttr().Set(height)
    cylinder.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(cylinder, Usd.TimeCode.Default()))
    return cylinder


def __convert_capsule(parent: Usd.Prim, name: str, geom: mujoco.MjsGeom, data: ConversionData) -> UsdGeom.Capsule:
    radius = geom.size[0]
    start, end = get_fromto_vectors(geom)
    # FUTURE: mesh/fitscale
    if start is not None and end is not None:  # noqa: SIM108
        height = (end - start).GetLength()
    else:
        height = geom.size[1] * 2

    capsule: UsdGeom.Capsule = UsdGeom.Capsule.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    capsule.GetAxisAttr().Set(UsdGeom.Tokens.z)
    capsule.GetRadiusAttr().Set(radius)
    capsule.GetHeightAttr().Set(height)
    capsule.CreateExtentAttr().Set(UsdGeom.Boundable.ComputeExtentFromPlugins(capsule, Usd.TimeCode.Default()))
    return capsule


def __bind_material(geom_prim: Usd.Prim, name: str, data: ConversionData):
    local_materials = data.content[Tokens.Materials].GetDefaultPrim().GetChild(Tokens.Materials)
    ref_material: Usd.Prim = data.references[Tokens.Materials].get(name)
    if not ref_material:
        Tf.RaiseRuntimeError(f"Material '{name}' not found in Material Library {data.libraries[Tokens.Materials].GetRootLayer().identifier}")
    material_prim = UsdShade.Material(local_materials.GetChild(ref_material.GetName()))
    if not material_prim:
        material_prim = UsdShade.Material(defineRelativeReference(local_materials, ref_material, ref_material.GetName()))
    geom_over = data.content[Tokens.Materials].OverridePrim(geom_prim.GetPath())
    usdex.core.bindMaterial(geom_over, material_prim)
