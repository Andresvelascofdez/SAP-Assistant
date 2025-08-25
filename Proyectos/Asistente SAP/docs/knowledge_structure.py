# ====================================================================
# ESTRUCTURA RECOMENDADA PARA ORGANIZAR CONOCIMIENTO SAP IS-U
# ====================================================================

knowledge_structure = {
    "📊 MASTER_DATA": {
        "description": "Documentación de tablas principales",
        "examples": [
            "BUT000 - Business Partner",
            "EVER - Instalaciones y contratos", 
            "EABL - Documentos de facturación",
            "EABLG - Lecturas de aparatos",
            "EUITRANS - Puntos de suministro",
            "EANLH - Historial de aparatos",
            "ERCH - Cabeceras de factura",
            "DFKKOP - Partidas abiertas FI-CA"
        ],
        "scope": "STANDARD",
        "format": """
        Tabla: [NOMBRE] - [Descripción corta]
        ===================================
        
        Descripción: [Propósito de la tabla]
        
        Campos principales:
        - CAMPO1: Descripción
        - CAMPO2: Descripción
        
        Relaciones:
        - TABLA_REL: Via campo X
        
        T-codes relacionadas:
        - TX01: Descripción
        
        Validaciones:
        - Regla 1
        - Regla 2
        
        Errores comunes:
        - Error: Solución
        """
    },
    
    "🔧 TRANSACTIONS": {
        "description": "T-codes y transacciones",
        "examples": [
            "EC85 - Facturación manual",
            "ES21 - Alta de instalación",
            "ES31 - Cuentas contractuales",
            "EL31 - Gestión de aparatos",
            "BP - Business Partner",
            "FPL9 - Plan de pagos"
        ],
        "scope": "STANDARD", 
        "format": """
        T-code: [CODIGO] - [Descripción]
        ===============================
        
        Propósito: [Para qué sirve]
        Módulo: [IS-U área]
        
        Campos obligatorios:
        - Campo1: Descripción
        
        Proceso:
        1. Paso 1
        2. Paso 2
        
        Validaciones:
        - Verificación 1
        
        Errores frecuentes:
        - Error: Causa y solución
        
        Tablas actualizadas:
        - TABLA1: Qué actualiza
        """
    },
    
    "🔄 BUSINESS_PROCESSES": {
        "description": "Procesos de negocio end-to-end",
        "examples": [
            "Move-in (Alta de suministro)",
            "Move-out (Baja de suministro)", 
            "Facturación periódica",
            "Gestión de lecturas",
            "Proceso de cobranza",
            "Change of supplier"
        ],
        "scope": "STANDARD",
        "format": """
        Proceso: [NOMBRE]
        =================
        
        Objetivo: [Meta del proceso]
        
        FASE 1: [Nombre fase]
        --------------------
        1. Actividad 1
        2. Actividad 2
        
        FASE 2: [Nombre fase]
        --------------------
        1. Actividad 1
        
        Validaciones críticas:
        - Validación 1
        
        Errores frecuentes:
        - Error: Solución
        
        T-codes: [Lista]
        Tablas: [Lista]
        """
    },
    
    "🚨 INCIDENT_SOLUTIONS": {
        "description": "Soluciones a incidencias técnicas",
        "examples": [
            "Error BP no válido en ES21",
            "Factura duplicada en EC85",
            "Aparato no encontrado en EL31",
            "Error de lectura en EABLG",
            "Problemas de autorización",
            "Errores de customizing"
        ],
        "scope": "CLIENT_SPECIFIC",  # Pueden ser específicas por cliente
        "format": """
        Incidencia: [Descripción del problema]
        =====================================
        
        Síntoma: [Cómo se manifiesta]
        
        Causas posibles:
        1. Causa 1
        2. Causa 2
        
        Diagnóstico:
        1. Verificar X
        2. Revisar Y
        
        Solución:
        1. Acción 1
        2. Acción 2
        
        Prevención:
        - Medida preventiva
        
        Severidad: [Alta/Media/Baja]
        T-codes: [Lista]
        Tablas: [Lista]
        """
    },
    
    "⚙️ CONFIGURATION": {
        "description": "Customizing y configuración",
        "examples": [
            "Configuración de tipos de contrato",
            "Setup de aparatos de medición",
            "Customizing de facturación",
            "Configuración de Business Partner",
            "Setup de rate determination",
            "Configuración de FI-CA"
        ],
        "scope": "CLIENT_SPECIFIC",
        "format": """
        Configuración: [Área de customizing]
        ===================================
        
        Propósito: [Para qué se configura]
        
        Path SPRO: [Ruta en customizing]
        
        Pasos de configuración:
        1. Paso 1
        2. Paso 2
        
        Tablas de customizing:
        - TABLA1: Qué configura
        
        Consideraciones:
        - Consideración 1
        
        Impacto:
        - En proceso X
        - En transacción Y
        """
    },
    
    "💻 PROGRAMS_REPORTS": {
        "description": "Programas ABAP y reportes",
        "examples": [
            "SAPLIS-U1 - Facturación masiva",
            "RFKKEDR1 - Extracto de cuenta",
            "RFBU0001 - Lista de BP",
            "Programas Z customizados",
            "Reportes de análisis",
            "Jobs de background"
        ],
        "scope": "CLIENT_SPECIFIC",
        "format": """
        Programa: [NOMBRE] - [Descripción]
        =================================
        
        Tipo: [Report/Function/Class]
        Propósito: [Para qué sirve]
        
        Parámetros principales:
        - PARAM1: Descripción
        
        Funcionalidad:
        1. Función 1
        2. Función 2
        
        Consideraciones:
        - Performance
        - Autorizaciones
        
        Scheduling:
        - Frecuencia recomendada
        - Variantes útiles
        """
    },
    
    "📋 FUNCTIONAL_SPECS": {
        "description": "Especificaciones funcionales",
        "examples": [
            "Spec para desarrollo Z",
            "Requirement de interfaz",
            "Especificación de reporte",
            "Documentos de diseño",
            "User stories",
            "Test cases"
        ],
        "scope": "CLIENT_SPECIFIC",
        "format": """
        Especificación: [TÍTULO]
        ========================
        
        Objetivo: [Meta funcional]
        
        Requirements:
        1. Requirement 1
        2. Requirement 2
        
        Diseño:
        - Approach técnico
        
        Test scenarios:
        1. Scenario 1
        2. Scenario 2
        
        Dependencies:
        - Dependencia 1
        """
    },
    
    "🎓 TRAINING_MATERIALS": {
        "description": "Material de capacitación",
        "examples": [
            "Guías de usuario para T-codes",
            "Procedimientos operativos",
            "Manuales de procesos",
            "Casos de uso típicos",
            "Best practices",
            "Tips y trucos"
        ],
        "scope": "CLIENT_SPECIFIC",
        "format": """
        Guía: [TÍTULO]
        ==============
        
        Audiencia: [Usuario final/Técnico/Funcional]
        
        Objetivos de aprendizaje:
        1. Objetivo 1
        2. Objetivo 2
        
        Procedimiento:
        1. Paso 1 [Screenshot opcional]
        2. Paso 2
        
        Ejercicios prácticos:
        - Ejercicio 1
        
        Referencias:
        - Documento relacionado
        """
    }
}

# ====================================================================
# COMANDOS PARA ALIMENTAR POR CATEGORÍA
# ====================================================================

def get_feeding_examples():
    """Ejemplos de cómo alimentar cada categoría"""
    
    examples = {
        "frontend_web": """
        1. Acceder a http://localhost
        2. Modo "Añadir" 📝
        3. Seleccionar tenant y scope
        4. Arrastrar archivo o pegar texto
        5. Sistema extrae metadatos automáticamente
        6. Procesar para ingesta
        """,
        
        "api_direct": """
        curl -X POST "http://localhost:8000/api/v1/ingest/text" \\
             -H "Authorization: Bearer $TOKEN" \\
             -H "Content-Type: application/json" \\
             -d '{
               "tenant_slug": "STANDARD",
               "scope": "STANDARD",
               "text": "Documentación de tabla BUT000...",
               "metadata": {
                 "system": "IS-U",
                 "topic": "master-data",
                 "tables": ["BUT000"],
                 "tcodes": ["BP"]
               }
             }'
        """,
        
        "batch_script": """
        # Usar scripts/feed_knowledge.py
        python scripts/feed_knowledge.py
        
        # O alimentar desde directorio
        python -c "
        from scripts.feed_knowledge import KnowledgeFeeder
        feeder = KnowledgeFeeder()
        feeder.authenticate()
        feeder.feed_from_files('/path/to/knowledge/docs')
        "
        """,
        
        "file_organization": """
        knowledge/
        ├── tables/
        │   ├── BUT000_business_partner.md
        │   ├── EVER_installations.md
        │   └── EABL_billing_docs.md
        ├── processes/
        │   ├── move_in_process.md
        │   ├── billing_process.md
        │   └── reading_process.md
        ├── incidents/
        │   ├── bp_errors.json
        │   ├── billing_issues.md
        │   └── device_problems.md
        └── config/
            ├── customizing_guide.md
            └── authorization_setup.md
        """
    }
    
    return examples

print("📚 Estructura de conocimiento definida exitosamente!")
print("\nCategorías disponibles:")
for category, info in knowledge_structure.items():
    print(f"  {category}: {info['description']}")

print(f"\n🎯 Total de categorías: {len(knowledge_structure)}")
print("📖 Ver examples con: get_feeding_examples()")
