@echo off
REM Test runner with proper PATH setup for DLL loading

echo ======================================================================
echo FastMeshUpdater Phase 1 Tests - Hello World
echo ======================================================================
echo.

REM Add Python directory to PATH
set PYTHON_DIR=C:\Users\qixot\AppData\Local\Programs\Python\Python313
set PATH=%PYTHON_DIR%;%PATH%

echo Python directory added to PATH: %PYTHON_DIR%
echo.

REM Change to test directory
cd /d C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids\qixotic\tendroids

REM Run test
python test_phase1.py

pause
