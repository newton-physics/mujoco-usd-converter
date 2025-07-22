# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import usdex.core
from pxr import Gf, Usd, UsdPhysics, Vt

from .data import ConversionData, Tokens
from .numpy import convert_vec3d
from .utils import set_schema_attribute

__all__ = ["convert_scene"]


def convert_scene(data: ConversionData):
    asset_stage: Usd.Stage = data.content[Tokens.Asset]
    content_stage: Usd.Stage = data.content[Tokens.Contents]
    physics_stage: Usd.Stage = data.content[Tokens.Physics]

    # ensure the name is valid across all layers
    safe_name = data.name_cache.getPrimName(asset_stage.GetPseudoRoot(), "PhysicsScene")

    # author the scene in the physics layer
    scene: UsdPhysics.Scene = UsdPhysics.Scene.Define(physics_stage, asset_stage.GetPseudoRoot().GetPath().AppendChild(safe_name))
    scene_prim: Usd.Prim = scene.GetPrim()
    # apply the MJC scene API
    scene_prim.ApplyAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsSceneAPI"))

    # reference the scene in the asset layer, but from the content layer
    content_scene: Usd.Prim = content_stage.GetPseudoRoot().GetChild(safe_name)
    usdex.core.definePayload(asset_stage.GetPseudoRoot(), content_scene, safe_name)

    # set the gravity
    gravity_vector: Gf.Vec3d = convert_vec3d(data.spec.option.gravity)
    scene.CreateGravityDirectionAttr().Set(gravity_vector.GetNormalized())
    scene.CreateGravityMagnitudeAttr().Set(gravity_vector.GetLength())

    # Flag attributes - disable flags (default enabled = 1, disabled when bit is set)
    set_schema_attribute(scene_prim, "mjc:flag:actuation", not __is_disabled(1 << 10, data))
    set_schema_attribute(scene_prim, "mjc:flag:autoreset", not __is_disabled(1 << 15, data))
    set_schema_attribute(scene_prim, "mjc:flag:clampctrl", not __is_disabled(1 << 7, data))
    set_schema_attribute(scene_prim, "mjc:flag:constraint", not __is_disabled(1 << 0, data))
    set_schema_attribute(scene_prim, "mjc:flag:contact", not __is_disabled(1 << 4, data))
    set_schema_attribute(scene_prim, "mjc:flag:equality", not __is_disabled(1 << 1, data))
    set_schema_attribute(scene_prim, "mjc:flag:eulerdamp", not __is_disabled(1 << 14, data))
    set_schema_attribute(scene_prim, "mjc:flag:filterparent", not __is_disabled(1 << 9, data))
    set_schema_attribute(scene_prim, "mjc:flag:frictionloss", not __is_disabled(1 << 2, data))
    set_schema_attribute(scene_prim, "mjc:flag:gravity", not __is_disabled(1 << 6, data))
    set_schema_attribute(scene_prim, "mjc:flag:limit", not __is_disabled(1 << 3, data))
    set_schema_attribute(scene_prim, "mjc:flag:midphase", not __is_disabled(1 << 13, data))
    set_schema_attribute(scene_prim, "mjc:flag:nativeccd", not __is_disabled(1 << 16, data))
    set_schema_attribute(scene_prim, "mjc:flag:passive", not __is_disabled(1 << 5, data))
    set_schema_attribute(scene_prim, "mjc:flag:refsafe", not __is_disabled(1 << 11, data))
    set_schema_attribute(scene_prim, "mjc:flag:sensor", not __is_disabled(1 << 12, data))
    set_schema_attribute(scene_prim, "mjc:flag:warmstart", not __is_disabled(1 << 8, data))

    # Flag attributes - enable flags (default disabled = 0, enabled when bit is set)
    set_schema_attribute(scene_prim, "mjc:flag:energy", __is_enabled(1 << 1, data))
    set_schema_attribute(scene_prim, "mjc:flag:fwdinv", __is_enabled(1 << 2, data))
    set_schema_attribute(scene_prim, "mjc:flag:invdiscrete", __is_enabled(1 << 3, data))
    set_schema_attribute(scene_prim, "mjc:flag:island", __is_enabled(1 << 5, data))
    set_schema_attribute(scene_prim, "mjc:flag:multiccd", __is_enabled(1 << 4, data))
    set_schema_attribute(scene_prim, "mjc:flag:override", __is_enabled(1 << 0, data))

    actuator_groups = [i for i in range(31) if data.spec.option.disableactuator & (1 << i)]
    set_schema_attribute(scene_prim, "mjc:option:actuatorgroupdisable", Vt.IntArray(actuator_groups))

    set_schema_attribute(scene_prim, "mjc:option:apirate", data.spec.option.apirate)
    set_schema_attribute(scene_prim, "mjc:option:ccd_iterations", data.spec.option.ccd_iterations)
    set_schema_attribute(scene_prim, "mjc:option:ccd_tolerance", data.spec.option.ccd_tolerance)
    set_schema_attribute(scene_prim, "mjc:option:cone", __get_cone_token(data.spec.option.cone))
    set_schema_attribute(scene_prim, "mjc:option:density", data.spec.option.density)
    set_schema_attribute(scene_prim, "mjc:option:impratio", data.spec.option.impratio)
    set_schema_attribute(scene_prim, "mjc:option:integrator", __get_integrator_token(data.spec.option.integrator))
    set_schema_attribute(scene_prim, "mjc:option:iterations", data.spec.option.iterations)
    set_schema_attribute(scene_prim, "mjc:option:jacobian", __get_jacobian_token(data.spec.option.jacobian))
    set_schema_attribute(scene_prim, "mjc:option:ls_iterations", data.spec.option.ls_iterations)
    set_schema_attribute(scene_prim, "mjc:option:ls_tolerance", data.spec.option.ls_tolerance)
    set_schema_attribute(scene_prim, "mjc:option:magnetic", convert_vec3d(data.spec.option.magnetic))
    set_schema_attribute(scene_prim, "mjc:option:noslip_iterations", data.spec.option.noslip_iterations)
    set_schema_attribute(scene_prim, "mjc:option:noslip_tolerance", data.spec.option.noslip_tolerance)
    set_schema_attribute(scene_prim, "mjc:option:o_friction", Vt.DoubleArray(data.spec.option.o_friction))
    set_schema_attribute(scene_prim, "mjc:option:o_margin", data.spec.option.o_margin)
    set_schema_attribute(scene_prim, "mjc:option:o_solimp", Vt.DoubleArray(data.spec.option.o_solimp))
    set_schema_attribute(scene_prim, "mjc:option:o_solref", Vt.DoubleArray(data.spec.option.o_solref))
    set_schema_attribute(scene_prim, "mjc:option:sdf_initpoints", data.spec.option.sdf_initpoints)
    set_schema_attribute(scene_prim, "mjc:option:sdf_iterations", data.spec.option.sdf_iterations)
    set_schema_attribute(scene_prim, "mjc:option:solver", __get_solver_token(data.spec.option.solver))
    set_schema_attribute(scene_prim, "mjc:option:timestep", data.spec.option.timestep)
    set_schema_attribute(scene_prim, "mjc:option:tolerance", data.spec.option.tolerance)
    set_schema_attribute(scene_prim, "mjc:option:viscosity", data.spec.option.viscosity)
    set_schema_attribute(scene_prim, "mjc:option:wind", convert_vec3d(data.spec.option.wind))

    # mjc compiler settings
    set_schema_attribute(scene_prim, "mjc:compiler:alignFree", data.spec.compiler.alignfree)
    set_schema_attribute(scene_prim, "mjc:compiler:angle", __get_angle_token(data.spec.compiler.degree))
    set_schema_attribute(scene_prim, "mjc:compiler:autoLimits", data.spec.compiler.autolimits)
    set_schema_attribute(scene_prim, "mjc:compiler:balanceInertia", data.spec.compiler.balanceinertia)
    set_schema_attribute(scene_prim, "mjc:compiler:boundInertia", data.spec.compiler.boundinertia)
    set_schema_attribute(scene_prim, "mjc:compiler:boundMass", data.spec.compiler.boundmass)
    set_schema_attribute(scene_prim, "mjc:compiler:fitAABB", data.spec.compiler.fitaabb)
    set_schema_attribute(scene_prim, "mjc:compiler:fuseStatic", data.spec.compiler.fusestatic)
    set_schema_attribute(scene_prim, "mjc:compiler:inertiaFromGeom", __get_inertia_from_geom_token(data.spec.compiler.inertiafromgeom))
    set_schema_attribute(scene_prim, "mjc:compiler:inertiaGroupRange:max", int(data.spec.compiler.inertiagrouprange[1]))
    set_schema_attribute(scene_prim, "mjc:compiler:inertiaGroupRange:min", int(data.spec.compiler.inertiagrouprange[0]))
    set_schema_attribute(scene_prim, "mjc:compiler:saveInertial", data.spec.compiler.saveinertial)
    set_schema_attribute(scene_prim, "mjc:compiler:setTotalMass", data.spec.compiler.settotalmass)
    set_schema_attribute(scene_prim, "mjc:compiler:useThread", data.spec.compiler.usethread)


def __is_disabled(flag_bit: int, data: ConversionData) -> bool:
    return bool(data.spec.option.disableflags & flag_bit)


def __is_enabled(flag_bit: int, data: ConversionData) -> bool:
    return bool(data.spec.option.enableflags & flag_bit)


def __get_integrator_token(integrator: int) -> str:
    return {0: "euler", 1: "rk4", 2: "implicit", 3: "implicitfast"}[integrator]


def __get_cone_token(cone: int) -> str:
    return {0: "pyramidal", 1: "elliptic"}[cone]


def __get_jacobian_token(jacobian: int) -> str:
    return {0: "dense", 1: "sparse", 2: "auto"}[jacobian]


def __get_solver_token(solver: int) -> str:
    return {0: "pgs", 1: "cg", 2: "newton"}[solver]


def __get_angle_token(degree: bool) -> str:
    return "degree" if degree else "radian"


def __get_inertia_from_geom_token(inertiafromgeom: int) -> str:
    return {0: "false", 1: "true", 2: "auto"}[inertiafromgeom]
