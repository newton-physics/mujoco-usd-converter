# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
MuJoCo Menagerie Benchmark Script

This script benchmarks the mujoco-usd-converter against all models in the MuJoCo Menagerie repository.
It generates a comprehensive report with success/failure metrics, performance data,
and templates for manual evaluation.
"""

import argparse
import csv
import logging
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin

# TOML parsing imports (handle both Python 3.11+ and older versions)
try:
    import tomllib
except ImportError:
    import tomli as tomllib

import yaml

HOST_ARCH = platform.machine()
if HOST_ARCH == "AMD64":
    HOST_ARCH = "x86_64"

Path("benchmarks").mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("benchmarks/benchmarks.log", mode="a")],
)
logger = logging.getLogger(__name__)


def get_converter_version() -> str:
    """Read the converter version from pyproject.toml in the parent directory."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    try:
        with Path.open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)

        version = pyproject_data.get("project", {}).get("version", "unknown")
        logger.debug("Read converter version from pyproject.toml: %s", version)
        return version
    except Exception as e:
        logger.warning("Failed to read version from pyproject.toml: %s", e)
        return "unknown"


# Import the converter and USD dependencies
# These should work properly when run through uv in the project environment
try:
    import usdex.core

    logger.info("Successfully imported usdex.core")
except ImportError as e:
    logger.error("Failed to import required dependencies: %s", e)
    logger.error("Make sure you're running this script with: uv run benchmark")
    logger.error("Or: uv run python benchmark_menagerie.py")
    sys.exit(1)


@dataclass
class BenchmarkResult:
    """Data class for storing benchmark results for a single model."""

    asset_name: str
    variant_name: str
    menagerie_url: str
    local_path: str
    success: bool
    error_count: int
    warning_count: int
    error_message: str
    warnings: str
    conversion_time_seconds: float
    total_file_size_mb: float
    verified: str = "No"  # Manual annotation template
    notes: str = ""  # Manual annotation template

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class DiagnosticsCapture:
    """Custom diagnostics capture using usdex.core diagnostics system."""

    def __init__(self):
        self.warnings = []
        self.errors = []
        self.statuses = []
        self.captured_output = []
        self.original_stream = None

    def reset(self):
        """Reset captured diagnostics."""
        self.warnings.clear()
        self.errors.clear()
        self.statuses.clear()
        self.captured_output.clear()

    def get_counts(self) -> tuple[int, int]:
        """Get error and warning counts."""
        return len(self.errors), len(self.warnings)

    def capture_subprocess_output(self, cmd: list[str], cwd: str | None = None) -> tuple[str, str, int]:
        """Run a command and capture its output including diagnostics."""
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)  # 5 minute timeout

            # Parse both stdout and stderr for diagnostics
            combined_output = result.stdout + result.stderr
            self._parse_captured_output(combined_output)

            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"Failed to run conversion: {e}")

    def _parse_captured_output(self, output: str):
        """Parse captured output to extract warnings and errors."""
        if not output:
            return

        lines = output.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse structured diagnostic messages in format [Level] [Component] Message
            if line.startswith("[") and "]" in line:
                # Extract the level from [Level] at the start
                first_bracket_end = line.find("]")
                if first_bracket_end != -1:
                    level = line[1:first_bracket_end].lower()

                    if level in ["error", "fatal", "critical"]:
                        self.errors.append(line)
                    elif level in ["warning", "warn"]:
                        self.warnings.append(line)
                    elif level in ["status", "info", "debug"]:
                        self.statuses.append(line)
                    else:
                        # If we can't categorize it but it looks like a diagnostic message
                        self.statuses.append(line)
                    continue

            # Fallback: Look for common error/warning patterns in other formats
            lower_line = line.lower()
            if any(pattern in lower_line for pattern in ["error:", "failed:", "exception:", "fatal:", "critical:", "abort"]):
                self.errors.append(line)
            elif any(pattern in lower_line for pattern in ["warning:", "warn:", "deprecated:", "caution:"]):
                self.warnings.append(line)
            elif any(pattern in lower_line for pattern in ["status:", "info:", "note:", "debug:"]):
                self.statuses.append(line)


class MenagerieBenchmark:
    """Main benchmark class for testing mujoco-usd-converter against MuJoCo Menagerie."""

    MENAGERIE_REPO_URL = "https://github.com/google-deepmind/mujoco_menagerie.git"
    MENAGERIE_BASE_URL = "https://github.com/google-deepmind/mujoco_menagerie/tree/main/"
    DEFAULT_ANNOTATION_FILE = "menagerie_annotations.yaml"

    def __init__(
        self,
        menagerie_path: str | None = None,
        report_output_dir: str = "benchmarks",
        conversion_output_dir: str = "benchmarks",
        annotation_file: str | None = None,
    ):
        self.menagerie_path = Path(menagerie_path) if menagerie_path else None
        self.report_output_dir = Path(report_output_dir)
        self.conversion_output_dir = Path(conversion_output_dir)
        self.temp_menagerie = False
        self.diagnostics = DiagnosticsCapture()
        self.results: list[BenchmarkResult] = []
        self.annotations: dict[str, dict] = {}

        # Setup annotation file path
        if annotation_file:
            self.annotation_file = Path(annotation_file)
        else:
            self.annotation_file = Path(__file__).parent / self.DEFAULT_ANNOTATION_FILE

        # Create output directory
        self.report_output_dir.mkdir(parents=True, exist_ok=True)
        self.conversion_output_dir.mkdir(parents=True, exist_ok=True)

        # Load annotations
        self._load_annotations()

        # Setup USD diagnostics
        self._setup_diagnostics()

    def _load_annotations(self):
        """Load manual annotations from YAML file."""

        if not self.annotation_file.exists():
            logger.warning("Annotation file not found: %s", self.annotation_file)
            logger.info("Using default annotation values. Create the file to add manual evaluations.")
            return

        try:
            with Path.open(self.annotation_file, encoding="utf-8") as f:
                self.annotations = yaml.safe_load(f) or {}
            logger.info("Loaded %d manual annotations from %s", len(self.annotations), self.annotation_file)
        except Exception as e:
            logger.error("Failed to load annotations from %s: %s", self.annotation_file, e)
            logger.info("Using default annotation values.")

    def _get_annotation(self, asset_name: str, model_name: str) -> tuple[str, str]:
        """Get Verified and notes for a specific model variant."""
        if asset_name not in self.annotations:
            return "Unknown", ""

        annotation = self.annotations[asset_name]
        xml_files = annotation.get("xml_files", [])

        # Find the specific variant
        for xml_info in xml_files:
            if xml_info.get("model_name") == model_name:
                verified = xml_info.get("verified", "Unknown")
                notes = xml_info.get("notes", "")
                return verified, notes

        # If variant not found, return defaults (should not happen with properly updated annotations)
        logger.warning("Variant %s not found in annotations for asset %s", model_name, asset_name)
        return "Unknown", ""

    def _setup_diagnostics(self):
        """Setup USD diagnostics to capture warnings and errors."""
        try:
            # Activate the usdex.core diagnostics delegate
            usdex.core.activateDiagnosticsDelegate()

            # Set diagnostics level to capture all messages
            usdex.core.setDiagnosticsLevel(usdex.core.DiagnosticsLevel.eStatus)

            logger.info("Successfully activated usdex.core diagnostics delegate")
        except Exception as e:
            logger.warning("Failed to setup USD diagnostics: %s", e)

    def setup_menagerie(self) -> Path:
        """Setup MuJoCo Menagerie repository (clone if needed)."""
        if self.menagerie_path and self.menagerie_path.exists():
            logger.info("Using existing Menagerie at: %s", self.menagerie_path)
            return self.menagerie_path

        # Clone to temporary directory
        temp_dir = tempfile.mkdtemp(prefix="menagerie_benchmark_")
        menagerie_path = Path(temp_dir) / "mujoco_menagerie"

        logger.info("Cloning MuJoCo Menagerie to: %s", menagerie_path)
        try:
            subprocess.run(["git", "clone", "--depth", "1", self.MENAGERIE_REPO_URL, str(menagerie_path)], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to clone Menagerie: %s", e)
            raise

        self.menagerie_path = menagerie_path
        self.temp_menagerie = True
        return menagerie_path

    def find_mjcf_models(self) -> list[tuple[str, str, Path]]:
        """Find all MJCF models based on annotations file."""
        models = []

        if not self.annotations:
            logger.error("No annotations loaded. Cannot determine which models to convert.")
            return []

        # Use annotations to determine which XML files to convert
        for asset_name, annotation in self.annotations.items():
            xml_files = annotation.get("xml_files", [])

            if not xml_files:
                logger.warning("Asset %s has no xml_files defined in annotations", asset_name)
                continue

            asset_dir = self.menagerie_path / asset_name
            if not asset_dir.exists():
                logger.warning("Asset directory not found: %s", asset_dir)
                continue

            # Add each XML file as a separate model to convert
            for xml_info in xml_files:
                xml_filename = xml_info["filename"]
                model_name = xml_info["model_name"]
                xml_path = asset_dir / xml_filename

                if xml_path.exists():
                    models.append((asset_name, model_name, xml_path))
                    logger.debug("Added model: %s -> %s (%s)", asset_name, model_name, xml_filename)
                else:
                    logger.warning("XML file not found: %s", xml_path)

        logger.info("Found %d MJCF models from annotations", len(models))
        return sorted(models)

    def convert_model(self, asset_name: str, model_name: str, mjcf_path: Path) -> BenchmarkResult:
        """Convert a single model and return the benchmark result."""
        logger.info("Converting model: %s", model_name)

        # Create result object
        result = BenchmarkResult(
            asset_name=asset_name,
            variant_name=model_name,
            menagerie_url=urljoin(self.MENAGERIE_BASE_URL, f"{asset_name}/"),
            local_path=str(mjcf_path),
            success=False,
            error_count=0,
            warning_count=0,
            error_message="",
            warnings="",
            conversion_time_seconds=0.0,
            total_file_size_mb=0.0,
            verified="No",  # Initialize with default
            notes="",  # Initialize with default
        )

        # Create output directory for this model
        model_output_dir = self.conversion_output_dir / model_name
        model_output_dir.mkdir(parents=True, exist_ok=True)

        # Reset diagnostics for this model
        self.diagnostics.reset()

        start_time = time.time()

        # Run conversion via subprocess to capture diagnostics properly
        stdout, stderr, return_code = self.diagnostics.capture_subprocess_output(
            [
                "uv",
                "run",
                "mujoco_usd_converter",
                str(mjcf_path),
                str(model_output_dir),
                "--verbose",
                "--comment",
                f"Converted from MuJoCo Menagerie model: {model_name}",
            ]
        )

        end_time = time.time()
        result.conversion_time_seconds = end_time - start_time

        if return_code != 0:
            result.error_message = f"Conversion failed with return code {return_code}. Stderr: {stderr}"
            logger.error("Failed to convert %s: %s", model_name, result.error_message)
        else:
            layer_files = [f for f in model_output_dir.iterdir() if f.is_file() and f.suffix.lower() == ".usda"]

            if layer_files:
                result.success = True
                result.total_file_size_mb = self._get_categorized_file_sizes(model_output_dir)
                logger.info("Successfully converted %s in %.2fs", model_name, result.conversion_time_seconds)
            else:
                result.error_message = f"Conversion completed but no USD layer file found in {model_output_dir}"
                logger.warning("Conversion completed but no USD layer found for %s", model_name)

        # Capture diagnostics counts
        result.error_count, result.warning_count = self.diagnostics.get_counts()
        result.warnings = "\n".join([x.rpartition("] ")[2].strip() for x in self.diagnostics.warnings])

        # Get manual annotations
        result.verified, result.notes = self._get_annotation(asset_name, model_name)

        return result

    def _get_categorized_file_sizes(self, directory: Path) -> float:
        """Get total file size in MB."""

        total_size = 0

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        file_size = file_path.stat().st_size
                        total_size += file_size

                    except OSError as e:
                        logger.warning("Failed to get size for file %s: %s", file_path, e)
                        continue

        except Exception as e:
            logger.error("Failed to scan directory %s: %s", directory, e)
            return 0.0

        # Convert bytes to MB
        total_size_mb = total_size / (1024 * 1024)

        return total_size_mb

    def _format_time_duration(self, seconds: float) -> str:
        """Format time duration as XXmYY.ZZs."""
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"

    def run_benchmark(self) -> list[BenchmarkResult]:
        """Run the complete benchmark suite."""
        logger.info("Starting MuJoCo Menagerie benchmark")

        # Setup Menagerie
        self.setup_menagerie()

        # Find all models
        models = self.find_mjcf_models()

        if not models:
            logger.error("No MJCF models found in Menagerie")
            return []

        # Convert each model
        results = []
        for i, (asset_name, model_name, mjcf_path) in enumerate(models, 1):
            logger.info("Processing model %d/%d: %s", i, len(models), model_name)
            result = self.convert_model(asset_name, model_name, mjcf_path)
            results.append(result)

            # Log progress
            success_count = sum(1 for r in results if r.success)
            logger.info("Progress: %d/%d processed, %d successful", i, len(models), success_count)

        self.results = results
        return results

    def generate_report(self, format_type: str = "all") -> dict[str, Path]:
        """Generate benchmark report in specified format(s)."""
        if not self.results:
            logger.warning("No results to generate report from")
            return {}

        reports = {}

        if format_type in ["csv", "all"]:
            reports["csv"] = self._generate_csv_report()

        if format_type in ["html", "all"]:
            reports["html"] = self._generate_html_report()

        if format_type in ["md", "all"]:
            reports["md"] = self._generate_markdown_report()

        # Generate summary
        self._generate_summary(save_to_file=format_type == "all")

        return reports

    def _generate_csv_report(self) -> Path:
        """Generate CSV report."""
        csv_path = self.report_output_dir / "benchmarks.csv"

        fieldnames = [
            "Asset Name",
            "Variant Name",
            "Menagerie URL",
            "Local Path",
            "Success",
            "Error Count",
            "Warning Count",
            "Conversion Time (s)",
            "Total Size (MB)",
            "Verified (Manual)",
            "Notes (Manual)",
            "Errors",
        ]

        # Sort results by asset name, then variant name
        sorted_results = sorted(self.results, key=lambda r: (r.asset_name, r.variant_name))

        with Path.open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            previous_asset = None
            for result in sorted_results:
                # Only show asset name for first variant in each group
                asset_display = result.asset_name if result.asset_name != previous_asset else ""
                previous_asset = result.asset_name

                writer.writerow(
                    {
                        "Asset Name": asset_display,
                        "Variant Name": result.variant_name,
                        "Menagerie URL": result.menagerie_url if asset_display else "",
                        "Local Path": result.local_path,
                        "Success": "Yes" if result.success else "No",
                        "Error Count": result.error_count,
                        "Warning Count": result.warning_count,
                        "Conversion Time (s)": f"{result.conversion_time_seconds:.3f}" if result.success else "N/A",
                        "Total Size (MB)": f"{result.total_file_size_mb:.2f}",
                        "Verified (Manual)": result.verified,
                        "Notes (Manual)": result.notes,
                        "Errors": result.error_message,
                    }
                )

        logger.info("CSV report generated: %s", csv_path.absolute())
        return csv_path

    def _generate_html_report(self) -> Path:
        """Generate HTML report."""
        html_path = self.report_output_dir / "benchmarks.html"

        # Calculate statistics
        total_models = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_models - successful
        total_errors = sum(r.error_count for r in self.results)
        total_warnings = sum(r.warning_count for r in self.results)
        avg_time = sum(r.conversion_time_seconds for r in self.results) / total_models if total_models > 0 else 0
        total_time = sum(r.conversion_time_seconds for r in self.results)
        total_file_size = sum(r.total_file_size_mb for r in self.results)

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MuJoCo Menagerie Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; flex-wrap: wrap; }}
        .stat-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center; margin: 5px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th:nth-child(10), td:nth-child(10) {{ min-width: 350px; width: 350px; }}
        th {{ background-color: #f2f2f2; }}
        .success-cell {{ background-color: #d4edda; }}
        .failure-cell {{ background-color: #f8d7da; }}
        .warning-cell {{ background-color: #faaa64; }}
        .manual-annotation {{ background-color: #fff3cd; font-style: italic; }}
        .numeric {{ text-align: right; }}
        .asset-group {{ border-top: 2px solid #007bff; }}
        .variant-row {{ border-top: 1px solid #e9ecef; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MuJoCo Menagerie Benchmark Report</h1>
        <p>Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Repository: <a href="{self.MENAGERIE_REPO_URL}">{self.MENAGERIE_REPO_URL}</a></p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <h3>Total Models</h3>
            <p>{total_models}</p>
        </div>
        <div class="stat-box">
            <h3 class="success">Successful</h3>
            <p>{successful} ({successful/total_models*100:.1f}%)</p>
        </div>
        <div class="stat-box">
            <h3 class="failure">Failed</h3>
            <p>{failed} ({failed/total_models*100:.1f}%)</p>
        </div>
        <div class="stat-box">
            <h3 class="warning">Total Warnings</h3>
            <p>{total_warnings}</p>
        </div>
        <div class="stat-box">
            <h3 class="failure">Total Errors</h3>
            <p>{total_errors}</p>
        </div>
        <div class="stat-box">
            <h3>Avg Time</h3>
            <p>{avg_time:.2f}s</p>
        </div>
        <div class="stat-box">
            <h3>Total Time</h3>
            <p>{self._format_time_duration(total_time)}</p>
        </div>
        <div class="stat-box">
            <h3>Total File Size</h3>
            <p>{total_file_size:.2f} MB</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Asset</th>
                <th>Variant</th>
                <th>Success</th>
                <th><a href="#manual-annotation-instructions" style="color: inherit; text-decoration: none;">Verified (Manual)</a></th>
                <th>Errors</th>
                <th>Warnings</th>
                <th>Time (s)</th>
                <th>Total Size (MB)</th>
                <th>Notes</th>
                <th>Errors</th>
                <th>Warnings</th>
            </tr>
        </thead>
        <tbody>
"""

        # Sort results by asset name, then variant name
        sorted_results = sorted(self.results, key=lambda r: (r.asset_name, r.variant_name))

        previous_asset = None
        for result in sorted_results:
            success_class = "success-cell" if result.success else "failure-cell"
            verified_class = "success-cell" if result.verified == "Yes" else "" if result.verified == "Unknown" else "failure-cell"

            # Determine if this is the first variant of a new asset
            is_new_asset = result.asset_name != previous_asset
            row_class = "asset-group" if is_new_asset else "variant-row"

            # Only show asset name and link for first variant in each group
            if is_new_asset:
                link_style = "color: inherit; text-decoration: none;"
                asset_link = f'<a href="{result.menagerie_url}" target="_blank" style="{link_style}">{result.asset_name}</a>'
                asset_display = f"<strong>{asset_link}</strong>"
            else:
                asset_display = ""

            previous_asset = result.asset_name

            # Convert newlines and tabs to HTML for proper display
            error_message_html = result.error_message.replace("\n", "<br>")
            warnings_html = result.warnings.replace("\n", "<br>")

            html_content += f"""
            <tr class="{row_class}">
                <td>{asset_display}</td>
                <td>{result.variant_name}</td>
                <td class="{success_class}">{'Yes' if result.success else 'No'}</td>
                <td class="{verified_class}">{result.verified}</td>
                <td class="numeric">{result.error_count}</td>
                <td class="numeric">{result.warning_count}</td>
                <td class="numeric">{result.conversion_time_seconds:.2f}</td>
                <td class="numeric">{result.total_file_size_mb:.2f}</td>
                <td>{result.notes}</td>
                <td>{error_message_html}</td>
                <td>{warnings_html}</td>
            </tr>
"""

        html_content += """
        </tbody>
    </table>

    <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
        <h3 id="manual-annotation-instructions">Manual Annotation Instructions</h3>
        <p><strong>Verified:</strong> Each model variant can be individually annotated with "Yes", "No", or "Unknown"
        based on manual inspection of the converted USD files. Update the annotations in the
        <code>tools/menagerie_annotations.yaml</code> file under each variant's <code>verified</code> field.
        Consider factors like:</p>
        <ul>
            <li>Visual correctness when loaded in USD viewer</li>
            <li>Proper hierarchy and naming</li>
            <li>Material and texture fidelity</li>
            <li>Physics properties preservation</li>
            <li>Simulation correctness in MuJoCo Simulate compared to the original MJCF file</li>
        </ul>
        <p><strong>Notes:</strong> Document any known issues, limitations, or special considerations for each
        model variant in the <code>notes</code> field under each variant in the annotations file.</p>

        <h3>Annotation Structure</h3>
        <p>Annotations are now per-variant rather than per-asset. Each XML file listed under an asset's
        <code>xml_files</code> array has its own <code>verified</code>, <code>notes</code>,
        <code>evaluation_date</code>, <code>evaluator</code>, and <code>notes</code> fields.</p>

        <h3>File Size Information</h3>
        <p><strong>Total Size:</strong> Overall size of all files in the output directory, including USD files,
        textures, and any other generated assets.</p>
    </div>
</body>
</html>
"""

        with Path.open(html_path, "w", encoding="utf-8") as htmlfile:
            htmlfile.write(html_content)

        logger.info("HTML report generated: %s", html_path.absolute())
        return html_path

    def _generate_markdown_report(self) -> Path:
        """Generate Markdown report."""
        md_path = self.report_output_dir / "benchmarks.md"

        # Calculate statistics
        total_models = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_models - successful
        total_errors = sum(r.error_count for r in self.results)
        total_warnings = sum(r.warning_count for r in self.results)
        avg_time = sum(r.conversion_time_seconds for r in self.results) / total_models if total_models > 0 else 0
        total_time = sum(r.conversion_time_seconds for r in self.results)
        total_file_size = sum(r.total_file_size_mb for r in self.results)

        # Start building markdown content
        md_content = f"""# MuJoCo Menagerie Benchmark Report

**Generated on:** {time.strftime("%Y-%m-%d %H:%M:%S")}

**Repository:** [{self.MENAGERIE_REPO_URL}]({self.MENAGERIE_REPO_URL})

## Summary Statistics

| Total Models | Successful | Failed | Total Warnings | Total Errors | Average Time | Total Time | Total File Size |
|:------------:|:----------:|:------:|:--------------:|:------------:|:------------:|:----------:|:---------------:|
"""

        # Build summary data row (split to avoid long line)
        summary_row = (
            f"| {total_models} | {successful} ({successful/total_models*100:.1f}%) | "
            f"{failed} ({failed/total_models*100:.1f}%) | {total_warnings} | {total_errors} | "
            f"{avg_time:.2f}s | {self._format_time_duration(total_time)} | {total_file_size:.2f} MB |"
        )
        md_content += (
            summary_row
            + """

## Detailed Results

"""
        )

        # Add table header (split to avoid long line)
        table_header = (
            "| Asset | Variant | Success | [Verified (Manual)](#manual-annotation-instructions) | Errors | Warnings | "
            "Time (s) | Size (MB) | Notes | Error Messages | Warning Messages |\n"
        )
        table_separator = (
            "|-------|---------|---------|----------|-------:|--------:|"
            "---------:|---------:|----------------------|----------------|------------------|\n"
        )
        md_content += table_header + table_separator

        # Sort results by asset name, then variant name
        sorted_results = sorted(self.results, key=lambda r: (r.asset_name, r.variant_name))

        previous_asset = None
        for result in sorted_results:
            # Determine if this is the first variant of a new asset
            is_new_asset = result.asset_name != previous_asset

            # Only show asset name and link for first variant in each group
            asset_display = f"**[{result.asset_name}]({result.menagerie_url})**" if is_new_asset else ""
            previous_asset = result.asset_name

            # Success status with emoji
            success_display = "✅" if result.success else "❌"

            # Verified status with emoji
            if result.verified == "Yes":
                verified_display = "✅"
            elif result.verified == "Unknown":
                verified_display = "❓"
            else:
                verified_display = "❌"

            # Escape pipe characters and clean up text for markdown table
            def clean_for_table(text: str) -> str:
                if not text:
                    return ""
                # Replace pipes with escaped pipes, newlines with <br> for markdown, and clean carriage returns
                cleaned = text.replace("|", "\\|").replace("\n", "<br>").replace("\r", "")
                return cleaned

            error_messages = clean_for_table(result.error_message)
            warning_messages = clean_for_table(result.warnings)
            notes = clean_for_table(result.notes)

            # Build table row (split to avoid long line)
            row_parts = [
                asset_display,
                result.variant_name,
                success_display,
                verified_display,
                str(result.error_count),
                str(result.warning_count),
                f"{result.conversion_time_seconds:.2f}",
                f"{result.total_file_size_mb:.2f}",
                notes,
                error_messages,
                warning_messages,
            ]
            md_content += "| " + " | ".join(row_parts) + " |\n"

        # Add manual annotation instructions
        md_content += """

## Manual Annotation Instructions

### Verified Status
Each model variant can be individually annotated with "Yes", "No", or "Unknown" based on manual
inspection of the converted USD files. Update the annotations in the `tools/menagerie_annotations.yaml`
file under each variant's `verified` field.

**Consider these factors:**
- Visual correctness when loaded in USD viewer
- Proper hierarchy and naming
- Material and texture fidelity
- Physics properties preservation
- Simulation correctness in MuJoCo Simulate compared to the original MJCF file

### Notes
Document any known issues, limitations, or special considerations for each model variant in the
`notes` field under each variant in the annotations file.

### Annotation Structure
Annotations are per-variant rather than per-asset. Each XML file listed under an asset's
`xml_files` array has its own `verified`, `notes`, `evaluation_date`, `evaluator`, and `notes` fields.

### File Size Information
**Total Size:** Overall size of all files in the output directory, including USD files, textures,
and any other generated assets.

---

*Report generated by mujoco-usd-converter benchmark tool*
"""

        with Path.open(md_path, "w", encoding="utf-8") as mdfile:
            mdfile.write(md_content)

        logger.info("Markdown report generated: %s", md_path.absolute())
        return md_path

    def _generate_summary(self, save_to_file: bool = True):
        """Generate a summary of the benchmark results."""
        if not self.results:
            return

        total_models = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_models - successful
        total_errors = sum(r.error_count for r in self.results)
        total_warnings = sum(r.warning_count for r in self.results)
        total_time = sum(r.conversion_time_seconds for r in self.results)
        total_file_size = sum(r.total_file_size_mb for r in self.results)

        # Count unique assets
        unique_assets = len({r.asset_name for r in self.results})

        summary = f"""
=== MuJoCo Menagerie Benchmark Summary ===
Total Assets: {unique_assets}
Total Model Variants: {total_models}
Successful Conversions: {successful} ({successful/total_models*100:.1f}%)
Failed Conversions: {failed} ({failed/total_models*100:.1f}%)
Total Errors: {total_errors}
Total Warnings: {total_warnings}
Total Conversion Time: {self._format_time_duration(total_time)}
Average Time per Model: {self._format_time_duration(total_time/total_models)}

=== File Size Analysis ===
Total File Size: {total_file_size:.2f} MB
Average Size per Model: {total_file_size/total_models:.2f} MB"""

        failed_results = [result for result in self.results if not result.success]
        if failed_results:
            summary += "\n\n=== Failed Models ===\n"
            # Group failed results by asset for better readability
            failed_by_asset = {}
            for result in failed_results:
                if result.asset_name not in failed_by_asset:
                    failed_by_asset[result.asset_name] = []
                failed_by_asset[result.asset_name].append(result)

            for asset_name, variants in sorted(failed_by_asset.items()):
                summary += f"\n{asset_name}:\n"
                for result in variants:
                    summary += f"  - {result.variant_name}: {result.error_message}\n"

        logger.info(summary)

        if save_to_file:
            summary_path = self.report_output_dir / "benchmark_summary.txt"
            with Path.open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary)
            logger.info("Summary saved to: %s", summary_path.absolute())

    def cleanup(self):
        """Clean up temporary resources."""
        if self.temp_menagerie and self.menagerie_path:
            try:
                shutil.rmtree(self.menagerie_path.parent)
                logger.info("Cleaned up temporary Menagerie directory")
            except Exception as e:
                logger.warning("Failed to clean up temporary directory: %s", e)


def main():
    """Main entry point for the benchmark script."""
    parser = argparse.ArgumentParser(
        description="Benchmark mujoco-usd-converter against MuJoCo Menagerie models", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--menagerie-path", type=str, help="Path to existing MuJoCo Menagerie repository (will clone if not provided)")
    parser.add_argument("--conversion-output-dir", type=str, default="benchmarks/usd_menagerie", help="Directory to store converted USD assets")
    parser.add_argument("--report-output-dir", type=str, default="benchmarks", help="Directory to store benchmark reports")
    parser.add_argument("--report-format", choices=["csv", "html", "md", "all"], default="all", help="Format for the benchmark report")
    parser.add_argument(
        "--annotation-file",
        type=str,
        default="tools/menagerie_annotations.yaml",
        help="Path to a YAML file containing manual annotations for models.",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create benchmark instance
    benchmark = MenagerieBenchmark(
        menagerie_path=args.menagerie_path,
        report_output_dir=args.report_output_dir,
        conversion_output_dir=args.conversion_output_dir,
        annotation_file=args.annotation_file,
    )

    try:
        # Run benchmark
        results = benchmark.run_benchmark()

        if not results:
            logger.error("No results generated")
            return 1

        # Generate reports
        reports = benchmark.generate_report(args.report_format)

        logger.info("Benchmark completed successfully!")
        logger.info("USD Assets saved to: %s", Path(args.conversion_output_dir).absolute())
        logger.info("Reports saved to: %s", Path(args.report_output_dir).absolute())

        for format_type, path in reports.items():
            logger.info("%s report: %s", format_type.upper(), path.absolute())

        return 0

    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
        return 1
    except Exception as e:
        logger.error("Benchmark failed: %s", e)
        raise Exception(e)
    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    sys.exit(main())
