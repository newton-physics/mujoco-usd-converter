# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
from ._impl.convert import Converter
from ._version import __version__

__all__ = ["Converter", "__version__"]

# register the mjcPhysics schema plugin
__import__("pxr").Plug.Registry().RegisterPlugins([(__import__("pathlib").Path(__file__).parent / "plugins").absolute().as_posix()])
