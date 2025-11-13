@echo off
REM Simple build script using CLion's embedded CMake
REM Run from cpp/ directory

echo Building C++ extension...

cd /d "%~dp0"

REM Clean old build
if exist "_build" rmdir /S /Q _build
mkdir _build
cd _build

REM Use CLion's cmake (usually in PATH if CLion is installed)
REM Or use system cmake with NMake
cmake .. -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 goto error

cmake --build . --config Release
if errorlevel 1 goto error

REM Copy to Python directory
copy /Y fast_mesh_updater.pyd ..\..\
if errorlevel 1 (
    echo Warning: Could not copy .pyd file
    echo You may need to copy it manually from _build\
)

cd ..
echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo .pyd location: qixotic\tendroids\fast_mesh_updater.pyd
echo.
echo Now restart USD Composer and test!
echo.
goto end

:error
echo.
echo ========================================
echo Build FAILED!
echo ========================================
echo.
echo Try building in CLion instead:
echo 1. Open CLion
echo 2. File -^> Open -^> cpp/
echo 3. Build -^> Build Project
echo.

:end
pause
