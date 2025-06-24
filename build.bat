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

REM Ensure uv is available (for local development)
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: uv is not installed. Please install uv first:
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    exit /b 1
)

REM Install dependencies and build
echo Installing dependencies with uv...
uv sync --group dev

echo Using uv version:
uv --version
if exist "dist" (
    rd /s /q "dist"
)
echo Building wheel...
uv build --wheel
