# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Update Markdown links for PyPI

This script updates markdown files for PyPI by:
- Replacing local repository links with the github URL, eg.
  - [Contributing Guide](./CONTRIBUTING.md)
  - [License](/LICENSE.md)
  - [Examples](./examples/basic.py)
"""

import argparse
import logging
import pathlib
import re
import sys

__github_url = "https://github.com/newton-physics/mujoco-usd-converter"


def update_markdown_for_pypi(markdown_path: str) -> bool:
    """Update markdown file by replacing local links with GitHub URLs."""
    try:
        markdown_file = pathlib.Path(markdown_path)
        if not markdown_file.exists():
            logging.error("Markdown file not found: %s", markdown_path)
            return False

        with markdown_file.open("r", encoding="utf-8") as f:
            content = f.read()

        # Replace local "./" links with GitHub URL
        # Pattern to match markdown links like [text](./path) or [text](path)
        def replace_local_link(match):
            text = match.group(1)
            path = match.group(2)
            # Remove leading "./" if present
            clean_path = path.lstrip("./")
            return f"[{text}]({__github_url}/blob/main/{clean_path})"

        # Replace links that start with ./ or are relative paths in the repo
        updated_content = re.sub(r"\[([^\]]+)\]\(\.?/([^)]+)\)", replace_local_link, content)

        if content != updated_content:
            with markdown_file.open("w", encoding="utf-8") as f:
                f.write(updated_content)
            logging.info("Updated markdown file: %s", markdown_path)
            return True
        else:
            logging.info("No changes needed for: %s", markdown_path)
            return True

    except Exception as e:
        logging.error("Error updating markdown file %s: %s", markdown_path, e)
        return False


class __ColoredFormatter(logging.Formatter):
    RED = "\033[31m"
    RESET = "\033[0m"

    def format(self, record):
        if record.levelno >= logging.ERROR:
            record.msg = f"{self.RED}{record.msg}{self.RESET}"
        return super().format(record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Markdown Update")
    parser.description = "Tool to update markdown files for PyPI"
    parser.add_argument(
        "markdown_path",
        type=str,
        help="Path to the markdown file to update",
    )

    args = parser.parse_args()

    # Setup colored logging
    handler = logging.StreamHandler()
    handler.setFormatter(__ColoredFormatter("[%(levelname)s] %(name)s: %(message)s"))
    logger = logging.getLogger(parser.prog)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # Update the markdown file
    result = update_markdown_for_pypi(args.markdown_path)

    sys.exit(0 if result else 1)
