#!/bin/bash

# 🎩 Lucien Bot - Script de Instalación

echo "🎩 ==========================================="
echo "🎩  Lucien Bot - Guardián de los Secretos"
echo "🎩 ==========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instale Python 3.9 o superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python versión detectada: $PYTHON_VERSION"

# Crear entorno virtual
echo ""
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo ""
echo "📥 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env si no existe
echo ""
if [ ! -f .env ]; then
    echo "📝 Creando archivo de configuración..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edite el archivo .env con su BOT_TOKEN y ADMIN_IDS"
else
    echo "✅ Archivo .env ya existe"
fi

# Crear directorio para logs si no existe
mkdir -p logs

echo ""
echo "🎩 ==========================================="
echo "🎩  Instalación completada!"
echo "🎩 ==========================================="
echo ""
echo "📋 Pasos siguientes:"
echo "   1. Edite el archivo .env con sus configuraciones"
echo "   2. Obtenga su BOT_TOKEN de @BotFather"
echo "   3. Obtenga su ADMIN_ID de @userinfobot"
echo ""
echo "🚀 Para iniciar el bot:"
echo "   source venv/bin/activate"
echo "   python bot.py"
echo ""
echo "🎩 'Diana observa... y Lucien sirve.'"
