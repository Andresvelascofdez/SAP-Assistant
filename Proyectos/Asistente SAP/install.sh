#!/bin/bash

# =============================================================================
# Script de Instalación Completa - Wiki Inteligente SAP IS-U
# =============================================================================

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para verificar comandos
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "Comando '$1' no encontrado. Por favor instálalo primero."
        return 1
    fi
    return 0
}

# Banner
echo "=================================================================="
echo "      🔍 Wiki Inteligente SAP IS-U - Instalación Completa      "
echo "=================================================================="
echo

# 1. Verificar prerrequisitos
log_info "1. Verificando prerrequisitos..."

# Verificar Git
if ! check_command git; then
    log_error "Git es requerido"
    exit 1
fi

# Verificar Docker
if ! check_command docker; then
    log_error "Docker es requerido"
    exit 1
fi

# Verificar Docker Compose
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose es requerido"
    exit 1
fi

# Verificar Python
if ! check_command python3; then
    log_error "Python 3 es requerido"
    exit 1
fi

# Verificar pip
if ! check_command pip3; then
    log_error "pip3 es requerido"
    exit 1
fi

log_success "Prerrequisitos verificados"

# 2. Configurar variables de entorno
log_info "2. Configurando variables de entorno..."

# Directorio base
PROJECT_DIR="$(pwd)"
ENV_FILE="$PROJECT_DIR/.env"

# Crear archivo .env si no existe
if [ ! -f "$ENV_FILE" ]; then
    log_info "Creando archivo .env..."
    cat > "$ENV_FILE" << EOF
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
DATABASE_URL=postgresql://sapisu_user:$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)@postgres:5432/sapisu_db
POSTGRES_DB=sapisu_db
POSTGRES_USER=sapisu_user
POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Qdrant Configuration
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
QDRANT_COLLECTION=sapisu_embeddings

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-3.5-turbo

# Security
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
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
EOF

    log_success "Archivo .env creado con configuración segura"
else
    log_warning "Archivo .env ya existe. Usando configuración existente."
fi

# 3. Crear estructura de directorios
log_info "3. Creando estructura de directorios..."

mkdir -p {data/{postgres,qdrant,backups},logs/{api,scheduler,traefik},ssl,config}

log_success "Estructura de directorios creada"

# 4. Instalar dependencias de Python
log_info "4. Instalando dependencias de Python..."

if [ -f "requirements.txt" ]; then
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        log_info "Creando entorno virtual..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Actualizar pip
    pip install --upgrade pip
    
    # Instalar dependencias
    pip install -r requirements.txt
    
    log_success "Dependencias de Python instaladas"
else
    log_warning "requirements.txt no encontrado. Saltando instalación de dependencias Python."
fi

# 5. Configurar base de datos
log_info "5. Configurando base de datos..."

# Generar migraciones si no existen
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    log_info "Generando migraciones de base de datos..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Inicializar Alembic si no está configurado
    if [ ! -f "alembic.ini" ]; then
        alembic init alembic
    fi
    
    # Crear migración inicial
    alembic revision --autogenerate -m "Migración inicial"
fi

log_success "Base de datos configurada"

# 6. Construir imágenes Docker
log_info "6. Construyendo imágenes Docker..."

# Construir imagen de la API
log_info "Construyendo imagen de la API..."
docker build -t sapisu-api:latest -f docker/Dockerfile.api .

# Construir imagen del scheduler
log_info "Construyendo imagen del scheduler..."
docker build -t sapisu-scheduler:latest -f docker/Dockerfile.scheduler .

# Construir imagen de Nginx (si existe)
if [ -f "docker/Dockerfile.nginx" ]; then
    log_info "Construyendo imagen de Nginx..."
    docker build -t sapisu-nginx:latest -f docker/Dockerfile.nginx .
fi

log_success "Imágenes Docker construidas"

# 7. Configurar SSL/TLS
log_info "7. Configurando SSL/TLS..."

# Crear certificados auto-firmados para desarrollo
if [ ! -f "ssl/sapisu.crt" ]; then
    log_info "Generando certificados SSL auto-firmados..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/sapisu.key \
        -out ssl/sapisu.crt \
        -subj "/C=ES/ST=Madrid/L=Madrid/O=SAP ISU Wiki/CN=sapisu.local"
    
    log_success "Certificados SSL generados"
fi

# 8. Inicializar servicios
log_info "8. Inicializando servicios..."

# Levantar servicios de infraestructura primero
log_info "Iniciando servicios de infraestructura (PostgreSQL, Qdrant, Redis)..."
docker compose up -d postgres qdrant redis

# Esperar a que los servicios estén listos
log_info "Esperando a que los servicios estén listos..."
sleep 30

# Verificar que PostgreSQL esté listo
log_info "Verificando PostgreSQL..."
until docker compose exec postgres pg_isready -U sapisu_user -d sapisu_db; do
    log_info "Esperando PostgreSQL..."
    sleep 5
done

# Verificar que Qdrant esté listo
log_info "Verificando Qdrant..."
until curl -f http://localhost:6333/health > /dev/null 2>&1; do
    log_info "Esperando Qdrant..."
    sleep 5
done

log_success "Servicios de infraestructura iniciados"

# 9. Ejecutar migraciones
log_info "9. Ejecutando migraciones de base de datos..."

# Ejecutar migraciones a través del contenedor
docker compose run --rm api alembic upgrade head

log_success "Migraciones ejecutadas"

# 10. Ejecutar script de setup
log_info "10. Ejecutando script de inicialización..."

if [ -f "scripts/setup.py" ]; then
    docker compose run --rm api python scripts/setup.py
    log_success "Script de inicialización ejecutado"
else
    log_warning "Script de setup no encontrado. Saltando inicialización."
fi

# 11. Poblar datos de ejemplo
log_info "11. Poblando datos de ejemplo..."

if [ -f "scripts/populate_data.py" ]; then
    docker compose run --rm api python scripts/populate_data.py
    log_success "Datos de ejemplo poblados"
else
    log_warning "Script de datos de ejemplo no encontrado."
fi

# 12. Iniciar todos los servicios
log_info "12. Iniciando todos los servicios..."

docker compose up -d

# Esperar a que la API esté lista
log_info "Esperando a que la API esté lista..."
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    log_info "Esperando API..."
    sleep 5
done

log_success "Todos los servicios iniciados"

# 13. Verificar instalación
log_info "13. Verificando instalación..."

# Verificar salud de servicios
echo
echo "Estado de los servicios:"
echo "========================"

# PostgreSQL
if docker compose exec postgres pg_isready -U sapisu_user -d sapisu_db > /dev/null 2>&1; then
    log_success "PostgreSQL: ✅ Funcionando"
else
    log_error "PostgreSQL: ❌ Error"
fi

# Qdrant
if curl -f http://localhost:6333/health > /dev/null 2>&1; then
    log_success "Qdrant: ✅ Funcionando"
else
    log_error "Qdrant: ❌ Error"
fi

# Redis
if docker compose exec redis redis-cli ping > /dev/null 2>&1; then
    log_success "Redis: ✅ Funcionando"
else
    log_error "Redis: ❌ Error"
fi

# API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log_success "API: ✅ Funcionando"
else
    log_error "API: ❌ Error"
fi

# Scheduler
if docker compose ps scheduler | grep -q "Up"; then
    log_success "Scheduler: ✅ Funcionando"
else
    log_error "Scheduler: ❌ Error"
fi

# Traefik
if docker compose ps traefik | grep -q "Up"; then
    log_success "Traefik: ✅ Funcionando"
else
    log_error "Traefik: ❌ Error"
fi

echo

# 14. Mostrar información de acceso
log_info "14. Información de acceso:"

echo
echo "=================================================================="
echo "                    🎉 INSTALACIÓN COMPLETADA                    "
echo "=================================================================="
echo
echo "📍 Servicios disponibles:"
echo "   • Web Frontend:  http://localhost (o https://sapisu.local)"
echo "   • API Backend:   http://localhost:8000"
echo "   • API Docs:      http://localhost:8000/docs"
echo "   • Qdrant UI:     http://localhost:6333/dashboard"
echo "   • Traefik UI:    http://localhost:8080"
echo
echo "🔐 Credenciales por defecto:"
echo "   • Email:    admin@sapisu.local"
echo "   • Password: admin123"
echo
echo "📁 Directorios importantes:"
echo "   • Logs:     $PROJECT_DIR/logs/"
echo "   • Data:     $PROJECT_DIR/data/"
echo "   • Backups:  $PROJECT_DIR/data/backups/"
echo
echo "🔧 Comandos útiles:"
echo "   • Ver logs:         docker compose logs -f"
echo "   • Parar servicios:  docker compose down"
echo "   • Reiniciar:        docker compose restart"
echo "   • Backup manual:    docker compose exec api python scripts/backup.py"
echo
echo "📖 Próximos pasos:"
echo "   1. Configurar tu API key de OpenAI en el archivo .env"
echo "   2. Acceder al frontend en http://localhost"
echo "   3. Subir documentos SAP IS-U iniciales"
echo "   4. Configurar dominios personalizados si es necesario"
echo
echo "=================================================================="

# 15. Crear script de mantenimiento
log_info "15. Creando script de mantenimiento..."

cat > "maintenance.sh" << 'EOF'
#!/bin/bash

# Script de mantenimiento para Wiki Inteligente SAP IS-U

case "$1" in
    start)
        echo "Iniciando servicios..."
        docker compose up -d
        ;;
    stop)
        echo "Deteniendo servicios..."
        docker compose down
        ;;
    restart)
        echo "Reiniciando servicios..."
        docker compose down && docker compose up -d
        ;;
    logs)
        docker compose logs -f ${2:-}
        ;;
    backup)
        echo "Ejecutando backup..."
        docker compose exec api python scripts/backup.py
        ;;
    restore)
        if [ -z "$2" ]; then
            echo "Uso: ./maintenance.sh restore <archivo_backup>"
            exit 1
        fi
        echo "Restaurando desde $2..."
        docker compose exec api python scripts/restore.py "$2"
        ;;
    update)
        echo "Actualizando imágenes..."
        docker compose pull
        docker compose up -d
        ;;
    status)
        echo "Estado de servicios:"
        docker compose ps
        ;;
    clean)
        echo "Limpiando contenedores e imágenes no utilizadas..."
        docker system prune -f
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|logs|backup|restore|update|status|clean}"
        echo
        echo "Comandos:"
        echo "  start    - Iniciar servicios"
        echo "  stop     - Detener servicios"
        echo "  restart  - Reiniciar servicios"
        echo "  logs     - Ver logs (logs <servicio> para uno específico)"
        echo "  backup   - Ejecutar backup manual"
        echo "  restore  - Restaurar backup"
        echo "  update   - Actualizar imágenes"
        echo "  status   - Ver estado de servicios"
        echo "  clean    - Limpiar sistema Docker"
        exit 1
        ;;
esac
EOF

chmod +x maintenance.sh

log_success "Script de mantenimiento creado (./maintenance.sh)"

# 16. Verificación final de OpenAI
echo
log_warning "⚠️  IMPORTANTE: Configuración de OpenAI"
echo "=================================================================="
echo "Para que el sistema funcione completamente, necesitas:"
echo
echo "1. Obtener una API key de OpenAI en: https://platform.openai.com"
echo "2. Editar el archivo .env y reemplazar:"
echo "   OPENAI_API_KEY=sk-your-openai-api-key-here"
echo "   con tu API key real"
echo "3. Reiniciar los servicios: ./maintenance.sh restart"
echo
echo "Sin una API key válida, las funciones de embeddings y chat"
echo "no funcionarán correctamente."
echo "=================================================================="

log_success "Instalación completa finalizada con éxito! 🎉"

exit 0
