@echo off
TITLE Build DEBUG - HealthPACSWeb
cd /d "%~dp0"
cd ..
set "ROOT_DIR=%CD%"

echo ============================================================
echo    BUILD DEBUG - HealthPACSWeb
echo    Root Progetto: %ROOT_DIR%
echo ============================================================
echo.

echo [1/3] Arresto processi HealthPACSWeb in esecuzione...
taskkill /F /IM HealthPACSWeb.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Pulizia build e dist vecchie...
if exist "%ROOT_DIR%\compiling\dist\HealthPACSWeb" rd /s /q "%ROOT_DIR%\compiling\dist\HealthPACSWeb" >nul 2>&1
if exist "%ROOT_DIR%\compiling\build\HealthPACSWeb" rd /s /q "%ROOT_DIR%\compiling\build\HealthPACSWeb" >nul 2>&1
timeout /t 1 /nobreak >nul

echo [3/3] Compilazione PyInstaller...
"%ROOT_DIR%\venv\Scripts\python.exe" -m PyInstaller --noconfirm --onedir --console ^
    --name "HealthPACSWeb" ^
    --distpath "%ROOT_DIR%\compiling\dist" ^
    --workpath "%ROOT_DIR%\compiling\build" ^
    --specpath "%ROOT_DIR%\compiling\specs" ^
    --clean ^
    --hidden-import "engineio.async_drivers.threading" ^
    --exclude-module "pysqlite2" ^
    --exclude-module "MySQLdb" ^
    --add-data "%ROOT_DIR%\library;library" ^
    --add-data "%ROOT_DIR%\templates;templates" ^
    --add-data "%ROOT_DIR%\static;static" ^
    HealthPACSWeb.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERRORE] Compilazione fallita.
    pause
    exit /b %ERRORLEVEL%
)

rem --- GESTIONE DEI FILE ESTERNI IN DIST ---
set "DIST_DIR=%ROOT_DIR%\compiling\dist"

rem Creazione cartella log in dist
if not exist "%DIST_DIR%\log" mkdir "%DIST_DIR%\log"

rem Copia del file .ini direttamente dentro dist (fuori dalla cartella dell'exe)
if exist "%ROOT_DIR%\healthpacsconfig.ini" (
    copy /Y "%ROOT_DIR%\healthpacsconfig.ini" "%DIST_DIR%\" >nul
)

cd /d "%ROOT_DIR%"

echo.
echo ============================================================
echo    BUILD DEBUG COMPLETATA CON SUCCESSO!
echo ============================================================
echo.
pause