@echo off
echo ========================================
echo Particle System Performance Comparison
echo ========================================
echo.

REM Set Omniverse paths
set USD_COMPOSER="C:\Users\qixio\AppData\Local\ov\pkg\prod-usd_composer-2024.1.1\USD Composer.bat"

REM Test Warp GPU particles
echo Testing Warp GPU particles...
%USD_COMPOSER% --enable qixotic.tendroids --exec "test_particle_comparison.py"

echo.
echo Test complete. Check logs for results.
pause
