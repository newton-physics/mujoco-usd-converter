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

        data.references[Tokens.PhysicsJoints][joint.name] = joint_prim.GetPrim()

        apply_mjc_joint_api(joint_prim.GetPrim(), joint, limits[0] is not None and limits[1] is not None, data)


def apply_mjc_joint_api(prim: Usd.Prim, joint: mujoco.MjsJoint, is_joint_limited: bool, data: ConversionData):
    prim.ApplyAPI("MjcJointAPI")
    prim.ApplyAPI("NewtonJointAPI")

    limited_token = mj_limited_to_token(joint.actfrclimited)
    set_schema_attribute(prim, "mjc:actuatorfrclimited", limited_token)
    set_schema_attribute(prim, "mjc:actuatorfrcrange:min", joint.actfrcrange[0])
    set_schema_attribute(prim, "mjc:actuatorfrcrange:max", joint.actfrcrange[1])
    set_schema_attribute(prim, "mjc:actuatorgravcomp", bool(joint.actgravcomp))
    set_schema_attribute(prim, "mjc:armature", joint.armature)
    set_schema_attribute(prim, "mjc:damping", joint.damping[0])
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
    set_schema_attribute(prim, "mjc:stiffness", joint.stiffness[0])

    set_schema_attribute(prim, "newton:armature", joint.armature)
    set_schema_attribute(prim, "newton:damping", to_newton_angular_gain(joint, joint.damping[0]))
    set_schema_attribute(prim, "newton:friction", joint.frictionloss)
    if is_joint_limited:
        limit_stiffness, limit_damping = get_newton_limit_stiffness_damping(joint, get_limit_force_scale(joint, data))
        if limit_stiffness is not None:
            set_schema_attribute(prim, "newton:limitStiffness", limit_stiffness)
        if limit_damping is not None:
            set_schema_attribute(prim, "newton:limitDamping", limit_damping)


def to_newton_angular_gain(joint: mujoco.MjsJoint, value: float) -> float:
    """Convert a MuJoCo per-radian gain to the per-degree convention used by NewtonJointAPI.

    MuJoCo authors angular gains (damping, stiffness, limit gains) per radian, while the
    NewtonJointAPI attributes are per degree. Linear DOFs are unaffected.
    """
    if joint.type in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_BALL):
        return value * (np.pi / 180.0)
    return value


def get_limit_force_scale(joint: mujoco.MjsJoint, data: ConversionData) -> float:
    """Compute the factor relating a normalized limit gain to its effort-space equivalent.

    MuJoCo's `solreflimit` describes the limit constraint in normalized (acceleration)
    units, so the effort it produces depends on the constraint's effective inertia.
    `NewtonJointAPI` instead defines `effort = limitStiffness * penetration`, so the two
    differ by that inertia, which MuJoCo exposes as the DOF's `invweight0` narrowed by the
    impedance width `solimp[1]`.

    Returns 1.0 when the joint has no compiled counterpart, or when MuJoCo itself would
    not narrow the constraint, matching how the values are consumed downstream.
    """
    model = data.get_model()
    joint_id = _get_compiled_joint_id(joint, data)
    if joint_id < 0:
        return 1.0
    invweight = float(model.dof_invweight0[model.jnt_dofadr[joint_id]])
    dmax = float(model.jnt_solimp[joint_id][1])
    if invweight > 0.0 and dmax < 1.0:
        return invweight * (1.0 - dmax)
    return 1.0


def _get_compiled_joint_id(joint: mujoco.MjsJoint, data: ConversionData) -> int:
    """Resolve a spec joint's id in the compiled model.

    `MjsJoint.id` stays unset because conversion compiles a copy of the spec, so named
    joints resolve through the model while unnamed ones fall back to their position in
    the spec, which the compiler preserves.
    """
    if joint.name:
        return mujoco.mj_name2id(data.get_model(), mujoco.mjtObj.mjOBJ_JOINT, joint.name)
    try:
        return list(data.spec.joints).index(joint)
    except ValueError:
        return -1


def get_newton_limit_stiffness_damping(joint: mujoco.MjsJoint, force_scale: float) -> tuple[float | None, float | None]:
    timeconst = joint.solref_limit[0]
    dampratio = joint.solref_limit[1]

    if timeconst < 0.0 and dampratio < 0.0:
        stiffness = -timeconst
        damping = -dampratio
    else:
        if timeconst <= 0.0 or dampratio <= 0.0:
            return None, None
        stiffness = 1.0 / (timeconst * timeconst * dampratio * dampratio)
        damping = 2.0 / timeconst

    # Both gains are normalized by the constraint's effective inertia, so undo that to
    # reach the effort space NewtonJointAPI defines. See get_limit_force_scale.
    stiffness /= force_scale
    damping /= force_scale

    # NewtonJointAPI angular limit stiffness/damping are authored per degree.
    return to_newton_angular_gain(joint, stiffness), to_newton_angular_gain(joint, damping)


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
