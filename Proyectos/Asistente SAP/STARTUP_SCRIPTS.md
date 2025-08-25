# 🚀 Scripts de Inicio - SAP IS-U Smart Wiki

Este directorio contiene scripts automatizados para iniciar fácilmente todos los servicios necesarios del SAP IS-U Smart Wiki.

## 📁 Scripts Disponibles

### 🖥️ Windows

#### `start-sapisu-wiki.ps1` (Recomendado)
**Script de PowerShell completo con todas las características**

```powershell
# Ejecutar en PowerShell
.\start-sapisu-wiki.ps1
```

**Características:**
- ✅ Verificación completa de prerequisitos
- ✅ Detección y parada automática de servicios existentes
- ✅ Configuración automática del entorno Python
- ✅ Inicio automático de Docker Compose
- ✅ Verificación de salud de todos los servicios
- ✅ Apertura automática del navegador
- ✅ Monitoreo continuo de servicios
- ✅ Limpieza automática al salir

#### `start-sapisu-wiki.bat`
**Script batch simple para usuarios sin PowerShell**

```batch
# Doble click o ejecutar en CMD
start-sapisu-wiki.bat
```

**Características:**
- ✅ Verificación básica de prerequisitos
- ✅ Inicio de servicios Docker y FastAPI
- ✅ Apertura automática del navegador
- ✅ Interfaz simplificada

### 🐧 Linux / 🍎 macOS

#### `start-sapisu-wiki.sh`
**Script bash completo para sistemas Unix**

```bash
# Hacer ejecutable (solo la primera vez)
chmod +x start-sapisu-wiki.sh

# Ejecutar
./start-sapisu-wiki.sh
```

**Características:**
- ✅ Todas las características del script de PowerShell
- ✅ Compatibilidad con Linux y macOS
- ✅ Detección automática del comando para abrir navegador
- ✅ Logs detallados y limpieza automática

## 🎯 Uso Rápido

### Para Windows (Recomendado)
1. **Abrir PowerShell como Administrador**
2. **Navegar al directorio del proyecto**
   ```powershell
   cd "C:\ruta\a\tu\SAP-Assistant"
   ```
3. **Ejecutar el script**
   ```powershell
   .\start-sapisu-wiki.ps1
   ```
4. **¡Listo!** El navegador se abrirá automáticamente

### Para Linux/Mac
1. **Abrir terminal**
2. **Navegar al directorio del proyecto**
   ```bash
   cd /ruta/a/tu/SAP-Assistant
   ```
3. **Hacer ejecutable (solo primera vez)**
   ```bash
   chmod +x start-sapisu-wiki.sh
   ```
4. **Ejecutar el script**
   ```bash
   ./start-sapisu-wiki.sh
   ```
5. **¡Listo!** El navegador se abrirá automáticamente

## ✨ Qué Hace Cada Script

### 1. **Detener Servicios Existentes**
- Mata procesos Python/uvicorn anteriores
- Detiene contenedores Docker existentes
- Limpia recursos bloqueados

### 2. **Verificar Prerequisitos**
- ✅ Docker y Docker Compose instalados
- ✅ Python 3.11+ disponible
- ✅ Archivo `.env` configurado
- ✅ API Key de OpenAI válida

### 3. **Iniciar Infraestructura**
- 🐳 PostgreSQL (puerto 5432)
- 🔍 Qdrant (puerto 6333)
- 🐍 Entorno virtual Python
- 📦 Instalación de dependencias

### 4. **Lanzar Aplicación**
- 🚀 Servidor FastAPI (puerto 8000)
- 🧪 Verificación de endpoints
- 🌐 Apertura automática del navegador

### 5. **Monitoreo Continuo**
- 📊 Estado de servicios en tiempo real
- 🔄 Reinicio automático si es necesario
- 🧹 Limpieza al salir (Ctrl+C)

## 🔧 Configuración Previa

### 1. Archivo `.env`
```bash
# Copiar plantilla
cp .env.example .env

# Editar con tu API key
OPENAI_API_KEY=sk-proj-tu-api-key-aqui
```

### 2. Docker Desktop
- Instalar Docker Desktop
- Asegurar que está ejecutándose
- Verificar: `docker --version`

### 3. Python
- Python 3.11 o superior
- Verificar: `python --version`

## 🌐 URLs de Acceso

Una vez iniciado, puedes acceder a:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Interfaz Principal** | http://localhost:8000 | ChatGPT-style interface |
| **API Docs** | http://localhost:8000/docs | Documentación interactiva |
| **Health Check** | http://localhost:8000/health | Estado de servicios |
| **PostgreSQL** | localhost:5432 | Base de datos (interno) |
| **Qdrant** | http://localhost:6333 | Base vectorial (interno) |

## 🛑 Detener Servicios

### Método 1: Ctrl+C
- Presiona `Ctrl+C` en la ventana del script
- Limpieza automática de todos los recursos

### Método 2: Comando Manual
```bash
# Detener contenedores Docker
docker-compose down

# Matar procesos Python (si es necesario)
# Windows:
taskkill /F /IM python.exe

# Linux/Mac:
pkill -f "uvicorn\|python.*api"
```

## 🔍 Solución de Problemas

### Error: "Docker no encontrado"
```bash
# Verificar instalación
docker --version
docker-compose --version

# Si no están instalados, descargar Docker Desktop
```

### Error: "Puerto 8000 en uso"
```bash
# El script automáticamente mata procesos existentes
# Si persiste, reiniciar y ejecutar de nuevo
```

### Error: "API Key no configurada"
```bash
# Verificar archivo .env
cat .env | grep OPENAI_API_KEY

# Configurar correctamente
OPENAI_API_KEY=sk-proj-tu-key-real-aqui
```

### Error: "Python no encontrado"
```bash
# Verificar instalación Python
python --version
# o
python3 --version

# Instalar Python 3.11+ si es necesario
```

## 📝 Logs y Depuración

### Ver Logs de la Aplicación
```bash
# FastAPI logs
tail -f fastapi.log

# Docker logs
docker-compose logs -f

# Logs específicos
docker-compose logs postgres
docker-compose logs qdrant
```

### Verificar Estado Manual
```bash
# Test de conectividad
curl http://localhost:8000/health

# Test de chat
curl -X POST "http://localhost:8000/api/v1/search/chat-public" \
     -H "Content-Type: application/json" \
     -d '{"query": "test", "tenant_slug": "default"}'
```

## 🎉 ¡Listo para Usar!

Una vez que veas el mensaje:
```
🎉 ¡SAP IS-U Smart Wiki está listo para usar!
```

Puedes:
1. **Chatear** con el asistente SAP IS-U
2. **Guardar incidencias** usando el botón "💾 Guardar Incidencia"
3. **Subir documentos** con el botón 📎
4. **Explorar la API** en `/docs`

¡Disfruta usando tu asistente inteligente SAP IS-U! 🚀
