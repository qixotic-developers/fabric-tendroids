@echo off
REM FastMeshUpdater Cleanup - Remove Duplicate .pyd Files
REM =====================================================
REM
REM This script deletes duplicate fast_mesh_updater.pyd files from build directories
REM Keeps ONLY the copy in: qixotic\tendroids\fast_mesh_updater.pyd

echo ======================================================================
echo FastMeshUpdater Cleanup - Remove Duplicate .pyd Files
echo ======================================================================
echo.
echo This will DELETE duplicate .pyd files in build directories:
echo   - cpp\build-omniverse\Release\fast_mesh_updater.pyd
echo   - cpp\build-vs2022\Release\fast_mesh_updater.pyd
echo   - cpp\cmake-build-release\fast_mesh_updater.pyd
echo.
echo Keeping ONLY:
echo   - qixotic\tendroids\fast_mesh_updater.pyd
echo.
echo This fixes the "PerfStats already registered" error
echo.
pause

cd /d C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids

echo.
echo Checking for duplicate files...
echo.

REM Delete build-omniverse copy
if exist "qixotic\tendroids\cpp\build-omniverse\Release\fast_mesh_updater.pyd" (
    echo Deleting: cpp\build-omniverse\Release\fast_mesh_updater.pyd
    del /F "qixotic\tendroids\cpp\build-omniverse\Release\fast_mesh_updater.pyd"
    if errorlevel 1 (
        echo   [FAILED] Could not delete file
    ) else (
        echo   [OK] Deleted
    )
) else (
    echo [SKIP] cpp\build-omniverse\Release\fast_mesh_updater.pyd - not found
)

echo.

REM Delete build-vs2022 copy
if exist "qixotic\tendroids\cpp\build-vs2022\Release\fast_mesh_updater.pyd" (
    echo Deleting: cpp\build-vs2022\Release\fast_mesh_updater.pyd
    del /F "qixotic\tendroids\cpp\build-vs2022\Release\fast_mesh_updater.pyd"
    if errorlevel 1 (
        echo   [FAILED] Could not delete file
    ) else (
        echo   [OK] Deleted
    )
) else (
    echo [SKIP] cpp\build-vs2022\Release\fast_mesh_updater.pyd - not found
)

echo.

REM Delete cmake-build-release copy
if exist "qixotic\tendroids\cpp\cmake-build-release\fast_mesh_updater.pyd" (
    echo Deleting: cpp\cmake-build-release\fast_mesh_updater.pyd
    del /F "qixotic\tendroids\cpp\cmake-build-release\fast_mesh_updater.pyd"
    if errorlevel 1 (
        echo   [FAILED] Could not delete file
    ) else (
        echo   [OK] Deleted
    )
) else (
    echo [SKIP] cpp\cmake-build-release\fast_mesh_updater.pyd - not found
)

echo.
echo ======================================================================
echo Verifying main .pyd file exists...
echo ======================================================================

if exist "qixotic\tendroids\fast_mesh_updater.pyd" (
    echo [OK] Main file exists: qixotic\tendroids\fast_mesh_updater.pyd
) else (
    echo [ERROR] Main file NOT found: qixotic\tendroids\fast_mesh_updater.pyd
    echo.
    echo You need to copy the .pyd file from a build directory first!
    echo Example: copy cpp\build-vs2022\Release\fast_mesh_updater.pyd qixotic\tendroids\
    goto :end
)

echo.
echo ======================================================================
echo Cleanup Complete!
echo ======================================================================
echo.
echo Next steps:
echo   1. RESTART Omniverse Composer (important!)
echo   2. Load your Tendroids extension
echo   3. Check console - should NOT see "PerfStats already registered" error
echo   4. Should see: [TendroidBuilder] FastMeshUpdater loaded successfully
echo   5. Run stress test again for accurate performance data
echo.

:end
pause
