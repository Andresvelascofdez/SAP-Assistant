#!/usr/bin/env python3
"""Check Qdrant collection status"""
import asyncio
from qdrant_client import AsyncQdrantClient

async def check_qdrant():
    try:
        client = AsyncQdrantClient(url='http://localhost:6333')
        
        # Ver info de la colección
        info = await client.get_collection('sapisu_knowledge')
        print(f'Colección sapisu_knowledge:')
        print(f'Puntos totales: {info.points_count}')
        
        # Obtener algunos puntos para ver la estructura
        if info.points_count > 0:
            points = await client.scroll(
                collection_name='sapisu_knowledge',
                limit=3,
                with_payload=True
            )
            
            print(f'\nPuntos encontrados: {len(points[0])}')
            for i, point in enumerate(points[0][:3]):
                print(f'Punto {i+1}:')
                print(f'  ID: {point.id}')
                if point.payload:
                    print(f'  Tenant: {point.payload.get("tenant", "N/A")}')
                    print(f'  Source: {point.payload.get("source", "N/A")}')
                    print(f'  Type: {point.payload.get("type", "N/A")}')
                    content = point.payload.get("content", "")
                    print(f'  Content: {content[:100]}...')
                print()
        else:
            print('La colección está vacía - no hay documentos almacenados aún')
            
    except Exception as e:
        print(f'Error conectando a Qdrant: {e}')

if __name__ == "__main__":
    asyncio.run(check_qdrant())
