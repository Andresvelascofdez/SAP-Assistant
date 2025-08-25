#!/usr/bin/env powershell
<#
.SYNOPSIS
    SAP IS-U Smart Wiki - Startup Script
    
.DESCRIPTION
    Script completo para iniciar todos los servicios necesarios del SAP IS-U Smart Wiki.
    Mata procesos existentes, inicia Docker, configura el entorno y lanza la aplicación.
    
.EXAMPLE
    .\start-sapisu-wiki.ps1
    
.NOTES
    Autor: SAP IS-U Smart Wiki Team
    Versión: 1.1.0
    Fecha: 2025-08-26
#>

# Configuración de colores para output
$Host.UI.RawUI.ForegroundColor = "White"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    $currentColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Host $Message
    $Host.UI.RawUI.ForegroundColor = $currentColor
}

function Show-Banner {
    Write-ColorOutput "=========================================" "Cyan"
    Write-ColorOutput "🔍 SAP IS-U Smart Wiki - Startup Script" "Cyan"
    Write-ColorOutput "=========================================" "Cyan"
    Write-ColorOutput "Versión: 1.1.0" "Gray"
    Write-ColorOutput "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    Write-ColorOutput "" "White"
}

function Stop-ExistingServices {
    Write-ColorOutput "🛑 Deteniendo servicios existentes..." "Yellow"
    
    # Matar procesos Python (FastAPI)
    try {
        $pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
        if ($pythonProcesses) {
            Write-ColorOutput "   - Deteniendo procesos Python..." "Gray"
            $pythonProcesses | Stop-Process -Force
            Start-Sleep -Seconds 2
        }
    }
    catch {
        Write-ColorOutput "   - No hay procesos Python ejecutándose" "Gray"
    }
    
    # Matar procesos uvicorn
    try {
        $uvicornProcesses = Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.CommandLine -like "*uvicorn*" }
        if ($uvicornProcesses) {
            Write-ColorOutput "   - Deteniendo procesos Uvicorn..." "Gray"
            $uvicornProcesses | Stop-Process -Force
        }
    }
    catch {
        Write-ColorOutput "   - No hay procesos Uvicorn ejecutándose" "Gray"
    }
    
    # Detener contenedores Docker existentes
    Write-ColorOutput "   - Deteniendo contenedores Docker..." "Gray"
    try {
        docker-compose down --remove-orphans 2>$null
        Start-Sleep -Seconds 3
    }
    catch {
        Write-ColorOutput "   - Error al detener Docker Compose (puede ser normal)" "Gray"
    }
    
    Write-ColorOutput "✅ Servicios detenidos correctamente" "Green"
    Write-ColorOutput "" "White"
}

function Test-Prerequisites {
    Write-ColorOutput "🔍 Verificando prerequisitos..." "Yellow"
    
    $errors = @()
    
    # Verificar Docker
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-ColorOutput "   ✅ Docker: $dockerVersion" "Green"
        } else {
            $errors += "Docker no está instalado o no está en PATH"
        }
    }
    catch {
        $errors += "Docker no está disponible"
    }
    
    # Verificar Docker Compose
    try {
        $composeVersion = docker-compose --version 2>$null
        if ($composeVersion) {
            Write-ColorOutput "   ✅ Docker Compose: $composeVersion" "Green"
        } else {
            $errors += "Docker Compose no está instalado"
        }
    }
    catch {
        $errors += "Docker Compose no está disponible"
    }
    
    # Verificar Python
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion) {
            Write-ColorOutput "   ✅ Python: $pythonVersion" "Green"
        } else {
            $errors += "Python no está instalado o no está en PATH"
        }
    }
    catch {
        $errors += "Python no está disponible"
    }
    
    # Verificar archivo .env
    if (Test-Path ".env") {
        Write-ColorOutput "   ✅ Archivo .env encontrado" "Green"
        
        # Verificar API Key de OpenAI
        $envContent = Get-Content ".env" -Raw
        if ($envContent -match "OPENAI_API_KEY=sk-") {
            Write-ColorOutput "   ✅ API Key de OpenAI configurada" "Green"
        } else {
            $errors += "API Key de OpenAI no está configurada en .env"
        }
    } else {
        $errors += "Archivo .env no encontrado. Ejecuta: cp .env.example .env"
    }
    
    if ($errors.Count -gt 0) {
        Write-ColorOutput "" "White"
        Write-ColorOutput "❌ Errores encontrados:" "Red"
        foreach ($error in $errors) {
            Write-ColorOutput "   - $error" "Red"
        }
        Write-ColorOutput "" "White"
        Write-ColorOutput "Por favor, corrige estos errores antes de continuar." "Red"
        exit 1
    }
    
    Write-ColorOutput "✅ Todos los prerequisitos están satisfechos" "Green"
    Write-ColorOutput "" "White"
}

function Start-DockerServices {
    Write-ColorOutput "🐳 Iniciando servicios Docker..." "Yellow"
    
    # Iniciar Docker Compose
    Write-ColorOutput "   - Iniciando PostgreSQL y Qdrant..." "Gray"
    try {
        docker-compose up -d postgres qdrant 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "   ✅ Contenedores Docker iniciados" "Green"
        } else {
            Write-ColorOutput "   ❌ Error iniciando contenedores Docker" "Red"
            exit 1
        }
    }
    catch {
        Write-ColorOutput "   ❌ Error ejecutando docker-compose" "Red"
        exit 1
    }
    
    # Esperar a que los servicios estén listos
    Write-ColorOutput "   - Esperando que los servicios estén listos..." "Gray"
    $maxAttempts = 30
    $attempt = 0
    
    do {
        $attempt++
        Start-Sleep -Seconds 2
        
        # Verificar PostgreSQL
        $pgReady = $false
        try {
            $pgStatus = docker exec sapisu_postgres pg_isready -U postgres 2>$null
            $pgReady = ($LASTEXITCODE -eq 0)
        }
        catch { }
        
        # Verificar Qdrant
        $qdrantReady = $false
        try {
            $qdrantResponse = Invoke-WebRequest -Uri "http://localhost:6333" -TimeoutSec 5 -ErrorAction SilentlyContinue
            $qdrantReady = ($qdrantResponse.StatusCode -eq 200)
        }
        catch { }
        
        if ($pgReady -and $qdrantReady) {
            Write-ColorOutput "   ✅ PostgreSQL y Qdrant están listos" "Green"
            break
        }
        
        Write-ColorOutput "   - Intento $attempt/$maxAttempts - Esperando servicios..." "Gray"
        
    } while ($attempt -lt $maxAttempts)
    
    if ($attempt -ge $maxAttempts) {
        Write-ColorOutput "   ❌ Timeout esperando que los servicios estén listos" "Red"
        Write-ColorOutput "   - Verificar logs con: docker-compose logs" "Yellow"
        exit 1
    }
    
    Write-ColorOutput "" "White"
}

function Setup-PythonEnvironment {
    Write-ColorOutput "🐍 Configurando entorno Python..." "Yellow"
    
    # Verificar/crear entorno virtual
    if (-not (Test-Path "venv")) {
        Write-ColorOutput "   - Creando entorno virtual..." "Gray"
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "   ❌ Error creando entorno virtual" "Red"
            exit 1
        }
    }
    
    # Activar entorno virtual
    Write-ColorOutput "   - Activando entorno virtual..." "Gray"
    & ".\venv\Scripts\Activate.ps1"
    
    # Verificar e instalar dependencias
    Write-ColorOutput "   - Verificando dependencias..." "Gray"
    try {
        $pipList = pip list 2>$null
        if ($pipList -notmatch "fastapi" -or $pipList -notmatch "openai") {
            Write-ColorOutput "   - Instalando dependencias..." "Gray"
            pip install -r requirements.txt --quiet
            if ($LASTEXITCODE -ne 0) {
                Write-ColorOutput "   ❌ Error instalando dependencias" "Red"
                exit 1
            }
        }
    }
    catch {
        Write-ColorOutput "   - Instalando dependencias..." "Gray"
        pip install -r requirements.txt --quiet
    }
    
    Write-ColorOutput "   ✅ Entorno Python configurado" "Green"
    Write-ColorOutput "" "White"
}

function Start-FastAPIServer {
    Write-ColorOutput "🚀 Iniciando servidor FastAPI..." "Yellow"
    
    # Cambiar al directorio del proyecto
    $originalLocation = Get-Location
    
    try {
        # Iniciar servidor en background
        Write-ColorOutput "   - Lanzando uvicorn en segundo plano..." "Gray"
        
        # Crear un trabajo en background
        $job = Start-Job -ScriptBlock {
            param($ProjectPath)
            Set-Location $ProjectPath
            & ".\venv\Scripts\Activate.ps1"
            python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
        } -ArgumentList $PWD
        
        # Esperar a que el servidor esté listo
        Write-ColorOutput "   - Esperando que el servidor esté listo..." "Gray"
        $maxAttempts = 30
        $attempt = 0
        
        do {
            $attempt++
            Start-Sleep -Seconds 2
            
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
                if ($response.StatusCode -eq 200) {
                    Write-ColorOutput "   ✅ Servidor FastAPI está ejecutándose" "Green"
                    break
                }
            }
            catch { }
            
            # Verificar si el job sigue ejecutándose
            if ($job.State -ne "Running") {
                Write-ColorOutput "   ❌ El servidor FastAPI se detuvo inesperadamente" "Red"
                Receive-Job -Job $job
                Remove-Job -Job $job
                exit 1
            }
            
            Write-ColorOutput "   - Intento $attempt/$maxAttempts - Esperando servidor..." "Gray"
            
        } while ($attempt -lt $maxAttempts)
        
        if ($attempt -ge $maxAttempts) {
            Write-ColorOutput "   ❌ Timeout esperando el servidor FastAPI" "Red"
            Stop-Job -Job $job
            Remove-Job -Job $job
            exit 1
        }
        
        # Guardar el ID del job para poder limpiarlo después
        $Global:FastAPIJob = $job
        
    }
    finally {
        Set-Location $originalLocation
    }
    
    Write-ColorOutput "" "White"
}

function Test-Services {
    Write-ColorOutput "🧪 Verificando servicios..." "Yellow"
    
    # Test de salud general
    try {
        $healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 10
        $healthData = $healthResponse.Content | ConvertFrom-Json
        
        if ($healthData.status -eq "healthy") {
            Write-ColorOutput "   ✅ API Health Check: OK" "Green"
        } else {
            Write-ColorOutput "   ⚠️ API Health Check: WARNING" "Yellow"
        }
    }
    catch {
        Write-ColorOutput "   ❌ API Health Check: FAILED" "Red"
    }
    
    # Test de chat
    try {
        $chatData = @{
            query = "test"
            tenant_slug = "default"
        } | ConvertTo-Json
        
        $chatResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/search/chat-public" -Method POST -Body $chatData -ContentType "application/json" -TimeoutSec 15
        
        if ($chatResponse.StatusCode -eq 200) {
            Write-ColorOutput "   ✅ Chat Endpoint: OK" "Green"
        } else {
            Write-ColorOutput "   ⚠️ Chat Endpoint: WARNING" "Yellow"
        }
    }
    catch {
        Write-ColorOutput "   ❌ Chat Endpoint: FAILED" "Red"
        Write-ColorOutput "   Error: $($_.Exception.Message)" "Gray"
    }
    
    Write-ColorOutput "" "White"
}

function Show-ServiceStatus {
    Write-ColorOutput "📊 Estado de los servicios:" "Cyan"
    Write-ColorOutput "" "White"
    
    # PostgreSQL
    try {
        $pgStatus = docker exec sapisu_postgres pg_isready -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "   🟢 PostgreSQL: Running (puerto 5432)" "Green"
        } else {
            Write-ColorOutput "   🔴 PostgreSQL: Error" "Red"
        }
    }
    catch {
        Write-ColorOutput "   🔴 PostgreSQL: Not Running" "Red"
    }
    
    # Qdrant
    try {
        $qdrantResponse = Invoke-WebRequest -Uri "http://localhost:6333" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($qdrantResponse.StatusCode -eq 200) {
            Write-ColorOutput "   🟢 Qdrant: Running (puerto 6333)" "Green"
        } else {
            Write-ColorOutput "   🔴 Qdrant: Error" "Red"
        }
    }
    catch {
        Write-ColorOutput "   🔴 Qdrant: Not Running" "Red"
    }
    
    # FastAPI
    try {
        $apiResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($apiResponse.StatusCode -eq 200) {
            Write-ColorOutput "   🟢 FastAPI: Running (puerto 8000)" "Green"
        } else {
            Write-ColorOutput "   🔴 FastAPI: Error" "Red"
        }
    }
    catch {
        Write-ColorOutput "   🔴 FastAPI: Not Running" "Red"
    }
    
    Write-ColorOutput "" "White"
}

function Show-AccessInformation {
    Write-ColorOutput "🌐 URLs de acceso:" "Cyan"
    Write-ColorOutput "" "White"
    Write-ColorOutput "   📱 Interfaz Principal:  http://localhost:8000" "White"
    Write-ColorOutput "   📚 Documentación API:   http://localhost:8000/docs" "White"
    Write-ColorOutput "   ❤️  Health Check:       http://localhost:8000/health" "White"
    Write-ColorOutput "   🐘 PostgreSQL:         localhost:5432" "Gray"
    Write-ColorOutput "   🔍 Qdrant:             http://localhost:6333" "Gray"
    Write-ColorOutput "" "White"
    
    Write-ColorOutput "🎯 Para usar la herramienta:" "Cyan"
    Write-ColorOutput "   1. Abre tu navegador web" "White"
    Write-ColorOutput "   2. Navega a: http://localhost:8000" "Yellow"
    Write-ColorOutput "   3. ¡Comienza a chatear con el asistente SAP IS-U!" "Green"
    Write-ColorOutput "   4. Usa '💾 Guardar Incidencia' para almacenar conocimiento" "Green"
    Write-ColorOutput "" "White"
}

function Start-Browser {
    Write-ColorOutput "🌐 Abriendo navegador..." "Yellow"
    try {
        Start-Process "http://localhost:8000"
        Write-ColorOutput "   ✅ Navegador abierto automáticamente" "Green"
    }
    catch {
        Write-ColorOutput "   ⚠️ No se pudo abrir el navegador automáticamente" "Yellow"
        Write-ColorOutput "   Por favor, abre manualmente: http://localhost:8000" "Yellow"
    }
    Write-ColorOutput "" "White"
}

function Show-StopInstructions {
    Write-ColorOutput "🛑 Para detener todos los servicios:" "Cyan"
    Write-ColorOutput "   - Presiona Ctrl+C en esta ventana" "White"
    Write-ColorOutput "   - O ejecuta: docker-compose down" "White"
    Write-ColorOutput "" "White"
}

# Función de limpieza al salir
function Cleanup {
    Write-ColorOutput "🧹 Limpiando recursos..." "Yellow"
    
    if ($Global:FastAPIJob) {
        try {
            Stop-Job -Job $Global:FastAPIJob -ErrorAction SilentlyContinue
            Remove-Job -Job $Global:FastAPIJob -ErrorAction SilentlyContinue
        }
        catch { }
    }
    
    Write-ColorOutput "✅ Limpieza completada" "Green"
}

# Configurar limpieza al salir
Register-EngineEvent PowerShell.Exiting -Action { Cleanup }
$null = Register-ObjectEvent -InputObject ([System.Console]) -EventName CancelKeyPress -Action { Cleanup; exit }

# === EJECUCIÓN PRINCIPAL ===

try {
    Show-Banner
    Stop-ExistingServices
    Test-Prerequisites
    Start-DockerServices
    Setup-PythonEnvironment
    Start-FastAPIServer
    Test-Services
    Show-ServiceStatus
    Show-AccessInformation
    Start-Browser
    Show-StopInstructions
    
    Write-ColorOutput "🎉 ¡SAP IS-U Smart Wiki está listo para usar!" "Green"
    Write-ColorOutput "   Presiona Ctrl+C para detener todos los servicios" "Gray"
    Write-ColorOutput "" "White"
    
    # Mantener el script ejecutándose
    try {
        while ($true) {
            Start-Sleep -Seconds 30
            
            # Verificar que el job sigue ejecutándose
            if ($Global:FastAPIJob -and $Global:FastAPIJob.State -ne "Running") {
                Write-ColorOutput "⚠️ El servidor FastAPI se detuvo inesperadamente" "Yellow"
                break
            }
        }
    }
    catch {
        Write-ColorOutput "🛑 Deteniendo servicios..." "Yellow"
    }
}
catch {
    Write-ColorOutput "❌ Error durante la ejecución: $($_.Exception.Message)" "Red"
    exit 1
}
finally {
    Cleanup
}
