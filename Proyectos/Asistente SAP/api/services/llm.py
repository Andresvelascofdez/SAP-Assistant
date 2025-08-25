"""
Servicio de LLM para estructuración de contenido
Wiki Inteligente SAP IS-U
"""
import json
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from api.config import settings
from api.models.schemas import DocumentStructured
from api.utils.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Servicio para interacciones con LLM"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-3.5-turbo"
    
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
        tenant_slug: str
    ) -> Dict[str, Any]:
        """Generar respuesta de chat usando contexto recuperado"""
        
        prompt = self._get_chat_prompt()
        context = self._format_context(context_chunks)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"""
Tenant: {tenant_slug}
Pregunta: {query}

Contexto disponible:
{context}
"""}
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
