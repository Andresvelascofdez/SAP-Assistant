#!/usr/bin/env python3
"""Test incidence storage and retrieval"""
import asyncio
import aiohttp
import json

async def test_incidence_workflow():
    print("=== Test de Flujo Completo de Incidencias ===\n")
    
    # 1. Guardar una incidencia de prueba
    print("1. Guardando incidencia de prueba...")
    
    incidence_data = {
        "tenant_slug": "default",
        "scope": "CLIENT_SPECIFIC", 
        "type": "incidencia",
        "system": "IS-U",
        "topic": "billing",
        "title": "Error en cálculo de consumo estimado",
        "text": """TÍTULO: Error en cálculo de consumo estimado

SISTEMA: IS-U
TEMA: billing

DESCRIPCIÓN:
Al ejecutar el proceso de facturación automática en el sistema IS-U, 
se detectó que el cálculo de consumo estimado no está funcionando 
correctamente para contratos con perfil de carga especial.

CAUSA RAÍZ:
El parámetro ESTIMATION_PROFILE en la tabla EABLG no se está leyendo 
correctamente cuando el tipo de suministro es 'GAS_INDUSTRIAL'.

SOLUCIÓN:
1. Verificar configuración en transacción EG02
2. Revisar tabla EABLG campos EST_PROF y EST_METHOD  
3. Ejecutar programa RGVVBEST con modo de prueba
4. Validar resultados antes de producción

TCODES: EG02, EC85, RGVVBEST
TABLAS: EABLG, ERCH, EEST

TAGS: estimacion, consumo, facturacion, gas, industrial

FECHA: 26/01/2025 15:30:00""",
        "tags": ["estimacion", "consumo", "facturacion", "EG02", "EABLG"],
        "source": "test-script"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # Guardar incidencia
            async with session.post('http://localhost:8000/api/v1/ingest/text-public', 
                                   json=incidence_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Incidencia guardada con ID: {result['id']}")
                    print(f"   Título: {result['title']}")
                    print(f"   Sistema: {result['system']}")
                    print(f"   Chunks creados: {len(result.get('chunks', []))}")
                else:
                    error_text = await response.text()
                    print(f"❌ Error al guardar: {response.status} - {error_text}")
                    return
                    
        except Exception as e:
            print(f"❌ Error de conexión al guardar: {e}")
            return
    
    # 2. Esperar un momento para que se procese
    print("\n2. Esperando procesamiento...")
    await asyncio.sleep(3)
    
    # 3. Verificar que se almacenó en Qdrant
    print("\n3. Verificando almacenamiento en Qdrant...")
    try:
        from qdrant_client import AsyncQdrantClient
        client = AsyncQdrantClient(url='http://localhost:6333')
        
        info = await client.get_collection('sapisu_knowledge')
        print(f"   Puntos totales en Qdrant: {info.points_count}")
        
        if info.points_count > 0:
            points = await client.scroll(
                collection_name='sapisu_knowledge',
                limit=3,
                with_payload=True
            )
            
            for point in points[0]:
                if point.payload and 'estimacion' in point.payload.get('content', '').lower():
                    print(f"   ✅ Encontrada incidencia: {point.payload.get('title', 'Sin título')[:50]}...")
                    break
                    
    except Exception as e:
        print(f"   ⚠️  Error verificando Qdrant: {e}")
    
    # 4. Probar búsqueda a través del chat
    print("\n4. Probando búsqueda a través del chat...")
    
    async with aiohttp.ClientSession() as session:
        try:
            search_data = {
                "query": "problema con estimación de consumo gas industrial",
                "tenant_slug": "default"
            }
            
            async with session.post('http://localhost:8000/api/v1/search/chat-public', 
                                   json=search_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Chat respondió correctamente")
                    print(f"   Confianza: {result.get('confidence', 0):.2f}")
                    print(f"   Fuentes encontradas: {len(result.get('sources', []))}")
                    print(f"   Respuesta: {result.get('answer', 'Sin respuesta')[:100]}...")
                    
                    if result.get('sources'):
                        for source in result['sources'][:2]:
                            print(f"   📄 Fuente: {source.get('title', 'Sin título')}")
                else:
                    error_text = await response.text()
                    print(f"❌ Error en búsqueda: {response.status} - {error_text}")
                    
        except Exception as e:
            print(f"❌ Error de conexión en búsqueda: {e}")
    
    print("\n=== Test completado ===")

if __name__ == "__main__":
    asyncio.run(test_incidence_workflow())
