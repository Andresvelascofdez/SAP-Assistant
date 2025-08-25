# 🚀 Script de Inicio Unificado - SAP IS-U Smart Wiki

Script único automatizado para instalación y ejecución completa del SAP IS-U Smart Wiki.

## 📁 Script Disponible

### 🖥️ Windows

#### `START-SAPISU-WIKI-UNIFICADO.ps1` (Único Script Necesario)
**Script de PowerShell unificado que incluye instalación completa y ejecución**

```powershell
# Ejecutar en PowerShell
.\START-SAPISU-WIKI-UNIFICADO.ps1
```

**Características Integradas:**
- ✅ Verificación completa de prerequisitos (Python 3.11+, Docker Desktop)
- ✅ Detección y parada automática de servicios existentes
- ✅ Configuración automática del entorno virtual Python
- ✅ Instalación automática de todas las dependencias (incluye email-validator)
- ✅ Corrección automática de importaciones Python
- ✅ Inicio automático de servicios Docker (PostgreSQL + Qdrant)
- ✅ Inicialización de base de datos y colecciones vector
- ✅ Verificación de conectividad OpenAI API
- ✅ Lanzamiento del servidor FastAPI completo
- ✅ Verificación de salud de todos los servicios
- ✅ Información completa de URLs de acceso
- ✅ Limpieza automática al salir (Ctrl+C)

## 🎯 Uso Simplificado

### Para Windows
1. **Abrir PowerShell como Administrador**
2. **Navegar al directorio del proyecto**
   ```powershell
   cd "C:\ruta\a\tu\SAP-Assistant"
   ```
3. **Ejecutar el script unificado**
   ```powershell
   .\START-SAPISU-WIKI-UNIFICADO.ps1
   ```
4. **¡Listo!** El sistema completo se instalará y ejecutará automáticamente

> ⚠️ **Nota:** Solo se necesita un script. No hay versiones para Linux/Mac en este momento.

## ✨ Lo Que Hace el Script Unificado

### 1. **Verificación de Prerequisitos**
- ✅ Python 3.11+ disponible
- ✅ Docker Desktop instalado y ejecutándose
- ✅ Permisos de ejecución PowerShell

### 2. **Limpieza de Servicios Existentes**
- 🧹 Mata procesos Python/uvicorn anteriores
- 🐳 Detiene contenedores Docker existentes
- 🔄 Limpia recursos bloqueados

### 3. **Configuración Automática del Entorno**
- 🐍 Crea/activa entorno virtual Python
- 📦 Instala dependencias principales (uvicorn, fastapi, openai)
- 📋 Instala dependencias del proyecto (requirements.txt)
- 📧 Instala email-validator
- 🔧 Corrige automáticamente importaciones Python (absolutos vs relativos)

### 4. **Inicio de Infraestructura**
- 🐳 PostgreSQL (puerto 5432) con usuario sapisu_user
- 🔍 Qdrant (puerto 6333) para vectores
- � Verificación de salud de servicios
- ⏱️ Espera hasta que estén completamente listos

### 5. **Lanzamiento de Aplicación**
- 🚀 Servidor FastAPI (puerto 8000) desde directorio /api
- 🔗 Verificación de conectividad OpenAI API
- 🗄️ Inicialización automática de base de datos
- � Creación de colección Qdrant 'sapisu_knowledge'
- 🌐 URLs de acceso mostradas al usuario

## 🔧 Configuración Previa Mínima

### 1. Archivo `.env` (Requerido)
```bash
# El archivo .env ya existe en el proyecto
# Solo necesitas configurar tu API key de OpenAI
OPENAI_API_KEY=sk-proj-tu-api-key-aqui
```

### 2. Docker Desktop (Requerido)
- Descargar e instalar Docker Desktop
- Asegurar que está ejecutándose antes de ejecutar el script
- El script verifica automáticamente la disponibilidad

### 3. Python (Automático)
- Python 3.11 o superior
- El script verifica automáticamente la versión
- Si no está disponible, muestra instrucciones de instalación

> ✅ **Todo lo demás es automático** - El script se encarga de la instalación y configuración completa.

## 🌐 URLs de Acceso

Una vez iniciado, el script muestra todas las URLs disponibles:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Aplicación Web** | http://localhost:8000 | Interfaz ChatGPT-style principal |
| **Documentación API** | http://localhost:8000/docs | Documentación interactiva Swagger |
| **Chat Público** | http://localhost:8000/api/v1/search/chat-public | Endpoint de chat directo |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Dashboard base vectorial |

## 🛑 Detener Servicios

### Método Recomendado: Ctrl+C
- Presiona `Ctrl+C` en la ventana del script
- Limpieza automática de todos los recursos
- Detiene Docker containers y procesos Python

### Salida del Script
Al presionar Ctrl+C verás:
```
[XX:XX:XX] Limpiando servicios...
[XX:XX:XX] Servicios Docker detenidos
```

## 🔍 Solución de Problemas

### Error: "Docker no encontrado"
**Problema:** Docker Desktop no está instalado o no está ejecutándose
**Solución:**
1. Descargar Docker Desktop desde docker.com
2. Instalarlo y ejecutarlo
3. Esperar que Docker esté completamente iniciado (icono en systray)
4. Ejecutar el script nuevamente

### Error: "Python no encontrado" 
**Problema:** Python 3.11+ no está disponible
**Solución:**
1. Descargar Python 3.11+ desde python.org
2. Asegurar que se agrega al PATH durante la instalación
3. Reiniciar PowerShell
4. Ejecutar el script nuevamente

### Error: "API Key no configurada"
**Problema:** Archivo .env no tiene OPENAI_API_KEY válida
**Solución:**
1. Abrir archivo `.env` en el directorio del proyecto
2. Agregar/actualizar: `OPENAI_API_KEY=sk-proj-tu-key-real-aqui`
3. Guardar el archivo
4. Ejecutar el script nuevamente

### Error: "Puerto 8000 en uso"
**Problema:** Otro servicio está usando el puerto 8000
**Solución:**
1. El script automáticamente mata procesos existentes
2. Si persiste, reiniciar el equipo
3. Ejecutar el script nuevamente

### Error: "Importaciones Python"
**Problema:** Conflictos en importaciones relativas/absolutas
**Solución:**
- ✅ **Automático** - El script corrige todas las importaciones automáticamente
- No requiere intervención manual

### Script Se Detiene Inesperadamente
**Solución:**
1. Verificar que PowerShell tiene permisos de ejecución
2. Ejecutar como Administrador
3. Verificar logs en la ventana del terminal
4. Si persiste, reportar el error específico

## 🎉 ¡Listo para Usar!

Una vez que veas el mensaje final del script:
```
=================================================================
[XX:XX:XX] SERVIDOR SAP IS-U SMART WIKI INICIADO
=================================================================
[XX:XX:XX] Aplicacion Web: http://localhost:8000
[XX:XX:XX] Documentacion API: http://localhost:8000/docs
[XX:XX:XX] Chat Publico: http://localhost:8000/api/v1/search/chat-public
[XX:XX:XX] Qdrant Dashboard: http://localhost:6333/dashboard
=================================================================

[XX:XX:XX] Presiona Ctrl+C para detener el servidor
```

Puedes:
1. **💬 Chatear** con el asistente SAP IS-U usando la interfaz web
2. **💾 Guardar incidencias** usando el botón "Guardar Incidencia"  
3. **📎 Subir documentos** para ampliar la base de conocimiento
4. **📖 Explorar la API** en `/docs` para integraciones
5. **🔍 Monitorear vectores** en el dashboard de Qdrant

## ⚡ Características Principales

### 🤖 Chat Inteligente
- Interfaz estilo ChatGPT
- Respuestas basadas en conocimiento SAP IS-U
- Historial de conversaciones
- Respuestas contextuales y precisas

### 📊 Gestión de Incidencias  
- Modal integrado para guardar problemas
- Campos estructurados (título, descripción, prioridad, categoría)
- Almacenamiento en PostgreSQL
- Trazabilidad completa

### 🔧 Sistema RAG
- Búsqueda vectorial con Qdrant
- Embeddings OpenAI text-embedding-3-small
- Modelo GPT-4o-mini para generación
- Base de conocimiento SAP IS-U extensible

¡Disfruta usando tu asistente inteligente SAP IS-U! 🚀
