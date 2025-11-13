@echo off
REM Quick build script for FastMeshUpdater C++ extension
REM Run from cpp/ directory

echo ============================================================
echo FastMeshUpdater Phase 1 Build Script
echo ============================================================
echo.

REM Check if we're in the right directory
if not exist CMakeLists.txt (
    echo ERROR: CMakeLists.txt not found
    echo Please run this script from the cpp/ directory
    pause
    exit /b 1
)

echo Creating build directory...
if not exist _build mkdir _build
cd _build

echo.
echo Configuring CMake...
cmake .. -G "Visual Studio 17 2022" -A x64
if errorlevel 1 (
    echo.
    echo ERROR: CMake configuration failed
    echo.
    echo Common fixes:
    echo   1. Install pybind11: pip install pybind11
    echo   2. Verify Visual Studio 2022 is installed
    echo   3. Check KIT_SDK_PATH in CMakeLists.txt
    echo.
    pause
    exit /b 1
)

echo.
echo Building Release configuration...
cmake --build . --config Release
if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    echo Check the error messages above
    echo.
    pause
    exit /b 1
)

cd ..

echo.
echo ============================================================
echo Build successful!
echo ============================================================
echo.
echo Output: cpp\_build\Release\fast_mesh_updater.pyd
echo.
echo Next step: Run tests
echo   python ..\test_phase1.py
echo.
pause
