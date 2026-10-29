# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from typing import Any

import mujoco
import numpy as np
import usdex.core
from pxr import Gf, Tf, Usd, UsdGeom

from .._version import __version__
from .data import ConversionData
from .numpy import convert_quatf, convert_vec3d

__all__ = ["get_authoring_metadata", "get_fromto_vectors", "mj_limited_to_token", "set_purpose", "set_schema_attribute", "set_transform"]


def get_authoring_metadata() -> str:
    return f"MuJoCo USD Converter v{__version__}"


def set_purpose(prim: UsdGeom.Imageable, group: int) -> None:
    # in MuJoCo, groups 0, 1, 2 are visible for default visualizations, and any other group is hidden
    if group not in (0, 1, 2):
        prim.GetPurposeAttr().Set(UsdGeom.Tokens.guide)


def set_schema_attribute(prim: Usd.Prim, name: str, value: Any):
    attr: Usd.Attribute = prim.GetAttribute(name)
    if not attr.IsValid():
        Tf.RaiseCodingError(f'Attribute "{name}" is not valid for prim <{prim.GetPath()}> with schemas {prim.GetAppliedSchemas()}')
    # Only set the value if it is different from the schema default value
    default = attr.Get()
    if default is None or value != default:
        attr.Set(value)


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
    mjc_object: mujoco.MjsBody | mujoco.MjsGeom | mujoco.MjsJoint | mujoco.MjsCamera | mujoco.MjsLight | mujoco.MjsSite,
    spec: mujoco.MjSpec,
) -> None:
    # get the current transform (including any inherited via references)
    pos, pivot, orient, scale = usdex.core.getLocalTransformComponentsQuat(prim)
    current_transform = Gf.Transform(translation=pos, rotation=Gf.Rotation(orient), scale=Gf.Vec3d(scale), pivotPosition=pivot)

    # check for a local frame not represented in the prim hierarchy
    frame_transform: Gf.Transform = get_frame_transform(mjc_object, spec)

    # fromto overrides position and orientation
    pos = None
    quat = None
    start, end = get_fromto_vectors(mjc_object)
    if start is not None and end is not None:
        pos = (end + start) / 2
        quat = vec_to_quat(end - start)

    # position always exists
    if pos is None:
        pos = convert_vec3d(mjc_object.pos)

    # orientation always exists
    if quat is None:
        quat = get_orientation(mjc_object, spec)

    # compute the final transform
    new_transform: Gf.Transform = Gf.Transform()
    new_transform.SetTranslation(pos)
    new_transform.SetRotation(Gf.Rotation(quat))

    # Special case for Cubes, which may have a scale applied already,
    # that needs to be considered part of the new transform rather than
    # the pre-existing local transform. Cubes never have reference arcs,
    # and neither MjsGeom nor MjsFrame have scale, so we can safely
    # transfer scale across and avoid multiplying it in the next step.
    if prim.GetPrim().IsA(UsdGeom.Cube):
        new_transform.SetScale(current_transform.GetScale())
        current_transform.SetScale(Gf.Vec3d(1))

    # the inherited transform (e.g. a referenced mesh's reference pose) applies first, then the object's own, then its frame
    final_transform: Gf.Transform = multiply_transforms_preserve_scale(
        multiply_transforms_preserve_scale(current_transform, new_transform),
        frame_transform,
    )

    # extract the translation, orientation, and scale so we can set them as components
    pos = final_transform.GetTranslation()
    orient = Gf.Quatf(final_transform.GetRotation().GetQuat())
    scale = Gf.Vec3f(final_transform.GetScale())

    usdex.core.setLocalTransform(prim, pos, orient, scale)


def vec_to_quat(vec: Gf.Vec3d) -> Gf.Quatf:
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


def get_orientation(
    mjc_object: mujoco.MjsBody | mujoco.MjsGeom | mujoco.MjsJoint | mujoco.MjsCamera | mujoco.MjsLight | mujoco.MjsSite | mujoco.MjsFrame,
    spec: mujoco.MjSpec,
) -> Gf.Quatf:
    orient_type = mujoco.mjtOrientation.mjORIENTATION_QUAT
    if hasattr(mjc_object, "alt"):
        orient_type = mjc_object.alt.type
    if orient_type == mujoco.mjtOrientation.mjORIENTATION_QUAT:
        quat = convert_quatf(mjc_object.quat)
    else:
        # an attached model keeps its own compiler, so its angle units and euler sequence may differ from the spec's
        compiler = mjc_object.compiler
        quat = Gf.Quatf(*spec.resolve_orientation(degree=compiler.degree, sequence=compiler.eulerseq, orientation=mjc_object.alt))
    return quat.GetNormalized()


def get_frame_transform(
    mjc_object: mujoco.MjsBody | mujoco.MjsGeom | mujoco.MjsJoint | mujoco.MjsCamera | mujoco.MjsLight | mujoco.MjsSite | mujoco.MjsFrame,
    spec: mujoco.MjSpec,
) -> Gf.Transform:
    if not hasattr(mjc_object, "frame"):
        return Gf.Transform()

    frame: mujoco.MjsFrame = mjc_object.frame

    if frame is None:
        return Gf.Transform()

    transform = Gf.Transform()
    transform.SetTranslation(convert_vec3d(frame.pos))
    transform.SetRotation(Gf.Rotation(get_orientation(frame, spec)))
    if frame.frame:
        Tf.Warn("Recursive frames are not supported")
    return transform


def multiply_transforms_preserve_scale(transform1: Gf.Transform, transform2: Gf.Transform) -> Gf.Transform:
    """
    Multiply two Gf.Transform objects while preserving non-uniform scales.

    This function uses matrix multiplication but then carefully decomposes the result
    to extract and preserve the non-uniform scale components that would otherwise
    be lost or corrupted in standard matrix decomposition.

    Args:
        transform1: The first transform (applied first in the composition)
        transform2: The second transform (applied second in the composition)

    Returns:
        A new Gf.Transform representing transform1 * transform2 with preserved scales.
        Gf composes transforms so that the left operand is applied first.
    """
    # Extract scale components before matrix multiplication
    s1 = transform1.GetScale()
    s2 = transform2.GetScale()

    # Create transforms without scale for matrix multiplication
    transform1_no_scale = Gf.Transform()
    transform1_no_scale.SetTranslation(transform1.GetTranslation())
    transform1_no_scale.SetRotation(transform1.GetRotation())

    transform2_no_scale = Gf.Transform()
    transform2_no_scale.SetTranslation(transform2.GetTranslation())
    transform2_no_scale.SetRotation(transform2.GetRotation())

    # Multiply the transforms without scale using standard matrix multiplication
    result_no_scale = transform1_no_scale * transform2_no_scale

    # Compute the combined scale (component-wise multiplication)
    combined_scale = Gf.CompMult(s1, s2)

    # Create the final result with the preserved scale
    result = Gf.Transform()
    result.SetTranslation(result_no_scale.GetTranslation())
    result.SetRotation(result_no_scale.GetRotation())
    result.SetScale(combined_scale)

    return result


def mj_limited_to_token(
    limited_val: mujoco.mjtLimited,
    value_range: Sequence[float],
    mjc_object: mujoco.MjsJoint | mujoco.MjsTendon | mujoco.MjsActuator,
    data: ConversionData,
) -> str:
    if limited_val == mujoco.mjtLimited.mjLIMITED_FALSE:
        return "false"
    elif limited_val == mujoco.mjtLimited.mjLIMITED_TRUE:
        return "true"
    # An attached model keeps its own compiler, so it may allow an auto limit with a range
    # that mjc:compiler:autoLimits rejects. Resolve it as MuJoCo does instead.
    scene_autolimits = data.spec.compiler.autolimits if data.scene else True
    if mjc_object.compiler.autolimits and not scene_autolimits:
        return "true" if value_range[0] < value_range[1] else "false"
    return "auto"
