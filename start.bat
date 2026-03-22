@echo off
setlocal EnableDelayedExpansion
title NovelForge v3.1

echo.
echo =============================================
echo   NovelForge v3.1 - Starting
echo =============================================
echo.

:: -- Pre-flight checks --------------------------------------------
if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause & exit /b 1
)

if not exist backend\main.py (
    echo [ERROR] backend\main.py not found. Are you in the NovelForge directory?
    pause & exit /b 1
)

:: -- Check port availability --------------------------------------
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr LISTENING') do set PORT_PID=%%a
if defined PORT_PID (
    echo [WARNING] Port 8000 is in use by PID %PORT_PID%.
    echo If this is a stale NovelForge process, close it and try again.
    echo To use a different port, edit BACKEND_PORT in .env
    echo.
    set /p CONTINUE="Continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" exit /b 0
)

:: -- Activate venv -----------------------------------------------
call venv\Scripts\activate.bat

:: -- Smart frontend rebuild --------------------------------------
:: Only rebuild if any file in frontend/src/ is newer than dist/index.html
:: This saves 30-60 seconds on every start after the first build.
set NEEDS_BUILD=0
if not exist frontend\dist\index.html (
    set NEEDS_BUILD=1
    echo Frontend dist not found - building...
) else (
    :: xcopy /D copies only newer files; if it would copy anything, rebuild is needed
    xcopy frontend\src frontend\_src_check /S /D /L /Y 2>nul | findstr "File(s)" >nul 2>&1
    if not errorlevel 1 (
        set NEEDS_BUILD=1
        echo Frontend source changed - rebuilding...
    )
    if exist frontend\_src_check rmdir /s /q frontend\_src_check 2>nul
)

if "!NEEDS_BUILD!"=="1" (
    cd frontend
    call npm run build
    if errorlevel 1 (
        echo [WARNING] Frontend build failed. Using last successful build if available.
    ) else (
        echo [OK] Frontend built.
    )
    cd ..
) else (
    echo [OK] Frontend is up to date (skipping rebuild).
)

:: -- Start backend ------------------------------------------------
echo.
echo Starting backend server...
start "NovelForge Backend" /MIN cmd /c ^
    "call venv\Scripts\activate.bat && python -m uvicorn backend.main:app ^
    --host 127.0.0.1 --port 8000 --workers 1 ^
    2>&1 | powershell -Command \"$input | Tee-Object -FilePath novelforge.log -Append\""

:: -- Wait for backend readiness ----------------------------------
echo Waiting for backend to start...
set /a ATTEMPTS=0
:waitloop
timeout /t 1 /nobreak >nul
set /a ATTEMPTS+=1
curl -s -f http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    if %ATTEMPTS% LSS 30 goto waitloop
    echo [ERROR] Backend did not start within 30 seconds.
    echo Check novelforge.log for details.
    pause & exit /b 1
)

echo [OK] Backend ready.

:: -- Open browser -------------------------------------------------
echo.
echo =============================================
echo   NovelForge is running!
echo   http://localhost:8000
echo =============================================
echo.
start "" "http://localhost:8000"

echo Backend log: novelforge.log
echo Close the "NovelForge Backend" window to stop the server.
echo This window can be closed.
pause
