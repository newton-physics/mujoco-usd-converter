# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

import mujoco
import usdex.core
from pxr import Usd

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


@dataclass
class ConversionData:
    spec: mujoco.MjSpec
    model: mujoco.MjModel | None
    content: dict[Tokens, Usd.Stage]
    libraries: dict[Tokens, Usd.Stage]
    references: dict[Tokens, dict[str, Usd.Prim]]
    name_cache: usdex.core.NameCache
    scene: bool
    comment: str
