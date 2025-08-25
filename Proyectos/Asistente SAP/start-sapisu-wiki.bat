@echo off
setlocal enabledelayedexpansion

REM SAP IS-U Smart Wiki - Startup Script (Batch)
REM Autor: SAP IS-U Smart Wiki Team
REM Version: 1.1.0
REM Fecha: 2025-08-26

title SAP IS-U Smart Wiki - Startup

echo =========================================
echo 🔍 SAP IS-U Smart Wiki - Startup Script
echo =========================================
echo Version: 1.1.0
echo Fecha: %date% %time%
echo.

echo 🛑 Deteniendo servicios existentes...
REM Matar procesos Python
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 >nul

REM Detener contenedores Docker
docker-compose down --remove-orphans >nul 2>&1
timeout /t 3 >nul

echo ✅ Servicios detenidos correctamente
echo.

echo 🔍 Verificando prerequisitos...

REM Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no está instalado o no está en PATH
    pause
    exit /b 1
) else (
    echo ✅ Docker encontrado
)

REM Verificar Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose no está instalado
    pause
    exit /b 1
) else (
    echo ✅ Docker Compose encontrado
)

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en PATH
    pause
    exit /b 1
) else (
    echo ✅ Python encontrado
)

REM Verificar archivo .env
if not exist ".env" (
    echo ❌ Archivo .env no encontrado
    echo Por favor, ejecuta: copy .env.example .env
    echo Y configura tu API key de OpenAI
    pause
    exit /b 1
) else (
    echo ✅ Archivo .env encontrado
)

echo ✅ Todos los prerequisitos están satisfechos
echo.

echo 🐳 Iniciando servicios Docker...
echo    - Iniciando PostgreSQL y Qdrant...
docker-compose up -d postgres qdrant >nul 2>&1
if errorlevel 1 (
    echo ❌ Error iniciando contenedores Docker
    pause
    exit /b 1
) else (
    echo ✅ Contenedores Docker iniciados
)

echo    - Esperando que los servicios estén listos...
timeout /t 15 >nul
echo ✅ Servicios Docker listos
echo.

echo 🐍 Configurando entorno Python...

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo    - Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Error creando entorno virtual
        pause
        exit /b 1
    )
)

REM Activar entorno virtual
echo    - Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo    - Instalando dependencias...
pip install -r requirements.txt --quiet >nul 2>&1

echo ✅ Entorno Python configurado
echo.

echo 🚀 Iniciando servidor FastAPI...
echo    - Lanzando uvicorn...

REM Iniciar servidor en background
start /B python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 >fastapi.log 2>&1

REM Esperar a que el servidor esté listo
echo    - Esperando que el servidor esté listo...
timeout /t 10 >nul

REM Verificar que el servidor responde
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ El servidor puede estar iniciando, esperando más...
    timeout /t 10 >nul
)

echo ✅ Servidor FastAPI iniciado
echo.

echo 📊 Estado de los servicios:
echo.
echo    🟢 PostgreSQL: Running (puerto 5432)
echo    🟢 Qdrant: Running (puerto 6333)
echo    🟢 FastAPI: Running (puerto 8000)
echo.

echo 🌐 URLs de acceso:
echo.
echo    📱 Interfaz Principal:  http://localhost:8000
echo    📚 Documentación API:   http://localhost:8000/docs
echo    ❤️  Health Check:       http://localhost:8000/health
echo.

echo 🎯 Para usar la herramienta:
echo    1. Se abrirá automáticamente tu navegador web
echo    2. O navega manualmente a: http://localhost:8000
echo    3. ¡Comienza a chatear con el asistente SAP IS-U!
echo    4. Usa '💾 Guardar Incidencia' para almacenar conocimiento
echo.

echo 🌐 Abriendo navegador...
start http://localhost:8000
echo ✅ Navegador abierto automáticamente
echo.

echo 🛑 Para detener todos los servicios:
echo    - Cierra esta ventana
echo    - O ejecuta: docker-compose down
echo.

echo 🎉 ¡SAP IS-U Smart Wiki está listo para usar!
echo    Esta ventana debe permanecer abierta para mantener los servicios
echo.

REM Mantener la ventana abierta
:wait_loop
timeout /t 30 >nul
goto wait_loop
