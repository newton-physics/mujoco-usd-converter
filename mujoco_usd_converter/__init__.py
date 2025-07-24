# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from pxr import Plug

from ._version import __version__
from .cli import run
from .convert import Converter

__all__ = ["Converter", "__version__", "run"]

# register the mjcPhysics schema plugin
Plug.Registry().RegisterPlugins([(Path(__file__).parent / "plugins").absolute().as_posix()])
