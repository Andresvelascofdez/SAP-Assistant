#!/usr/bin/env python3
"""
Test interno para verificar conexión con OpenAI
"""
import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

async def test_openai_connection():
    """Test de conexión con OpenAI"""
    # Cargar variables de entorno
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    print(f"🔑 API Key configurada: {'Sí' if api_key else 'No'}")
    if api_key:
        print(f"🔑 API Key empieza con: {api_key[:10]}..." if len(api_key) > 10 else "Key muy corta")
    
    # Test de embeddings
    client = AsyncOpenAI(api_key=api_key)
    
    print("\n📡 Testeando embeddings...")
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input="test"
        )
        print("✅ Embeddings funcionando correctamente")
    except Exception as e:
        print(f"❌ Error en embeddings: {e}")
        return False
    
    print("\n🤖 Testeando chat con gpt-4o-mini...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente útil."},
                {"role": "user", "content": "Di 'test exitoso'"}
            ],
            max_tokens=50
        )
        message = response.choices[0].message.content
        print(f"✅ Chat funcionando: {message}")
    except Exception as e:
        print(f"❌ Error en chat: {e}")
        return False
    
    print("\n🤖 Testeando chat con gpt-4.1-preview (modelo que está fallando)...")
    try:
        response = await client.chat.completions.create(
            model="gpt-4.1-preview",
            messages=[
                {"role": "system", "content": "Eres un asistente útil."},
                {"role": "user", "content": "Di 'test exitoso'"}
            ],
            max_tokens=50
        )
        message = response.choices[0].message.content
        print(f"✅ Chat con gpt-4.1-preview funcionando: {message}")
    except Exception as e:
        print(f"❌ Error en chat con gpt-4.1-preview: {e}")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_openai_connection())
