# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

import mujoco
import usdex.core
from pxr import Usd

from ._future import Tokens

__all__ = ["ConversionData"]


@dataclass
class ConversionData:
    spec: mujoco.MjSpec
    content: dict[Tokens, Usd.Stage]
    libraries: dict[Tokens, Usd.Stage]
    references: dict[Tokens, dict[str, Usd.Prim]]
    name_cache: usdex.core.NameCache
    scene: bool
    comment: str
