# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

import mujoco
import usdex.core
from pxr import Sdf, Usd

__all__ = ["ConversionData", "Tokens"]


class Tokens:
    Asset = usdex.core.getAssetToken()
    Library = usdex.core.getLibraryToken()
    Contents = usdex.core.getContentsToken()
    Geometry = usdex.core.getGeometryToken()
    Materials = usdex.core.getMaterialsToken()
    Textures = usdex.core.getTexturesToken()
    Payload = usdex.core.getPayloadToken()
    Physics = usdex.core.getPhysicsToken()
    # Mujoco element types exist within namespaces, use separate dictionaries to avoid clashes
    PhysicsBodies = "PhysicsBodies"
    PhysicsJoints = "PhysicsJoints"
    PhysicsSites = "PhysicsSites"
    PhysicsTendons = "PhysicsTendons"


@dataclass
class ConversionData:
    spec: mujoco.MjSpec
    model: mujoco.MjModel | None
    content: dict[Tokens, Usd.Stage]
    libraries: dict[Tokens, Usd.Stage]
    references: dict[Tokens, dict[str, Usd.Prim]]
    geom_targets: dict[str, Sdf.Path]
    name_cache: usdex.core.NameCache
    scene: bool
    comment: str
