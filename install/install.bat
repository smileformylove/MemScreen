@echo off
REM ==============================================================================
REM MemScreen Windows Installation Script
REM
REM This script automates the installation of MemScreen on Windows, including:
REM - Checking system requirements
REM - Installing Python (if needed)
REM - Installing Ollama (if needed)
REM - Downloading AI models
REM - Installing MemScreen Python package
REM - Creating desktop shortcuts
REM
REM Usage: Right-click > Run as Administrator
REM ==============================================================================

setlocal enabledelayedexpansion

REM Set color codes (Windows 10+ supports ANSI escape codes)
set "INFO=[92m"    % Green
set "WARN=[93m"    % Yellow
set "ERROR=[91m"   % Red
set "RESET=[0m"    % Reset

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%  🦉 MemScreen Installation for Windows%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

echo This script will install MemScreen with the following components:
echo   • Python 3.8+ (if not installed)
echo   • Ollama AI Runtime (if not installed)
echo   • Required AI Models (~3GB)
echo   • MemScreen Application
echo.

set /p CONTINUE="Continue with installation? (y/n): "
if /i not "%CONTINUE%"=="y" (
    echo.
    echo %INFO%Installation cancelled.%RESET%
    pause
    exit /b 0
)

REM ==============================================================================
REM Step 1: Check Windows Version
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 1: Checking System Requirements%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

REM Get Windows version
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j

echo %INFO%Detected Windows version: %VERSION%%RESET%

REM Check if Windows 10 or later (version 10.0)
if "%VERSION%" GEQ "10.0" (
    echo %INFO%✅ Windows version is compatible%RESET%
) else (
    echo %ERROR%❌ Windows 10 or later is required%RESET%
    echo %INFO%Your version: %VERSION%%RESET%
    pause
    exit /b 1
)

REM ==============================================================================
REM Step 2: Check and Install Python
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 2: Checking Python Installation%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VERSION=%%i
    echo %INFO%Python found: version %PY_VERSION%%RESET%
    echo %INFO%✅ Python is installed%RESET%
) else (
    echo %WARN%⚠️  Python not found. Installing...%RESET%
    echo %INFO%Downloading Python installer...%RESET%

    REM Download Python 3.11 installer
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe -OutFile %TEMP%\python-installer.exe"

    echo %INFO%Installing Python...%RESET%
    %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

    REM Wait for installation to complete
    timeout /t 30 /nobreak >nul

    echo %INFO%✅ Python installed%RESET%

    REM Refresh environment variables
    refreshenv >nul 2>&1
)

REM ==============================================================================
REM Step 3: Check and Install Ollama
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 3: Checking Ollama Installation%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

where ollama >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=*" %%i in ('ollama --version') do set OLLAMA_VERSION=%%i
    echo %INFO%✅ Ollama found: %OLLAMA_VERSION%%RESET%
) else (
    echo %WARN%⚠️  Ollama not found. Installing...%RESET%

    echo %INFO%Downloading Ollama...%RESET%
    powershell -Command "Invoke-WebRequest -Uri https://ollama.com/download/Ollama-windows-amd64.zip -OutFile %TEMP%\ollama.zip"

    echo %INFO%Extracting Ollama...%RESET%
    powershell -Command "Expand-Archive %TEMP%\ollama.zip -DestinationPath %TEMP%\Ollama -Force"

    echo %INFO%Installing Ollama to %%APPDATA%%...%RESET%
    xcopy "%TEMP%\Ollama\*" "%APPDATA%\Ollama\" /E /I /Y

    echo %INFO%Adding Ollama to PATH...%RESET%
    setx PATH "%PATH%;%APPDATA%\Ollama" /M

    echo %INFO%✅ Ollama installed%RESET%

    REM Refresh environment variables
    refreshenv >nul 2>&1
)

REM ==============================================================================
REM Step 4: Start Ollama Service
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 4: Starting Ollama Service%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

echo %INFO%Checking if Ollama service is running...%RESET%

tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo %INFO%✅ Ollama service is already running%RESET%
) else (
    echo %INFO%Starting Ollama service...%RESET%
    start /B "" "%APPDATA%\Ollama\ollama.exe" serve

    REM Wait for service to start
    timeout /t 5 /nobreak >nul

    echo %INFO%✅ Ollama service started%RESET%
)

REM ==============================================================================
REM Step 5: Download AI Models
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 5: Downloading AI Models%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

echo %INFO%Required models:%RESET%
echo   • qwen2.5vl:3b (~2GB) - Vision model for screen understanding
echo   • mxbai-embed-large (~1GB) - Text embedding for semantic search
echo.
echo %WARN%⚠️  This may take several minutes depending on your internet connection...%RESET%
echo.

REM Check if models are already downloaded
"%APPDATA%\Ollama\ollama.exe" list | findstr /C:"qwen2.5vl" >nul
if %ERRORLEVEL% EQU 0 (
    echo %INFO%✅ qwen2.5vl:3b already downloaded%RESET%
) else (
    echo %INFO%Downloading qwen2.5vl:3b...%RESET%
    "%APPDATA%\Ollama\ollama.exe" pull qwen2.5vl:3b
)

"%APPDATA%\Ollama\ollama.exe" list | findstr /C:"mxbai-embed-large" >nul
if %ERRORLEVEL% EQU 0 (
    echo %INFO%✅ mxbai-embed-large already downloaded%RESET%
) else (
    echo %INFO%Downloading mxbai-embed-large...%RESET%
    "%APPDATA%\Ollama\ollama.exe" pull mxbai-embed-large
)

echo %INFO%✅ All models downloaded%RESET%

REM ==============================================================================
REM Step 6: Install MemScreen
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 6: Installing MemScreen%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

echo %INFO%Upgrading pip...%RESET%
python -m pip install --upgrade pip

echo %INFO%Installing Python dependencies...%RESET%

REM Get script directory (parent of install directory)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

if exist "%PROJECT_ROOT%\requirements.txt" (
    python -m pip install -r "%PROJECT_ROOT%\requirements.txt"
    echo %INFO%✅ Python dependencies installed%RESET%
) else (
    echo %ERROR%❌ requirements.txt not found in project root%RESET%
    pause
    exit /b 1
)

REM ==============================================================================
REM Step 7: Create Desktop Shortcut
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 7: Creating Desktop Shortcut%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

set "SHORTCUT_PATH=%USERPROFILE%\Desktop\MemScreen.lnk"
set "TARGET_PATH=%PROJECT_ROOT%\start.py"
set "WORKING_DIR=%PROJECT_ROOT%"

REM Create PowerShell script to generate shortcut
set "PS_SCRIPT=%TEMP%\create_shortcut.ps1"

echo $WshShell = New-Object -ComObject WScript.Shell > "%PS_SCRIPT%"
echo $Shortcut = $WshShell.CreateShortcut("%SHORTCUT_PATH%") >> "%PS_SCRIPT%"
echo $Shortcut.TargetPath = "python" >> "%PS_SCRIPT%"
echo $Shortcut.Arguments = '"%TARGET_PATH%"' >> "%PS_SCRIPT%"
echo $Shortcut.WorkingDirectory = "%WORKING_DIR%" >> "%PS_SCRIPT%"
echo $Shortcut.Description = "MemScreen - AI-Powered Visual Memory" >> "%PS_SCRIPT%"
echo $Shortcut.Save() >> "%PS_SCRIPT%"

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%"

echo %INFO%✅ Desktop shortcut created%RESET%

REM ==============================================================================
REM Step 8: Create Start Menu Entry
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 8: Creating Start Menu Entry%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

set "START_MENU_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\MemScreen.lnk"

echo $WshShell = New-Object -ComObject WScript.Shell > "%PS_SCRIPT%"
echo $Shortcut = $WshShell.CreateShortcut("%START_MENU_PATH%") >> "%PS_SCRIPT%"
echo $Shortcut.TargetPath = "python" >> "%PS_SCRIPT%"
echo $Shortcut.Arguments = '"%TARGET_PATH%"' >> "%PS_SCRIPT%"
echo $Shortcut.WorkingDirectory = "%WORKING_DIR%" >> "%PS_SCRIPT%"
echo $Shortcut.Description = "MemScreen - AI-Powered Visual Memory" >> "%PS_SCRIPT%"
echo $Shortcut.Save() >> "%PS_SCRIPT%"

powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
del "%PS_SCRIPT%"

echo %INFO%✅ Start menu entry created%RESET%

REM ==============================================================================
REM Step 9: Verify Installation
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Step 9: Verifying Installation%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

set ERRORS=0

REM Check Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %INFO%✅ Python is available%RESET%
) else (
    echo %ERROR%❌ Python not found%RESET%
    set /a ERRORS+=1
)

REM Check Ollama
where ollama >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %INFO%✅ Ollama is available%RESET%
) else (
    echo %ERROR%❌ Ollama not found%RESET%
    set /a ERRORS+=1
)

REM Check Ollama service
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo %INFO%✅ Ollama service is running%RESET%
) else (
    echo %WARN%⚠️  Ollama service is not running%RESET%
)

REM Check models
"%APPDATA%\Ollama\ollama.exe" list | findstr /C:"qwen2.5vl" >nul
if %ERRORLEVEL% EQU 0 (
    echo %INFO%✅ Vision model (qwen2.5vl:3b) is installed%RESET%
) else (
    echo %ERROR%❌ Vision model not found%RESET%
    set /a ERRORS+=1
)

"%APPDATA%\Ollama\ollama.exe" list | findstr /C:"mxbai-embed-large" >nul
if %ERRORLEVEL% EQU 0 (
    echo %INFO%✅ Embedding model (mxbai-embed-large) is installed%RESET%
) else (
    echo %ERROR%❌ Embedding model not found%RESET%
    set /a ERRORS+=1
)

REM ==============================================================================
REM Installation Complete
REM ==============================================================================

echo.
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo %INFO%Installation Complete%RESET%
echo %INFO%━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━%RESET%
echo.

if %ERRORS% EQU 0 (
    echo %INFO%✅ MemScreen installed successfully!%RESET%
    echo.
    echo %INFO%To launch MemScreen:%RESET%
    echo   • Double-click the MemScreen shortcut on your desktop
    echo   • Or find it in the Start Menu
    echo   • Or run: cd "%PROJECT_ROOT%" ^&^& python start.py
    echo.
    echo %INFO%For more information, see the README.md file.%RESET%
    echo.
    echo %INFO%Enjoy using MemScreen! 🦉%RESET%
) else (
    echo %WARN%⚠️  Installation completed with %ERRORS% error(s)%RESET%
    echo %INFO%Please review the errors above and troubleshoot accordingly.%RESET%
)

echo.
pause
