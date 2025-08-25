#!/bin/bash
set -e

# SAP IS-U Smart Wiki - Startup Script
# Autor: SAP IS-U Smart Wiki Team
# Versión: 1.1.0
# Fecha: 2025-08-26

# Configuración de colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Variables globales
FASTAPI_PID=""
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Función para mostrar mensajes con color
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Banner de inicio
show_banner() {
    print_color $CYAN "========================================="
    print_color $CYAN "🔍 SAP IS-U Smart Wiki - Startup Script"
    print_color $CYAN "========================================="
    print_color $GRAY "Versión: 1.1.0"
    print_color $GRAY "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# Detener servicios existentes
stop_existing_services() {
    print_color $YELLOW "🛑 Deteniendo servicios existentes..."
    
    # Matar procesos Python/uvicorn
    print_color $GRAY "   - Deteniendo procesos Python..."
    pkill -f "uvicorn\|fastapi\|python.*api" 2>/dev/null || true
    sleep 2
    
    # Detener contenedores Docker
    print_color $GRAY "   - Deteniendo contenedores Docker..."
    cd "$PROJECT_DIR"
    docker-compose down --remove-orphans 2>/dev/null || true
    sleep 3
    
    print_color $GREEN "✅ Servicios detenidos correctamente"
    echo ""
}

# Verificar prerequisitos
test_prerequisites() {
    print_color $YELLOW "🔍 Verificando prerequisitos..."
    
    local errors=()
    
    # Verificar Docker
    if command -v docker &> /dev/null; then
        local docker_version=$(docker --version)
        print_color $GREEN "   ✅ Docker: $docker_version"
    else
        errors+=("Docker no está instalado o no está en PATH")
    fi
    
    # Verificar Docker Compose
    if command -v docker-compose &> /dev/null; then
        local compose_version=$(docker-compose --version)
        print_color $GREEN "   ✅ Docker Compose: $compose_version"
    else
        errors+=("Docker Compose no está instalado")
    fi
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version)
        print_color $GREEN "   ✅ Python: $python_version"
    elif command -v python &> /dev/null; then
        local python_version=$(python --version)
        print_color $GREEN "   ✅ Python: $python_version"
    else
        errors+=("Python no está instalado o no está en PATH")
    fi
    
    # Verificar archivo .env
    if [[ -f ".env" ]]; then
        print_color $GREEN "   ✅ Archivo .env encontrado"
        
        # Verificar API Key de OpenAI
        if grep -q "OPENAI_API_KEY=sk-" ".env"; then
            print_color $GREEN "   ✅ API Key de OpenAI configurada"
        else
            errors+=("API Key de OpenAI no está configurada en .env")
        fi
    else
        errors+=("Archivo .env no encontrado. Ejecuta: cp .env.example .env")
    fi
    
    # Mostrar errores si los hay
    if [[ ${#errors[@]} -gt 0 ]]; then
        echo ""
        print_color $RED "❌ Errores encontrados:"
        for error in "${errors[@]}"; do
            print_color $RED "   - $error"
        done
        echo ""
        print_color $RED "Por favor, corrige estos errores antes de continuar."
        exit 1
    fi
    
    print_color $GREEN "✅ Todos los prerequisitos están satisfechos"
    echo ""
}

# Iniciar servicios Docker
start_docker_services() {
    print_color $YELLOW "🐳 Iniciando servicios Docker..."
    
    # Iniciar Docker Compose
    print_color $GRAY "   - Iniciando PostgreSQL y Qdrant..."
    cd "$PROJECT_DIR"
    
    if docker-compose up -d postgres qdrant 2>/dev/null; then
        print_color $GREEN "   ✅ Contenedores Docker iniciados"
    else
        print_color $RED "   ❌ Error iniciando contenedores Docker"
        exit 1
    fi
    
    # Esperar a que los servicios estén listos
    print_color $GRAY "   - Esperando que los servicios estén listos..."
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        ((attempt++))
        sleep 2
        
        # Verificar PostgreSQL
        local pg_ready=false
        if docker exec sapisu_postgres pg_isready -U postgres &>/dev/null; then
            pg_ready=true
        fi
        
        # Verificar Qdrant
        local qdrant_ready=false
        if curl -s "http://localhost:6333" &>/dev/null; then
            qdrant_ready=true
        fi
        
        if [[ $pg_ready == true && $qdrant_ready == true ]]; then
            print_color $GREEN "   ✅ PostgreSQL y Qdrant están listos"
            break
        fi
        
        print_color $GRAY "   - Intento $attempt/$max_attempts - Esperando servicios..."
    done
    
    if [[ $attempt -ge $max_attempts ]]; then
        print_color $RED "   ❌ Timeout esperando que los servicios estén listos"
        print_color $YELLOW "   - Verificar logs con: docker-compose logs"
        exit 1
    fi
    
    echo ""
}

# Configurar entorno Python
setup_python_environment() {
    print_color $YELLOW "🐍 Configurando entorno Python..."
    
    cd "$PROJECT_DIR"
    
    # Verificar/crear entorno virtual
    if [[ ! -d "venv" ]]; then
        print_color $GRAY "   - Creando entorno virtual..."
        if command -v python3 &> /dev/null; then
            python3 -m venv venv
        else
            python -m venv venv
        fi
        
        if [[ $? -ne 0 ]]; then
            print_color $RED "   ❌ Error creando entorno virtual"
            exit 1
        fi
    fi
    
    # Activar entorno virtual
    print_color $GRAY "   - Activando entorno virtual..."
    source venv/bin/activate
    
    # Verificar e instalar dependencias
    print_color $GRAY "   - Verificando dependencias..."
    if ! pip list 2>/dev/null | grep -q "fastapi\|openai"; then
        print_color $GRAY "   - Instalando dependencias..."
        pip install -r requirements.txt --quiet
        
        if [[ $? -ne 0 ]]; then
            print_color $RED "   ❌ Error instalando dependencias"
            exit 1
        fi
    fi
    
    print_color $GREEN "   ✅ Entorno Python configurado"
    echo ""
}

# Iniciar servidor FastAPI
start_fastapi_server() {
    print_color $YELLOW "🚀 Iniciando servidor FastAPI..."
    
    cd "$PROJECT_DIR"
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Iniciar servidor en background
    print_color $GRAY "   - Lanzando uvicorn en segundo plano..."
    nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
    FASTAPI_PID=$!
    
    # Esperar a que el servidor esté listo
    print_color $GRAY "   - Esperando que el servidor esté listo..."
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        ((attempt++))
        sleep 2
        
        if curl -s "http://localhost:8000/health" &>/dev/null; then
            print_color $GREEN "   ✅ Servidor FastAPI está ejecutándose (PID: $FASTAPI_PID)"
            break
        fi
        
        # Verificar si el proceso sigue ejecutándose
        if ! kill -0 $FASTAPI_PID 2>/dev/null; then
            print_color $RED "   ❌ El servidor FastAPI se detuvo inesperadamente"
            print_color $GRAY "   - Verificar logs en: fastapi.log"
            exit 1
        fi
        
        print_color $GRAY "   - Intento $attempt/$max_attempts - Esperando servidor..."
    done
    
    if [[ $attempt -ge $max_attempts ]]; then
        print_color $RED "   ❌ Timeout esperando el servidor FastAPI"
        kill $FASTAPI_PID 2>/dev/null || true
        exit 1
    fi
    
    echo ""
}

# Verificar servicios
test_services() {
    print_color $YELLOW "🧪 Verificando servicios..."
    
    # Test de salud general
    if curl -s "http://localhost:8000/health" | grep -q "healthy"; then
        print_color $GREEN "   ✅ API Health Check: OK"
    else
        print_color $RED "   ❌ API Health Check: FAILED"
    fi
    
    # Test de chat
    local chat_data='{"query": "test", "tenant_slug": "default"}'
    if curl -s -X POST "http://localhost:8000/api/v1/search/chat-public" \
            -H "Content-Type: application/json" \
            -d "$chat_data" \
            --max-time 15 &>/dev/null; then
        print_color $GREEN "   ✅ Chat Endpoint: OK"
    else
        print_color $RED "   ❌ Chat Endpoint: FAILED"
    fi
    
    echo ""
}

# Mostrar estado de servicios
show_service_status() {
    print_color $CYAN "📊 Estado de los servicios:"
    echo ""
    
    # PostgreSQL
    if docker exec sapisu_postgres pg_isready -U postgres &>/dev/null; then
        print_color $GREEN "   🟢 PostgreSQL: Running (puerto 5432)"
    else
        print_color $RED "   🔴 PostgreSQL: Not Running"
    fi
    
    # Qdrant
    if curl -s "http://localhost:6333" &>/dev/null; then
        print_color $GREEN "   🟢 Qdrant: Running (puerto 6333)"
    else
        print_color $RED "   🔴 Qdrant: Not Running"
    fi
    
    # FastAPI
    if curl -s "http://localhost:8000/health" &>/dev/null; then
        print_color $GREEN "   🟢 FastAPI: Running (puerto 8000)"
    else
        print_color $RED "   🔴 FastAPI: Not Running"
    fi
    
    echo ""
}

# Mostrar información de acceso
show_access_information() {
    print_color $CYAN "🌐 URLs de acceso:"
    echo ""
    echo -e "   📱 Interfaz Principal:  ${YELLOW}http://localhost:8000${NC}"
    echo -e "   📚 Documentación API:   ${YELLOW}http://localhost:8000/docs${NC}"
    echo -e "   ❤️  Health Check:       ${YELLOW}http://localhost:8000/health${NC}"
    print_color $GRAY "   🐘 PostgreSQL:         localhost:5432"
    print_color $GRAY "   🔍 Qdrant:             http://localhost:6333"
    echo ""
    
    print_color $CYAN "🎯 Para usar la herramienta:"
    echo -e "   1. Abre tu navegador web"
    echo -e "   2. Navega a: ${YELLOW}http://localhost:8000${NC}"
    print_color $GREEN "   3. ¡Comienza a chatear con el asistente SAP IS-U!"
    print_color $GREEN "   4. Usa '💾 Guardar Incidencia' para almacenar conocimiento"
    echo ""
}

# Abrir navegador
start_browser() {
    print_color $YELLOW "🌐 Abriendo navegador..."
    
    local url="http://localhost:8000"
    
    # Detectar el comando para abrir navegador según el OS
    if command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "$url" 2>/dev/null &
    elif command -v open &> /dev/null; then
        # macOS
        open "$url" 2>/dev/null &
    elif command -v start &> /dev/null; then
        # Windows (Git Bash)
        start "$url" 2>/dev/null &
    else
        print_color $YELLOW "   ⚠️ No se pudo abrir el navegador automáticamente"
        print_color $YELLOW "   Por favor, abre manualmente: $url"
        return
    fi
    
    print_color $GREEN "   ✅ Navegador abierto automáticamente"
    echo ""
}

# Mostrar instrucciones para detener
show_stop_instructions() {
    print_color $CYAN "🛑 Para detener todos los servicios:"
    echo -e "   - Presiona ${YELLOW}Ctrl+C${NC} en esta ventana"
    echo -e "   - O ejecuta: ${YELLOW}docker-compose down${NC}"
    echo ""
}

# Función de limpieza
cleanup() {
    print_color $YELLOW "🧹 Limpiando recursos..."
    
    # Matar proceso FastAPI
    if [[ -n "$FASTAPI_PID" ]]; then
        kill $FASTAPI_PID 2>/dev/null || true
        wait $FASTAPI_PID 2>/dev/null || true
    fi
    
    # Detener contenedores Docker
    cd "$PROJECT_DIR"
    docker-compose down --remove-orphans 2>/dev/null || true
    
    print_color $GREEN "✅ Limpieza completada"
    exit 0
}

# Configurar señales para limpieza
trap cleanup SIGINT SIGTERM EXIT

# === EJECUCIÓN PRINCIPAL ===

main() {
    show_banner
    stop_existing_services
    test_prerequisites
    start_docker_services
    setup_python_environment
    start_fastapi_server
    test_services
    show_service_status
    show_access_information
    start_browser
    show_stop_instructions
    
    print_color $GREEN "🎉 ¡SAP IS-U Smart Wiki está listo para usar!"
    print_color $GRAY "   Presiona Ctrl+C para detener todos los servicios"
    echo ""
    
    # Mantener el script ejecutándose
    while true; do
        sleep 30
        
        # Verificar que FastAPI sigue ejecutándose
        if [[ -n "$FASTAPI_PID" ]] && ! kill -0 $FASTAPI_PID 2>/dev/null; then
            print_color $YELLOW "⚠️ El servidor FastAPI se detuvo inesperadamente"
            break
        fi
    done
}

# Ejecutar función principal
main "$@"
