# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import mujoco
import numpy as np
import usdex.core
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
    mjc_object: mujoco.MjsBody | mujoco.MjsGeom | mujoco.MjsJoint | mujoco.MjsCamera | mujoco.MjsLight | mujoco.MjsSite | mujoco.MjsMesh,
    spec: mujoco.MjSpec,
) -> None:
    # get the current transform (including any inherited via references)
    current_transform: Gf.Transform = usdex.core.getLocalTransform(prim.GetPrim())
    # check for a local frame not represented in the prim hierarchy
    frame_transform: Gf.Transform = __get_frame_transform(mjc_object, spec)
    local_transform: Gf.Transform = frame_transform * current_transform

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

    # orientation always exists
    if quat is None:
        quat = __get_orientation(mjc_object, spec)

    # additional scale is optional
    scale = Gf.Vec3d(1)
    if hasattr(mjc_object, "scale"):
        scale = convert_vec3d(mjc_object.scale)

    # compute the final transform
    new_transform: Gf.Transform = Gf.Transform()
    new_transform.SetTranslation(pos)
    new_transform.SetRotation(Gf.Rotation(quat))
    new_transform.SetScale(scale)

    # Special case for Cubes, which may have a scale applied already,
    # that needs to be considered part of the new transform rather than
    # the pre-existing local transform. Cubes never have reference arcs,
    # and neither MjsGeom nor MjsFrame have scale, so we can safely
    # transfer scale across and avoid multiplying it in the next step.
    if prim.GetPrim().IsA(UsdGeom.Cube):
        new_transform.SetScale(local_transform.GetScale())
        local_transform.SetScale(Gf.Vec3d(1))

    final_transform: Gf.Transform = new_transform * local_transform

    # extract the translation, orientation, and scale so we can set them as components
    pos = final_transform.GetTranslation()
    orient = Gf.Quatf(final_transform.GetRotation().GetQuat())
    scale = final_transform.GetScale()

    # FUTURE: call usdex.core.setLocalTransform once it supports orient
    prim.ClearXformOpOrder()
    prim.AddTranslateOp().Set(pos)
    prim.AddOrientOp().Set(orient)
    prim.AddScaleOp().Set(scale)


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
        ).GetNormalized()


def __get_orientation(
    mjc_object: mujoco.MjsBody | mujoco.MjsGeom | mujoco.MjsJoint | mujoco.MjsCamera | mujoco.MjsLight | mujoco.MjsSite | mujoco.MjsFrame,
    spec: mujoco.MjSpec,
) -> Gf.Quatf:
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
    return quat.GetNormalized()


def __get_frame_transform(
    mjc_object: mujoco.MjsBody | mujoco.MjsGeom | mujoco.MjsJoint | mujoco.MjsCamera | mujoco.MjsLight | mujoco.MjsSite | mujoco.MjsFrame,
    spec: mujoco.MjSpec,
) -> Gf.Transform:
    if not hasattr(mjc_object, "frame"):
        return Gf.Transform()

    if callable(mjc_object.frame):
        frame: mujoco.MjsFrame = mjc_object.frame()
    else:
        frame: mujoco.MjsFrame = mjc_object.frame

    if frame is None:
        return Gf.Transform()

    transform = Gf.Transform()
    transform.SetTranslation(convert_vec3d(frame.pos))
    transform.SetRotation(Gf.Rotation(__get_orientation(frame, spec)))
    # FUTURE: recursive frames
    return transform
