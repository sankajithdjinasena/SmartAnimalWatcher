@echo off
:: Run the Python script
python app.py

:: Wait a few seconds for server to start
timeout /t 5 /nobreak > nul

:: Open browser automatically
start http://127.0.0.1:5000/

:: Keep window open
pause