#!/usr/bin/env python3
"""
Script para alimentar conocimiento base masivo
Wiki Inteligente SAP IS-U
"""

import asyncio
import json
import os
from typing import List, Dict
from pathlib import Path

# Nota: requests se instala con: pip install requests
try:
    import requests
except ImportError:
    print("⚠️  Warning: 'requests' no instalado. Ejecutar: pip install requests")
    requests = None

# Configuración del sistema
API_BASE = "http://localhost:8000/api/v1"
TENANT = "STANDARD"  # O tu tenant específico
AUTH_EMAIL = "admin@sapisu.local"
AUTH_PASSWORD = "admin123"

class KnowledgeFeeder:
    """Alimentador de conocimiento masivo"""
    
    def __init__(self):
        self.session = requests.Session()
        self.token = None
    
    def authenticate(self):
        """Autenticarse en el sistema"""
        response = self.session.post(f"{API_BASE}/auth/login", json={
            "email": AUTH_EMAIL,
            "password": AUTH_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            print("✅ Autenticación exitosa")
        else:
            raise Exception("❌ Error de autenticación")
    
    def feed_table_documentation(self, table_docs: List[Dict]):
        """Alimentar documentación de tablas"""
        print(f"\n📊 Alimentando documentación de {len(table_docs)} tablas...")
        
        for doc in table_docs:
            try:
                response = self.session.post(f"{API_BASE}/ingest/text", json={
                    "tenant_slug": TENANT,
                    "scope": "STANDARD",
                    "text": doc["content"],
                    "source": f"table_doc_{doc['table']}",
                    "metadata": {
                        "system": "IS-U",
                        "topic": "master-data",
                        "tables": [doc["table"]],
                        "tcodes": doc.get("tcodes", []),
                        "type": "table_documentation"
                    }
                })
                
                if response.status_code == 200:
                    print(f"  ✅ {doc['table']}: Documentación procesada")
                else:
                    print(f"  ❌ {doc['table']}: Error - {response.text}")
                    
            except Exception as e:
                print(f"  ❌ {doc['table']}: Excepción - {e}")
    
    def feed_process_documentation(self, process_docs: List[Dict]):
        """Alimentar documentación de procesos"""
        print(f"\n🔄 Alimentando {len(process_docs)} procesos de negocio...")
        
        for doc in process_docs:
            try:
                response = self.session.post(f"{API_BASE}/ingest/text", json={
                    "tenant_slug": TENANT,
                    "scope": "STANDARD", 
                    "text": doc["content"],
                    "source": f"process_{doc['name']}",
                    "metadata": {
                        "system": "IS-U",
                        "topic": doc.get("topic", "business-process"),
                        "tcodes": doc.get("tcodes", []),
                        "tables": doc.get("tables", []),
                        "type": "process_documentation"
                    }
                })
                
                if response.status_code == 200:
                    print(f"  ✅ {doc['name']}: Proceso documentado")
                else:
                    print(f"  ❌ {doc['name']}: Error - {response.text}")
                    
            except Exception as e:
                print(f"  ❌ {doc['name']}: Excepción - {e}")
    
    def feed_incident_solutions(self, incidents: List[Dict]):
        """Alimentar soluciones de incidencias"""
        print(f"\n🔧 Alimentando {len(incidents)} soluciones de incidencias...")
        
        for incident in incidents:
            try:
                response = self.session.post(f"{API_BASE}/ingest/text", json={
                    "tenant_slug": TENANT,
                    "scope": "STANDARD",
                    "text": incident["content"],
                    "source": f"incident_{incident['id']}",
                    "metadata": {
                        "system": "IS-U",
                        "topic": incident.get("topic", "troubleshooting"),
                        "tcodes": incident.get("tcodes", []),
                        "tables": incident.get("tables", []),
                        "type": "incident_solution",
                        "severity": incident.get("severity", "medium")
                    }
                })
                
                if response.status_code == 200:
                    print(f"  ✅ Incidencia {incident['id']}: Solución agregada")
                else:
                    print(f"  ❌ Incidencia {incident['id']}: Error - {response.text}")
                    
            except Exception as e:
                print(f"  ❌ Incidencia {incident['id']}: Excepción - {e}")
    
    def feed_from_files(self, directory: str):
        """Alimentar desde archivos en directorio"""
        print(f"\n📁 Procesando archivos en {directory}...")
        
        path = Path(directory)
        if not path.exists():
            print(f"❌ Directorio no existe: {directory}")
            return
        
        # Procesar diferentes tipos de archivo
        for file_path in path.rglob("*"):
            if file_path.is_file():
                extension = file_path.suffix.lower()
                
                if extension in ['.txt', '.md']:
                    self._process_text_file(file_path)
                elif extension in ['.json']:
                    self._process_json_file(file_path)
                elif extension in ['.pdf', '.docx']:
                    self._process_binary_file(file_path)
    
    def _process_text_file(self, file_path: Path):
        """Procesar archivo de texto"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Inferir metadatos del nombre del archivo
            metadata = self._infer_metadata_from_filename(file_path.name)
            
            response = self.session.post(f"{API_BASE}/ingest/text", json={
                "tenant_slug": TENANT,
                "scope": "STANDARD",
                "text": content,
                "source": f"file_{file_path.name}",
                "metadata": metadata
            })
            
            if response.status_code == 200:
                print(f"  ✅ {file_path.name}: Archivo procesado")
            else:
                print(f"  ❌ {file_path.name}: Error - {response.text}")
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: Excepción - {e}")
    
    def _process_json_file(self, file_path: Path):
        """Procesar archivo JSON estructurado"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Si es un array de documentos
            if isinstance(data, list):
                for item in data:
                    if "content" in item:
                        self._ingest_json_item(item, file_path.name)
            # Si es un documento único
            elif "content" in data:
                self._ingest_json_item(data, file_path.name)
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: Excepción JSON - {e}")
    
    def _ingest_json_item(self, item: Dict, filename: str):
        """Ingestar item individual desde JSON"""
        response = self.session.post(f"{API_BASE}/ingest/text", json={
            "tenant_slug": TENANT,
            "scope": item.get("scope", "STANDARD"),
            "text": item["content"],
            "source": f"json_{filename}_{item.get('id', 'unknown')}",
            "metadata": item.get("metadata", {})
        })
        
        if response.status_code == 200:
            print(f"    ✅ Item {item.get('id', 'sin_id')}: Procesado")
        else:
            print(f"    ❌ Item {item.get('id', 'sin_id')}: Error")
    
    def _process_binary_file(self, file_path: Path):
        """Procesar archivos binarios (PDF, DOCX)"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {
                    'tenant_slug': TENANT,
                    'scope': 'STANDARD'
                }
                
                response = self.session.post(f"{API_BASE}/ingest/file", 
                                           files=files, data=data)
            
            if response.status_code == 200:
                print(f"  ✅ {file_path.name}: Archivo binario procesado")
            else:
                print(f"  ❌ {file_path.name}: Error - {response.text}")
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: Excepción - {e}")
    
    def _infer_metadata_from_filename(self, filename: str) -> Dict:
        """Inferir metadatos del nombre del archivo"""
        metadata = {"system": "IS-U", "type": "general"}
        
        filename_lower = filename.lower()
        
        # Inferir tema
        if any(word in filename_lower for word in ['tabla', 'table']):
            metadata["topic"] = "master-data"
            metadata["type"] = "table_documentation"
        elif any(word in filename_lower for word in ['proceso', 'process']):
            metadata["topic"] = "business-process"
            metadata["type"] = "process_documentation"
        elif any(word in filename_lower for word in ['incidencia', 'error', 'problem']):
            metadata["topic"] = "troubleshooting"
            metadata["type"] = "incident_solution"
        elif any(word in filename_lower for word in ['config', 'customizing']):
            metadata["topic"] = "configuration"
            metadata["type"] = "configuration_guide"
        
        return metadata


# ====================================================================
# DATOS DE EJEMPLO PARA ALIMENTAR
# ====================================================================

# Documentación de tablas principales
TABLE_DOCS = [
    {
        "table": "BUT000",
        "content": """
Tabla BUT000 - Business Partner Master Data
===========================================

Descripción: Tabla principal para almacenar datos básicos de Business Partners en SAP IS-U.

Campos clave:
- PARTNER: Número único de Business Partner (10 caracteres)
- TYPE: Tipo de BP (1=Persona física, 2=Organización, 3=Grupo)
- TITLE: Tratamiento (Sr., Sra., Dr., etc.)
- NAME1: Apellido o nombre de empresa
- NAME2: Nombre o denominación adicional
- BIRTHDT: Fecha de nacimiento (solo personas físicas)
- CREAT_DATE: Fecha de creación del registro
- CREAT_TIME: Hora de creación

Indices principales:
- Primario: PARTNER
- Secundario: SEARCHTERM1 (término de búsqueda)

Relaciones:
- BUT020: Direcciones del Business Partner
- BUT050: Datos de comunicación (teléfono, email, fax)
- EVER: Contratos de suministro asociados
- FKKVKP: Datos de partner contractual para facturación

Validaciones importantes:
- PARTNER debe ser único en el sistema
- NAME1 es campo obligatorio
- TYPE debe corresponder a valores válidos en customizing
- SEARCHTERM1 se genera automáticamente si no se proporciona

Customizing relacionado:
- SPRO → IS-U → Business Partner → Basic Settings
- Definición de tipos de BP
- Configuración de campos obligatorios por tipo

Errores comunes:
- "Business Partner does not exist": PARTNER no existe en BUT000
- "Incomplete data": Campos obligatorios no completados
- "Duplicate search term": SEARCHTERM1 ya existe para otro BP

Programas útiles:
- SAPDBUT0: Creación masiva de Business Partners
- RFBU0001: Lista de Business Partners
- BUP2: Mantenimiento individual de BP (transacción)
        """,
        "tcodes": ["BP", "BUP2", "ES21", "ES31"]
    },
    {
        "table": "EVER",
        "content": """
Tabla EVER - Installation Master Data
=====================================

Descripción: Tabla central para instalaciones y contratos en SAP IS-U.

Campos principales:
- ANLAGE: Número de instalación (clave primaria)
- PARTNER: Business Partner asociado (referencia a BUT000)
- VERTRAG: Número de contrato
- VERTRAGSART: Tipo de contrato
- EINZDAT: Fecha de move-in (alta)
- AUSZDAT: Fecha de move-out (baja)
- STATUS: Estado del contrato (A=Activo, I=Inactivo, etc.)
- SPARTE: División (electricidad, gas, agua)
- TARIFF: Tarifa aplicable
- AKTIVDAT: Fecha de activación

Estados de contrato:
- A: Activo
- I: Inactivo
- T: Terminado
- S: Suspendido

Campos de fecha críticos:
- EINZDAT: Inicio del suministro
- AUSZDAT: Fin del suministro
- AKTIVDAT: Activación del contrato
- BEENDDAT: Fecha de finalización

Relaciones importantes:
- BUT000: Datos del Business Partner (via PARTNER)
- EUITRANS: Punto de suministro técnico
- EABL: Documentos de facturación
- EANLH: Historial de aparatos instalados

Validaciones críticas:
- PARTNER debe existir en BUT000
- Fechas no pueden solaparse para mismo punto de suministro
- STATUS debe ser válido según customizing
- SPARTE debe estar configurada en sistema

T-codes relacionadas:
- ES21: Crear instalación
- ES22: Modificar instalación  
- ES23: Visualizar instalación
- ES31: Account determination
- ES32: Activar contrato

Índices:
- Primario: ANLAGE
- Secundarios: PARTNER, VERTRAG, VKONTO

Programas de análisis:
- ES03: Lista de instalaciones
- ES13: Análisis de contratos
- RFIS-U01: Extracto de instalaciones
        """,
        "tcodes": ["ES21", "ES22", "ES23", "ES31", "ES32"]
    }
]

# Procesos de negocio
PROCESS_DOCS = [
    {
        "name": "move_in_process",
        "topic": "move-in",
        "content": """
Proceso Move-in: Alta de Suministro en SAP IS-U
===============================================

Objetivo: Dar de alta un nuevo suministro para un cliente.

FASE 1: Preparación y Validación
--------------------------------
1. Verificar datos del Business Partner:
   - Transacción: BP
   - Validar completitud en BUT000
   - Confirmar roles asignados en BUT020
   - Verificar datos de comunicación en BUT050

2. Validar disponibilidad del punto de suministro:
   - Consultar EUITRANS para estado
   - Verificar que no haya contratos activos solapados
   - Confirmar datos técnicos de la instalación

FASE 2: Creación de la Instalación
----------------------------------
1. Ejecutar transacción ES21:
   - Ingresar Business Partner
   - Seleccionar point of delivery
   - Configurar fechas de inicio
   - Asignar tipo de contrato

2. Sistema actualiza:
   - EVER: Crea registro de instalación
   - EVERG: Relaciona BP con instalación
   - EUITRANS: Actualiza estado del punto

FASE 3: Configuración de Aparatos
---------------------------------
1. Asignar aparatos de medición:
   - Transacción: EL31
   - Configurar en EANLH
   - Establecer lecturas iniciales

2. Registrar lectura inicial:
   - Transacción: EL21
   - Actualizar EABLG
   - Validar datos técnicos

FASE 4: Activación del Contrato
-------------------------------
1. Activar con ES32:
   - Sistema valida todas las dependencias
   - Actualiza EVER.STATUS = 'A'
   - Establece EVER.AKTIVDAT

Validaciones críticas:
- BP debe tener rol 'Applicant'
- Fechas no pueden solaparse
- Aparatos deben estar correctamente configurados
- Lectura inicial es obligatoria

Errores frecuentes y soluciones:
- "BP not authorized": Asignar rol correcto en BUT020
- "Installation exists": Verificar fechas en EVER
- "Device conflict": Revisar EANLH para solapamientos
- "Missing reading": Completar EABLG con EL21

Post-proceso:
- Verificar creación correcta con ES23
- Configurar facturación automática si aplica
- Documentar casos especiales
        """,
        "tcodes": ["BP", "ES21", "ES23", "ES32", "EL31", "EL21"],
        "tables": ["BUT000", "BUT020", "EVER", "EANLH", "EABLG", "EUITRANS"]
    }
]

# Soluciones de incidencias
INCIDENT_SOLUTIONS = [
    {
        "id": "001_bp_not_valid",
        "topic": "troubleshooting",
        "severity": "high",
        "content": """
Incidencia: Business Partner no válido en ES21
==============================================

Síntoma: Al intentar crear instalación con ES21, sistema muestra error "Business Partner not valid" o "BP not authorized".

Causas posibles:
1. BP no existe en tabla BUT000
2. BP no tiene el rol correcto asignado
3. BP está inactivo o bloqueado
4. Faltan datos obligatorios en BUT000

Diagnóstico paso a paso:
1. Verificar existencia del BP:
   - Transacción: BP
   - Buscar por número o nombre
   - Confirmar que existe en BUT000

2. Verificar roles asignados:
   - En BP, ir a pestaña "Roles"
   - Verificar que tiene rol "Applicant" (FLROLE 'APL')
   - Fechas de validez del rol deben incluir fecha actual

3. Verificar estado del BP:
   - Campo BUT000.PARTNERSTAT debe ser activo
   - No debe tener indicadores de bloqueo

4. Verificar datos obligatorios:
   - BUT000.NAME1 debe estar completo
   - Según configuración, pueden requerirse otros campos

Solución:
1. Si BP no existe: Crear con transacción BP
2. Si falta rol: Asignar rol "Applicant" con fechas válidas
3. Si está bloqueado: Desbloquear o crear BP nuevo
4. Si faltan datos: Completar campos obligatorios

Prevención:
- Validar BP antes de procesos de move-in
- Mantener roles actualizados
- Documentar requirements por tipo de BP

Tablas afectadas: BUT000, BUT020
Transacciones: BP, ES21
Severidad: Alta (bloquea proceso de alta)
        """,
        "tcodes": ["BP", "ES21"],
        "tables": ["BUT000", "BUT020"]
    }
]


def main():
    """Función principal para alimentar conocimiento"""
    print("🔍 Wiki Inteligente SAP IS-U - Alimentador de Conocimiento")
    print("=" * 60)
    
    # Inicializar feeder
    feeder = KnowledgeFeeder()
    
    try:
        # Autenticarse
        feeder.authenticate()
        
        # Alimentar diferentes tipos de conocimiento
        feeder.feed_table_documentation(TABLE_DOCS)
        feeder.feed_process_documentation(PROCESS_DOCS)
        feeder.feed_incident_solutions(INCIDENT_SOLUTIONS)
        
        # Opcionalmente, procesar archivos de un directorio
        knowledge_dir = input("\n📁 ¿Directorio con archivos adicionales? (Enter para saltar): ")
        if knowledge_dir and os.path.exists(knowledge_dir):
            feeder.feed_from_files(knowledge_dir)
        
        print("\n🎉 ¡Alimentación de conocimiento completada!")
        print("\nPuedes ahora hacer consultas como:")
        print("- ¿Qué campos son obligatorios en BUT000?")
        print("- ¿Cómo solucionar error de BP no válido en ES21?")
        print("- Explica el proceso de move-in paso a paso")
        
    except Exception as e:
        print(f"\n❌ Error durante alimentación: {e}")
        print("Verifica que el sistema esté ejecutándose en http://localhost:8000")


if __name__ == "__main__":
    main()
