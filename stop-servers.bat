@echo off
echo Stopping RAG SaaS Servers and Clearing Cache...
echo.

:: Kill Node.js processes (Frontend)
echo Stopping Frontend (Node.js)...
taskkill /IM node.exe /F 2>nul
if %errorlevel%==0 (
    echo   Frontend stopped.
) else (
    echo   No frontend process found.
)

:: Kill Python processes (Backend)
echo Stopping Backend (Python/Uvicorn)...
taskkill /IM python.exe /F 2>nul
if %errorlevel%==0 (
    echo   Backend stopped.
) else (
    echo   No backend process found.
)

:: Clear Frontend Cache
echo.
echo Clearing Frontend Cache...
if exist "c:\file analysier\rag-saas\frontend\node_modules\.vite" (
    rmdir /s /q "c:\file analysier\rag-saas\frontend\node_modules\.vite"
    echo   Vite cache cleared.
)
if exist "c:\file analysier\rag-saas\frontend\dist" (
    rmdir /s /q "c:\file analysier\rag-saas\frontend\dist"
    echo   Build dist cleared.
)

:: Clear Browser Storage Reminder
echo.
echo Clearing Python Cache...
for /d /r "c:\file analysier\rag-saas\backend" %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
    )
)
echo   Python cache cleared.

:: Clear .pyc files
del /s /q "c:\file analysier\rag-saas\backend\*.pyc" 2>nul

echo.
echo ========================================
echo All servers stopped and cache cleared!
echo ========================================
echo.
echo TIP: To clear browser cache, press Ctrl+Shift+Delete in your browser.
echo.
pause
