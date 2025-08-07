# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Python wheel upload script for JFrog Artifactory.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def get_version_from_wheel(wheel_name):
    """Extract version from wheel filename."""
    match = re.search(r"mujoco_usd_converter-([^-]*)-", wheel_name)
    if match:
        version = match.group(1)
        return version

    return ""


def is_stable_release(version):
    """Determine if this is a stable release."""
    # Check if CI_COMMIT_TAG is set and non-empty
    ci_commit_tag = os.environ.get("CI_COMMIT_TAG", "")
    if not ci_commit_tag:
        return False

    # Extract version part before "+" if it exists
    version_part = version.split("+")[0]

    # Check for pre-release suffixes (dev, rc)
    # Allow alpha and beta tags
    return not re.search(r"(dev|rc)", version_part)


def main():
    """Main function to process and upload wheel files."""
    wheel_count = 0
    print("Starting wheel processing...")

    # Find all wheel files in dist/
    packages_dir = Path("dist")
    wheel_files = list(packages_dir.glob("*.whl"))

    if not wheel_files:
        print("No wheel files found in dist/")
        sys.exit(1)

    for wheel_path in wheel_files:
        if wheel_path.is_file():
            wheel_filename = wheel_path.name
            print(f"Processing wheel: {wheel_filename}")

            # Extract metadata from wheel filename
            os_name = "all"
            arch = "any"
            version = get_version_from_wheel(wheel_filename)
            branch = os.environ.get("CI_COMMIT_REF_NAME", "unknown")

            print(f"  OS: {os_name}")
            print(f"  Architecture: {arch}")
            print(f"  Version: {version}")
            print(f"  Branch: {branch}")

            # Determine release status based on tag and version stability
            release_status = "ready" if is_stable_release(version) else "preview"

            print(f"  Release Status: {release_status}")

            # Build matrix properties string
            properties = (
                f"component_name=mujoco_usd_converter;os={os_name};arch={arch};"
                f"branch={branch};version={version};release_status={release_status};"
                f"release_approver=akaufman"
            )

            # Upload wheel with matrix properties
            print(f"Uploading {wheel_filename} with properties: {properties}")

            jfrog_cmd = [
                Path("~/bin/jfrog").expanduser(),
                "rt",
                "upload",
                str(wheel_path),
                f"ct-omniverse-pypi/mujoco-usd-converter/{version}/",
                "--props",
                properties,
            ]

            try:
                result = subprocess.run(jfrog_cmd, capture_output=False, check=False)
                upload_result = result.returncode

                if upload_result == 0:
                    print(f"Successfully uploaded {wheel_filename}")
                    wheel_count += 1
                else:
                    print(f"Failed to upload {wheel_filename} (exit code: {upload_result})")
                    sys.exit(1)

            except Exception as e:
                print(f"Failed to upload {wheel_filename}: {e}")
                sys.exit(1)

            print("")
        else:
            print(f"File does not exist or is not a regular file: {wheel_path}", file=sys.stderr)

    if wheel_count == 0:
        print("No wheel files found in dist/")
        sys.exit(1)
    else:
        print(f"Successfully uploaded {wheel_count} wheel(s) to Artifactory with matrix properties")


if __name__ == "__main__":
    main()
