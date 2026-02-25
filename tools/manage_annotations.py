# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
"""
Annotation Management Utility

This script helps manage the menagerie_annotations.yaml file by:
- Generating templates for new assets discovered in the MuJoCo Menagerie
- Validating existing annotations
- Updating the annotation file with new assets
"""

import argparse
import logging
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

    MENAGERIE_REPO_URL = "https://github.com/google-deepmind/mujoco_menagerie.git"
    MENAGERIE_BASE_URL = "https://github.com/google-deepmind/mujoco_menagerie/tree/main/"

    def __init__(self, annotation_file: Path):
        self.annotation_file = annotation_file
        self.menagerie_path = self.setup_menagerie()
        self.annotations: dict[str, dict] = {}

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

    def setup_menagerie(self) -> Path:
        """Setup MuJoCo Menagerie repository (clone if needed)."""

        # Clone to temporary directory
        temp_dir = tempfile.mkdtemp(prefix="menagerie_analysis_")
        menagerie_path = Path(temp_dir) / "mujoco_menagerie"

        logger.info("Cloning MuJoCo Menagerie to: %s", menagerie_path)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", self.MENAGERIE_REPO_URL, str(menagerie_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error("Failed to clone Menagerie: %s", e)
            raise

        self.menagerie_path = menagerie_path
        self.temp_menagerie = True
        return menagerie_path

    def discover_menagerie_assets(self) -> set[str]:
        """Discover asset names from MuJoCo Menagerie directory."""
        assets = set()
        for item in self.menagerie_path.iterdir():
            # Check if it contains XML files (likely a model)
            if item.is_dir() and not item.name.startswith(".") and any(item.glob("*.xml")):
                assets.add(item.name)

        logger.info("Discovered %d assets in Menagerie", len(assets))
        return assets

    def validate_annotations(self) -> list[str]:
        """Validate existing annotations and return any issues."""
        issues = []

        valid_success_values = {"Yes", "No", "Unknown"}

        for asset_name, annotation in self.annotations.items():
            if not isinstance(annotation, dict):
                issues.append(f"{asset_name}: annotation must be a dictionary")
                continue

            # Check practical_success value
            success = annotation.get("practical_success", "No")
            if success not in valid_success_values:
                issues.append(f"{asset_name}: practical_success must be one of {valid_success_values}, got '{success}'")

            # Check required fields exist
            required_fields = ["practical_success", "notes"]
            issues.extend(f"{asset_name}: missing required field '{field}'" for field in required_fields if field not in annotation)

        return issues

    def generate_template_for_asset(self, asset_name: str) -> dict:
        """Generate a template annotation for a new asset."""
        return {"practical_success": "No", "verified_in_newton": "No", "evaluation_date": "", "evaluator": "", "notes": ""}

    def update_annotation_file(self, new_assets: set[str], dry_run: bool = False):
        """Update the annotation file with new assets."""
        if not new_assets:
            logger.info("No new assets to add")
            return

        logger.info("Adding templates for %d new assets: %s", len(new_assets), ", ".join(sorted(new_assets)))

        # Add templates for new assets
        for asset_name in new_assets:
            self.annotations[asset_name] = self.generate_template_for_asset(asset_name)

        if dry_run:
            logger.info("Dry run: would update annotation file")
            return

        # Write updated annotations
        try:
            with Path.open(self.annotation_file, "w", encoding="utf-8") as f:
                yaml.dump(self.annotations, f, default_flow_style=False, sort_keys=True, allow_unicode=True, width=100)
            logger.info("Updated annotation file: %s", self.annotation_file)
        except Exception as e:
            logger.error("Failed to update annotation file: %s", e)

    def print_summary(self):
        """Print a summary of annotations."""
        if not self.annotations:
            logger.info("No annotations loaded")
            return

        success_counts = {"Yes": 0, "No": 0, "Unknown": 0}
        evaluated_count = 0

        for asset_name, annotation in self.annotations.items():
            success = annotation.get("practical_success", "No")
            success_counts[success] = success_counts.get(success, 0) + 1

            if annotation.get("evaluation_date") or annotation.get("evaluator"):
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
                if annotation.get("evaluation_date"):
                    date = annotation["evaluation_date"]
                    evaluator = annotation.get("evaluator", "Unknown")
                    success = annotation.get("practical_success", "No")
                    print(f"  {asset_name}: {success} ({date}, {evaluator})")


def main():
    parser = argparse.ArgumentParser(description="Manage MuJoCo Menagerie annotations", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--annotation-file", type=Path, default=Path("tools/menagerie_annotations.yaml"), help="Path to the annotation YAML file")

    parser.add_argument("--update", action="store_true", help="Update the annotation file with new assets found in Menagerie")

    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    parser.add_argument("--validate", action="store_true", help="Validate existing annotations")

    args = parser.parse_args()

    # Create annotation manager
    manager = AnnotationManager(args.annotation_file)

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
        discovered_assets = manager.discover_menagerie_assets()
        existing_assets = set(manager.annotations.keys())
        new_assets = discovered_assets - existing_assets

        if new_assets:
            manager.update_annotation_file(new_assets, dry_run=args.dry_run)
        else:
            logger.info("No new assets found")

    # Print summary
    manager.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
