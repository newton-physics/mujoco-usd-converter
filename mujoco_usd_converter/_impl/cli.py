# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import argparse
from pathlib import Path

import mujoco
import usdex.core
from pxr import Tf, Usd

from .._version import __version__
from .convert import Converter


def run() -> int:
    """
    Main method in the command line interface.
    """
    parser = __create_parser()
    args = parser.parse_args()

    # Argument validation
    # Check input_file
    if not args.input_file.exists():
        Tf.Warn(f"Input file does not exist: {args.input_file}")
        return 1
    if not args.input_file.is_file():
        Tf.Warn(f"Input path is not a file: {args.input_file}")
        return 1
    if args.input_file.suffix.lower() != ".xml":
        Tf.Warn(f"Only MJCF (.xml) files are supported as input, got: {args.input_file.suffix}")
        return 1
    # Check output_dir
    if args.output_dir.exists() and not args.output_dir.is_dir():
        Tf.Warn(f"Output path exists but is not a directory: {args.output_dir}")
        return 1
    if not args.output_dir.exists():
        try:
            args.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            Tf.Warn(f"Failed to create output directory: {args.output_dir}, error: {e}")
            return 1

    usdex.core.activateDiagnosticsDelegate()
    usdex.core.setDiagnosticsLevel(usdex.core.DiagnosticsLevel.eStatus if args.verbose else usdex.core.DiagnosticsLevel.eWarning)
    Tf.Status("Running mujoco_usd_converter")
    Tf.Status(f"Version: {__version__}")
    Tf.Status(f"USD Version: {Usd.GetVersion()}")
    Tf.Status(f"USDEX Version: {usdex.core.version()}")
    Tf.Status(f"MuJoCo Version: {mujoco.__version__}")

    try:
        converter = Converter(layer_structure=not args.no_layer_structure, scene=not args.no_physics_scene, comment=args.comment)
        if result := converter.convert(args.input_file, args.output_dir):
            Tf.Status(f"Created USD Asset: {result.path}")
            return 0
        else:
            Tf.Warn("Conversion failed for unknown reason. Try running with --verbose for more information.")
            return 1
    except Exception as e:
        if args.verbose:
            raise e
        else:
            Tf.Warn(f"Conversion failed: {e}")
            return 1


def __create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert MuJoCo MJCF files to USD format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input MJCF (MuJoCo XML) file",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="""
        Path to the output USD directory. The primary USD file will be <output_dir>/<modelname>.usda
        and it will be an Atomic Component with Asset Interface layer and payloaded contents
        (unless --no-layer-structure is used)
        """,
    )

    # Optional arguments
    # FUTURE: add arg to flatten hierarchy
    parser.add_argument(
        "--no-layer-structure",
        action="store_true",
        default=False,
        help="Create a single USDC layer rather than an Atomic Component structure with Asset Interface layer and payloaded contents",
    )
    parser.add_argument(
        "--no-physics-scene",
        action="store_true",
        default=False,
        help="Disable authoring a `UsdPhysics.Scene` prim with the `MjcPhysicsSceneAPI` as a sibling of the default prim",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )
    parser.add_argument(
        "--comment",
        "-c",
        default="",
        help="Comment to add to the USD file",
    )

    return parser
