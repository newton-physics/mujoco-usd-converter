# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import mujoco
import usdex.core
from pxr import Sdf, Usd, UsdGeom

from ._future import Tokens
from .data import ConversionData
from .geom import convert_geom, get_geom_name
from .utils import set_transform

__all__ = ["convert_bodies"]


def convert_bodies(data: ConversionData):
    geo_scope = data.content[Tokens.Geometry].GetDefaultPrim().GetChild(Tokens.Geometry).GetPrim()
    safe_names = data.name_cache.getPrimNames(geo_scope, [x.name for x in data.spec.worldbody.bodies])
    for body, safe_name in zip(data.spec.worldbody.bodies, safe_names):
        __convert_body(parent=geo_scope, name=safe_name, body=body, data=data)
        # FUTURE: articulation root
        # FUTURE: consider freejoint
        # FUTURE: mocap -> kinematicEnabled (recursive)

    safe_names = data.name_cache.getPrimNames(geo_scope, [get_geom_name(x) for x in data.spec.worldbody.geoms])
    for geom, safe_name in zip(data.spec.worldbody.geoms, safe_names):
        convert_geom(parent=geo_scope, name=safe_name, geom=geom, data=data)

    # FUTURE: lights, cameras, sites


def __convert_body(parent: Usd.Prim, name: str, body: mujoco.MjsBody, data: ConversionData) -> UsdGeom.Xform:
    body_xform = usdex.core.defineXform(parent, name)
    body_prim = body_xform.GetPrim()
    set_transform(body_xform, body, data.spec)
    # FUTURE: specialize from childclass (asset: spot, cassie)
    if name != body.name:
        usdex.core.setDisplayName(body_prim, body.name)

    # FUTURE: account for frame-local geom
    safe_names = data.name_cache.getPrimNames(body_prim, [get_geom_name(x) for x in body.geoms])
    for geom, safe_name in zip(body.geoms, safe_names):
        convert_geom(parent=body_prim, name=safe_name, geom=geom, data=data)

    # FUTURE: camera
    # FUTURE: light
    # FUTURE: site

    # FUTURE: author physics using MjcPhysics schemas
    # Store concept gaps as custom attributes
    body_over = data.content[Tokens.Physics].OverridePrim(body_prim.GetPath())
    body_over.CreateAttribute("mjc:body:gravcomp", Sdf.ValueTypeNames.Float, custom=True).Set(body.gravcomp)
    # FUTURE: intertial
    # FUTURE: joints

    safe_names = data.name_cache.getPrimNames(body_prim, [x.name for x in body.bodies])
    for child_body, safe_name in zip(body.bodies, safe_names):
        __convert_body(parent=body_prim, name=safe_name, body=child_body, data=data)
