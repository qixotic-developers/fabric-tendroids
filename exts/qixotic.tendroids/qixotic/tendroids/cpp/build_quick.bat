@echo off
REM Quick build script for C++ extension
REM Run from the cpp/ directory

echo ========================================
echo Building fast_mesh_updater C++ extension
echo ========================================
echo.

cd /d "%~dp0"

if not exist "_build" (
    echo Creating build directory...
    mkdir _build
)

cd _build

echo.
echo Configuring with CMake...
cmake .. -G "Visual Studio 17 2022" -A x64

if errorlevel 1 (
    echo.
    echo ERROR: CMake configuration failed!
    pause
    exit /b 1
)

echo.
echo Building Release...
cmake --build . --config Release

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Installing (copying to Python directory)...
cmake --install .

if errorlevel 1 (
    echo.
    echo WARNING: Install failed (this is often OK)
)

cd ..

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo The .pyd file should be in:
echo   qixotic\tendroids\
echo.
echo Now restart USD Composer and run the C++ Batch 15 test!
echo.
pause
