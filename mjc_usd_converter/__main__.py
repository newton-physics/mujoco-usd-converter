# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import sys

import mujoco
import usdex.core
from pxr import Usd


def cli_main():
    """
    Main method in command line interface.
    """
    print("Running mjc_usd_converter")
    print(f"USD Version: {Usd.GetVersion()}")
    print(f"USDEX Version: {usdex.core.version()}")
    print(f"MuJoCo Version: {mujoco.__version__}")
    # parser = create_validation_parser()
    # args = ValidationNamespaceExec(parser.parse_args(args))
    # successful: bool = args.run_validation()
    if not True:
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(cli_main())
