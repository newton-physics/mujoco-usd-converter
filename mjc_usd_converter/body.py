# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import mujoco
import usdex.core
from pxr import Sdf, Usd, UsdGeom, UsdPhysics

from ._future import Tokens
from .data import ConversionData
from .geom import convert_geom, get_geom_name
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

    # FUTURE: intertial
    # FUTURE: joints

    safe_names = data.name_cache.getPrimNames(body_prim, [x.name for x in body.bodies])
    for child_body, safe_name in zip(body.bodies, safe_names):
        child_body_prim = __convert_body(parent=body_prim, name=safe_name, body=child_body, data=data)
        if child_body_prim and body == data.spec.worldbody:
            child_body_over = data.content[Tokens.Physics].OverridePrim(child_body_prim.GetPath())
            UsdPhysics.ArticulationRootAPI.Apply(child_body_over)
            # FUTURE: consider freejoint

    return body_prim


def __is_kinematic(body: mujoco.MjsBody, physics_prim: Usd.Prim) -> bool:
    if body.mocap:
        return True

    kinematicAttr = UsdPhysics.RigidBodyAPI(physics_prim.GetParent()).GetKinematicEnabledAttr()
    return kinematicAttr and kinematicAttr.Get()
