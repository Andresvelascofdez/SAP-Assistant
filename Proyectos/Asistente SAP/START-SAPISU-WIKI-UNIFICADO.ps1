# SAP IS-U Smart Wiki - Script Unificado de Instalacion y Ejecucion
# Incluye todas las correcciones probadas que funcionan

param(
    [int]$Port = 8000,
    [switch]$SkipInstall,
    [switch]$OpenBrowser
)

# Configurar politica de ejecucion
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Funcion para mostrar mensajes con color
function Write-Message {
    param([string]$Text, [string]$Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Text" -ForegroundColor $Color
}

Clear-Host
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "           SAP IS-U SMART WIKI - SCRIPT UNIFICADO              " -ForegroundColor Cyan
Write-Host "              Instalacion + Ejecucion Completa                 " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_PATH = Join-Path $SCRIPT_DIR "venv"
$API_PATH = Join-Path $SCRIPT_DIR "api"

try {
    # 1. VERIFICAR PRERREQUISITOS
    Write-Message "Verificando prerrequisitos..." "Yellow"
    
    # Verificar Python
    try {
        $pythonVersion = & python --version 2>&1
        Write-Message "Python encontrado: $pythonVersion" "Green"
    } catch {
        Write-Message "ERROR: Python no encontrado. Instala Python 3.8+ desde python.org" "Red"
        exit 1
    }
    
    # Verificar Docker
    try {
        $dockerVersion = & docker --version 2>&1
        Write-Message "Docker encontrado: $dockerVersion" "Green"
    } catch {
        Write-Message "ERROR: Docker no encontrado. Instala Docker Desktop" "Red"
        exit 1
    }

    # 2. LIMPIAR SERVICIOS EXISTENTES
    Write-Message "Limpiando servicios existentes..." "Yellow"
    
    # Detener procesos Python/FastAPI
    try {
        Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Message "Procesos Python detenidos" "Green"
    } catch {}
    
    # Detener contenedores Docker
    try {
        $containers = & docker ps -q 2>$null
        if ($containers) {
            & docker stop $containers 2>$null | Out-Null
            Write-Message "Contenedores Docker detenidos" "Green"
        }
    } catch {}

    # 3. CONFIGURAR ENTORNO PYTHON
    if (-not $SkipInstall) {
        Write-Message "Configurando entorno Python..." "Yellow"
        
        # Crear entorno virtual si no existe
        if (-not (Test-Path $VENV_PATH)) {
            Write-Message "Creando entorno virtual..." "Cyan"
            & python -m venv $VENV_PATH
        }
        
        # Activar entorno virtual
        $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
        & $activateScript
        Write-Message "Entorno virtual activado" "Green"
        
        # Instalar dependencias principales
        Write-Message "Instalando dependencias principales..." "Cyan"
        & pip install --upgrade pip --quiet
        & pip install fastapi uvicorn --quiet
        
        # Instalar todas las dependencias del proyecto
        if (Test-Path "requirements.txt") {
            Write-Message "Instalando dependencias del proyecto..." "Cyan"
            & pip install -r requirements.txt --quiet
        }
        
        # Instalar email-validator (requerido)
        Write-Message "Instalando email-validator..." "Cyan"
        & pip install email-validator --quiet
        
        Write-Message "Dependencias instaladas correctamente" "Green"
    } else {
        # Solo activar entorno existente
        $activateScript = Join-Path $VENV_PATH "Scripts\Activate.ps1"
        & $activateScript
        Write-Message "Entorno virtual activado (saltando instalacion)" "Green"
    }

    # 4. CORREGIR IMPORTACIONES SI ES NECESARIO
    if (-not $SkipInstall) {
        Write-Message "Corrigiendo importaciones Python..." "Yellow"
        
        Set-Location $API_PATH
        
        # Script para corregir importaciones relativas
        $fixScript = @"
import os
import re

def fix_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Cambiar importaciones relativas a absolutas
                content = re.sub(r'from \.\.', 'from ', content)
                content = re.sub(r'from \.', 'from ', content)
                content = re.sub(r'from api\.', 'from ', content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

fix_imports('.')
print('Importaciones corregidas')
"@
        
        $fixScript | & python
        Write-Message "Importaciones corregidas" "Green"
        
        Set-Location $SCRIPT_DIR
    }

    # 5. INICIAR SERVICIOS DOCKER
    Write-Message "Iniciando servicios Docker..." "Yellow"
    
    # Usar docker-compose simplificado
    if (Test-Path "docker-compose-simple.yml") {
        & docker-compose -f docker-compose-simple.yml up -d
    } else {
        & docker-compose up -d
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Message "ERROR: Fallo al iniciar servicios Docker" "Red"
        exit 1
    }
    
    Write-Message "PostgreSQL y Qdrant iniciados" "Green"

    # 6. ESPERAR SERVICIOS
    Write-Message "Esperando que los servicios esten listos..." "Yellow"
    Start-Sleep -Seconds 10
    
    # Verificar Qdrant
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:6333" -TimeoutSec 5 -ErrorAction Stop
        Write-Message "Qdrant listo en puerto 6333" "Green"
    } catch {
        Write-Message "Advertencia: Qdrant puede tardar en estar listo" "Yellow"
    }

    # 7. ACTUALIZAR CONFIGURACION .ENV
    Write-Message "Verificando configuracion .env..." "Yellow"
    
    if (Test-Path ".env") {
        # Leer contenido actual
        $envContent = Get-Content ".env" -Raw
        
        # Asegurar que las credenciales coincidan con docker-compose-simple.yml
        if ($envContent -notmatch "sapisu_user:sapisu_password") {
            $envContent = $envContent -replace "postgres:changeme", "sapisu_user:sapisu_password"
            $envContent = $envContent -replace "/sapisu", "/sapisu_wiki"
            $envContent | Set-Content ".env" -NoNewline
            Write-Message "Configuracion .env actualizada" "Green"
        }
    }

    # 8. INICIAR SERVIDOR FASTAPI
    Write-Message "Iniciando servidor FastAPI..." "Yellow"
    
    Set-Location $API_PATH
    $env:PYTHONPATH = (Get-Location).Path
    
    # Mostrar informacion final
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Message "SERVIDOR SAP IS-U SMART WIKI INICIADO" "Green"
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Message "Aplicacion Web: http://localhost:$Port" "Green"
    Write-Message "Documentacion API: http://localhost:$Port/docs" "Green"
    Write-Message "Chat Publico: http://localhost:$Port/api/v1/search/chat-public" "Green"
    Write-Message "Qdrant Dashboard: http://localhost:6333/dashboard" "Green"
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Message "Presiona Ctrl+C para detener el servidor" "Yellow"
    Write-Host ""
    
    # Abrir navegador si se solicita
    if ($OpenBrowser) {
        Start-Sleep -Seconds 3
        Start-Process "http://localhost:$Port"
    }
    
    # Iniciar servidor FastAPI
    & uvicorn main:app --host 0.0.0.0 --port $Port --reload

} catch {
    Write-Message "ERROR: $($_.Exception.Message)" "Red"
    exit 1
} finally {
    Write-Host ""
    Write-Message "Limpiando servicios..." "Yellow"
    try {
        Set-Location $SCRIPT_DIR
        if (Test-Path "docker-compose-simple.yml") {
            & docker-compose -f docker-compose-simple.yml down 2>$null
        } else {
            & docker-compose down 2>$null
        }
        Write-Message "Servicios Docker detenidos" "Green"
    } catch {
        Write-Message "Error al limpiar servicios" "Yellow"
    }
}
