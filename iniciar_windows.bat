@echo off
setlocal
cd /d "%~dp0"
echo =============================================
echo  MiniDB Studio - Inicio en Windows
 echo =============================================
where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3"
) else (
    set "PYTHON_CMD=python"
)
if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :error
)
echo Instalando / verificando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error
where docker >nul 2>nul
if %errorlevel% equ 0 (
    echo Iniciando contenedores PostgreSQL y MongoDB...
    docker compose up -d
    if errorlevel 1 echo AVISO: Docker no pudo iniciarse. Abre Docker Desktop y prueba: docker compose up -d
) else (
    echo AVISO: Docker no encontrado. Instala Docker Desktop para usar las bases locales.
)
echo Iniciando interfaz grafica...
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto :error
goto :end
:error
echo.
echo ERROR: Revisa los mensajes anteriores y el README.md.
pause
:end
endlocal
