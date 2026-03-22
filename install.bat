@echo off
setlocal EnableDelayedExpansion
title NovelForge Installer v3.1

echo.
echo =============================================
echo   NovelForge v3.1 - Installer
echo =============================================
echo.

:: -- Check Python -------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    echo During installation, check "Add Python to PATH".
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1 delims=." %%m in ("%PYVER%") do set PYMAJ=%%m
for /f "tokens=2 delims=." %%m in ("%PYVER%") do set PYMIN=%%m
if %PYMAJ% LSS 3 ( echo [ERROR] Python 3.10+ required, found %PYVER% & pause & exit /b 1 )
if %PYMAJ% EQU 3 if %PYMIN% LSS 10 ( echo [ERROR] Python 3.10+ required, found %PYVER% & pause & exit /b 1 )
echo [OK] Python %PYVER%

:: -- Check Node.js ------------------------------------------------
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found.
    echo Please install Node.js 18 or higher from https://nodejs.org/
    pause & exit /b 1
)
for /f %%v in ('node --version') do set NODEVER=%%v
echo [OK] Node.js %NODEVER%

:: -- Virtual environment ------------------------------------------
echo.
echo Creating Python virtual environment...
python -m venv venv
if errorlevel 1 ( echo [ERROR] Failed to create virtual environment. & pause & exit /b 1 )
call venv\Scripts\activate.bat

echo Installing Python dependencies (this may take a few minutes)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed. Check the error above.
    pause & exit /b 1
)
echo [OK] Python dependencies installed.

:: -- Frontend -----------------------------------------------------
echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 ( echo [ERROR] npm install failed. & cd .. & pause & exit /b 1 )
echo Building frontend...
call npm run build
if errorlevel 1 ( echo [ERROR] Frontend build failed. & cd .. & pause & exit /b 1 )
cd ..
echo [OK] Frontend ready.

:: -- .env ---------------------------------------------------------
if not exist .env (
    echo Creating .env from .env.example...
    if exist .env.example (
        copy .env.example .env >nul
    ) else (
        echo ENVIRONMENT=production> .env
        echo LM_STUDIO_URL=http://localhost:1234/v1>> .env
        echo LM_STUDIO_MODEL=local-model>> .env
        echo LM_STUDIO_TIMEOUT=300>> .env
        echo BACKEND_PORT=8000>> .env
        echo PROJECTS_DIR=projects>> .env
        echo DB_PATH=novelforge.db>> .env
    )
    echo [OK] .env created.
)

:: -- Directories --------------------------------------------------
if not exist projects md projects
if not exist projects\templates md projects\templates

:: -- Database init ------------------------------------------------
echo Initialising database...
call venv\Scripts\activate.bat
python -c "from backend.database.connection import init_db; init_db(); print('OK')"
if errorlevel 1 ( echo [ERROR] Database init failed. & pause & exit /b 1 )

echo.
echo =============================================
echo   Installation complete!
echo =============================================
echo.
echo Next steps:
echo   1. Open LM Studio (download from https://lmstudio.ai if needed)
echo   2. Load a model (recommended: any 7B-13B GGUF, Q4_K_M quantization)
echo   3. Click "Start Server" in LM Studio
echo   4. Run start.bat
echo.
pause
