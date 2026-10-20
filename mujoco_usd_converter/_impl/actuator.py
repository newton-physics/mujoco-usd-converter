# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import mujoco
import usdex.core
from pxr import Tf, Usd

from .data import ConversionData, Tokens
from .utils import mj_limited_to_token, set_schema_attribute

__all__ = ["convert_actuators"]


def convert_actuators(data: ConversionData):
    if not data.spec.actuators:
        return

    actuators = [actuator for actuator in data.spec.actuators if is_supported(actuator)]

    # Convert each actuator to a MjcActuator prim
    physics_scope = data.content[Tokens.Physics].GetDefaultPrim().GetChild(Tokens.Physics)
    source_names = [get_actuator_name(actuator) for actuator in actuators]
    safe_names = data.name_cache.getPrimNames(physics_scope, source_names)
    for actuator, source_name, safe_name in zip(actuators, source_names, safe_names):
        actuator_prim = convert_actuator(physics_scope, safe_name, actuator, data)
        if source_name != safe_name:
            usdex.core.setDisplayName(actuator_prim, source_name)


def is_supported(actuator: mujoco.MjsActuator) -> bool:
    unsupported = []
    if convert_gain_type(actuator.gaintype) is None:
        unsupported.append(f"gain type '{get_unsupported_gain_type(actuator.gaintype)}'")
    if convert_bias_type(actuator.biastype) is None:
        unsupported.append(f"bias type '{get_unsupported_bias_type(actuator.biastype)}'")
    if convert_dyn_type(actuator.dyntype) is None:
        unsupported.append(f"dyn type '{get_unsupported_dyn_type(actuator.dyntype)}'")
    if unsupported:
        Tf.Warn(f"Actuator '{get_actuator_name(actuator)}' is not converted because the MjcPhysics schema does not support: {', '.join(unsupported)}")
    return not unsupported


def get_unsupported_gain_type(gaintype: mujoco.mjtGain) -> str:
    if gaintype == mujoco.mjtGain.mjGAIN_DCMOTOR:
        return "dcmotor"
    elif gaintype == mujoco.mjtGain.mjGAIN_SO3:
        return "so3"
    elif gaintype == mujoco.mjtGain.mjGAIN_PID:
        return "pid"
    return str(gaintype)


def get_unsupported_bias_type(biastype: mujoco.mjtBias) -> str:
    if biastype == mujoco.mjtBias.mjBIAS_DCMOTOR:
        return "dcmotor"
    elif biastype == mujoco.mjtBias.mjBIAS_SO3:
        return "so3"
    return str(biastype)


def get_unsupported_dyn_type(dyntype: mujoco.mjtDyn) -> str:
    if dyntype == mujoco.mjtDyn.mjDYN_DCMOTOR:
        return "dcmotor"
    elif dyntype == mujoco.mjtDyn.mjDYN_PID:
        return "pid"
    return str(dyntype)


def get_actuator_name(actuator: mujoco.MjsActuator) -> str:
    if actuator.name:
        return actuator.name
    else:
        return f"Actuator_{actuator.id}"


def convert_actuator(parent: Usd.Prim, name: str, actuator: mujoco.MjsActuator, data: ConversionData) -> Usd.Prim:
    actuator_prim: Usd.Prim = parent.GetStage().DefinePrim(parent.GetPath().AppendChild(name))
    actuator_prim.SetTypeName("MjcActuator")

    set_schema_attribute(actuator_prim, "mjc:group", actuator.group)

    if actuator.trntype == mujoco.mjtTrn.mjTRN_BODY:
        references = data.references[Tokens.PhysicsBodies]
    elif actuator.trntype == mujoco.mjtTrn.mjTRN_JOINT:
        references = data.references[Tokens.PhysicsJoints]
    elif actuator.trntype == mujoco.mjtTrn.mjTRN_SITE or actuator.trntype == mujoco.mjtTrn.mjTRN_SLIDERCRANK:
        references = data.references[Tokens.PhysicsSites]
    elif actuator.trntype == mujoco.mjtTrn.mjTRN_TENDON:
        references = data.references[Tokens.PhysicsTendons]
    else:
        Tf.Warn(f"Unsupported transmission type '{actuator.trntype}' for actuator '{actuator.name}'")
        return actuator_prim

    if actuator.target and actuator.target in references:
        target_path = references[actuator.target].GetPath()
        actuator_prim.GetRelationship("mjc:target").SetTargets([target_path])
    else:
        Tf.Warn(f"Target '{actuator.target}' not found for actuator '{actuator.name}'")
        return actuator_prim

    if actuator.refsite:
        if actuator.refsite in data.references[Tokens.PhysicsSites]:
            refsite_path = data.references[Tokens.PhysicsSites][actuator.refsite].GetPath()
            actuator_prim.GetRelationship("mjc:refSite").SetTargets([refsite_path])
        else:
            Tf.Warn(f"Refsite '{actuator.refsite}' not found for actuator '{actuator.name}'")
            return actuator_prim

    if actuator.slidersite:
        if actuator.slidersite in data.references[Tokens.PhysicsSites]:
            slidersite_path = data.references[Tokens.PhysicsSites][actuator.slidersite].GetPath()
            actuator_prim.GetRelationship("mjc:sliderSite").SetTargets([slidersite_path])
        else:
            Tf.Warn(f"Slidersite '{actuator.slidersite}' not found for actuator '{actuator.name}'")
            return actuator_prim

    set_schema_attribute(actuator_prim, "mjc:actDim", actuator.actdim)
    set_schema_attribute(actuator_prim, "mjc:actEarly", bool(actuator.actearly))
    set_schema_attribute(actuator_prim, "mjc:actLimited", mj_limited_to_token(actuator.actlimited))
    set_schema_attribute(actuator_prim, "mjc:actRange:min", actuator.actrange[0])
    set_schema_attribute(actuator_prim, "mjc:actRange:max", actuator.actrange[1])
    set_schema_attribute(actuator_prim, "mjc:biasPrm", list(actuator.biasprm))
    set_schema_attribute(actuator_prim, "mjc:biasType", convert_bias_type(actuator.biastype))
    set_schema_attribute(actuator_prim, "mjc:crankLength", actuator.cranklength)
    set_schema_attribute(actuator_prim, "mjc:ctrlLimited", mj_limited_to_token(actuator.ctrllimited))
    set_schema_attribute(actuator_prim, "mjc:ctrlRange:min", actuator.ctrlrange[0])
    set_schema_attribute(actuator_prim, "mjc:ctrlRange:max", actuator.ctrlrange[1])
    set_schema_attribute(actuator_prim, "mjc:dynPrm", list(actuator.dynprm))
    set_schema_attribute(actuator_prim, "mjc:dynType", convert_dyn_type(actuator.dyntype))
    set_schema_attribute(actuator_prim, "mjc:forceLimited", mj_limited_to_token(actuator.forcelimited))
    set_schema_attribute(actuator_prim, "mjc:forceRange:min", actuator.forcerange[0])
    set_schema_attribute(actuator_prim, "mjc:forceRange:max", actuator.forcerange[1])
    set_schema_attribute(actuator_prim, "mjc:gainPrm", list(actuator.gainprm))
    set_schema_attribute(actuator_prim, "mjc:gainType", convert_gain_type(actuator.gaintype))
    set_schema_attribute(actuator_prim, "mjc:gear", list(actuator.gear))
    set_schema_attribute(actuator_prim, "mjc:group", actuator.group)
    set_schema_attribute(actuator_prim, "mjc:inheritRange", actuator.inheritrange)
    set_schema_attribute(actuator_prim, "mjc:lengthRange:min", actuator.lengthrange[0])
    set_schema_attribute(actuator_prim, "mjc:lengthRange:max", actuator.lengthrange[1])

    return actuator_prim


def convert_dyn_type(dyntype: mujoco.mjtDyn) -> str:
    if dyntype == mujoco.mjtDyn.mjDYN_NONE:
        return "none"
    elif dyntype == mujoco.mjtDyn.mjDYN_INTEGRATOR:
        return "integrator"
    elif dyntype == mujoco.mjtDyn.mjDYN_FILTER:
        return "filter"
    elif dyntype == mujoco.mjtDyn.mjDYN_FILTEREXACT:
        return "filterexact"
    elif dyntype == mujoco.mjtDyn.mjDYN_MUSCLE:
        return "muscle"
    elif dyntype == mujoco.mjtDyn.mjDYN_USER:
        return "user"


def convert_gain_type(gaintype: mujoco.mjtGain) -> str:
    if gaintype == mujoco.mjtGain.mjGAIN_FIXED:
        return "fixed"
    elif gaintype == mujoco.mjtGain.mjGAIN_AFFINE:
        return "affine"
    elif gaintype == mujoco.mjtGain.mjGAIN_MUSCLE:
        return "muscle"
    elif gaintype == mujoco.mjtGain.mjGAIN_USER:
        return "user"


def convert_bias_type(biastype: mujoco.mjtBias) -> str:
    if biastype == mujoco.mjtBias.mjBIAS_NONE:
        return "none"
    elif biastype == mujoco.mjtBias.mjBIAS_AFFINE:
        return "affine"
    elif biastype == mujoco.mjtBias.mjBIAS_MUSCLE:
        return "muscle"
    elif biastype == mujoco.mjtBias.mjBIAS_USER:
        return "user"
