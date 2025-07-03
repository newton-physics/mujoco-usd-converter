# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import mujoco
import numpy as np
import usdex.core
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

from ._future import Tokens
from .data import ConversionData
from .geom import convert_geom, get_geom_name
from .joint import convert_joints
from .numpy import convert_quat, convert_vec3d
from .utils import set_transform

__all__ = ["convert_bodies"]


def convert_bodies(data: ConversionData):
    geo_scope = data.content[Tokens.Geometry].GetDefaultPrim().GetChild(Tokens.Geometry).GetPrim()
    __convert_body(parent=geo_scope, name=data.spec.modelname, body=data.spec.worldbody, data=data)


def __convert_body(parent: Usd.Prim, name: str, body: mujoco.MjsBody, data: ConversionData) -> UsdGeom.Xform:
    if body == data.spec.worldbody:
        # the worldbody is already converted as the default prim and
        # its children need to be nested under the geometry scope
        body_prim = parent
    else:
        body_xform = usdex.core.defineXform(parent, name)
        body_prim = body_xform.GetPrim()
        set_transform(body_xform, body, data.spec)
        # FUTURE: specialize from childclass (asset: spot, cassie)
        if name != body.name:
            usdex.core.setDisplayName(body_prim, body.name)

    safe_names = data.name_cache.getPrimNames(body_prim, [get_geom_name(x) for x in body.geoms])
    for geom, safe_name in zip(body.geoms, safe_names):
        convert_geom(parent=body_prim, name=safe_name, geom=geom, data=data)

    # sites are specialized geoms used as frame markers, so we convert them as guide Gprims
    safe_names = data.name_cache.getPrimNames(body_prim, [get_geom_name(x) for x in body.sites])
    for site, safe_name in zip(body.sites, safe_names):
        if site_prim := convert_geom(parent=body_prim, name=safe_name, geom=site, data=data):
            site_prim.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
            site_prim.GetPrim().ApplyAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsSiteAPI"))

    # FUTURE: camera
    # FUTURE: light

    if body != data.spec.worldbody:
        body_over = data.content[Tokens.Physics].OverridePrim(body_prim.GetPath())
        rbd: UsdPhysics.RigidBodyAPI = UsdPhysics.RigidBodyAPI.Apply(body_over)
        # when the parent body is kinematic, the child body must also be kinematic
        if __is_kinematic(body, body_over):
            rbd.CreateKinematicEnabledAttr().Set(True)

        # Store concept gaps as custom attributes
        # FUTURE: use MjcPhysics schemas
        if body.gravcomp != 0:
            body_over.CreateAttribute("mjc:body:gravcomp", Sdf.ValueTypeNames.Float, custom=True).Set(body.gravcomp)

        if body.explicitinertial:
            mass_api: UsdPhysics.MassAPI = UsdPhysics.MassAPI.Apply(body_over)
            mass_api.CreateMassAttr().Set(body.mass)
            mass_api.CreateCenterOfMassAttr().Set(convert_vec3d(body.ipos))
            if np.isnan(body.fullinertia[0]):
                mass_api.CreatePrincipalAxesAttr().Set(convert_quat(body.iquat))
                mass_api.CreateDiagonalInertiaAttr().Set(convert_vec3d(body.inertia))
            else:
                quat, inertia = __extract_inertia(body.fullinertia)
                mass_api.CreatePrincipalAxesAttr().Set(quat)
                mass_api.CreateDiagonalInertiaAttr().Set(inertia)

        convert_joints(parent=body_over, body=body, data=data)

    safe_names = data.name_cache.getPrimNames(body_prim, [x.name for x in body.bodies])
    for child_body, safe_name in zip(body.bodies, safe_names):
        child_body_prim = __convert_body(parent=body_prim, name=safe_name, body=child_body, data=data)
        if child_body_prim and body == data.spec.worldbody:
            child_body_over = data.content[Tokens.Physics].OverridePrim(child_body_prim.GetPath())
            UsdPhysics.ArticulationRootAPI.Apply(child_body_over)

    return body_prim


def __is_kinematic(body: mujoco.MjsBody, physics_prim: Usd.Prim) -> bool:
    if body.mocap:
        return True

    kinematic_attr = UsdPhysics.RigidBodyAPI(physics_prim.GetParent()).GetKinematicEnabledAttr()
    return kinematic_attr and kinematic_attr.Get()


def __extract_inertia(fullinertia: np.ndarray) -> tuple[Gf.Quatf, Gf.Vec3f]:
    mat = np.zeros((3, 3))
    mat[0, 0] = fullinertia[0]
    mat[1, 1] = fullinertia[1]
    mat[2, 2] = fullinertia[2]
    mat[0, 1] = fullinertia[3]
    mat[1, 0] = fullinertia[3]
    mat[0, 2] = fullinertia[4]
    mat[2, 0] = fullinertia[4]
    mat[1, 2] = fullinertia[5]
    mat[2, 1] = fullinertia[5]

    # mju_eig3 expects flattened column-major matrix
    flat_mat = mat.flatten("F")

    eigval = np.zeros(3)
    eigvec = np.zeros(9)
    quat = np.zeros(4)

    # Call mju_eig3 to get principal axes and diagonal inertia
    mujoco.mju_eig3(eigval, eigvec, quat, flat_mat)
    diag_inertia = Gf.Vec3f(*eigval)

    return convert_quat(quat), diag_inertia
