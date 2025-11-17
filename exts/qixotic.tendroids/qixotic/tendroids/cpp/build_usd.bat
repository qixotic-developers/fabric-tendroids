@echo off
REM FastMeshUpdater C++ Build Script - Phase 2C (USD Integration)
REM
REM Builds the C++ extension with full USD integration for 240x speedup

echo ===============================================================================
echo FastMeshUpdater C++ Build - Phase 2C (USD Integration)
echo ===============================================================================

cd /d "%~dp0"

REM Clean previous build
if exist "build-omniverse" (
    echo Cleaning previous build...
    rmdir /s /q "build-omniverse"
)

REM Create build directory
mkdir "build-omniverse"
cd "build-omniverse"

REM Configure with CMake
echo.
echo Configuring with CMake...
cmake .. ^
    -G "Visual Studio 17 2022" ^
    -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DUSD_ROOT=C:/dev/omniverse-old/omnikitsdk-108.1.0

if %errorlevel% neq 0 (
    echo ERROR: CMake configuration failed!
    pause
    exit /b 1
)

REM Build
echo.
echo Building Release configuration...
cmake --build . --config Release

if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Copy output
echo.
echo Copying fast_mesh_updater.pyd...
copy Release\fast_mesh_updater.pyd ..\..\ /Y

if %errorlevel% neq 0 (
    echo ERROR: Failed to copy .pyd file!
    pause
    exit /b 1
)

echo.
echo ===============================================================================
echo Build SUCCESS!
echo ===============================================================================
echo Output: fast_mesh_updater.pyd (with USD integration)
echo Version: 0.3.0-usd-integration
echo Mode: Full C++ (computation + USD)
echo.
echo Next step: Test in Omniverse Composer
echo ===============================================================================

pause
