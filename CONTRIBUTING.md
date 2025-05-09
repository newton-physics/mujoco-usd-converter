# Contributing

## Development

This project uses [poetry](https://python-poetry.org) as the primary dev tool and [poethepoet](https://github.com/nat-n/poethepoet) for command automation.

If you have `poetry` installed already, you can use it directly.

If you would like to bootstrap `poetry` within a local virtual environment, use `build.sh` or `build.bat` to install poetry and run the full build process.

> Note: The `build.sh|bat` scripts also run several poetry commands (build, lock, install).

The most common commands are as follows:
- Update dependencies: Edit `pyproject.toml` and then `poetry lock`
- Build the sdist and wheel: `poetry build`
- Build just the wheel: `poetry build --format=wheel`
- Install to the venv: `poetry install`
- Activate the venv:
    - Linux: `source .venv/bin/activate`
    - Windows: `call .venv\Scripts\activate.bat`

Once the venv is active, the following commands can be run manually or in CI processes:
- Run the test suite: `poe test`
- Run the Linters: `poe lint`
- Run auto-formatters: `poe format`

## Testing

As noted above the tests can be run via `poe test` within the venv.

The converter CLI can also be manually tested within the venv by running `mjc_usd_converter` or from outside the venv via `poetry run mjc_usd_converter`.
