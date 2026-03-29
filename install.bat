@echo off
chcp 65001 >nul

:: 🎩 Lucien Bot - Script de Instalación (Windows)

echo 🎩 ===========================================
echo 🎩  Lucien Bot - Guardian de los Secretos
echo 🎩 ===========================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no esta instalado. Por favor instale Python 3.9 o superior.
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version') do set PYTHON_VERSION=%%a
echo ✅ Python detectado: %PYTHON_VERSION%

:: Crear entorno virtual
echo.
echo 📦 Creando entorno virtual...
python -m venv venv

:: Activar entorno virtual
echo 🔄 Activando entorno virtual...
call venv\Scripts\activate.bat

:: Instalar dependencias
echo.
echo 📥 Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Crear archivo .env si no existe
echo.
if not exist .env (
    echo 📝 Creando archivo de configuracion...
    copy .env.example .env
    echo ⚠️  IMPORTANTE: Edite el archivo .env con su BOT_TOKEN y ADMIN_IDS
) else (
    echo ✅ Archivo .env ya existe
)

:: Crear directorio para logs
if not exist logs mkdir logs

echo.
echo 🎩 ===========================================
echo 🎩  Instalacion completada!
echo 🎩 ===========================================
echo.
echo 📋 Pasos siguientes:
echo    1. Edite el archivo .env con sus configuraciones
echo    2. Obtenga su BOT_TOKEN de @BotFather
echo    3. Obtenga su ADMIN_ID de @userinfobot
echo.
echo 🚀 Para iniciar el bot:
e    call venv\Scripts\activate.bat
echo    python bot.py
echo.
echo 🎩 "Diana observa... y Lucien sirve."

pause
