# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import mujoco
import usdex.core
from pxr import Gf, Tf, Usd, Vt

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
    for equality, source_name, safe_name in zip(data.spec.equalities, source_names, safe_names):
        equality_prim, prim_created = convert_equality(physics_scope, safe_name, equality, data)
        if prim_created and source_name != safe_name:
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
    prim2 = references[equality.name2] if equality.name2 else data.content[Tokens.Physics].GetDefaultPrim()

    body0 = data.content[Tokens.Geometry].GetPrimAtPath(prim1.GetPath())
    body1 = data.content[Tokens.Geometry].GetPrimAtPath(prim2.GetPath())
    return body0, body1, anchor


def convert_equality(parent: Usd.Prim, name: str, equality: mujoco.MjsEquality, data: ConversionData) -> Usd.Prim:
    equality_prim = Usd.Prim()
    if equality.type == mujoco.mjtEq.mjEQ_WELD:
        equality_prim: Usd.Prim = parent.GetStage().DefinePrim(parent.GetPath().AppendChild(name))
        use_qpos0 = False
        body0, body1, anchor = get_joint_prims_and_anchor(equality, data)
        if not body0 or not body1:
            return equality_prim, True

        if equality.objtype == mujoco.mjtObj.mjOBJ_BODY:
            relpose_pos = convert_vec3d(equality.data[3:6])
            relpose_quat_data = equality.data[6:10]
            # If relpose_quat is all zeros, as in the default setting, this attribute is ignored
            if relpose_quat_data.any():
                relpose_quat = convert_quatd(relpose_quat_data)
            else:
                use_qpos0 = True

            # anchor: Coordinates of the weld point relative to body2.
            # If relpose is not specified, the meaning of this parameter is the same as for connect constraints,
            # except that is relative to body2.
            #  Coordinates of the 3D anchor point where the two bodies are connected, in the local coordinate frame of body2
            # If relpose is specified, body1 will use the pose to compute its anchor point.

        frame = usdex.core.JointFrame(usdex.core.JointFrame.Space.World, Gf.Vec3d(0, 0, 0), Gf.Quatd.GetIdentity())
        joint_prim = usdex.core.definePhysicsFixedJoint(equality_prim, body0, body1, frame)

        if equality.objtype == mujoco.mjtObj.mjOBJ_BODY:
            # localPos0 = anchor
            # localPos1 = anchor / body1_scale
            # localRot0 = relpose_quat` (with `localRot1 = identity`)
            # localPos0 = (relpose_pos + relpose_quat.Transform(anchor)) / body0_scale
            if use_qpos0:
                # When relpose quat is all zeros, MuJoCo uses the reference pose (qpos0)
                # We compute the actual relative transform from the body positions
                body0_xform = usdex.core.getLocalTransform(body0).GetMatrix()
                body1_xform = usdex.core.getLocalTransform(body1).GetMatrix()
                # relative_xform = body1 pose relative to body0
                relative_xform = body0_xform.GetInverse() * body1_xform
                relpose_pos = Gf.Vec3d(relative_xform.ExtractTranslation())
                relpose_quat = Gf.Quatd(relative_xform.ExtractRotationQuat())

            # Apply the standard formula:
            # localPos1 = anchor (weld point in body1's frame)
            # localRot1 = identity
            # localPos0 = relpose_pos + relpose_quat.Transform(anchor)
            # localRot0 = relpose_quat
            local_pos0 = relpose_pos + relpose_quat.Transform(anchor)
            joint_prim.GetLocalPos0Attr().Set(local_pos0)
            joint_prim.GetLocalRot0Attr().Set(Gf.Quatf(relpose_quat))
            joint_prim.GetLocalPos1Attr().Set(anchor)
            joint_prim.GetLocalRot1Attr().Set(Gf.Quatf.GetIdentity())

        joint_prim.GetExcludeFromArticulationAttr().Set(True)
        set_schema_attribute(equality_prim, "physics:jointEnabled", equality.active)

        equality_prim.ApplyAPI("MjcEqualityWeldAPI")
        set_base_equality_schema_attrs(equality, equality_prim)
        torque_scale = equality.data[10]
        set_schema_attribute(equality_prim, "mjc:torqueScale", torque_scale)

    elif equality.type == mujoco.mjtEq.mjEQ_CONNECT:
        equality_prim: Usd.Prim = parent.GetStage().DefinePrim(parent.GetPath().AppendChild(name))
        body0, body1, anchor = get_joint_prims_and_anchor(equality, data)
        if not body0 or not body1:
            return equality_prim, True

        # Create a spherical joint between the two bodies or sites
        frame = usdex.core.JointFrame(usdex.core.JointFrame.Space.World, Gf.Vec3d(0, 0, 0), Gf.Quatd.GetIdentity())
        joint_prim = usdex.core.definePhysicsSphericalJoint(equality_prim, body0, body1, frame, Gf.Vec3f(1.0, 0.0, 0.0))
        joint_prim.GetLocalPos0Attr().Set(Gf.Vec3d(0, 0, 0))
        joint_prim.GetLocalRot0Attr().Set(Gf.Quatf.GetIdentity())
        joint_prim.GetLocalPos1Attr().Set(anchor)
        joint_prim.GetLocalRot1Attr().Set(Gf.Quatf.GetIdentity())

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
            return None, False

        if equality.name2 and equality.name2 in references:
            target_joint_prim = references[equality.name2]
            target_joint_path = target_joint_prim.GetPath()
        else:
            Tf.Warn(f"Joint '{equality.name2}' not found for equality '{equality.name}'")
            return None, False

        # Apply the MjcEqualityJointAPI schema
        joint_prim.ApplyAPI("MjcEqualityJointAPI")
        set_base_equality_schema_attrs(equality, joint_prim)
        set_schema_attribute(joint_prim, "mjc:coef0", equality.data[0])
        set_schema_attribute(joint_prim, "mjc:coef1", equality.data[1])
        set_schema_attribute(joint_prim, "mjc:coef2", equality.data[2])
        set_schema_attribute(joint_prim, "mjc:coef3", equality.data[3])
        set_schema_attribute(joint_prim, "mjc:coef4", equality.data[4])
        joint_prim.CreateRelationship("mjc:target", custom=False).AddTarget(target_joint_path)
        set_schema_attribute(joint_prim, "physics:jointEnabled", equality.active)

        # Apply the NewtonMimicAPI schema
        joint_prim.ApplyAPI("NewtonMimicAPI")
        set_schema_attribute(joint_prim, "newton:mimicEnabled", equality.active)
        set_schema_attribute(joint_prim, "newton:mimicCoef0", equality.data[0])
        set_schema_attribute(joint_prim, "newton:mimicCoef1", equality.data[1])
        joint_prim.CreateRelationship("newton:mimicJoint", custom=False).AddTarget(target_joint_path)

        return joint_prim, False

    elif equality.type == mujoco.mjtEq.mjEQ_TENDON:
        Tf.Warn("Tendon equalities are not supported")
    elif equality.type == mujoco.mjtEq.mjEQ_FLEX:
        Tf.Warn("Flex equalities are not supported")
    elif equality.type == mujoco.mjtEq.mjEQ_FLEXVERT:
        Tf.Warn("Flexvert equalities are not supported")

    return equality_prim, True
