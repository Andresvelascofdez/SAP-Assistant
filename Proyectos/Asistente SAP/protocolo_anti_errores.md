# 🛡️ Protocolo Anti-Errores (Copilot/Claude) — Herramienta RAG SAP IS-U

## 0) Principios innegociables
- No tocar código estable sin: **(1) issue documentado, (2) plan de cambio, (3) PR con tests**.
- Cambios **mínimos y atómicos** (una intención por PR).
- **Prohibido** crear ficheros temporales, “dummy”, mocks vacíos o clases sin uso.
- **No crear ficheros de testing artificiales**: los tests deben escribirse en `/tests/` y cubrir la funcionalidad real → no scaffolds inventados.
- Las correcciones deben hacerse sobre **ficheros completos**, asegurando que no se pierde funcionalidad existente ni se rompe código que funciona.
- Guardado **recurrente y consistente**: todo archivo modificado debe guardarse en disco (sin fragmentos ni buffers corruptos).
- **Subir siempre a GitHub**: commits frecuentes, sin dejar código local sin versionar (evita ficheros mal cacheados).

---

## 1) Flujo Git disciplinado
**Branching**
- `main` (protegida, merge solo con PR y CI verde)
- `feat/<scope>` | `fix/<bug>` | `chore/<tarea>` | `refactor/<módulo>`

**Commits (Conventional Commits)**
- `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`, `perf:`
- Mensaje: qué + por qué + impacto (API/DB si aplica)
- Frecuencia: cada paso significativo (≤30 min/commit)

**Push seguro**
- `pre-commit` activo (lint, mypy, tests, secrets scan)
- Nunca `--force` salvo hotfix con aprobación

---

## 2) Política sobre ficheros
- **Correcciones → archivo completo**: Copilot debe devolver el fichero entero, no un parche parcial, para evitar inconsistencias.
- **Nada de archivos de prueba aislados** (“test_file.py”, “sandbox.py”) → los tests deben integrarse en `/tests` siguiendo Pytest.
- **Nada de duplicados** (“Copy of …”, `*_bak.py`, `tmp_*.py`).
- **Guardado recurrente**: todo cambio se guarda y sube → no se trabaja con cachés corruptos ni con “working copies” sin commit.

---

## 3) Guardarraíles para Copilot/Claude
**Prompt de edición segura:**
> “Haz un diff mínimo y autocontenido. No crees archivos de prueba aislados ni clases vacías. Si corriges, devuelve el fichero completo manteniendo toda funcionalidad previa. Guarda y versiona de forma recurrente. No generes mocks ni scaffolds fuera de `/tests`. Mantén firmas públicas intactas. Si requiere DB, añade migración Alembic idempotente.”

**Prompt de verificación:**
> “Valida que los cambios cumplen los Acceptance Criteria, que no se han eliminado funcionalidades existentes, que el archivo completo se mantiene coherente, que los tests están en `/tests` y no hay basura. Explica cada línea que modifica lógica.”

---

## 4) CI y control de calidad
- CI debe rechazar cualquier commit con:
  - Archivos “basura” (`tmp`, `sandbox`, `*_bak.py`, etc.)
  - Tests fuera de `/tests`
  - Clases/módulos sin referencias
- **Check recurrente**: CI asegura que todos los ficheros se guardaron y subieron (no quedan sin trackear).
- **Tests primero (TDD pragmático)**: reproducir bug → fix en fichero completo → test verde.

---

## 5) Checklist de PR
Antes de abrir PR:
- [ ] Issue vinculado  
- [ ] Archivo completo guardado (sin fragmentos)  
- [ ] Tests en `/tests` (no archivos sueltos)  
- [ ] Sin ficheros temporales/dummy  
- [ ] Documentado riesgo/rollback  

Durante revisión:
- [ ] El diff no crea archivos de prueba artificiales  
- [ ] No se rompe funcionalidad existente  
- [ ] Logs y errores claros (con tenant/doc_id/request_id)  

Merge:
- [ ] CI verde: lint + mypy + pytest + alembic  
- [ ] No hay archivos cacheados o corruptos  
- [ ] Commit/tag semántico si es release  

---

## 6) Estrategia de seguridad contra “ficheros basura”
- **Pre-commit hook**: falla si aparecen archivos fuera de estructura esperada (`/api`, `/scheduler`, `/tests`, `/web`, `/docs`).  
- **CI “scan job”**: bloquea PRs con:
  - `sandbox.py`, `test_file.py`, `tmp_*.py`
  - Archivos sin extensión reconocida
  - Tests fuera de `/tests`

---

## 7) Buenas prácticas adicionales
- **Revisión de ficheros completos** → evita “código zombie” perdido en caché.
- **Commits frecuentes** → sube cada avance a GitHub para no perderlo.
- **No dependencias innecesarias**: revisar cualquier `import` sugerido por Copilot.
- **Nunca exponer secretos en código** (usar `.env` + Secrets de Actions).
- **Versionado semántico** en cada entrega (`v1.2.3`).

---

✅ Con este protocolo, Copilot/Claude trabajan siempre sobre **archivos completos y funcionales**, sin generar “basura de testing”, con **guardado y subida recurrente a GitHub**. Esto evita errores por cachés, inconsistencias o código fantasma.
