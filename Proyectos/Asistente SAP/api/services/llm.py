"""
Servicio de LLM para estructuración de contenido
Wiki Inteligente SAP IS-U
"""
import json
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from config import settings
from models.schemas import DocumentStructured
from utils.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Servicio para interacciones con LLM"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model
    
    async def extract_structure(self, text: str) -> DocumentStructured:
        """Extraer estructura del texto usando LLM"""
        
        prompt = self._get_extraction_prompt()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Texto a estructurar:\n\n{text}"}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Intentar parsear JSON
            try:
                data = json.loads(content)
                return DocumentStructured(**data)
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")
                return DocumentStructured(
                    needs_clarification=True,
                    questions=["Could not automatically structure content. Please provide manual structure."]
                )
                
        except Exception as e:
            logger.error(f"Error calling LLM for structure extraction: {e}")
            return DocumentStructured(
                needs_clarification=True,
                questions=["Error processing content. Please provide manual structure."]
            )
    
    async def generate_chat_response(
        self, 
        query: str, 
        context_chunks: list, 
        tenant_slug: str,
        additional_context: str = None
    ) -> Dict[str, Any]:
        """Generar respuesta de chat usando contexto recuperado"""
        
        prompt = self._get_chat_prompt()
        context = self._format_context(context_chunks)
        
        # LOG DE DEPURACIÓN: Mostrar el contexto formateado final
        logger.info(
            "=== CONTEXTO FORMATEADO PARA LLM ===",
            tenant_slug=tenant_slug,
            query=query,
            context_length=len(context),
            has_additional_context=additional_context is not None,
            additional_context_length=len(additional_context) if additional_context else 0,
            formatted_context=context[:500] + "..." if len(context) > 500 else context
        )
        
        # GPT-4o-mini tiene 128,000 tokens de límite real
        # Configuramos límites más generosos
        MAX_ADDITIONAL_CONTEXT_TOKENS = 100000  # Mucho más generoso
        MAX_ADDITIONAL_CONTEXT_CHARS = MAX_ADDITIONAL_CONTEXT_TOKENS * 4  # ~400,000 caracteres
        
        if additional_context and len(additional_context) > MAX_ADDITIONAL_CONTEXT_CHARS:
            original_length = len(additional_context)
            logger.info(
                "=== CONTEXTO ADICIONAL EXTREMADAMENTE LARGO - GENERANDO RESUMEN ===",
                original_length=original_length,
                max_chars=MAX_ADDITIONAL_CONTEXT_CHARS,
                note="Solo archivos mayores a 400K caracteres necesitan resumen"
            )
            
            # Generar resumen del contenido largo
            additional_context = await self._summarize_large_content(additional_context)
            
            logger.info(
                "=== RESUMEN GENERADO ===",
                original_length=original_length,
                summary_length=len(additional_context),
                compression_ratio=f"{(len(additional_context)/original_length)*100:.1f}%"
            )
        else:
            # Log para mostrar que NO se necesita resumen
            if additional_context:
                logger.info(
                    "=== CONTEXTO ADICIONAL PROCESADO COMPLETO ===",
                    content_length=len(additional_context),
                    estimated_tokens=len(additional_context) // 4,
                    note="Archivo dentro del límite, se usa contenido completo"
                )
        
        # Preparar el prompt del usuario con todos los contextos
        user_prompt = f"""
Tenant: {tenant_slug}
Pregunta: {query}

Contexto disponible (RAG):
{context}"""
        
        if additional_context:
            user_prompt += f"""

Contexto adicional (archivo subido):
{additional_context}"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            answer = response.choices[0].message.content
            
            # Analizar confianza basado en el contexto
            confidence = self._calculate_confidence(query, context_chunks, answer)
            
            return {
                "answer": answer,
                "confidence": confidence,
                "needs_clarification": confidence < 0.6
            }
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return {
                "answer": "Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, inténtalo de nuevo.",
                "confidence": 0.0,
                "needs_clarification": True
            }
    
    def _get_extraction_prompt(self) -> str:
        """Prompt para extracción de estructura"""
        return """Eres un experto en SAP IS-U. Tu tarea es estructurar información de incidencias y documentación técnica.

Convierte el texto en un JSON con la siguiente estructura:
{
  "title": "Título descriptivo de la incidencia/documento",
  "root_cause": "Causa raíz del problema",
  "steps": ["Paso 1", "Paso 2", "Paso 3"],
  "risks": ["Riesgo 1", "Riesgo 2"],
  "needs_clarification": false,
  "questions": []
}

Instrucciones:
- Si el texto no contiene información suficiente para algunos campos, omítelos o déjalos vacíos
- Si faltan campos críticos, marca needs_clarification=true y añade 1-2 preguntas específicas
- Mantén los pasos concretos y accionables
- Incluye t-codes y tablas SAP en los pasos cuando sea relevante
- Los riesgos deben ser técnicos y específicos

Devuelve SOLO el JSON válido, sin explicaciones adicionales."""
    
    def _get_chat_prompt(self) -> str:
        """Prompt para respuestas de chat"""
        return """Eres un asistente experto en SAP IS-U que ayuda a consultores resolver incidencias.

Instrucciones:
- Responde SOLO con información del CONTEXTO proporcionado
- Da pasos concretos con t-codes y tablas SAP específicas
- Estructura tu respuesta: Causa → Pasos → Riesgos
- Si la información es insuficiente, pide aclaraciones específicas
- NUNCA inventes información que no esté en el contexto
- Cita las fuentes relevantes al final

Formato de respuesta:
**Causa probable:**
[Descripción de la causa]

**Pasos de resolución:**
1. [Paso concreto con t-code]
2. [Paso concreto con tabla/campo]
...

**Riesgos a considerar:**
- [Riesgo específico]

**Fuentes consultadas:**
- [Fuente 1]
- [Fuente 2]"""
    
    def _format_context(self, context_chunks: list) -> str:
        """Formatear chunks de contexto para el prompt"""
        if not context_chunks:
            return "No hay contexto disponible."
        
        formatted = []
        for i, chunk in enumerate(context_chunks[:5], 1):  # Máximo 5 chunks
            source = chunk.get('metadata', {}).get('source', 'Desconocido')
            content = chunk.get('content', '')
            formatted.append(f"[Fuente {i}: {source}]\n{content}")
        
        return "\n\n---\n\n".join(formatted)
    
    async def _summarize_large_content(self, content: str) -> str:
        """Resumir contenido largo usando el LLM"""
        try:
            # Dividir el contenido en chunks más pequeños si es necesario
            max_chunk_size = 15000  # ~3750 tokens por chunk
            
            if len(content) <= max_chunk_size:
                # Contenido pequeño, resumir directamente
                return await self._create_summary(content)
            else:
                # Contenido muy grande, dividir y resumir por partes
                chunks = []
                for i in range(0, len(content), max_chunk_size):
                    chunk = content[i:i + max_chunk_size]
                    chunk_summary = await self._create_summary(chunk)
                    chunks.append(chunk_summary)
                
                # Si hay múltiples resúmenes, combinarlos
                if len(chunks) > 1:
                    combined = "\n\n".join(chunks)
                    # Si el resultado combinado sigue siendo largo, resumir una vez más
                    if len(combined) > 8000:  # ~2000 tokens
                        return await self._create_summary(combined, final_summary=True)
                    return combined
                else:
                    return chunks[0]
                    
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            # Fallback: truncar si el resumen falla
            return content[:8000] + "\n\n[RESUMEN AUTOMÁTICO FALLÓ - CONTENIDO TRUNCADO]"
    
    async def _create_summary(self, content: str, final_summary: bool = False) -> str:
        """Crear un resumen de contenido específico"""
        summary_type = "resumen final conciso" if final_summary else "resumen detallado"
        
        summary_prompt = f"""Crea un {summary_type} del siguiente contenido, manteniendo toda la información técnica importante, números de transacciones, códigos, configuraciones y detalles relevantes.

IMPORTANTE:
- Mantén todos los códigos de transacciones SAP (como EL02, EUITRANS, etc.)
- Conserva números, configuraciones y parámetros técnicos
- Incluye todos los procedimientos y pasos importantes
- Mantén la estructura lógica del contenido
- Usa un formato claro y organizado

Contenido a resumir:
{content}

Resumen:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.1,  # Baja temperatura para consistencia
                max_tokens=1500 if final_summary else 2000
            )
            
            summary = response.choices[0].message.content
            return f"[RESUMEN AUTOMÁTICO]\n{summary}"
            
        except Exception as e:
            logger.error(f"Error calling OpenAI for summary: {e}")
            raise e
    
    def _calculate_confidence(self, query: str, context_chunks: list, answer: str) -> float:
        """Calcular confianza de la respuesta"""
        if not context_chunks:
            return 0.1
        
        # Factores que afectan la confianza:
        # 1. Número de chunks relevantes
        chunk_factor = min(len(context_chunks) / 3.0, 1.0)
        
        # 2. Longitud de la respuesta (respuestas muy cortas o muy largas son sospechosas)
        answer_length = len(answer.split())
        length_factor = 1.0
        if answer_length < 20:
            length_factor = 0.5
        elif answer_length > 300:
            length_factor = 0.8
        
        # 3. Si contiene t-codes o tablas (más específica)
        specificity_factor = 1.0
        if any(code in answer.upper() for code in ['EC85', 'ES21', 'EL31', 'EABL']):
            specificity_factor = 1.2
        
        # 4. Si admite incertidumbre ("podría", "posiblemente")
        uncertainty_phrases = ['podría', 'posiblemente', 'tal vez', 'no estoy seguro']
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            uncertainty_factor = 0.7
        else:
            uncertainty_factor = 1.0
        
        confidence = (chunk_factor * length_factor * specificity_factor * uncertainty_factor) * 0.85
        return min(max(confidence, 0.0), 1.0)
