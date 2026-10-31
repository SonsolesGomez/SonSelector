@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo No se encontro Python. Instala Python 3.12+ desde https://www.python.org/downloads/
  echo Marca la opcion "Add python.exe to PATH" durante la instalacion.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creando entorno virtual...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo No se pudo crear el entorno virtual.
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\streamlit.exe" (
  echo Instalando dependencias...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Fallo la instalacion de dependencias.
    pause
    exit /b 1
  )
)

echo Abriendo Son Selector Alumnos...
start "" ".venv\Scripts\streamlit.exe" run streamlit_app.py
exit /b 0
