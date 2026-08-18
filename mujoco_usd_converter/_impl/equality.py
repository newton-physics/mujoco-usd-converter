# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import mujoco
import numpy as np
import usdex.core
from pxr import Gf, Tf, Usd, UsdGeom, UsdPhysics, Vt

from .data import ConversionData, Tokens
from .numpy import convert_quatd, convert_vec3d
from .utils import set_schema_attribute

__all__ = ["convert_equalities"]


def convert_equalities(data: ConversionData):
    if not data.spec.equalities:
        return

    # Convert each equality constraint to a constraint and/or Mjc schema prim
    physics_scope = data.content[Tokens.Physics].GetDefaultPrim().GetChild(Tokens.Physics)
    source_names = [get_equality_name(equality) for equality in data.spec.equalities]
    safe_names = data.name_cache.getPrimNames(physics_scope, source_names)
    xform_cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    for equality, source_name, safe_name in zip(data.spec.equalities, source_names, safe_names):
        equality_prim, prim_created = convert_equality(physics_scope, safe_name, equality, data, xform_cache)
        if prim_created and equality_prim.IsValid() and source_name != safe_name:
            usdex.core.setDisplayName(equality_prim, source_name)


def get_equality_name(equality: mujoco.MjsEquality) -> str:
    if equality.name:
        return equality.name
    else:
        return "Equality"


def set_base_equality_schema_attrs(equality: mujoco.MjsEquality, equality_prim: Usd.Prim):
    set_schema_attribute(equality_prim, "mjc:solimp", Vt.DoubleArray(equality.solimp))
    set_schema_attribute(equality_prim, "mjc:solref", Vt.DoubleArray(equality.solref))


def get_joint_prims_and_anchor(equality: mujoco.MjsEquality, data: ConversionData) -> tuple[Usd.Prim, Usd.Prim, Gf.Vec3d]:
    references = {}
    anchor = Gf.Vec3d(0, 0, 0)
    if equality.objtype == mujoco.mjtObj.mjOBJ_BODY:
        references = data.references[Tokens.PhysicsBodies]
        anchor = convert_vec3d(equality.data[0:3])  # anchor: Coordinates of the weld point relative to body2.
    else:  # mjOBJ_SITE
        references = data.references[Tokens.PhysicsSites]

    if equality.name1 not in references:
        Tf.Warn(f"Body '{equality.name1}' not found for equality '{equality.name}'")
        return Usd.Prim(), Usd.Prim(), Gf.Vec3d(0, 0, 0)
    else:
        prim1 = references[equality.name1]

    # If body2 is omitted, the second body is the world body
    if equality.name2:
        if equality.name2 not in references:
            Tf.Warn(f"Body '{equality.name2}' not found for equality '{equality.name}'")
            return Usd.Prim(), Usd.Prim(), Gf.Vec3d(0, 0, 0)
        else:
            prim2 = references[equality.name2]
    else:
        prim2 = data.content[Tokens.Physics].GetDefaultPrim()

    body0 = data.content[Tokens.Geometry].GetPrimAtPath(prim1.GetPath())
    body1 = data.content[Tokens.Geometry].GetPrimAtPath(prim2.GetPath())
    return body0, body1, anchor


def resolve_site_body(site_prim: Usd.Prim, data: ConversionData, xform_cache: UsdGeom.XformCache) -> tuple[Usd.Prim, Gf.Vec3d, Gf.Quatd]:
    """Resolve a site to the body that owns it, along with the site's pose in that body's frame.

    UsdPhysics expects a joint's body relationships to target rigid bodies, and a site is a guide
    Gprim which never carries one. Targeting the owning body and folding the site pose into the
    joint's local frame describes the same constraint in terms a consumer can read directly.

    A site on the worldbody resolves to the default prim, matching how an omitted body2 is handled.
    """
    default_prim = site_prim.GetStage().GetDefaultPrim()
    body_paths = {prim.GetPath() for prim in data.references[Tokens.PhysicsBodies].values()}

    body_prim = default_prim
    ancestor = site_prim.GetParent()
    while ancestor and not ancestor.IsPseudoRoot() and ancestor != default_prim:
        if ancestor.GetPath() in body_paths:
            body_prim = ancestor
            break
        ancestor = ancestor.GetParent()

    relative = xform_cache.GetLocalToWorldTransform(body_prim).GetInverse() * xform_cache.GetLocalToWorldTransform(site_prim)
    # a site's scale is how large it draws as a guide, not part of the frame it marks, and leaving
    # it in the matrix would denormalize the extracted rotation
    relative = relative.RemoveScaleShear()
    return body_prim, Gf.Vec3d(relative.ExtractTranslation()), Gf.Quatd(relative.ExtractRotationQuat())


def resolve_site_bodies(
    site0: Usd.Prim,
    site1: Usd.Prim,
    data: ConversionData,
    xform_cache: UsdGeom.XformCache,
) -> tuple[Usd.Prim, Usd.Prim, tuple[Gf.Vec3d, Gf.Quatd, Gf.Vec3d, Gf.Quatd]]:
    body0, pos0, rot0 = resolve_site_body(site0, data, xform_cache)
    body1, pos1, rot1 = resolve_site_body(site1, data, xform_cache)
    return body0, body1, (pos0, rot0, pos1, rot1)


def set_site_joint_frames(joint_prim: UsdPhysics.Joint, frames: tuple[Gf.Vec3d, Gf.Quatd, Gf.Vec3d, Gf.Quatd]) -> None:
    """Author each side of the joint at its site's pose within the owning body.

    These are set explicitly rather than derived from a :class:`usdex.core.JointFrame`, which aligns
    the second body to the first using their current world poses. MuJoCo pulls separated sites
    together, so deriving the offsets would preserve the separation instead of constraining it away.
    """
    pos0, rot0, pos1, rot1 = frames
    joint_prim.GetLocalPos0Attr().Set(Gf.Vec3f(pos0))
    joint_prim.GetLocalRot0Attr().Set(Gf.Quatf(rot0))
    joint_prim.GetLocalPos1Attr().Set(Gf.Vec3f(pos1))
    joint_prim.GetLocalRot1Attr().Set(Gf.Quatf(rot1))


def convert_equality(
    parent: Usd.Prim,
    name: str,
    equality: mujoco.MjsEquality,
    data: ConversionData,
    xform_cache: UsdGeom.XformCache,
) -> tuple[Usd.Prim, bool]:
    equality_prim = Usd.Prim()
    if equality.type == mujoco.mjtEq.mjEQ_WELD:
        ignore_relpose = False
        body0, body1, anchor = get_joint_prims_and_anchor(equality, data)
        if not body0 or not body1:
            return equality_prim, False

        site_frames = None
        if equality.objtype == mujoco.mjtObj.mjOBJ_BODY:
            # relpose specifies the relative pose of body2 relative to body1
            relpose_pos = convert_vec3d(equality.data[3:6])
            relpose_quat_data = equality.data[6:10]
            # If relpose_quat is all zeros, ignore relpose completely
            if relpose_quat_data.any():
                relpose_quat = convert_quatd(relpose_quat_data)
            else:
                ignore_relpose = True
        else:
            body0, body1, site_frames = resolve_site_bodies(body0, body1, data, xform_cache)

        # Create a fixed joint between the two bodies
        equality_prim = parent.GetStage().DefinePrim(parent.GetPath().AppendChild(name))
        frame = usdex.core.JointFrame(usdex.core.JointFrame.Space.World, Gf.Vec3d(0, 0, 0), Gf.Quatd.GetIdentity())
        joint_prim = usdex.core.definePhysicsFixedJoint(equality_prim, body0, body1, frame)

        if equality.objtype == mujoco.mjtObj.mjOBJ_BODY:
            if ignore_relpose:
                # Compute the relative transform from the body positions
                body0_xform = xform_cache.GetLocalToWorldTransform(body0)
                body1_xform = xform_cache.GetLocalToWorldTransform(body1)

                # relative_xform = body1 pose relative to body0
                relative_xform = body0_xform.GetInverse() * body1_xform
                relpose_pos = Gf.Vec3d(relative_xform.ExtractTranslation())
                relpose_quat = Gf.Quatd(relative_xform.ExtractRotationQuat())

            local_pos0 = relpose_pos + relpose_quat.Transform(anchor)
            joint_prim.GetLocalPos0Attr().Set(local_pos0)
            joint_prim.GetLocalRot0Attr().Set(Gf.Quatf(relpose_quat))
            joint_prim.GetLocalPos1Attr().Set(anchor)
            joint_prim.GetLocalRot1Attr().Set(Gf.Quatf.GetIdentity())
        else:
            set_site_joint_frames(joint_prim, site_frames)

        joint_prim.GetExcludeFromArticulationAttr().Set(True)
        set_schema_attribute(equality_prim, "physics:jointEnabled", equality.active)

        equality_prim.ApplyAPI("MjcEqualityWeldAPI")
        set_base_equality_schema_attrs(equality, equality_prim)
        torque_scale = equality.data[10]
        set_schema_attribute(equality_prim, "mjc:torqueScale", torque_scale)

    elif equality.type == mujoco.mjtEq.mjEQ_CONNECT:
        body0, body1, anchor = get_joint_prims_and_anchor(equality, data)
        if not body0 or not body1:
            return equality_prim, False

        equality_prim = parent.GetStage().DefinePrim(parent.GetPath().AppendChild(name))

        site_frames = None
        if equality.objtype == mujoco.mjtObj.mjOBJ_SITE:
            body0, body1, site_frames = resolve_site_bodies(body0, body1, data, xform_cache)

        # Create a spherical joint between the two bodies
        # anchor is in body0's frame for connect equalities
        frame = usdex.core.JointFrame(usdex.core.JointFrame.Space.Body0, anchor, Gf.Quatd.GetIdentity())
        joint_prim = usdex.core.definePhysicsSphericalJoint(equality_prim, body0, body1, frame, Gf.Vec3f(1.0, 0.0, 0.0))
        if site_frames:
            set_site_joint_frames(joint_prim, site_frames)

        joint_prim.GetExcludeFromArticulationAttr().Set(True)
        set_schema_attribute(equality_prim, "physics:jointEnabled", equality.active)

        equality_prim.ApplyAPI("MjcEqualityConnectAPI")
        set_base_equality_schema_attrs(equality, equality_prim)

    elif equality.type == mujoco.mjtEq.mjEQ_JOINT:
        # Find the joint for equality.name1
        references = data.references[Tokens.PhysicsJoints]
        if equality.name1 and equality.name1 in references:
            joint_prim = references[equality.name1]
        else:
            Tf.Warn(f"Joint '{equality.name1}' not found for equality '{equality.name}'")
            return equality_prim, False

        if equality.name2 and equality.name2 in references:
            target_joint_prim = references[equality.name2]
            target_joint_path = target_joint_prim.GetPath()
        else:
            Tf.Warn(f"Joint '{equality.name2}' not found for equality '{equality.name}'")
            return equality_prim, False

        # NewtonMimicAPI authors coef0 in the follower joint's position units, which is
        # degrees for an angular joint. MuJoCo's polycoef[0] is always radians -- unlike
        # joint ranges it is not affected by compiler.degree -- so convert on joint type
        # alone. coef1 is dimensionless in both.
        coef0 = equality.data[0]
        follower = data.spec.joint(equality.name1)
        if follower is not None and follower.type in (mujoco.mjtJoint.mjJNT_HINGE, mujoco.mjtJoint.mjJNT_BALL):
            coef0 = np.degrees(coef0)

        # Apply the NewtonMimicAPI schema
        joint_prim.ApplyAPI("NewtonMimicAPI")
        set_schema_attribute(joint_prim, "newton:mimicEnabled", equality.active)
        set_schema_attribute(joint_prim, "newton:mimicCoef0", coef0)
        set_schema_attribute(joint_prim, "newton:mimicCoef1", equality.data[1])
        joint_prim.GetRelationship("newton:mimicJoint").SetTargets([target_joint_path])

        # Apply the MjcEqualityJointAPI schema
        joint_prim.ApplyAPI("MjcEqualityJointAPI")
        set_base_equality_schema_attrs(equality, joint_prim)
        set_schema_attribute(joint_prim, "mjc:coef2", equality.data[2])
        set_schema_attribute(joint_prim, "mjc:coef3", equality.data[3])
        set_schema_attribute(joint_prim, "mjc:coef4", equality.data[4])
        set_schema_attribute(joint_prim, "physics:jointEnabled", equality.active)

        return joint_prim, False

    elif equality.type == mujoco.mjtEq.mjEQ_TENDON:
        Tf.Warn("Tendon equalities are not supported")
    elif equality.type == mujoco.mjtEq.mjEQ_FLEX:
        Tf.Warn("Flex equalities are not supported")
    elif equality.type == mujoco.mjtEq.mjEQ_FLEXVERT:
        Tf.Warn("Flexvert equalities are not supported")

    return equality_prim, True
