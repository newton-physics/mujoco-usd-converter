# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import mujoco
import usdex.core
from pxr import Gf, Tf, Usd, Vt

from .data import ConversionData, Tokens
from .utils import mj_limited_to_token, set_schema_attribute

__all__ = ["convert_tendons"]


def convert_tendons(data: ConversionData):
    if not data.spec.tendons:
        return

    # Convert each tendon to a MjcTendon prim
    physics_scope = data.content[Tokens.Physics].GetDefaultPrim().GetChild(Tokens.Physics)
    source_names = [get_tendon_name(tendon) for tendon in data.spec.tendons]
    safe_names = data.name_cache.getPrimNames(physics_scope, source_names)
    for tendon, source_name, safe_name in zip(data.spec.tendons, source_names, safe_names):
        tendon_prim = convert_tendon(physics_scope, safe_name, tendon, data)
        if source_name != safe_name:
            usdex.core.setDisplayName(tendon_prim, source_name)


def get_tendon_name(tendon: mujoco.MjsTendon) -> str:
    if tendon.name:
        return tendon.name
    else:
        return f"Tendon_{tendon.id}"


def get_prim_from_stage(stage: Usd.Stage, name: str) -> Usd.Prim:
    for prim in Usd.PrimRange(stage.GetDefaultPrim(), Usd.PrimAllPrimsPredicate):
        if prim.GetName() == name:
            return prim
    return None


def convert_tendon(parent: Usd.Prim, name: str, tendon: mujoco.MjsTendon, data: ConversionData) -> Usd.Prim:
    tendon_prim: Usd.Prim = parent.GetStage().DefinePrim(parent.GetPath().AppendChild(name))
    tendon_prim.SetTypeName("MjcTendon")

    set_schema_attribute(tendon_prim, "mjc:stiffness", tendon.stiffness)
    set_schema_attribute(tendon_prim, "mjc:springlength", Vt.DoubleArray(tendon.springlength))
    set_schema_attribute(tendon_prim, "mjc:damping", tendon.damping)
    set_schema_attribute(tendon_prim, "mjc:frictionloss", tendon.frictionloss)
    set_schema_attribute(tendon_prim, "mjc:solreffriction", Vt.DoubleArray(tendon.solref_friction))
    set_schema_attribute(tendon_prim, "mjc:solimpfriction", Vt.DoubleArray(tendon.solimp_friction))
    set_schema_attribute(tendon_prim, "mjc:armature", tendon.armature)
    set_schema_attribute(tendon_prim, "mjc:limited", mj_limited_to_token(tendon.limited))
    set_schema_attribute(tendon_prim, "mjc:actuatorfrclimited", mj_limited_to_token(tendon.actfrclimited))
    set_schema_attribute(tendon_prim, "mjc:range:min", tendon.range[0])
    set_schema_attribute(tendon_prim, "mjc:range:max", tendon.range[1])
    set_schema_attribute(tendon_prim, "mjc:actuatorfrcrange:min", tendon.actfrcrange[0])
    set_schema_attribute(tendon_prim, "mjc:actuatorfrcrange:max", tendon.actfrcrange[1])
    set_schema_attribute(tendon_prim, "mjc:margin", tendon.margin)
    set_schema_attribute(tendon_prim, "mjc:solreflimit", Vt.DoubleArray(tendon.solref_limit))
    set_schema_attribute(tendon_prim, "mjc:solimplimit", Vt.DoubleArray(tendon.solimp_limit))

    # visual
    set_schema_attribute(
        tendon_prim, "mjc:rgba", Gf.Vec4f(float(tendon.rgba[0]), float(tendon.rgba[1]), float(tendon.rgba[2]), float(tendon.rgba[3]))
    )
    set_schema_attribute(tendon_prim, "mjc:width", tendon.width)
    set_schema_attribute(tendon_prim, "mjc:group", tendon.group)

    # path
    divisors = [1.0]
    side_sites = []
    side_sites_indices = []
    segment_counter = 0
    targets = []
    target_indices = []
    segments = []
    coefficients = []
    for i in range(len(tendon.path)):
        wrap = tendon.path[i]

        if wrap.type == mujoco.mjtWrap.mjWRAP_PULLEY:
            # If a path starts with a pulley, it's a degenerate case
            if i == 0:
                divisors[0] = wrap.divisor
            else:
                segment_counter += 1
                divisors.append(wrap.divisor)
        elif wrap.type == mujoco.mjtWrap.mjWRAP_JOINT:
            coefficients.append(wrap.coef)

        if wrap.target:
            segments.append(segment_counter)
            target_path = None
            # Try to find the target in the physics references
            if wrap.target.name in data.references[Tokens.Physics]:
                target_path = data.references[Tokens.Physics][wrap.target.name].GetPath()
            # If not found (it's a non-collision geom), try to find the target in the geometry layer
            if not target_path:
                target_prim = get_prim_from_stage(data.content[Tokens.Geometry], usdex.core.getValidPrimName(wrap.target.name))
                if target_prim:
                    target_path = target_prim.GetPath()
                    geom_over = data.content[Tokens.Geometry].OverridePrim(target_path)
                    data.references[Tokens.Physics][wrap.target.name] = geom_over
            if not target_path:
                Tf.Warn(f"Target '{wrap.target.name}' not found for tendon '{name}'")
                return tendon_prim

            if target_path not in targets:
                targets.append(target_path)
                tendon_prim.CreateRelationship("mjc:path", custom=False).AddTarget(target_path)
                target_indices.append(len(targets) - 1)
            else:
                target_indices.append(targets.index(target_path))

            if wrap.sidesite:
                if wrap.sidesite.name in data.references[Tokens.Physics]:
                    target_path = data.references[Tokens.Physics][wrap.sidesite.name].GetPath()
                    if target_path not in side_sites:
                        side_sites.append(target_path)
                        tendon_prim.CreateRelationship("mjc:sideSites", custom=False).AddTarget(target_path)
                        side_sites_indices.append(len(side_sites) - 1)
                    else:
                        side_sites_indices.append(side_sites.index(target_path))
                else:
                    Tf.Warn(f"Sidesite '{wrap.sidesite.name}' not found for tendon '{name}'")
                    return tendon_prim
            else:
                side_sites_indices.append(-1)

    set_schema_attribute(tendon_prim, "mjc:path:indices", Vt.IntArray(target_indices))

    if len(coefficients) > 0:
        # Force-write the type
        tendon_prim.GetAttribute("mjc:type").Set("fixed")
        set_schema_attribute(tendon_prim, "mjc:path:coef", Vt.DoubleArray(coefficients))
    elif len(segments) > 0:
        # Force-write the type
        tendon_prim.GetAttribute("mjc:type").Set("spatial")

        set_schema_attribute(tendon_prim, "mjc:path:segments", Vt.IntArray(segments))
        set_schema_attribute(tendon_prim, "mjc:path:divisors", Vt.DoubleArray(divisors))
        if len(side_sites) > 0 and len(side_sites_indices) > 0:
            set_schema_attribute(tendon_prim, "mjc:sideSites:indices", Vt.IntArray(side_sites_indices))

    # Add this in case an actuator targets it
    data.references[Tokens.Physics][name] = tendon_prim

    return tendon_prim
