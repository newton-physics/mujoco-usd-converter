@echo off

set "SCRIPT_DIR=%~dp0"
set "BUILD_VENV=%SCRIPT_DIR%.build_venv"
set "RUNTIME_VENV=%SCRIPT_DIR%.runtime_venv"

if "%1"=="-cc" (
    echo Cleaning everything...
    rd /s /q "%BUILD_VENV%"
    rd /s /q "%RUNTIME_VENV%"
    rd /s /q dist
) else if "%1"=="-c" (
    echo Cleaning distro and runtime...
    rd /s /q "%RUNTIME_VENV%"
    rd /s /q dist
)

REM setup the build environment
if exist "%BUILD_VENV%\" (
    call %BUILD_VENV%\Scripts\activate.bat
) else (
    echo "Building: %BUILD_VENV%"
    python -m venv "%BUILD_VENV%"
    call %BUILD_VENV%\Scripts\activate.bat
    python -m pip install poetry
)

REM do the build
poetry --version
if exist "%SCRIPT_DIR%dist\" (
    rd /s /q "%SCRIPT_DIR%dist"
)
poetry build --format=wheel
poetry lock

REM prepare the runtime environment
if not exist "%RUNTIME_VENV%\" (
    echo Building: %RUNTIME_VENV%
    python -m venv "%RUNTIME_VENV%"
)
call %RUNTIME_VENV%\Scripts\activate.bat

REM install the artifact to the runtime
poetry install
