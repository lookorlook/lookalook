@echo off
echo ========================================
echo   Invoice Reconciliation System
echo ========================================
echo.
echo Starting server at http://127.0.0.1:5000
echo.
echo Open your browser to: http://127.0.0.1:5000
echo.
start http://127.0.0.1:5000
cd /d "%~dp0"
"C:\Users\zt26501\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" project\server.py
pause
