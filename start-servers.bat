@echo off
echo ========================================
echo    Starting RAG SaaS Application
echo ========================================
echo.

:: Start Backend Server
echo [1/2] Starting Backend Server (Port 8000)...
start "RAG Backend - Port 8000" cmd /k "cd /d c:\file analysier\rag-saas\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend to initialize
echo      Waiting for backend to start...
timeout /t 5 /nobreak > nul

:: Start Frontend Server  
echo [2/2] Starting Frontend Server...
start "RAG Frontend" cmd /k "cd /d c:\file analysier\rag-saas\frontend && npm run dev"

echo.
echo ========================================
echo    Both servers are starting!
echo ========================================
echo.
echo Backend API:  http://localhost:8000
echo Frontend UI:  http://localhost:3000
echo              (or next available port like 3001, 3002)
echo.
echo Check the Frontend terminal window for the actual URL.
echo.
echo Press any key to exit this launcher...
pause > nul
