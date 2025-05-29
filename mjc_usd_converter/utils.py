# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import mujoco
import numpy as np
from pxr import Gf, Sdf, Tf, UsdGeom

from .numpy import convert_quat, convert_vec3d

__all__ = ["get_authoring_metadata", "get_fromto_vectors", "set_purpose", "set_transform"]


def get_authoring_metadata() -> str:
    return "MuJoCo USD Converter v0.1.0"


def set_purpose(prim: UsdGeom.Imageable, group: int) -> None:
    # in MuJoCo, groups 0, 1, 2 are visible for default visualizations, and any other group is hidden
    if group not in (0, 1, 2):
        prim.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
    # author the group as a custom attribute so it is retained in a roundtrip
    prim.GetPrim().CreateAttribute("mjc:group", Sdf.ValueTypeNames.Int, custom=True).Set(group)


def get_fromto_vectors(geom: mujoco.MjsGeom) -> tuple[Gf.Vec3d | None, Gf.Vec3d | None]:
    if not isinstance(geom, mujoco.MjsGeom):
        return None, None

    if geom.type not in (mujoco.mjtGeom.mjGEOM_CAPSULE, mujoco.mjtGeom.mjGEOM_CYLINDER, mujoco.mjtGeom.mjGEOM_BOX, mujoco.mjtGeom.mjGEOM_ELLIPSOID):
        return None, None

    if np.isnan(geom.fromto[0]):
        return None, None

    start = convert_vec3d(geom.fromto[0:3])
    end = convert_vec3d(geom.fromto[3:6])
    return start, end


def set_transform(
    prim: UsdGeom.Xformable,
    mjc_object: mujoco.MjsBody | mujoco.MjsFrame | mujoco.MjsGeom | mujoco.MjsMesh,
    spec: mujoco.MjSpec,
    suffix: str = "",
    prepend: bool = False,
) -> None:
    # respect existing ops which likely came from referenced meshes
    orig_ops = prim.GetOrderedXformOps()
    new_ops = []

    # fromto overrides position and orientation
    pos = None
    quat = None
    start, end = get_fromto_vectors(mjc_object)
    if start is not None and end is not None:
        pos = (end + start) / 2
        quat = __vec_to_quat(end - start)

    # position always exists
    if pos is None:
        if hasattr(mjc_object, "pos"):
            pos = convert_vec3d(mjc_object.pos)
        elif hasattr(mjc_object, "refpos"):
            pos = convert_vec3d(mjc_object.refpos)
    transform_op = prim.AddTranslateOp(opSuffix=suffix)
    transform_op.Set(pos)
    new_ops.append(transform_op)

    # orientation always exists
    if quat is None:
        orient_type = mujoco.mjtOrientation.mjORIENTATION_QUAT
        if hasattr(mjc_object, "alt"):
            orient_type = mjc_object.alt.type
        if orient_type == mujoco.mjtOrientation.mjORIENTATION_QUAT:
            if hasattr(mjc_object, "quat"):
                quat = convert_quat(mjc_object.quat)
            elif hasattr(mjc_object, "refquat"):
                quat = convert_quat(mjc_object.refquat)
        else:
            quat = __orientation_to_quat(mjc_object.alt, spec)

    orient = quat.GetNormalized()
    orient_op = prim.AddOrientOp(opSuffix=suffix)
    orient_op.Set(orient)
    new_ops.append(orient_op)

    # additional scale is optional
    scale = None
    if hasattr(mjc_object, "scale"):
        scale = convert_vec3d(mjc_object.scale)
        scale_op = prim.AddScaleOp(opSuffix=suffix)
        scale_op.Set(scale)
        new_ops.append(scale_op)

    if prepend:
        prim.SetXformOpOrder(new_ops + orig_ops)
    else:
        prim.SetXformOpOrder(orig_ops + new_ops)


def __vec_to_quat(vec: Gf.Vec3d) -> Gf.Quatf:
    z_axis = Gf.Vec3d(0, 0, 1)
    vec.Normalize()

    # Cross product of z-axis and vector
    cross = z_axis.GetCross(vec)
    s = cross.GetLength()

    if s < 1e-10:
        return Gf.Quatf(0, 1, 0, 0)
    else:
        # Normalize cross product
        cross.Normalize()

        # Calculate angle between z-axis and vector
        ang = np.arctan2(s, vec[2])

        # Construct quaternion
        return Gf.Quatf(
            np.cos(ang / 2.0),
            cross[0] * np.sin(ang / 2.0),
            cross[1] * np.sin(ang / 2.0),
            cross[2] * np.sin(ang / 2.0),
        )


def __orientation_to_quat(orient: mujoco.MjsOrientation, spec: mujoco.MjSpec) -> Gf.Quatf:
    quat = np.zeros(4)
    if error := __resolve_orientation(quat, degree=spec.compiler.degree, sequence=spec.compiler.eulerseq, orient=orient):
        Tf.Warn(f"Invalid orientation {orient.type} for geom '{orient.name}': {error}")
    return convert_quat(quat)


# FUTURE: replace functions below with call to mujoco.mjs_resolveOrientation once available


def __frame_to_quat(quat: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> None:
    """Convert frame (x, y, z axes) to quaternion.

    Args:
        quat: Output quaternion array of shape (4,)
        x: x-axis vector of shape (3,)
        y: y-axis vector of shape (3,)
        z: z-axis vector of shape (3,)
    """
    # q0 largest
    if x[0] + y[1] + z[2] > 0:
        quat[0] = 0.5 * np.sqrt(1 + x[0] + y[1] + z[2])
        quat[1] = 0.25 * (y[2] - z[1]) / quat[0]
        quat[2] = 0.25 * (z[0] - x[2]) / quat[0]
        quat[3] = 0.25 * (x[1] - y[0]) / quat[0]

    # q1 largest
    elif x[0] > y[1] and x[0] > z[2]:
        quat[1] = 0.5 * np.sqrt(1 + x[0] - y[1] - z[2])
        quat[0] = 0.25 * (y[2] - z[1]) / quat[1]
        quat[2] = 0.25 * (y[0] + x[1]) / quat[1]
        quat[3] = 0.25 * (z[0] + x[2]) / quat[1]

    # q2 largest
    elif y[1] > z[2]:
        quat[2] = 0.5 * np.sqrt(1 - x[0] + y[1] - z[2])
        quat[0] = 0.25 * (z[0] - x[2]) / quat[2]
        quat[1] = 0.25 * (y[0] + x[1]) / quat[2]
        quat[3] = 0.25 * (z[1] + y[2]) / quat[2]

    # q3 largest
    else:
        quat[3] = 0.5 * np.sqrt(1 - x[0] - y[1] + z[2])
        quat[0] = 0.25 * (x[1] - y[0]) / quat[3]
        quat[1] = 0.25 * (z[0] + x[2]) / quat[3]
        quat[2] = 0.25 * (z[1] + y[2]) / quat[3]

    # Normalize quaternion
    mujoco.mju_normalize4(quat)


def __resolve_orientation(quat: np.ndarray, degree: bool, sequence: str, orient: mujoco.MjsOrientation) -> str | None:
    # Copy orientation data
    axisangle = np.array(orient.axisangle)
    xyaxes = np.array(orient.xyaxes)
    zaxis = np.array(orient.zaxis)
    euler = np.array(orient.euler)
    eps = 1e-14

    # Handle axis-angle orientation
    if orient.type == mujoco.mjtOrientation.mjORIENTATION_AXISANGLE:
        # Convert to radians if necessary
        if degree:
            axisangle[3] = axisangle[3] / 180.0 * np.pi

        # Check if axis is too small
        if np.linalg.norm(axisangle[:3]) < mujoco.mjEPS:
            return "axisangle too small"

        # Construct quaternion
        ang2 = axisangle[3] / 2
        quat[0] = np.cos(ang2)
        quat[1] = np.sin(ang2) * axisangle[0]
        quat[2] = np.sin(ang2) * axisangle[1]
        quat[3] = np.sin(ang2) * axisangle[2]

    # Handle xy-axes orientation
    elif orient.type == mujoco.mjtOrientation.mjORIENTATION_XYAXES:
        # Normalize x axis
        if np.linalg.norm(xyaxes[:3]) < eps:
            return "xaxis too small"

        # Make y axis orthogonal to x axis
        d = np.dot(xyaxes[:3], xyaxes[3:6])
        xyaxes[3:6] -= xyaxes[:3] * d

        # Check if y axis is too small
        if np.linalg.norm(xyaxes[3:6]) < eps:
            return "yaxis too small"

        # Compute and normalize z axis
        z = np.cross(xyaxes[:3], xyaxes[3:6])
        if np.linalg.norm(z) < eps:
            return "cross(xaxis, yaxis) too small"

        # Convert frame to quaternion
        __frame_to_quat(quat, xyaxes[:3], xyaxes[3:6], z)

    # Handle z-axis orientation
    elif orient.type == mujoco.mjtOrientation.mjORIENTATION_ZAXIS:
        if np.linalg.norm(zaxis) < eps:
            return "zaxis too small"
        mujoco.mju_z2Quat(quat, zaxis)

    # Handle euler angles
    elif orient.type == mujoco.mjtOrientation.mjORIENTATION_EULER:
        # Convert to radians if necessary
        if degree:
            euler = euler / 180.0 * np.pi

        # Initialize quaternion
        quat[:] = [1, 0, 0, 0]

        # Loop over euler angles
        for i in range(3):
            # Construct rotation quaternion
            qrot = np.array([np.cos(euler[i] / 2), 0, 0, 0])
            sa = np.sin(euler[i] / 2)

            # Set appropriate component based on sequence
            if sequence[i].lower() == "x":
                qrot[1] = sa
            elif sequence[i].lower() == "y":
                qrot[2] = sa
            elif sequence[i].lower() == "z":
                qrot[3] = sa
            else:
                return "euler sequence can only contain x, y, z, X, Y, Z"

            # Accumulate rotation
            if sequence[i].islower():
                # Moving axes: post-multiply
                mujoco.mju_mulQuat(quat, quat, qrot)
            else:
                # Fixed axes: pre-multiply
                mujoco.mju_mulQuat(quat, qrot, quat)

        # Normalize quaternion
        mujoco.mju_normalize4(quat)

    return None
