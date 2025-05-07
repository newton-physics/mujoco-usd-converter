@echo off

set "SCRIPT_DIR=%~dp0"
set "RUNTIME_VENV=%SCRIPT_DIR%.runtime_venv"

if exist "%RUNTIME_VENV%\" (
    call %RUNTIME_VENV%\Scripts\activate.bat
) else (
    call %SCRIPT_DIR%\build.bat
)

mjc_usd_converter
