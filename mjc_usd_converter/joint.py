# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import mujoco
import numpy as np
import usdex.core
from pxr import Gf, Sdf, Tf, Usd, UsdPhysics

from .data import ConversionData, Tokens
from .numpy import convert_vec3d

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
    # In MJC, if there is no joint defined between nested bodies this implies the bodies are welded together
    # so we need to author a fixed joint between the parent and the ancestor.
    if not body.joints:
        # if the ancestor is the worldbody, we need to fix to the default prim rather than the immediate parent (the Geometry Scope)
        body0 = parent.GetStage().GetDefaultPrim() if body.parent == data.spec.worldbody else parent.GetParent()
        __define_fixed_joint(parent=parent, name=data.name_cache.getPrimName(parent, UsdPhysics.Tokens.PhysicsFixedJoint), body0=body0, body1=parent)
        return

    safe_names = data.name_cache.getPrimNames(parent, [get_joint_name(x) for x in body.joints])
    for joint, safe_name in zip(body.joints, safe_names):
        if joint.type == mujoco.mjtJoint.mjJNT_HINGE:
            joint_prim = __convert_hinge_joint(parent, safe_name, joint, data)
        elif joint.type == mujoco.mjtJoint.mjJNT_SLIDE:
            joint_prim = __convert_slide_joint(parent, safe_name, joint, data)
        elif joint.type == mujoco.mjtJoint.mjJNT_BALL:
            joint_prim = __convert_ball_joint(parent, safe_name, joint, data)
        elif joint.type == mujoco.mjtJoint.mjJNT_FREE:
            # Bodies in USD are free by default, so we don't need to author a joint
            continue

        joint_prim.CreateBody0Rel().SetTargets(["../.."])
        joint_prim.CreateBody1Rel().SetTargets([".."])

        # force joints to be x-aligned
        joint_prim.CreateAxisAttr().Set(UsdPhysics.Tokens.x)

        # set the joint local position relative to the parent body
        joint_pos = convert_vec3d(joint.pos)
        if not np.array_equal(joint.pos, data.spec.default.joint.pos):
            joint_prim.CreateLocalPos1Attr().Set(joint_pos)

        # align the joint axis with the x-axis of the parent body
        joint_rotation = __align_vector_to_x_axis(joint.axis)
        joint_prim.CreateLocalRot1Attr().Set(joint_rotation)

        # set the joint local position relative to the grandparent body
        parent_xform: Gf.Transform = usdex.core.getLocalTransform(data.content[Tokens.Geometry].GetPrimAtPath(parent.GetPath()))
        parent_rot: Gf.Rotation = parent_xform.GetRotation()
        grandparent_pos_offset = parent_xform.GetTranslation() + parent_rot.TransformDir(joint_pos)
        joint_prim.CreateLocalPos0Attr().Set(grandparent_pos_offset)

        # align the joint axis with the x-axis of the grandparent body
        grandparent_rot_offset = Gf.Quatf(parent_rot.GetQuat()) * joint_rotation
        joint_prim.CreateLocalRot0Attr().Set(grandparent_rot_offset)

        # author the group as a custom attribute so it is retained in a roundtrip
        joint_prim.GetPrim().CreateAttribute("mjc:group", Sdf.ValueTypeNames.Int, custom=True).Set(joint.group)

        # FUTURE: use MjcPhysics schemas to apply property gaps


def __define_fixed_joint(parent: Usd.Prim, name: str, body0: Usd.Prim, body1: Usd.Prim) -> UsdPhysics.FixedJoint:
    joint: UsdPhysics.FixedJoint = UsdPhysics.FixedJoint.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    joint.CreateBody0Rel().SetTargets([body0.GetPath()])
    joint.CreateBody1Rel().SetTargets([body1.GetPath()])
    return joint


def __convert_hinge_joint(parent: Usd.Prim, name: str, joint: mujoco.MjsJoint, data: ConversionData) -> UsdPhysics.RevoluteJoint:
    joint_prim: UsdPhysics.RevoluteJoint = UsdPhysics.RevoluteJoint.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    if __is_limited(joint, data):
        limits = joint.range if data.spec.compiler.degree else [np.degrees(joint.range[0]), np.degrees(joint.range[1])]
        joint_prim.CreateLowerLimitAttr().Set(limits[0])
        joint_prim.CreateUpperLimitAttr().Set(limits[1])
    return joint_prim


def __convert_slide_joint(parent: Usd.Prim, name: str, joint: mujoco.MjsJoint, data: ConversionData) -> UsdPhysics.PrismaticJoint:
    joint_prim: UsdPhysics.PrismaticJoint = UsdPhysics.PrismaticJoint.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    if __is_limited(joint, data):
        joint_prim.CreateLowerLimitAttr().Set(joint.range[0])
        joint_prim.CreateUpperLimitAttr().Set(joint.range[1])
    return joint_prim


def __convert_ball_joint(parent: Usd.Prim, name: str, joint: mujoco.MjsJoint, data: ConversionData) -> UsdPhysics.SphericalJoint:
    joint_prim: UsdPhysics.SphericalJoint = UsdPhysics.SphericalJoint.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    if __is_limited(joint, data):
        limit = joint.range[1] if data.spec.compiler.degree else np.degrees(joint.range[1])
        joint_prim.CreateConeAngle0LimitAttr().Set(limit)
        joint_prim.CreateConeAngle1LimitAttr().Set(limit)
    return joint_prim


def __is_limited(joint: mujoco.MjsJoint, data: ConversionData) -> bool:
    if joint.limited == mujoco.mjtLimited.mjLIMITED_TRUE:
        return True
    elif joint.limited == mujoco.mjtLimited.mjLIMITED_FALSE:
        return False
    elif data.spec.compiler.autolimits and joint.range[0] != joint.range[1]:
        return True
    return False


def __align_vector_to_x_axis(v: np.ndarray) -> Gf.Quatf:
    v = np.array(v, dtype=float)
    x_axis = np.array([1.0, 0.0, 0.0])

    # Normalize the input vector
    v_norm = np.linalg.norm(v)
    if v_norm == 0:
        # If the input vector is a zero vector, no rotation is needed.
        return Gf.Quatf.GetIdentity()

    v_unit = v / v_norm

    # If the vector is already aligned with the X-axis or directly opposite
    # Handle these edge cases to prevent division by zero or incorrect axis.
    if np.allclose(v_unit, x_axis):
        return Gf.Quatf.GetIdentity()
    elif np.allclose(v_unit, -x_axis):
        # If aligned with negative X-axis, rotate 180 degrees around Y-axis (or Z-axis)
        return Gf.Quatf(0.0, 0.0, 1.0, 0.0)  # Quaternion for 180 deg around Y-axis (w=0, x=0, y=sin(90), z=0)

    # Calculate the rotation axis (cross product of x_axis and v_unit)
    rotation_axis = np.cross(x_axis, v_unit)
    rotation_axis_norm = np.linalg.norm(rotation_axis)

    # This case should be handled by the np.allclose checks above.
    if rotation_axis_norm == 0:
        return Gf.Quatf.GetIdentity()

    rotation_axis_unit = rotation_axis / rotation_axis_norm

    # Calculate the angle (dot product of v_unit and x_axis)
    dot_product = np.dot(v_unit, x_axis)
    angle = np.arccos(np.clip(dot_product, -1.0, 1.0))  # Clip to avoid floating point errors

    # Construct the quaternion (wxyz order)
    w = np.cos(angle / 2.0)
    x = rotation_axis_unit[0] * np.sin(angle / 2.0)
    y = rotation_axis_unit[1] * np.sin(angle / 2.0)
    z = rotation_axis_unit[2] * np.sin(angle / 2.0)

    return Gf.Quatf(w, x, y, z)
