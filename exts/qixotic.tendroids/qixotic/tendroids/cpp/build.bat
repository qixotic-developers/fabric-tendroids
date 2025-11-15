@echo off
REM Quick build script for FastMeshUpdater C++ extension
REM Builds AND copies .pyd to the correct location

echo ========================================
echo Building FastMeshUpdater C++ Extension
echo ========================================
echo.

cd /d "%~dp0"

REM Clean old build if requested
if "%1"=="clean" (
    echo Cleaning build directories...
    if exist build-vs2022 rmdir /s /q build-vs2022
    if exist cmake-build-release rmdir /s /q cmake-build-release
    if exist build rmdir /s /q build
    echo Clean complete.
    echo.
)

REM Determine which build directory exists or should be created
set BUILD_DIR=
if exist cmake-build-release (
    set BUILD_DIR=cmake-build-release
    echo Using existing CMake build directory: cmake-build-release
) else if exist build-vs2022 (
    set BUILD_DIR=build-vs2022
    echo Using existing build directory: build-vs2022
) else (
    set BUILD_DIR=cmake-build-release
    echo Creating new build directory: cmake-build-release
    mkdir cmake-build-release
)

echo.
echo Configuring with CMake...
cd %BUILD_DIR%
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
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

REM Find the .pyd file (could be in Release subdir or root)
set PYD_SOURCE=
if exist "Release\fast_mesh_updater.pyd" (
    set PYD_SOURCE=Release\fast_mesh_updater.pyd
) else if exist "fast_mesh_updater.pyd" (
    set PYD_SOURCE=fast_mesh_updater.pyd
)

if "%PYD_SOURCE%"=="" (
    echo.
    echo [WARNING] Could not find fast_mesh_updater.pyd in build directory!
    echo Check build output above for errors.
    pause
    exit /b 1
)

REM Copy to extension directory
set DEST_DIR=..\..
echo.
echo Copying %PYD_SOURCE% to %DEST_DIR%\fast_mesh_updater.pyd
copy /Y "%PYD_SOURCE%" "%DEST_DIR%\fast_mesh_updater.pyd"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to copy .pyd file!
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Output: %DEST_DIR%\fast_mesh_updater.pyd
echo.
echo The .pyd file has been copied to the extension directory.
echo.
echo IMPORTANT: If Omniverse is running, RESTART IT now!
echo Python caches modules and won't pick up the new version.
echo.

if "%1"=="test" (
    echo Running tests...
    cd ..\..
    python test_phase1.py
)

if not "%1"=="test" pause
