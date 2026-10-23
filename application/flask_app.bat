@echo off
cd /d "%~dp0"
echo ========================================================
echo   Smart Animal Watcher - AI Security Surveillance
echo ========================================================
echo Starting Flask web server...

:: Launch Python Flask server in dedicated window
start "Smart Animal Watcher Server" python app.py

:: Wait for server to bind port
timeout /t 3 /nobreak > nul

:: Open browser automatically
start http://127.0.0.1:5000/
