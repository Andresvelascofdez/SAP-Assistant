"""
Guía completa para alimentar conocimiento base en Wiki Inteligente SAP IS-U
==========================================================================
"""

# ====================================================================
# 1. DOCUMENTACIÓN DE TABLAS SAP IS-U
# ====================================================================

tabla_but000_doc = """
Tabla: BUT000 - Business Partner
================================

Descripción: Tabla principal para datos de Business Partner en IS-U
Uso: Almacena información básica de clientes y proveedores

Campos principales:
- PARTNER: Número de Business Partner (clave)
- TYPE: Tipo de BP (1=Persona, 2=Organización)
- TITLE: Tratamiento
- NAME1: Nombre/Apellido 1
- NAME2: Apellido 2
- SEARCHTERM1: Término de búsqueda
- BIRTHDT: Fecha nacimiento
- CREAT_DATE: Fecha creación

Relaciones:
- BUT020: Direcciones del BP
- BUT050: Comunicaciones (teléfono, email)
- EVER: Contratos de suministro
- FKKVKP: Partner contractual

T-codes relacionadas:
- BP: Mantenimiento de Business Partner
- ES21: Alta de suministro (usa BUT000)
- ES31: Contratos (referencia BUT000)

Customizing:
- SPRO → IS-U → Business Partner → Configuración básica

Validaciones importantes:
- PARTNER debe ser único
- TYPE debe estar en tabla de dominio
- NAME1 es obligatorio
- SEARCHTERM1 se genera automáticamente si está vacío

Errores comunes:
- "BP no válido": PARTNER no existe en BUT000
- "Datos incompletos": Campos obligatorios vacíos
- "Duplicado": SEARCHTERM1 ya existe

Programas relacionados:
- SAPDBUT0: Creación masiva de BP
- RFBU0001: Reporte de BP
"""

# ====================================================================
# 2. T-CODES Y TRANSACCIONES
# ====================================================================

tcode_ec85_doc = """
T-code: EC85 - Creación de facturas
===================================

Propósito: Crear facturas manuales para servicios de utilities
Módulo: IS-U Billing

Navegación:
Menú SAP → Logistics → IS-U → Billing → Manual Billing → EC85

Campos obligatorios:
- Business Partner: BP válido de BUT000
- Contrato: VERTRAG de tabla EVER
- Período facturación: ABRPE
- Tipo factura: INVOICETYPE
- Fecha vencimiento: FAEDN

Proceso:
1. Ingresar BP en campo PARTNER
2. Sistema trae contratos activos de EVER
3. Seleccionar contrato y período
4. Validar datos en EABL/EABLG
5. Generar factura → Update ERCH

Validaciones automáticas:
- BP activo y con rol correcto
- Contrato vigente en fechas
- No facturas duplicadas para período
- Datos de lectura válidos

Errores frecuentes:
- "BP no autorizado": Falta rol en BUT020
- "Contrato no válido": EVER.STATUS ≠ 'A'
- "Período cerrado": EABL ya facturado
- "Falta lectura": EABL.ABLBELNR vacío

Tablas actualizadas:
- ERCH: Cabecera documento factura
- ERCHC: Posiciones de factura  
- DFKKOP: Partidas abiertas
- EABL: Marca como facturado

Programas relacionados:
- SAPLIS-U1: Batch billing
- RFKKEDR1: Extracto de cuenta
"""

# ====================================================================
# 3. PROCESOS DE NEGOCIO
# ====================================================================

proceso_movein_doc = """
Proceso: Move-in (Alta de suministro)
====================================

Descripción: Proceso completo para dar de alta un nuevo suministro
Involucra: BP, Contrato, Instalación, Aparatos

FASE 1: Preparación
-------------------
1. Verificar BP existente o crear nuevo:
   - T-code: BP
   - Tabla: BUT000
   - Validar: Datos completos, roles asignados

2. Verificar punto de suministro:
   - T-code: ES11 (Display premise)
   - Tabla: EUITRANS
   - Estado: Disponible para conexión

FASE 2: Creación de instalación
-------------------------------
1. T-code: ES21 (Create installation)
2. Datos requeridos:
   - Business Partner (BUT000.PARTNER)
   - Premise/Instalación (EVER.ANLAGE)
   - Fecha move-in (EVER.EINZDAT)
   - Tipo contrato (EVER.VERTRAGSART)

3. Sistema crea:
   - Instalación en EVER
   - Relación BP-Instalación en EVERG
   - Punto de conexión en EUITRANS

FASE 3: Configuración de aparatos
---------------------------------
1. T-code: ES31 (Contract accounts)
2. Asignar aparatos:
   - EL31: Mantenimiento aparatos
   - Tabla: EANLH (Device location)
   - Tabla: EGERH (Device history)

3. Lecturas iniciales:
   - EL21: Registrar lectura inicial
   - Tabla: EABLG (Readings)

FASE 4: Activación
------------------
1. Verificaciones finales:
   - Contrato activo: EVER.STATUS = 'A'
   - Aparatos instalados: EANLH.STATUS = 'I'
   - Lectura inicial: EABLG.ABLSTAT = 'A'

2. Liberación:
   - ES32: Activate contract
   - Sistema actualiza EVER.AKTIVDAT

Validaciones críticas:
- BP debe tener rol 'Applicant' en BUT020
- Premise disponible (no ocupado)
- Datos técnicos completos
- Sin solapamiento de fechas

Errores típicos:
- "Installation already exists": EVER duplicado
- "BP not authorized": Falta rol en BUT020  
- "Premise occupied": EUITRANS.STATUS ≠ 'Available'
- "Device conflict": EANLH overlapping dates

Reportes de control:
- ES03: Lista de instalaciones
- ES13: Status de contratos
- EL03: Reporte de aparatos
"""

# ====================================================================
# 4. CONFIGURACIÓN Y CUSTOMIZING
# ====================================================================

customizing_isu_doc = """
Customizing IS-U: Configuración esencial
========================================

SPRO Path: SAP Customizing Implementation Guide → IS-U

1. BASIC SETTINGS
-----------------
Path: IS-U → Basic Settings

• Company Codes
  - Assign company code to IS-U
  - Table: T001ISU
  - Transaction: EK02

• Rate Types  
  - Define rate categories
  - Table: TIA01
  - Used in: Contract accounts

• Portion Types
  - Define service portions
  - Table: TIA02  
  - Used in: Device categories

2. BUSINESS PARTNER
-------------------
Path: IS-U → Business Partner

• BP Roles
  - FLCUST00: Configure roles
  - Standard roles: Applicant, Contracting party, Invoice recipient
  - Table: TB010

• Number Ranges
  - Define BP number ranges
  - BUCF: Number range maintenance
  - Internal vs External numbering

• Authorization
  - Assign roles to BP types
  - Table: TB002
  - Controls access in transactions

3. CONTRACT ACCOUNTS
--------------------
Path: IS-U → Contract Accounts

• Contract Types
  - Define contract categories
  - Table: TTVAKLART
  - Examples: Standard, Special, Temporary

• Installation Types
  - Define installation categories  
  - Table: TTANLAGENART
  - Examples: Domestic, Commercial, Industrial

• Connection Objects
  - Configure technical objects
  - Table: TEANSCHL
  - Links to device management

4. DEVICE MANAGEMENT
--------------------
Path: IS-U → Device Management → Techinal Settings

• Device Categories
  - Define meter types
  - Table: TEGERAETEART
  - Examples: Electric, Gas, Water

• Register Groups
  - Configure register types
  - Table: TEREGISTERGRUPPE
  - Links consumption to billing

• Reading Reasons
  - Define reading types
  - Table: TEABLESEGRUND
  - Examples: Regular, Move-in, Move-out

5. BILLING
----------
Path: IS-U → Billing

• Billing Schemas
  - Configure billing procedures
  - Table: TBK01
  - Controls calculation flow

• Rate Determination
  - Set up pricing
  - Table: TK1*
  - Complex condition techniques

• Document Types
  - Define invoice types
  - Table: TFARGART
  - Examples: Regular, Correction, Credit

6. MASTER DATA TABLES
---------------------
Core tables que requieren configuración:

• BUT000: Business Partner basic data
• EVER: Installation/Contract data  
• EABL: Billing documents
• EABLG: Meter readings
• EANLH: Device installation history
• ERCH: Invoice headers
• ERCHC: Invoice line items

7. CRITICAL VALIDATIONS
-----------------------
Configurar validaciones obligatorias:

• BP Validation:
  - Required fields por role
  - Address validation
  - Communication validation

• Contract Validation:
  - Date consistency checks
  - BP authorization checks
  - Technical object assignments

• Billing Validation:  
  - Reading plausibility
  - Rate calculation checks
  - Invoice document checks

8. AUTHORIZATION OBJECTS
------------------------
Objetos de autorización IS-U:

• I_VTWEG: Sales organization
• I_PARTNER: Business Partner
• I_ANLAGE: Installation
• I_VERTRAG: Contract
• I_ABLESUNG: Readings
• I_RECHNUNG: Billing

9. INTEGRATION POINTS
---------------------
Integración con otros módulos:

• FI-CA: Financial Contract Accounting
  - Table: DFKKOP (Line items)
  - Table: DFKKKO (Contract accounts)

• PM: Plant Maintenance
  - Device maintenance orders
  - Table: EQKT (Equipment)

• SD: Sales & Distribution
  - Pricing procedures
  - Table: KNVV (Customer sales data)

10. PERFORMANCE CONSIDERATIONS
------------------------------
Optimizaciones críticas:

• Indexes:
  - BUT000: PARTNER, SEARCHTERM1
  - EVER: PARTNER, ANLAGE, VERTRAG
  - EABL: ANLAGE, ABLESEDAT

• Archiving:
  - Billing documents older than 7 years
  - Reading data older than 10 years
  - Programs: SAPLIS-U archiving

• Number ranges:
  - Size buffers appropriately
  - Monitor consumption
  - Plan for growth
"""

print("📚 Guía de conocimiento base creada exitosamente!")
print("\nPuedes alimentar el sistema con:")
print("1. Documentación de tablas")
print("2. Procesos de negocio") 
print("3. T-codes y transacciones")
print("4. Configuración y customizing")
print("5. Programas ABAP")
print("6. Incidencias y soluciones")
