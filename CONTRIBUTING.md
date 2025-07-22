# Contributing to mujoco-usd-converter

If you are interested in contributing to mujoco-usd-converter, your contributions will fall
into three categories:
1. You want to report a bug, feature request, or documentation issue
2. You want to implement a feature or bug-fix for an outstanding issue
3. You want to propose a new Feature and implement it

In all cases, first search the existing [GitHub Issues](https://github.com/newton-physics/mujoco-usd-converter/issues) to see if anyone has reported something similar.

If not, create a new [GitHub Issue](https://github.com/newton-physics/mujoco-usd-converter/issues/new/choose) describing what you encountered or what you want to see changed. If you have feedback that is best explained in code, feel free to fork the repository on GitHub, create a branch demonstrating your intent, and either link it to the GitHub Issue or open a Pull Request back upstream. See [Code Contributions](#code-contributions) for more details.

Whether adding details to an existing issue or creating a new one, please let us know what companies are impacted.

## Code contributions

If you want to implement a feature, or change the logic of existing features, you are welcome to modify the code on a personal clone/mirror/fork. See [Building](#building) for more details.

If you want to contribute your changes back upstream, please first start a GitHub Issue as described above.

If you intend to submit a Pull Request:
- First, ensure alignment with the Code Owners on the associated Issue, to avoid redundant work or wasted iterations.
- Develop your changes on a well named [development branch](#development-branches) within your personal clone/mirror/fork.
- Run all test suites locally & ensure passing results in your dev environment.
- Ensure all commits have a sign-off (see [Developer Certificate of Origin](#developer-certificate-of-origin))

Please note that in some cases, we may not merge GitHub Pull Requests directly. We will take suggestions under advisement and discuss internally. We may rebase your commits to provide alignment with internal development branches.

### Developer Certificate of Origin

Rather than requiring a formal Contributor License Agreement (CLA), we use the [Developer Certificate of Origin](https://developercertificate.org/) to ensure contributors have the right to submit their contributions to this project.

Please ensure that all commits have a [sign-off](https://git-scm.com/docs/git-commit#Documentation/git-commit.txt-code--signoffcode) added with an email address that matches the commit author to agree to the DCO terms for each particular contribution.

```text
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

### Branches and Versions

The default branch is named `main` and it is a protected branch. Our internal CI Pipeline automatically builds & tests all changes from this branch on both Windows and Linux. However, all new features target the `main` branch, and we may merge code changes to this branch at any time; it is not guaranteed to be stable/usable and may break API/ABI regularly.

We advise to use an official published wheel of the mujoco-usd-converter, or source from the GitHub tag associated with it, to ensure stability.

### Development Branches

For all development, changes are pushed into a branch in personal development forks, and code is submitted upstream for code review and CI verification before being merged into `main` or the target release branch.

We do not enforce any particular naming convention for development branches, other than avoiding the reserved branch patterns `main` and `production/*`. We recommend using legible branch names that imply the feature or fix being developed.

All code changes must contain either new unittests, or updates to existing tests, and we won't merge any code changes that have failing CI pipelines or sub-standard code coverage.

## Developing

This project uses [uv](https://docs.astral.sh/uv/) as the primary dev tool and [poethepoet](https://github.com/nat-n/poethepoet) for command automation.

### Quick Start

If you have `uv` installed already, you can use it directly:

```bash
# Run linting
uv run --group dev poe lint

# Run tests
uv run --group dev poe test

# Run the CLI
uv run mujoco_usd_converter --help

# Build the project
uv build
```

### Local Development Setup

If you prefer a traditional workflow with a persistent virtual environment, use the build scripts:

- **Linux/macOS**: `./build.sh`
- **Windows**: `.\build.bat`

> **Note**: The build scripts are designed for local development. The CI/CD pipeline uses the streamlined `uv run` approach directly.

### Installation Requirements

To use the build scripts locally, you need uv installed:

**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Common Commands

#### Direct uv Commands (Recommended)
- Update dependencies: Edit `pyproject.toml` and then run `uv lock`
- Build the sdist and wheel: `uv build`
- Build just the wheel: `uv build --wheel`
- Run linting: `uv run --group dev poe lint`
- Run tests: `uv run --group dev poe test`
- Run auto-formatters: `uv run --group dev poe format`
- Run the CLI: `uv run mujoco_usd_converter <args>`

#### Traditional Workflow (via build scripts)
- Build and setup environment: `./build.sh` or `.\build.bat`
- Activate the venv:
    - Linux: `source .venv/bin/activate`
    - Windows: `call .venv\Scripts\activate.bat`
- Run commands in activated environment: `poe lint`, `poe test`, etc.

## Testing

Tests can be run in several ways:

```bash
# Direct execution (recommended)
uv run --group dev poe test

# In activated venv (after running build script)
poe test

# Individual test discovery
uv run --group dev python -m unittest discover -v -s ./tests
```

The converter CLI can be tested:

```bash
# Direct execution
uv run mujoco_usd_converter --help

# In activated venv
mujoco_usd_converter --help
```

## Changing OpenUSD or MuJoCo Runtimes

By default the mujoco-usd-converter uses OpenUSD v25.05 & OpenUSD Exchange compiled for this same flavor. OpenUSD Exchange SDK can be compiled for many flavors of OpenUSD and Python. You can switch to a different flavor of OpenUSD by changing the `usd-exchange` version metadata within the the pyproject.toml or sdist.

The converter also uses MuJoCo 3.3.5, which contains the newest MjcPhysics schemas & newest features required for USD interop in MuJoCo. You may update the pyproject.toml or sdist to a newer version of MuJoCo as needed, but you cannot use an older version.

### Requesting new Build Flavors

If none of the existing USD flavors meet the requirements of your runtime, you have two options:
1. Build [OpenUSD Exchange SDK](https://github.com/NVIDIA-Omniverse/usd-exchange) from source as and when you need to & manage the build artifacts yourself
2. Submit an Feature Request to add a new flavor to our matrix
