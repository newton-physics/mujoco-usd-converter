# Contributing

## Development

This project uses [uv](https://docs.astral.sh/uv/) as the primary dev tool and [poethepoet](https://github.com/nat-n/poethepoet) for command automation.

### Quick Start

If you have `uv` installed already, you can use it directly:

```bash
# Run linting
uv run --group dev poe lint

# Run tests
uv run --group dev poe test

# Run the CLI
uv run mjc_usd_converter --help

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

## Common Commands

### Direct uv Commands (Recommended)
- Update dependencies: Edit `pyproject.toml` and then `uv lock`
- Build the sdist and wheel: `uv build`
- Build just the wheel: `uv build --wheel`
- Run linting: `uv run --group dev poe lint`
- Run tests: `uv run --group dev poe test`
- Run auto-formatters: `uv run --group dev poe format`
- Run the CLI: `uv run mjc_usd_converter <args>`

### Traditional Workflow (via build scripts)
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
uv run mjc_usd_converter --help

# In activated venv
mjc_usd_converter --help
```

## CI/CD Notes

The CI/CD pipeline uses the modern `uv run` approach for maximum efficiency:
- No manual venv management
- Automatic dependency resolution and installation
- Single-command execution for each task

This approach is faster and more reliable than traditional multi-step processes.
