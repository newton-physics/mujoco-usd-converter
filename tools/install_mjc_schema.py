# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path

import requests
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class MjcPhysicsSchemaBuildHook(BuildHookInterface):
    PLUGIN_NAME = "mjc_physics_schema"

    def initialize(self, version, build_data):
        """Called before the build starts"""
        self.target_dir = Path("mjc_usd_converter/plugins/mjcPhysics/resources")
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.download_schema_files()
        self.make_codeless_schema()

    def download_schema_files(self):
        """Download the MJC schema files from GitHub"""
        # FUTURE: lock to a specific tag or commit
        schema_url = "https://raw.githubusercontent.com/google-deepmind/mujoco/refs/heads/main/src/experimental/usd/mjcPhysics"
        for url, target_path in (
            (f"{schema_url}/generatedSchema.usda", self.target_dir / "generatedSchema.usda"),
            (f"{schema_url}/plugInfo.json", self.target_dir / "plugInfo.json"),
        ):
            self.download_schema_file(url, target_path)

    def download_schema_file(self, url: str, target_path: Path) -> None:
        """Download a schema file from a URL to a target path"""
        try:
            response = requests.get(url)
            response.raise_for_status()
            target_path.write_text(response.text)
            print(f"Downloaded schema file to {target_path}")
        except Exception as e:
            print(f"Failed to download schema file: {e}")
            raise

    def make_codeless_schema(self):
        """Make the schema codeless"""
        plug_info_path = self.target_dir / "plugInfo.json"
        if not plug_info_path.exists():
            print(f"Warning: plugInfo.json not found at {plug_info_path}")
            return

        with Path(plug_info_path).open() as f:
            plug_info = json.load(f)
        # Modify the LibraryPath to be an empty string so we have a codeless schema
        plug_info["Plugins"][0]["LibraryPath"] = ""

        # Re-write the file
        print(f"Writing plugInfo.json to {plug_info_path}")
        with Path(plug_info_path).open("w") as f:
            json.dump(plug_info, f, indent=2)
