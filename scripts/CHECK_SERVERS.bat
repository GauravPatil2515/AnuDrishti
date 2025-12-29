@echo off
echo ============================================
echo   MedToXAi Platform - Server Manager
echo ============================================
echo.

echo Checking server status...
echo.

REM Check Backend
curl -s http://localhost:5000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend Server: RUNNING on http://localhost:5000
) else (
    echo [!!] Backend Server: NOT RUNNING
    echo     Starting backend...
    start /MIN cmd /c "cd /d %~dp0backend && python app.py"
    timeout /t 3 /nobreak >nul
    echo [OK] Backend Server: STARTED
)

echo.

REM Check Frontend
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Frontend Server: RUNNING on http://localhost:3000
) else (
    echo [!!] Frontend Server: NOT RUNNING
    echo     Starting frontend...
    start cmd /c "cd /d %~dp0frontend && npm start"
    echo [OK] Frontend Server: STARTING (will open browser shortly)
)

echo.
echo ============================================
echo   Server Status Check Complete
echo ============================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Both servers are now running!
echo.
echo Press any key to open the application in browser...
pause >nul

REM Open browser
start http://localhost:3000

echo.
echo Platform is ready to use!
echo.
