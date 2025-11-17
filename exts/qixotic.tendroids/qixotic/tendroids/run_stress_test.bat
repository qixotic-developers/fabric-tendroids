@echo off
REM Phase 2 Stress Test Runner
REM Tests performance with 15, 20, 25, 30 Tendroids

echo ======================================================================
echo Tendroids Phase 2 - Performance Stress Test
echo ======================================================================
echo.
echo This will test performance at 15, 20, 25, and 30 Tendroids
echo Each test runs for 10 seconds
echo Total test time: approximately 50 seconds
echo.
echo Results will be saved to stress_test_results/ directory
echo.
pause

REM Add Python directory to PATH if needed
set PYTHON_DIR=C:\Users\qixot\AppData\Local\Programs\Python\Python313
set PATH=%PYTHON_DIR%;%PATH%

REM Change to extension directory
cd /d C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids\qixotic\tendroids

REM Run stress test
echo.
echo Starting stress test...
echo.
python test_stress_phase2.py

echo.
echo ======================================================================
echo Test Complete!
echo.
echo Check the console output above for summary
echo Log file saved in: stress_test_results/
echo ======================================================================
echo.
pause
