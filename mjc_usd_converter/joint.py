# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import mujoco
import numpy as np
from pxr import Gf, Sdf, Usd, UsdPhysics

from .data import ConversionData
from .numpy import convert_vec3d

__all__ = ["convert_joints"]


def convert_joints(parent: Usd.Prim, body: mujoco.MjsBody, data: ConversionData):
    # In MJC, if there is no joint defined between nested bodies this implies the bodies are welded together
    # so we need to author a fixed joint between the parent and the ancestor.
    if not body.joints:
        # if the ancestor is the worldbody, we need to fix to the default prim rather than the immediate parent (the Geometry Scope)
        body0 = parent.GetStage().GetDefaultPrim() if body.parent == data.spec.worldbody else parent.GetParent()
        __define_fixed_joint(parent=parent, name=data.name_cache.getPrimName(parent, "FixedJoint"), body0=body0, body1=parent)
        return

    safe_names = data.name_cache.getPrimNames(parent, [x.name for x in body.joints])
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

        if not np.array_equal(joint.pos, data.spec.default.joint.pos):
            joint_prim.CreateLocalPos1Attr().Set(convert_vec3d(joint.pos))

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
    joint_prim.CreateAxisAttr().Set(UsdPhysics.Tokens.x)
    joint_prim.CreateLocalRot1Attr().Set(__align_vector_to_axis(joint.axis, UsdPhysics.Tokens.x))
    if __is_limited(joint, data):
        limits = joint.range if data.spec.compiler.degree else [np.degrees(joint.range[0]), np.degrees(joint.range[1])]
        joint_prim.CreateLowerLimitAttr().Set(limits[0])
        joint_prim.CreateUpperLimitAttr().Set(limits[1])
    return joint_prim


def __convert_slide_joint(parent: Usd.Prim, name: str, joint: mujoco.MjsJoint, data: ConversionData) -> UsdPhysics.PrismaticJoint:
    joint_prim: UsdPhysics.PrismaticJoint = UsdPhysics.PrismaticJoint.Define(parent.GetStage(), parent.GetPath().AppendChild(name))
    joint_prim.CreateAxisAttr().Set(UsdPhysics.Tokens.x)
    joint_prim.CreateLocalRot1Attr().Set(__align_vector_to_axis(joint.axis, UsdPhysics.Tokens.x))
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
    elif joint.limited == mujoco.mjtLimited.mjLIMITED_AUTO and data.spec.compiler.autolimits and joint.range[0] != joint.range[1]:
        return True
    return False


def __align_vector_to_axis(axis: np.ndarray, axis_token: str) -> Gf.Quatf:
    """
    Compute a quaternion that rotates the given vector to align with the specified axis.

    Args:
        axis: The input vector to align (will be normalized)
        axis_token: Target axis ("X", "Y", or "Z")

    Returns:
        Quaternion representing the rotation needed to align the vector with the target axis
    """
    # Normalize the input vector
    vector = axis / np.linalg.norm(axis)

    # Define target axis based on token
    if axis_token == UsdPhysics.Tokens.x:
        target = np.array([1.0, 0.0, 0.0])
    elif axis_token == UsdPhysics.Tokens.y:
        target = np.array([0.0, 1.0, 0.0])
    elif axis_token == UsdPhysics.Tokens.z:
        target = np.array([0.0, 0.0, 1.0])
    else:
        raise ValueError(f"Invalid axis token: {axis_token}")

    # Check if vectors are already aligned
    if np.allclose(vector, target):
        return Gf.Quatf.GetIdentity()

    # Check if vectors are anti-parallel
    if np.allclose(vector, -target):
        # Choose an arbitrary perpendicular axis for 180-degree rotation
        if axis_token == UsdPhysics.Tokens.x:
            # For X-axis, rotate around Y or Z
            perp_axis = np.array([0.0, 1.0, 0.0]) if abs(vector[1]) < 0.9 else np.array([0.0, 0.0, 1.0])
        elif axis_token == UsdPhysics.Tokens.y:
            # For Y-axis, rotate around X or Z
            perp_axis = np.array([1.0, 0.0, 0.0]) if abs(vector[0]) < 0.9 else np.array([0.0, 0.0, 1.0])
        else:  # Z-axis
            # For Z-axis, rotate around X or Y
            perp_axis = np.array([1.0, 0.0, 0.0]) if abs(vector[0]) < 0.9 else np.array([0.0, 1.0, 0.0])

        return Gf.Quatf(180.0, Gf.Vec3f(perp_axis[0], perp_axis[1], perp_axis[2])).GetNormalized()

    # Compute rotation axis (perpendicular to both vectors)
    rotation_axis = np.cross(vector, target)
    rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

    # Compute rotation angle using dot product
    cos_angle = np.clip(np.dot(vector, target), -1.0, 1.0)
    angle_radians = np.arccos(cos_angle)
    angle_degrees = np.degrees(angle_radians)

    # Create and return the quaternion
    return Gf.Quatf(float(angle_degrees), Gf.Vec3f(rotation_axis[0], rotation_axis[1], rotation_axis[2])).GetNormalized()
