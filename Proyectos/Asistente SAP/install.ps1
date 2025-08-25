# =============================================================================
# Script de Instalación Completa - Wiki Inteligente SAP IS-U (Windows)
# =============================================================================

param(
    [switch]$SkipDocker,
    [switch]$SkipPython,
    [string]$OpenAIKey = ""
)

# Configurar colores para output
$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Log-Info($Message) {
    Write-ColorOutput Blue "[INFO] $Message"
}

function Log-Success($Message) {
    Write-ColorOutput Green "[SUCCESS] $Message"
}

function Log-Warning($Message) {
    Write-ColorOutput Yellow "[WARNING] $Message"
}

function Log-Error($Message) {
    Write-ColorOutput Red "[ERROR] $Message"
}

# Banner
Write-Host "=================================================================="
Write-Host "      🔍 Wiki Inteligente SAP IS-U - Instalación Windows      "
Write-Host "=================================================================="
Write-Host

# 1. Verificar prerrequisitos
Log-Info "1. Verificando prerrequisitos..."

# Verificar PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Log-Error "PowerShell 5.0 o superior es requerido"
    exit 1
}

# Verificar si estamos en el directorio correcto
if (!(Test-Path "docker-compose.yml")) {
    Log-Error "docker-compose.yml no encontrado. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
}

# Verificar Git
try {
    $null = git --version
    Log-Success "Git: Disponible"
}
catch {
    Log-Error "Git no encontrado. Instala Git desde https://git-scm.com/"
    exit 1
}

# Verificar Docker
if (!$SkipDocker) {
    try {
        $null = docker --version
        Log-Success "Docker: Disponible"
    }
    catch {
        Log-Error "Docker no encontrado. Instala Docker Desktop desde https://www.docker.com/products/docker-desktop"
        exit 1
    }

    try {
        $null = docker compose version
        Log-Success "Docker Compose: Disponible"
    }
    catch {
        Log-Error "Docker Compose no encontrado o Docker Desktop no está ejecutándose"
        exit 1
    }
}

# Verificar Python
if (!$SkipPython) {
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python 3\.([8-9]|1[0-9])") {
            Log-Success "Python: $pythonVersion"
        }
        else {
            Log-Error "Python 3.8+ es requerido. Versión encontrada: $pythonVersion"
            exit 1
        }
    }
    catch {
        Log-Error "Python no encontrado. Instala Python 3.8+ desde https://www.python.org/"
        exit 1
    }

    try {
        $null = pip --version
        Log-Success "pip: Disponible"
    }
    catch {
        Log-Error "pip no encontrado"
        exit 1
    }
}

# 2. Configurar variables de entorno
Log-Info "2. Configurando variables de entorno..."

$ProjectDir = Get-Location
$EnvFile = Join-Path $ProjectDir ".env"

# Generar passwords seguros
function Generate-SecurePassword($Length = 32) {
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    $password = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $password
}

# Crear archivo .env si no existe
if (!(Test-Path $EnvFile)) {
    Log-Info "Creando archivo .env..."
    
    $dbPassword = Generate-SecurePassword
    $qdrantKey = Generate-SecurePassword
    $secretKey = Generate-SecurePassword 50
    
    $envContent = @"
# =============================================================================
# Configuración de Producción - Wiki Inteligente SAP IS-U
# =============================================================================

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
DEBUG=false
ENVIRONMENT=production

# Database Configuration
DATABASE_URL=postgresql://sapisu_user:$dbPassword@postgres:5432/sapisu_db
POSTGRES_DB=sapisu_db
POSTGRES_USER=sapisu_user
POSTGRES_PASSWORD=$dbPassword

# Qdrant Configuration
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=$qdrantKey
QDRANT_COLLECTION=sapisu_embeddings

# OpenAI Configuration
OPENAI_API_KEY=$OpenAIKey
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4.1-preview

# Security
SECRET_KEY=$secretKey
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALGORITHM=HS256

# File Upload
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,docx,doc,txt,md,html

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
HEALTH_CHECK_INTERVAL=30
METRICS_ENABLED=true

# Traefik
TRAEFIK_DOMAIN=sapisu.local
ACME_EMAIL=admin@sapisu.local

# Redis (for caching)
REDIS_URL=redis://redis:6379/0

# Backup
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
"@

    $envContent | Out-File -FilePath $EnvFile -Encoding UTF8
    Log-Success "Archivo .env creado con configuración segura"
}
else {
    Log-Warning "Archivo .env ya existe. Usando configuración existente."
}

# 3. Crear estructura de directorios
Log-Info "3. Creando estructura de directorios..."

$directories = @(
    "data\postgres",
    "data\qdrant", 
    "data\backups",
    "logs\api",
    "logs\scheduler",
    "logs\traefik",
    "ssl",
    "config"
)

foreach ($dir in $directories) {
    $fullPath = Join-Path $ProjectDir $dir
    if (!(Test-Path $fullPath)) {
        New-Item -Path $fullPath -ItemType Directory -Force | Out-Null
    }
}

Log-Success "Estructura de directorios creada"

# 4. Instalar dependencias de Python
if (!$SkipPython) {
    Log-Info "4. Instalando dependencias de Python..."

    if (Test-Path "requirements.txt") {
        # Crear entorno virtual si no existe
        if (!(Test-Path "venv")) {
            Log-Info "Creando entorno virtual..."
            python -m venv venv
        }
        
        # Activar entorno virtual
        & "venv\Scripts\Activate.ps1"
        
        # Actualizar pip
        python -m pip install --upgrade pip
        
        # Instalar dependencias
        pip install -r requirements.txt
        
        Log-Success "Dependencias de Python instaladas"
    }
    else {
        Log-Warning "requirements.txt no encontrado. Saltando instalación de dependencias Python."
    }
}

# 5. Configurar base de datos
Log-Info "5. Configurando base de datos..."

# Generar migraciones si no existen
if (!(Test-Path "alembic\versions") -or ((Get-ChildItem "alembic\versions" -ErrorAction SilentlyContinue).Count -eq 0)) {
    Log-Info "Configurando migraciones de base de datos..."
    
    if (Test-Path "venv") {
        & "venv\Scripts\Activate.ps1"
    }
    
    # Verificar si Alembic está configurado
    if (!(Test-Path "alembic.ini")) {
        Log-Info "Inicializando Alembic..."
        alembic init alembic
    }
}

Log-Success "Base de datos configurada"

# 6. Construir imágenes Docker
if (!$SkipDocker) {
    Log-Info "6. Construyendo imágenes Docker..."

    # Verificar que Docker Desktop esté ejecutándose
    try {
        docker ps | Out-Null
    }
    catch {
        Log-Error "Docker Desktop no está ejecutándose. Por favor, inícialo."
        exit 1
    }

    # Construir imagen de la API
    Log-Info "Construyendo imagen de la API..."
    docker build -t sapisu-api:latest -f docker/Dockerfile.api .

    # Construir imagen del scheduler
    Log-Info "Construyendo imagen del scheduler..."
    docker build -t sapisu-scheduler:latest -f docker/Dockerfile.scheduler .

    # Construir imagen de Nginx (si existe)
    if (Test-Path "docker\Dockerfile.nginx") {
        Log-Info "Construyendo imagen de Nginx..."
        docker build -t sapisu-nginx:latest -f docker/Dockerfile.nginx .
    }

    Log-Success "Imágenes Docker construidas"
}

# 7. Configurar SSL/TLS
Log-Info "7. Configurando SSL/TLS..."

$sslCert = Join-Path $ProjectDir "ssl\sapisu.crt"
$sslKey = Join-Path $ProjectDir "ssl\sapisu.key"

if (!(Test-Path $sslCert)) {
    Log-Info "Generando certificados SSL auto-firmados..."
    
    # Verificar si OpenSSL está disponible
    try {
        $null = openssl version
        
        # Crear certificado auto-firmado
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $sslKey -out $sslCert -subj "/C=ES/ST=Madrid/L=Madrid/O=SAP ISU Wiki/CN=sapisu.local"
        
        Log-Success "Certificados SSL generados"
    }
    catch {
        Log-Warning "OpenSSL no encontrado. Saltando generación de certificados SSL."
        Log-Info "Puedes usar certificados existentes o configurar HTTPS más tarde."
    }
}

# 8. Inicializar servicios
if (!$SkipDocker) {
    Log-Info "8. Inicializando servicios..."

    # Levantar servicios de infraestructura primero
    Log-Info "Iniciando servicios de infraestructura (PostgreSQL, Qdrant, Redis)..."
    docker compose up -d postgres qdrant redis

    # Esperar a que los servicios estén listos
    Log-Info "Esperando a que los servicios estén listos (60 segundos)..."
    Start-Sleep 60

    # Verificar que PostgreSQL esté listo
    Log-Info "Verificando PostgreSQL..."
    $retries = 0
    do {
        try {
            docker compose exec postgres pg_isready -U sapisu_user -d sapisu_db | Out-Null
            $pgReady = $true
        }
        catch {
            $pgReady = $false
            Start-Sleep 5
            $retries++
        }
    } while (!$pgReady -and $retries -lt 12)

    if (!$pgReady) {
        Log-Error "PostgreSQL no está respondiendo después de 60 segundos"
        exit 1
    }

    # Verificar que Qdrant esté listo
    Log-Info "Verificando Qdrant..."
    $retries = 0
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 5
            $qdrantReady = $response.StatusCode -eq 200
        }
        catch {
            $qdrantReady = $false
            Start-Sleep 5
            $retries++
        }
    } while (!$qdrantReady -and $retries -lt 12)

    if (!$qdrantReady) {
        Log-Warning "Qdrant no está respondiendo. Continuando..."
    }

    Log-Success "Servicios de infraestructura iniciados"

    # 9. Ejecutar migraciones
    Log-Info "9. Ejecutando migraciones de base de datos..."

    try {
        docker compose run --rm api alembic upgrade head
        Log-Success "Migraciones ejecutadas"
    }
    catch {
        Log-Warning "Error ejecutando migraciones. Continuando..."
    }

    # 10. Ejecutar script de setup
    Log-Info "10. Ejecutando script de inicialización..."

    if (Test-Path "scripts\setup.py") {
        try {
            docker compose run --rm api python scripts/setup.py
            Log-Success "Script de inicialización ejecutado"
        }
        catch {
            Log-Warning "Error ejecutando script de setup. Continuando..."
        }
    }
    else {
        Log-Warning "Script de setup no encontrado. Saltando inicialización."
    }

    # 11. Poblar datos de ejemplo
    Log-Info "11. Poblando datos de ejemplo..."

    if (Test-Path "scripts\populate_data.py") {
        try {
            docker compose run --rm api python scripts/populate_data.py
            Log-Success "Datos de ejemplo poblados"
        }
        catch {
            Log-Warning "Error poblando datos de ejemplo. Continuando..."
        }
    }
    else {
        Log-Warning "Script de datos de ejemplo no encontrado."
    }

    # 12. Iniciar todos los servicios
    Log-Info "12. Iniciando todos los servicios..."

    docker compose up -d

    # Esperar a que la API esté lista
    Log-Info "Esperando a que la API esté lista..."
    $retries = 0
    do {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
            $apiReady = $response.StatusCode -eq 200
        }
        catch {
            $apiReady = $false
            Start-Sleep 5
            $retries++
        }
    } while (!$apiReady -and $retries -lt 24)

    if (!$apiReady) {
        Log-Warning "API no está respondiendo después de 2 minutos. Verifica los logs."
    }

    Log-Success "Todos los servicios iniciados"

    # 13. Verificar instalación
    Log-Info "13. Verificando instalación..."

    Write-Host ""
    Write-Host "Estado de los servicios:"
    Write-Host "========================"

    # PostgreSQL
    try {
        docker compose exec postgres pg_isready -U sapisu_user -d sapisu_db | Out-Null
        Log-Success "PostgreSQL: ✅ Funcionando"
    }
    catch {
        Log-Error "PostgreSQL: ❌ Error"
    }

    # Qdrant
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6333/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Log-Success "Qdrant: ✅ Funcionando"
        }
        else {
            Log-Error "Qdrant: ❌ Error"
        }
    }
    catch {
        Log-Error "Qdrant: ❌ Error"
    }

    # Redis
    try {
        docker compose exec redis redis-cli ping | Out-Null
        Log-Success "Redis: ✅ Funcionando"
    }
    catch {
        Log-Error "Redis: ❌ Error"
    }

    # API
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Log-Success "API: ✅ Funcionando"
        }
        else {
            Log-Error "API: ❌ Error"
        }
    }
    catch {
        Log-Error "API: ❌ Error"
    }

    # Verificar contenedores
    $containers = docker compose ps --format "table {{.Service}}\t{{.Status}}"
    Write-Host ""
    Write-Host "Contenedores Docker:"
    Write-Host $containers
}

Write-Host ""

# 14. Crear script de mantenimiento para Windows
Log-Info "14. Creando script de mantenimiento..."

$maintenanceScript = @'
# Script de mantenimiento para Wiki Inteligente SAP IS-U (Windows)

param([string]$Action, [string]$Service = "")

function Show-Help {
    Write-Host "Uso: .\maintenance.ps1 <acción> [servicio]"
    Write-Host ""
    Write-Host "Acciones:"
    Write-Host "  start    - Iniciar servicios"
    Write-Host "  stop     - Detener servicios"
    Write-Host "  restart  - Reiniciar servicios"
    Write-Host "  logs     - Ver logs (especifica servicio opcional)"
    Write-Host "  backup   - Ejecutar backup manual"
    Write-Host "  restore  - Restaurar backup (requiere archivo)"
    Write-Host "  update   - Actualizar imágenes"
    Write-Host "  status   - Ver estado de servicios"
    Write-Host "  clean    - Limpiar sistema Docker"
}

switch ($Action) {
    "start" {
        Write-Host "Iniciando servicios..."
        docker compose up -d
    }
    "stop" {
        Write-Host "Deteniendo servicios..."
        docker compose down
    }
    "restart" {
        Write-Host "Reiniciando servicios..."
        docker compose down
        docker compose up -d
    }
    "logs" {
        if ($Service) {
            docker compose logs -f $Service
        } else {
            docker compose logs -f
        }
    }
    "backup" {
        Write-Host "Ejecutando backup..."
        docker compose exec api python scripts/backup.py
    }
    "restore" {
        if (!$Service) {
            Write-Host "Uso: .\maintenance.ps1 restore <archivo_backup>"
            exit 1
        }
        Write-Host "Restaurando desde $Service..."
        docker compose exec api python scripts/restore.py $Service
    }
    "update" {
        Write-Host "Actualizando imágenes..."
        docker compose pull
        docker compose up -d
    }
    "status" {
        Write-Host "Estado de servicios:"
        docker compose ps
    }
    "clean" {
        Write-Host "Limpiando contenedores e imágenes no utilizadas..."
        docker system prune -f
    }
    default {
        Show-Help
        exit 1
    }
}
'@

$maintenanceScript | Out-File -FilePath "maintenance.ps1" -Encoding UTF8

Log-Success "Script de mantenimiento creado (maintenance.ps1)"

# 15. Mostrar información de acceso
Log-Info "15. Información de acceso:"

Write-Host ""
Write-Host "=================================================================="
Write-Host "                    🎉 INSTALACIÓN COMPLETADA                    "
Write-Host "=================================================================="
Write-Host ""
Write-Host "📍 Servicios disponibles:"
Write-Host "   • Web Frontend:  http://localhost (o https://sapisu.local)"
Write-Host "   • API Backend:   http://localhost:8000"
Write-Host "   • API Docs:      http://localhost:8000/docs"
Write-Host "   • Qdrant UI:     http://localhost:6333/dashboard"
Write-Host "   • Traefik UI:    http://localhost:8080"
Write-Host ""
Write-Host "🔐 Credenciales por defecto:"
Write-Host "   • Email:    admin@sapisu.local"
Write-Host "   • Password: admin123"
Write-Host ""
Write-Host "📁 Directorios importantes:"
Write-Host "   • Logs:     $ProjectDir\logs\"
Write-Host "   • Data:     $ProjectDir\data\"
Write-Host "   • Backups:  $ProjectDir\data\backups\"
Write-Host ""
Write-Host "🔧 Comandos útiles:"
Write-Host "   • Ver logs:         docker compose logs -f"
Write-Host "   • Parar servicios:  docker compose down"
Write-Host "   • Reiniciar:        .\maintenance.ps1 restart"
Write-Host "   • Backup manual:    .\maintenance.ps1 backup"
Write-Host ""
Write-Host "📖 Próximos pasos:"
Write-Host "   1. Configurar tu API key de OpenAI en el archivo .env"
Write-Host "   2. Acceder al frontend en http://localhost"
Write-Host "   3. Subir documentos SAP IS-U iniciales"
Write-Host "   4. Configurar dominios personalizados si es necesario"
Write-Host ""

# 16. Verificación final de OpenAI
if (!$OpenAIKey -or $OpenAIKey -eq "" -or $OpenAIKey -eq "sk-your-openai-api-key-here") {
    Log-Warning "⚠️  IMPORTANTE: Configuración de OpenAI"
    Write-Host "=================================================================="
    Write-Host "Para que el sistema funcione completamente, necesitas:"
    Write-Host ""
    Write-Host "1. Obtener una API key de OpenAI en: https://platform.openai.com"
    Write-Host "2. Editar el archivo .env y reemplazar:"
    Write-Host "   OPENAI_API_KEY=sk-your-openai-api-key-here"
    Write-Host "   con tu API key real"
    Write-Host "3. Reiniciar los servicios: .\maintenance.ps1 restart"
    Write-Host ""
    Write-Host "Sin una API key válida, las funciones de embeddings y chat"
    Write-Host "no funcionarán correctamente."
    Write-Host "=================================================================="
}
else {
    Log-Success "✅ API key de OpenAI configurada"
}

Write-Host "=================================================================="

Log-Success "Instalación completa finalizada con éxito! 🎉"

# Mostrar siguiente comando sugerido
if (!$SkipDocker) {
    Write-Host ""
    Log-Info "Para ver los logs en tiempo real, ejecuta:"
    Write-Host "docker compose logs -f"
}
