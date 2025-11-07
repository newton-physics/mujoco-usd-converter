# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import mujoco
import numpy as np
import usdex.core
from pxr import Gf, Tf, Usd, UsdPhysics

from .data import ConversionData, Tokens
from .numpy import convert_vec3d, convert_vec3f
from .utils import mj_limited_to_token, set_schema_attribute

__all__ = ["convert_joints", "get_joint_name"]


def get_joint_name(joint: mujoco.MjsJoint) -> str:
    if joint.name:
        return joint.name
    if joint.type == mujoco.mjtJoint.mjJNT_HINGE:
        return UsdPhysics.Tokens.PhysicsRevoluteJoint
    elif joint.type == mujoco.mjtJoint.mjJNT_SLIDE:
        return UsdPhysics.Tokens.PhysicsPrismaticJoint
    elif joint.type == mujoco.mjtJoint.mjJNT_BALL:
        return UsdPhysics.Tokens.PhysicsSphericalJoint
    elif joint.type == mujoco.mjtJoint.mjJNT_FREE:
        return "FreeJoint"
    else:
        Tf.Warn(f"Unsupported or unknown joint type {joint.type}")
        return ""


def convert_joints(parent: Usd.Prim, body: mujoco.MjsBody, data: ConversionData):
    # if the ancestor is the worldbody, we need to constrain to the default prim rather than the immediate parent (the Geometry Scope)
    body0: Usd.Prim = parent.GetStage().GetDefaultPrim() if body.parent == data.spec.worldbody else parent.GetParent()
    # we need to use the geometry prims for the bodies, otherwise the joint frame alignment will be authored in the wrong space
    # both bodies are only ever queried in this function, so we don't need to worry about setting edit targets
    body0 = data.content[Tokens.Geometry].GetPrimAtPath(body0.GetPath())
    body1: Usd.Prim = data.content[Tokens.Geometry].GetPrimAtPath(parent.GetPath())

    # In MJC, if there is no joint defined between nested bodies this implies the bodies are welded together
    # so we need to author a fixed joint between the parent and the ancestor.
    if not body.joints:
        name = data.name_cache.getPrimName(parent, UsdPhysics.Tokens.PhysicsFixedJoint)
        frame = usdex.core.JointFrame(usdex.core.JointFrame.Space.Body1, Gf.Vec3d(0, 0, 0), Gf.Quatd.GetIdentity())
        usdex.core.definePhysicsFixedJoint(parent, name, body0, body1, frame)
        return

    source_names = [get_joint_name(x) for x in body.joints]
    safe_names = data.name_cache.getPrimNames(parent, source_names)
    for joint, source_name, safe_name in zip(body.joints, source_names, safe_names):
        limits = get_limits(joint, data)
        axis = convert_vec3f(joint.axis)
        frame = usdex.core.JointFrame(usdex.core.JointFrame.Space.Body1, convert_vec3d(joint.pos), Gf.Quatd.GetIdentity())
        if joint.type == mujoco.mjtJoint.mjJNT_HINGE:
            joint_prim = usdex.core.definePhysicsRevoluteJoint(parent, safe_name, body0, body1, frame, axis, limits[0], limits[1])
        elif joint.type == mujoco.mjtJoint.mjJNT_SLIDE:
            joint_prim = usdex.core.definePhysicsPrismaticJoint(parent, safe_name, body0, body1, frame, axis, limits[0], limits[1])
        elif joint.type == mujoco.mjtJoint.mjJNT_BALL:
            # only the upper limit is used for ball joints and it applies to both cone angles
            joint_prim = usdex.core.definePhysicsSphericalJoint(parent, safe_name, body0, body1, frame, axis, limits[1], limits[1])
        elif joint.type == mujoco.mjtJoint.mjJNT_FREE:
            # Bodies in USD are free by default, so we don't need to author a joint
            continue

        if source_name and joint_prim.GetPrim().GetName() != source_name:
            usdex.core.setDisplayName(joint_prim.GetPrim(), source_name)

        data.references[Tokens.Physics][joint.name] = joint_prim.GetPrim()

        apply_mjc_joint_api(joint_prim.GetPrim(), joint)


def apply_mjc_joint_api(prim: Usd.Prim, joint: mujoco.MjsJoint):
    prim.ApplyAPI(Usd.SchemaRegistry.GetSchemaTypeName("MjcPhysicsJointAPI"))

    limited_token = mj_limited_to_token(joint.actfrclimited)
    set_schema_attribute(prim, "mjc:actuatorfrclimited", limited_token)
    set_schema_attribute(prim, "mjc:actuatorfrcrange:min", joint.actfrcrange[0])
    set_schema_attribute(prim, "mjc:actuatorfrcrange:max", joint.actfrcrange[1])
    set_schema_attribute(prim, "mjc:actuatorgravcomp", bool(joint.actgravcomp))
    set_schema_attribute(prim, "mjc:armature", joint.armature)
    set_schema_attribute(prim, "mjc:damping", joint.damping)
    set_schema_attribute(prim, "mjc:frictionloss", joint.frictionloss)
    set_schema_attribute(prim, "mjc:group", joint.group)
    set_schema_attribute(prim, "mjc:margin", joint.margin)
    set_schema_attribute(prim, "mjc:ref", joint.ref)
    set_schema_attribute(prim, "mjc:solimpfriction", list(joint.solimp_friction))
    set_schema_attribute(prim, "mjc:solimplimit", list(joint.solimp_limit))
    set_schema_attribute(prim, "mjc:solreffriction", list(joint.solref_friction))
    set_schema_attribute(prim, "mjc:solreflimit", list(joint.solref_limit))
    set_schema_attribute(prim, "mjc:springdamper", list(joint.springdamper))
    set_schema_attribute(prim, "mjc:springref", joint.springref)
    set_schema_attribute(prim, "mjc:stiffness", joint.stiffness)


def is_limited(joint: mujoco.MjsJoint, data: ConversionData) -> bool:
    if joint.limited == mujoco.mjtLimited.mjLIMITED_TRUE:
        return True
    elif joint.limited == mujoco.mjtLimited.mjLIMITED_FALSE:
        return False
    elif data.spec.compiler.autolimits and joint.range[0] != joint.range[1]:
        return True
    return False


def get_limits(joint: mujoco.MjsJoint, data: ConversionData) -> tuple[float, float]:
    if not is_limited(joint, data):
        return [None, None]
    if joint.type == mujoco.mjtJoint.mjJNT_SLIDE or data.spec.compiler.degree:
        return joint.range
    # for all other joint types, we need to convert the limits to degrees
    return [np.degrees(joint.range[0]), np.degrees(joint.range[1])]
