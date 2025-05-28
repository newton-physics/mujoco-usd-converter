# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import mujoco
import numpy as np
from pxr import Gf, Sdf, UsdGeom

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
            quat = Gf.Quatf(*spec.resolve_orientation(degree=spec.compiler.degree, sequence=spec.compiler.eulerseq, orientation=mjc_object.alt))

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
