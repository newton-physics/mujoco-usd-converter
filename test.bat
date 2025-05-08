@echo off

REM Determine the script's directory
set "SCRIPT_DIR=%~dp0"
set RUNTIME_VENV="%SCRIPT_DIR%\.runtime_venv"
cd /d "%RUNTIME_VENV%"
call Scripts\activate.bat

REM Run the tests
python -m unittest discover -v -s "%SCRIPT_DIR%\tests"
