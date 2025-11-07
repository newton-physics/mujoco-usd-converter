# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
"""
Python wheel upload script for JFrog Artifactory.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import requests


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


def send_kitmaker_post(version: str, wheel_filename: str):
    """Send a POST request to the KitMaker endpoint to trigger wheel publish"""

    omniverse_pypi_url = os.environ.get("OMNIVERSE_PYPI_URL")
    if not omniverse_pypi_url:
        raise RuntimeError("OMNIVERSE_PYPI_URL is not set")
    kitmaker_pic = os.environ.get("KITMAKER_PIC")
    if not kitmaker_pic:
        raise RuntimeError("KITMAKER_PIC is not set")

    payload = {
        "project_name": "mujoco-usd-converter",
        "payload": [
            {
                "pic": kitmaker_pic,
                "job_type": "wheel-release-job",
                "publish_to": "both_devzone_pypi",
                "url": f"{omniverse_pypi_url}/mujoco-usd-converter/{version}/{wheel_filename}",
                "size": "small",
                "upload": True,
            }
        ],
    }

    service_token = os.environ.get("KITMAKER_SERVICE_TOKEN")
    if not service_token:
        raise RuntimeError("KITMAKER_SERVICE_TOKEN is not set")
    headers = {"accept": "application/json", "Authorization": f"Bearer {service_token}", "Content-Type": "application/json"}

    # Mujoco project id is 171
    usdex_kitmaker_url = os.environ.get("KITMAKER_UPLOAD_URL")
    if not usdex_kitmaker_url:
        raise RuntimeError("KITMAKER_UPLOAD_URL is not set")
    response = requests.post(usdex_kitmaker_url, json=payload, headers=headers, verify=False)
    if response.status_code not in [200, 201, 202]:
        raise RuntimeError(f"Failed to send POST request to KitMaker: {response.status_code} | {response.text}")


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

                if is_stable_release(version):
                    send_kitmaker_post(version, wheel_filename)
                else:
                    print(f"Skipping KitMaker post for dev release {version}")

            except Exception as e:
                print(f"Failed to upload {wheel_filename}: {e}")
                import traceback

                traceback.print_exc()
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
