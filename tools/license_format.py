# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0
import argparse
import logging
import pathlib
import re
import sys
from datetime import datetime

__copyright = "# SPDX-FileCopyrightText: Copyright (c) {years} The Newton Developers"
__identifier = "# SPDX-License-Identifier: Apache-2.0"
# Escape special regex characters in the copyright template
__copyright_template = re.escape(__copyright).replace(re.escape("{years}"), "{years}")
__copyright_years = __copyright_template.replace("{years}", f"(?:2025|(?:20[0-9][0-4])-{datetime.now().year})")
__copyright_regex = re.compile(f"^{__copyright_years}$")


def __check(files: list) -> tuple[list, list]:
    passed = []
    failed = []
    for path in files:
        with pathlib.Path.open(path) as f:
            copyright = f.readline().strip()
            identifier = f.readline().strip()
        if not re.match(__copyright_regex, copyright) or identifier != __identifier:
            failed.append(path)
        else:
            passed.append(path)
    return (passed, failed)


def __fix(files: list) -> bool:
    current_year = datetime.now().year
    _, failed = __check(files)
    for path in failed:
        with pathlib.Path.open(path) as f:
            content = f.readlines()

        # Find first non-comment line
        first_code_line = 0
        for i, line in enumerate(content):
            if not line.strip().startswith("#"):
                first_code_line = i
                break

        # Extract year from first comment line if it exists
        start_year = current_year
        if first_code_line > 0:
            first_comment = content[0].strip()
            if "Copyright (c)" in first_comment:
                year_part = first_comment.split("Copyright (c)")[1].split()[0]
                year = year_part.split("-")[0] if "-" in year_part else year_part
                try:
                    year = int(year)
                    if year < current_year:
                        start_year = year
                except ValueError:
                    pass

        # Write file with correct headers
        with pathlib.Path.open(path, "w") as f:
            if start_year == current_year:
                f.write(__copyright.replace("{years}", str(current_year)) + "\n")
            else:
                f.write(__copyright.replace("{years}", f"{start_year}-{current_year}") + "\n")
            f.write(__identifier + "\n")
            f.writelines(content[first_code_line:])

    return True


class __ColoredFormatter(logging.Formatter):
    RED = "\033[31m"
    RESET = "\033[0m"

    def format(self, record):
        if record.levelno >= logging.ERROR:
            record.msg = f"{self.RED}{record.msg}{self.RESET}"
        return super().format(record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="License Check")
    parser.description = "Tool to generate lint and format license header comments in source files"
    parser.add_argument(
        "--include",
        dest="include_pattern",
        type=str,
        default="**/*.py",
        help="Glob pattern of paths to check",
    )
    parser.add_argument(
        "--exclude",
        dest="exclude_pattern",
        type=str,
        default=".venv",
        help="Glob pattern of paths to skip",
    )
    parser.add_argument(
        "--check",
        dest="check",
        action="store_true",
        help="Perform a linter check only. If specified, --fix will be ignored.",
    )
    parser.add_argument(
        "--fix",
        dest="fix",
        action="store_true",
        help="Perform a linter check & then fix the issues",
    )

    args = parser.parse_args()

    # Setup colored logging
    handler = logging.StreamHandler()
    handler.setFormatter(__ColoredFormatter("[%(levelname)s] %(name)s: %(message)s"))
    logger = logging.getLogger(parser.prog)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    files = [x for x in pathlib.Path().glob(args.include_pattern) if not str(x).startswith(args.exclude_pattern)]
    logger.info("Checking licenses in %d files.", len(files))
    if args.check:
        passed, failed = __check(files)
        if len(failed):
            logger.error("%d/%d files need to be fixed.", len(failed), len(passed) + len(failed))
            result = False
        else:
            logger.info("All %d files passed!", len(passed))
            result = True
    elif args.fix:
        if result := __fix(files):
            logger.info("All licenses fixed")
        else:
            logger.error("Some licenses could not be fixed")
    else:
        logger.warning("Either --check or --fix must be specified")
        result = False

    sys.exit(0 if result else 1)
