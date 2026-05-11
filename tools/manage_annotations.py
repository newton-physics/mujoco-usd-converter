# SPDX-FileCopyrightText: Copyright (c) 2025-2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
"""
Outputs a list of MJCF asset files contained in the specified directory or GitHub repository to a file.

target repository: https://github.com/google-deepmind/mujoco_menagerie

Navigate to this repository's directory in the command line and execute it.
Specify either a directory corresponding to a local repository or a repository url on GitHub.

Activate the virtual environment:
    # Windows
    .venv/Scripts/Activate

    # Linux
    source .venv/bin/activate

Usage:
    # Acquire MJCF asset information for new or additional datasets and create annotation files.
    # Specifying "--mjcf-repository-path" retrieves MJCF asset file information from the local repository or GitHub repository url.
    # This cannot be omitted.
    # If the repository path is a GitHub repository url, it will "git clone" the repository
    # from GitHub into your working directory to retrieve the MJCF asset file information.
    # Output destination is "tools/<repository name>_annotations.yaml".

    python tools/manage_annotations.py --mjcf-repository-path https://github.com/google-deepmind/mujoco_menagerie --update

    # This does not output a YAML file.
    # Lists information on whether MJCF asset files have been manually checked from the "tools/<repository_name>_annotations.yaml" file.

    python tools/manage_annotations.py --mjcf-repository-path https://github.com/google-deepmind/mujoco_menagerie --validate
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class AnnotationManager:
    """Utility class for managing annotation files."""

    def __init__(self, mjcf_repository_path: str, annotation_file: Path):
        if mjcf_repository_path.startswith("https://") and not mjcf_repository_path.startswith("https://github.com/"):
            logger.error("MJCF repository path must start with 'https://github.com/'")
            raise

        # Repository URL on GitHub.
        if mjcf_repository_path.startswith("https://github.com/"):
            self.mjcf_repository_url = mjcf_repository_path
        else:
            self.mjcf_repository_url = None

        # Local directory path.
        self.local_mjcf_directory = Path(mjcf_repository_path) if not self.mjcf_repository_url else None

        self.repository_name = self.mjcf_repository_url.split("/")[-1] if self.mjcf_repository_url else self.local_mjcf_directory.name
        self.annotation_file = annotation_file
        self.annotations: dict[str, dict] = {}
        self.temp_dir_context = None  # TemporaryDirectory context manager

        if not self.annotation_file:
            self.annotation_file = Path(f"tools/{self.repository_name}_annotations.yaml")

        # if the repository is "mujoco", the base directory is "model".
        self.base_dir = "" if self.repository_name != "mujoco" else "model"

    def _setup_mjcf_files_from_repository(self) -> Path:
        """Setup the MJCF repository in the temporary directory. (clone if needed)."""
        if self.local_mjcf_directory and self.local_mjcf_directory.exists():
            logger.info("Using existing MJCF repository at: %s", self.local_mjcf_directory)
            return self.local_mjcf_directory

        # Clone to temporary directory using TemporaryDirectory context manager
        self.temp_dir_context = tempfile.TemporaryDirectory(prefix=f"mjcf_{self.repository_name}_benchmark_")
        mjcf_files_path = Path(self.temp_dir_context.name) / self.repository_name

        logger.info("Cloning MJCF repository to: %s", mjcf_files_path)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", f"{self.mjcf_repository_url}.git", str(mjcf_files_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to clone %s: %s", self.repository_name, e)
            # Clean up temporary directory on error
            self.temp_dir_context.cleanup()
            self.temp_dir_context = None
            raise

        self.local_mjcf_directory = mjcf_files_path
        return mjcf_files_path

    def load_annotations(self) -> dict[str, dict]:
        """Load existing annotations from file."""
        if not self.annotation_file.exists():
            logger.info("Annotation file does not exist: %s", self.annotation_file)
            return {}

        try:
            with Path.open(self.annotation_file, encoding="utf-8") as f:
                self.annotations = yaml.safe_load(f) or {}
            logger.info("Loaded %d existing annotations", len(self.annotations))
            return self.annotations
        except Exception as e:
            logger.error("Failed to load annotations: %s", e)
            return {}

    def _discover_mjcf_asset_files(self) -> dict:
        """
        Retrieve the MJCF asset file paths from the repository.

        Returns:
            A dictionary of MJCF asset file paths.
        """
        # Setup the MJCF repository in the temporary directory. (clone if needed).
        # If 'self.local_mjcf_directory' already specifies a local path, this will be skipped.
        self._setup_mjcf_files_from_repository()

        if not self.local_mjcf_directory.exists():
            logger.error("Local file path does not exist: %s", self.local_mjcf_directory)
            return {}

        _local_mjcf_directory = self.local_mjcf_directory / self.base_dir

        # Store the file path from self.local_mjcf_directory.
        _mjcf_file_paths: list[Path] = [Path(os.path.relpath(file, _local_mjcf_directory)) for file in _local_mjcf_directory.glob("**/*.xml")]

        if len(_mjcf_file_paths) == 0:
            logger.error("No MJCF files found in the repository: %s", _local_mjcf_directory)
            return {}

        # Store the MJCF asset names and their file paths in a dictionary.
        # A single asset name may contain multiple XML files.
        mjcf_file_assets: dict[str, list[Path]] = {}
        for mjcf_path in _mjcf_file_paths:
            _path = mjcf_path.as_posix()

            path_parts = _path.split("/")
            if len(path_parts) == 0:
                continue
            if path_parts[0] not in mjcf_file_assets:
                mjcf_file_assets[path_parts[0]] = []
            mjcf_file_assets[path_parts[0]].append(mjcf_path)

        return mjcf_file_assets

    def create_annotation_file(self):
        """Create the annotation file."""
        if not self.annotation_file.exists():
            with Path.open(self.annotation_file, "w", encoding="utf-8") as f:
                f.write(self._get_annotation_header())

    def _get_annotation_header(self) -> str:
        """Get the annotation header."""
        return f"""# '{self.repository_name}' Manual Annotations
# This file contains manual evaluation results for the mujoco-usd-converter benchmark
#
# Format:
#   asset_name:
#     evaluation_date: "YYYY/MM/DD" (asset-level evaluation date)
#     evaluator: "Name or identifier of person who evaluated"
#     notes: "Additional notes about the evaluation"
#     xml_files: Array of XML files to convert for this asset
#       - filename: "model.xml"
#         model_name: "asset_model"
#         description: "Description of this model variant"
#         verified: "Yes" | "Unknown" | "Partial"
#         verified_in_newton: "Yes" | "Unknown" | "No"
#         evaluation_date: "YYYY/MM/DD"
#         evaluator: "Name or identifier of person who evaluated this variant"
#         notes: "Additional notes about this variant"
#     _metadata: (auto-generated)
#       has_scene_xml: true/false
#       total_xml_files: N
#
# Asset names correspond to directory names in the '{self.repository_name}' repository:
# {self.mjcf_repository_url if self.mjcf_repository_url else ""}
"""

    def validate_annotations(self) -> list[str]:
        """Validate existing annotations and return any issues."""
        issues = []
        valid_success_values = {"Yes", "No", "Unknown"}

        for asset_name, annotation in self.annotations.items():
            if not isinstance(annotation, dict):
                issues.append(f"{asset_name}: annotation must be a dictionary")
                continue

            # Check verified value
            _xml_files = annotation.get("xml_files", [])
            for xml_file in _xml_files:
                model_name = xml_file.get("model_name", "")
                success = xml_file.get("verified", "No")
                if success not in valid_success_values:
                    issues.append(f"{asset_name}: {model_name}: verified must be one of {valid_success_values}, got '{success}'")

                # Check required fields exist
                required_fields = ["verified", "notes"]
                for field in required_fields:
                    if field not in xml_file:
                        issues.extend(f"{asset_name}: {model_name}: missing required field '{field}'")

        return issues

    def _generate_template_for_asset(self, asset_name: str, file_paths: list[Path]) -> dict:
        """
        Generate a template annotation for a new asset.
        """
        _dict = {}
        _dict["_metadata"] = {
            "has_scene_xml": any(file_path.name == "scene.xml" for file_path in file_paths),
            "total_xml_files": len(file_paths),
        }
        _dict["evaluation_date"] = ""
        _dict["evaluator"] = ""
        _dict["notes"] = ""

        _dict["xml_files"] = []
        for file_path in file_paths:
            if file_path.name == "scene.xml":
                continue
            _dict["xml_files"].append(
                {
                    "asset": asset_name,
                    "description": f"Model variant: {file_path.stem}",
                    "evaluation_date": "",
                    "evaluator": "",
                    "filename": file_path.name,
                    "model_name": file_path.stem,
                    "notes": "",
                    "verified": "Unknown",
                    "verified_in_newton": "Unknown",
                }
            )

        return _dict

    def update_annotation_file(self, new_assets: set[str], discovered_files: dict[str, list[Path]], dry_run: bool = False):
        """
        Update the annotation file with new assets.

        Args:
            new_assets: The set of new asset names.
            discovered_files: The dictionary of discovered file paths.
            dry_run: Whether to run in dry run mode.
        """
        if not new_assets:
            logger.info("No new assets to add")
            return

        logger.info("Adding templates for %d new assets: %s", len(new_assets), ", ".join(sorted(new_assets)))

        # Add templates for new assets
        for asset_name in new_assets:
            self.annotations[asset_name] = self._generate_template_for_asset(asset_name, discovered_files[asset_name])

        if dry_run:
            logger.info("Dry run: would update annotation file")
            return

        # Write updated annotations
        try:
            with Path.open(self.annotation_file, "w", encoding="utf-8") as f:
                f.write(self._get_annotation_header())
                yaml.dump(self.annotations, f, default_flow_style=False, sort_keys=True, allow_unicode=True, width=100)
            logger.info("Updated annotation file: %s", self.annotation_file)
        except Exception as e:
            logger.error("Failed to update annotation file: %s", e)

    def cleanup(self):
        """Clean up temporary resources."""
        if self.temp_dir_context:
            try:
                self.temp_dir_context.cleanup()
                logger.info("Cleaned up temporary MJCF directory")
            except Exception as e:
                logger.warning("Failed to clean up temporary MJCF directory: %s", str(e))
            finally:
                self.temp_dir_context = None

    def print_summary(self):
        """Print a summary of annotations."""
        if not self.annotations:
            logger.info("No annotations loaded")
            return

        success_counts = {"Yes": 0, "No": 0, "Unknown": 0}
        evaluated_count = 0
        for asset_name, annotation in self.annotations.items():
            for xml_file in annotation["xml_files"]:
                success = xml_file.get("verified", "Unknown")
                success_counts[success] = success_counts.get(success, 0) + 1
                if xml_file.get("evaluation_date") or xml_file.get("evaluator"):
                    evaluated_count += 1

        print("\nAnnotation Summary:")
        print(f"  Total assets: {len(self.annotations)}")
        print(f"  Evaluated: {evaluated_count}")
        print("  Success breakdown:")
        for status, count in success_counts.items():
            print(f"    {status}: {count}")

        if evaluated_count > 0:
            print("\nRecently evaluated assets:")
            for asset_name, annotation in self.annotations.items():
                for xml_file in annotation["xml_files"]:
                    if xml_file.get("evaluation_date"):
                        date = xml_file["evaluation_date"]
                        evaluator = xml_file.get("evaluator", "Unknown")
                        success = xml_file.get("verified", "Unknown")
                        print(f"  {asset_name}: {success} ({date}, {evaluator})")


def main():
    parser = argparse.ArgumentParser(description="Manage MuJoCo MJCF repository annotations", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        "--mjcf-repository-path",
        type=str,
        required=True,
        help="URL or local path of the repository containing the MJCF.",
    )

    parser.add_argument("--annotation-file", type=Path, default=None, help="Path to the annotation YAML file")

    parser.add_argument("--update", action="store_true", help="Update the annotation file with new assets found in Menagerie")

    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    parser.add_argument("--validate", action="store_true", help="Validate existing annotations")

    args = parser.parse_args()

    # Create annotation manager
    manager = AnnotationManager(args.mjcf_repository_path, args.annotation_file)

    # Load existing annotations
    manager.load_annotations()

    # Validate annotations if requested
    if args.validate:
        issues = manager.validate_annotations()
        if issues:
            logger.error("Validation issues found:")
            for issue in issues:
                logger.error("  %s", issue)
            return 1
        else:
            logger.info("All annotations are valid")

    # Update annotations if requested
    if args.update:
        discovered_files = manager._discover_mjcf_asset_files()
        discovered_assets = discovered_files.keys()
        existing_assets = set(manager.annotations.keys())
        new_assets = discovered_assets - existing_assets

        if new_assets:
            manager.update_annotation_file(new_assets, discovered_files, dry_run=args.dry_run)
        else:
            logger.info("No new assets found")

    # Print summary
    manager.print_summary()

    # Clean up temporary resources.
    manager.cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
