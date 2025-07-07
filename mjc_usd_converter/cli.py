# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import argparse
from pathlib import Path

import mujoco
import usdex.core
from pxr import Tf, Usd

from .convert import Converter


def run() -> int:
    """
    Main method in the command line interface.
    """
    parser = __create_parser()
    args = parser.parse_args()

    # TODO: ensure args

    usdex.core.activateDiagnosticsDelegate()
    usdex.core.setDiagnosticsLevel(usdex.core.DiagnosticsLevel.eStatus if args.verbose else usdex.core.DiagnosticsLevel.eWarning)
    Tf.Status("Running mjc_usd_converter")
    Tf.Status(f"USD Version: {Usd.GetVersion()}")
    Tf.Status(f"USDEX Version: {usdex.core.version()}")
    Tf.Status(f"MuJoCo Version: {mujoco.__version__}")

    try:
        converter = Converter(flatten=args.flatten, comment=args.comment)
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
        Path to the output USD directory. The primary USD file will be <output_dir>/<modelname>.usd
        and it will be an Asset Interface around a Payload (unless --flatten is used)
        """,
    )

    # Optional arguments
    # TODO: add arg to flatten hierarchy
    # TODO: disambiguate from flattening hierarchy
    parser.add_argument(
        "--flatten",
        action="store_true",
        default=False,
        help="Flatten the USD stage before saving",
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
