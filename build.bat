@echo off

set VENV="%~dp0.venv"

if "%1"=="-c" (
    echo Cleaning...
    if exist "%VENV%" (
        rd /s /q "%VENV%"
    )
    if exist dist (
        rd /s /q dist
    )
)

REM setup the build environment
if exist "%VENV%\" (
    call %VENV%\Scripts\activate.bat
) else (
    echo "Building: %VENV%"
    python -m venv "%VENV%"
    call %VENV%\Scripts\activate.bat
    python -m pip install poetry
)

REM do the build
poetry --version
if exist "dist" (
    rd /s /q "dist"
)
poetry build --format=wheel
poetry lock
poetry install
