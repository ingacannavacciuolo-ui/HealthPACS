@echo off
TITLE Build DEBUG - HealthPACSService
cd /d "%~dp0"
cd ..
set "ROOT_DIR=%CD%"

echo ============================================================
echo   BUILD DEBUG - HealthPACSService
echo   Root Progetto: %ROOT_DIR%
echo ============================================================
echo.

echo [1/4] Arresto processi HealthPACSService in esecuzione...
taskkill /F /IM HealthPACSService.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/4] Pulizia cartella di destinazione...
if exist "%ROOT_DIR%\compiling\dist\HealthPACSService" (
    rd /s /q "%ROOT_DIR%\compiling\dist\HealthPACSService" >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo [3/4] Compilazione PyInstaller in modalita Console (DEBUG)...
"%ROOT_DIR%\venv\Scripts\python.exe" -m PyInstaller --noconfirm --onedir --console ^
    --name "HealthPACSService" ^
    --distpath "%ROOT_DIR%\compiling\dist" ^
    --workpath "%ROOT_DIR%\compiling\build" ^
    --specpath "%ROOT_DIR%\compiling\specs" ^
    --clean ^
    --hidden-import "pynetdicom" ^
    --hidden-import "pydicom" ^
    --hidden-import "socketio" ^
    --hidden-import "engineio.async_drivers.threading" ^
    --add-data "%ROOT_DIR%\library;library" ^
    HealthPACSService.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERRORE] Compilazione fallita.
    pause
    exit /b %ERRORLEVEL%
)

echo [4/4] Creazione cartella log e copia healthpacsconfig.ini...
if not exist "%ROOT_DIR%\compiling\dist\log" mkdir "%ROOT_DIR%\compiling\dist\log"

:: Copia healthpacsconfig.ini esclusivamente nella root di dist (sopra HealthPACSService)
if exist "%ROOT_DIR%\healthpacsconfig.ini" (
    copy /Y "%ROOT_DIR%\healthpacsconfig.ini" "%ROOT_DIR%\compiling\dist\" >nul
)

cd /d "%ROOT_DIR%"

echo.
echo ============================================================
echo   BUILD DEBUG COMPLETATA CON SUCCESSO!
echo   Eseguibile generato in: compiling\dist\HealthPACSService\
echo ============================================================
echo.
pause