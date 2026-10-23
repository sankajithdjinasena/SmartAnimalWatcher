@echo off
:: Navigate to application folder relative to this script
cd /d "%~dp0application"
call flask_app.bat
