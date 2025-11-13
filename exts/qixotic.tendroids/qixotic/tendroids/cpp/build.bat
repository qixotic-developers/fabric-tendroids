@echo off
REM Quick build script for FastMeshUpdater C++ extension
REM Works from any directory

echo ========================================
echo Building FastMeshUpdater C++ Extension
echo ========================================
echo.

cd /d "%~dp0"

REM Clean old build if requested
if "%1"=="clean" (
    echo Cleaning build directories...
    if exist build-vs2022 rmdir /s /q build-vs2022
    if exist build rmdir /s /q build
    echo Clean complete.
    echo.
)

REM Create build directory
if not exist build-vs2022 mkdir build-vs2022

echo Configuring with CMake...
cd build-vs2022
cmake .. -G "Visual Studio 17 2022" -A x64
if errorlevel 1 (
    echo.
    echo [ERROR] CMake configuration failed!
    echo.
    pause
    exit /b 1
)

echo.
echo Building Release configuration...
cmake --build . --config Release
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Output: build-vs2022\Release\fast_mesh_updater.pyd
echo.
echo To test, run:
echo   cd ..
echo   python test_phase1.py
echo.

if "%1"=="test" (
    echo Running tests...
    cd ..
    python test_phase1.py
)

if not "%1"=="test" pause
