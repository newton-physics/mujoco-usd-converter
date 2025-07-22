# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
MuJoCo Menagerie Model Analysis Script

This script analyzes the MuJoCo Menagerie repository to discover all XML files
for each asset and updates the annotations file with the xml_files array.
"""

import argparse
import logging
import subprocess
import tempfile
from pathlib import Path

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class MenagerieAnalyzer:
    """Analyzes MuJoCo Menagerie repository to discover XML files for each asset."""

    MENAGERIE_REPO_URL = "https://github.com/google-deepmind/mujoco_menagerie.git"

    def __init__(self, menagerie_path: Path | None = None, annotation_file: Path | None = None):
        self.menagerie_path = menagerie_path
        self.annotation_file = annotation_file or Path("tools/menagerie_annotations.yaml")
        self.temp_menagerie = False
        self.annotations = {}

    def setup_menagerie(self) -> Path:
        """Setup MuJoCo Menagerie repository (clone if needed)."""
        if self.menagerie_path and self.menagerie_path.exists():
            logger.info("Using existing Menagerie at: %s", self.menagerie_path)
            return self.menagerie_path

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

    def analyze_assets(self) -> dict[str, dict]:
        """Analyze all assets in the Menagerie repository."""
        logger.info("Analyzing MuJoCo Menagerie assets...")

        asset_data = {}

        # Look for asset directories
        for asset_dir in self.menagerie_path.iterdir():
            if not asset_dir.is_dir() or asset_dir.name.startswith("."):
                continue

            # Find all XML files in the asset directory
            xml_files = list(asset_dir.glob("*.xml"))
            if not xml_files:
                continue

            asset_name = asset_dir.name
            logger.info("Found asset: %s with %d XML files", asset_name, len(xml_files))

            # Categorize XML files
            xml_file_info = []
            scene_xml = None

            for xml_file in xml_files:
                xml_name = xml_file.name

                if "scene" in xml_name.lower():
                    scene_xml = xml_name
                    continue

                # For non-scene XML files, create a descriptive name
                # Remove .xml extension for the model name
                model_name = xml_file.stem
                xml_file_info.append(
                    {
                        "filename": xml_name,
                        "asset": asset_name,
                        "model_name": model_name,
                        "description": f"Model variant: {model_name}",
                        "practical_success": "Unknown",
                        "evaluation_date": "",
                        "evaluator": "",
                        "notes": "",
                    }
                )

            # Only include assets that have non-scene XML files
            if xml_file_info:
                asset_data[asset_name] = {"xml_files": xml_file_info, "has_scene_xml": scene_xml is not None, "total_xml_files": len(xml_files)}

                # Log details for this asset
                logger.info("  Asset: %s", asset_name)
                logger.info("    Has scene.xml: %s", scene_xml is not None)
                logger.info("    Model XML files: %d", len(xml_file_info))
                for xml_info in xml_file_info:
                    logger.info("      - %s -> %s", xml_info["filename"], xml_info["model_name"])

        logger.info("Analysis complete: found %d assets with convertible XML files", len(asset_data))
        return asset_data

    def load_existing_annotations(self) -> dict:
        """Load existing annotations from file."""
        if not self.annotation_file.exists():
            logger.info("Annotation file does not exist: %s", self.annotation_file)
            return {}

        try:
            with Path.open(self.annotation_file, encoding="utf-8") as f:
                annotations = yaml.safe_load(f) or {}
            logger.info("Loaded %d existing annotations", len(annotations))
            return annotations
        except Exception as e:
            logger.error("Failed to load annotations: %s", e)
            return {}

    def update_annotations(self, asset_data: dict[str, dict], dry_run: bool = False) -> None:
        """Update annotations file with discovered XML files."""
        # Load existing annotations
        existing_annotations = self.load_existing_annotations()

        # Update annotations with XML file information
        updated_annotations = {}

        for asset_name, data in asset_data.items():
            # Start with existing annotation if it exists
            if asset_name in existing_annotations:
                updated_annotations[asset_name] = existing_annotations[asset_name].copy()
            else:
                # Create new annotation entry with only essential asset-level fields
                updated_annotations[asset_name] = {
                    "evaluation_date": "",
                    "evaluator": "",
                    "notes": "",
                }

            # Merge xml_files array, preserving existing variant annotations
            existing_xml_files = updated_annotations[asset_name].get("xml_files", [])
            existing_variants = {xml_info.get("model_name"): xml_info for xml_info in existing_xml_files}

            # Update with discovered XML files, preserving existing variant annotations
            merged_xml_files = []
            for new_xml_info in data["xml_files"]:
                model_name = new_xml_info["model_name"]
                if model_name in existing_variants:
                    # Preserve existing variant annotations, but update structural info and add missing fields
                    existing_variant = existing_variants[model_name].copy()
                    existing_variant.update(
                        {"filename": new_xml_info["filename"], "asset": new_xml_info["asset"], "description": new_xml_info["description"]}
                    )

                    # Add missing per-variant annotation fields with defaults
                    if "practical_success" not in existing_variant:
                        existing_variant["practical_success"] = "Unknown"
                    if "evaluation_date" not in existing_variant:
                        existing_variant["evaluation_date"] = ""
                    if "evaluator" not in existing_variant:
                        existing_variant["evaluator"] = ""
                    if "notes" not in existing_variant:
                        existing_variant["notes"] = ""

                    merged_xml_files.append(existing_variant)
                else:
                    # New variant, use default annotations
                    merged_xml_files.append(new_xml_info)

            updated_annotations[asset_name]["xml_files"] = merged_xml_files

            # Add metadata about the asset
            updated_annotations[asset_name]["_metadata"] = {"has_scene_xml": data["has_scene_xml"], "total_xml_files": data["total_xml_files"]}

        # Add any existing annotations that weren't found in the current analysis
        for asset_name, annotation in existing_annotations.items():
            if asset_name not in updated_annotations:
                logger.warning("Asset %s exists in annotations but not found in Menagerie", asset_name)
                updated_annotations[asset_name] = annotation

        if dry_run:
            logger.info("DRY RUN: Would update annotations file with %d assets", len(updated_annotations))
            # Show sample of what would be updated
            for asset_name in list(updated_annotations.keys())[:3]:
                logger.info("  %s: %d XML files", asset_name, len(updated_annotations[asset_name].get("xml_files", [])))
        else:
            # Write updated annotations
            self._write_annotations(updated_annotations)
            logger.info("Updated annotations file: %s", self.annotation_file)

    def _write_annotations(self, annotations: dict) -> None:
        """Write annotations to file with proper formatting."""
        # Create header comment
        header = """# MuJoCo Menagerie Manual Annotations
# This file contains manual evaluation results for the mujoco-usd-converter benchmark
#
# Format:
#   asset_name:
#     evaluation_date: "YYYY-MM-DD" (asset-level evaluation date)
#     evaluator: "Name or identifier of person who evaluated"
#     notes: "Additional notes about the evaluation"
#     xml_files: Array of XML files to convert for this asset
#       - filename: "model.xml"
#         model_name: "asset_model"
#         description: "Description of this model variant"
#         practical_success: "Yes" | "Unknown" | "No"
#         evaluation_date: "YYYY-MM-DD"
#         evaluator: "Name or identifier of person who evaluated this variant"
#         notes: "Additional notes about this variant"
#     _metadata: (auto-generated)
#       has_scene_xml: true/false
#       total_xml_files: N
#
# Asset names correspond to directory names in the MuJoCo Menagerie repository:
# https://github.com/google-deepmind/mujoco_menagerie
"""

        with Path.open(self.annotation_file, "w", encoding="utf-8") as f:
            f.write(header)
            yaml.dump(annotations, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

    def cleanup(self):
        """Clean up temporary resources."""
        if self.temp_menagerie and self.menagerie_path:
            try:
                import shutil

                shutil.rmtree(self.menagerie_path.parent)
                logger.info("Cleaned up temporary Menagerie directory")
            except Exception as e:
                logger.warning("Failed to clean up temporary directory: %s", e)


def main():
    """Main entry point for the analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze MuJoCo Menagerie models and update annotations", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--menagerie-path", type=Path, help="Path to existing MuJoCo Menagerie repository (will clone if not provided)")

    parser.add_argument("--annotation-file", type=Path, default=Path("tools/menagerie_annotations.yaml"), help="Path to the annotation YAML file")

    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create analyzer
    analyzer = MenagerieAnalyzer(args.menagerie_path, args.annotation_file)

    try:
        # Setup Menagerie
        analyzer.setup_menagerie()

        # Analyze assets
        asset_data = analyzer.analyze_assets()

        if not asset_data:
            logger.error("No assets with XML files found")
            return 1

        # Update annotations
        analyzer.update_annotations(asset_data, dry_run=args.dry_run)

        logger.info("Analysis completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error("Analysis failed: %s", e)
        return 1
    finally:
        analyzer.cleanup()


if __name__ == "__main__":
    import sys

    sys.exit(main())
