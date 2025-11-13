@echo off
REM Build fast_mesh_updater using Omniverse's Python 3.12
REM This ensures DLL compatibility with USD Composer

echo ========================================
echo Building FastMeshUpdater for Omniverse
echo ========================================
echo.

REM Omniverse Python location (from diagnostic output)
set "OMNI_PYTHON=C:\Dev\Omniverse-old\OmniKitSDK-108.1.0\python\python.exe"

if not exist "%OMNI_PYTHON%" (
    echo ERROR: Omniverse Python not found at:
    echo   %OMNI_PYTHON%
    echo.
    echo Please check the path in this script
    pause
    exit /b 1
)

echo Found Omniverse Python: %OMNI_PYTHON%
echo.

REM Check Python version
echo Checking Python version...
"%OMNI_PYTHON%" --version
echo.

REM Check/Install pybind11 in Omniverse's Python
echo Checking for pybind11...
"%OMNI_PYTHON%" -m pip show pybind11 >nul 2>&1
if errorlevel 1 (
    echo Installing pybind11...
    "%OMNI_PYTHON%" -m pip install pybind11
    echo.
)

REM Clean previous build
if exist "build-omniverse" (
    echo Cleaning previous build...
    rmdir /s /q build-omniverse
)

REM Create build directory
mkdir build-omniverse
cd build-omniverse

echo.
echo ========================================
echo Running CMake...
echo ========================================

REM Configure with Omniverse Python 3.12
cmake .. ^
    -G "Visual Studio 17 2022" ^
    -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DPython3_EXECUTABLE="%OMNI_PYTHON%"

if errorlevel 1 (
    echo.
    echo ERROR: CMake configuration failed
    cd ..
    pause
    exit /b 1
)

echo.
echo ========================================
echo Building Release...
echo ========================================

cmake --build . --config Release

if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    cd ..
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Output: build-omniverse\Release\fast_mesh_updater.pyd
echo.

REM Copy to the location where TendroidBuilder looks for it
echo Copying to build-vs2022\Release (where code expects it)...
if not exist "..\build-vs2022\Release" mkdir "..\build-vs2022\Release"
copy /Y Release\fast_mesh_updater.pyd ..\build-vs2022\Release\
if errorlevel 1 (
    echo WARNING: Could not copy to build-vs2022\Release
) else (
    echo ✓ Copied successfully!
)

cd ..

echo.
echo ========================================
echo ✓ FastMeshUpdater built successfully!
echo ========================================
echo Built against: Omniverse Python 3.12.11
echo Location: cpp\build-vs2022\Release\fast_mesh_updater.pyd
echo.
echo Next steps:
echo   1. Close USD Composer (if open)
echo   2. Restart USD Composer
echo   3. Run your test again
echo.
pause
