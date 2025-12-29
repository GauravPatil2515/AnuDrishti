@echo off
echo ============================================
echo   🧪 DrugTox-AI Platform Startup
echo ============================================
echo.

echo Starting DrugTox-AI Platform...
echo.

echo [1/2] Starting Backend Server (Flask)...
start "DrugTox-Backend" cmd /k "cd /d "%~dp0backend" && python app.py"

echo Waiting for backend to initialize...
timeout /t 8 /nobreak >nul

echo [2/2] Starting Frontend Server (React)...
start "DrugTox-Frontend" cmd /k "cd /d "%~dp0frontend" && npm start"

echo.
echo ============================================
echo   🎉 Platform Started Successfully!
echo ============================================
echo.
echo Backend API: http://localhost:5000
echo Frontend UI: http://localhost:3000
echo.
echo ✅ Features Available:
echo   • Toxicity Prediction (5 endpoints)
echo   • AI-Powered ChemBio Assistant  
echo   • Molecular Visualization
echo   • Export Functionality
echo   • Real-time Analytics
echo.
echo Both servers are now running in separate windows.
echo Close this window when done using the platform.
echo.
pause