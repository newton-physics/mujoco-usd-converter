# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Tf, UsdPhysics

from .data import ConversionData, Tokens

__all__ = ["convert_excludes"]


def convert_excludes(data: ConversionData):
    if not data.spec.excludes:
        return

    for exclude in data.spec.excludes:
        if exclude.bodyname1 not in data.references[Tokens.PhysicsBodies] or exclude.bodyname2 not in data.references[Tokens.PhysicsBodies]:
            Tf.Warn(f"Body '{exclude.bodyname1}' or '{exclude.bodyname2}' not found for contact exclude")
            continue

        body1 = data.references[Tokens.PhysicsBodies][exclude.bodyname1].GetPrim()
        body2 = data.references[Tokens.PhysicsBodies][exclude.bodyname2].GetPrim()

        # Add the UsdPhysicsFilgeredPairsAPI to the first body
        UsdPhysics.FilteredPairsAPI.Apply(body1)
        filtered_pairs_api = UsdPhysics.FilteredPairsAPI(body1)
        filtered_pairs_api.GetFilteredPairsRel().AddTarget(body2.GetPath())
