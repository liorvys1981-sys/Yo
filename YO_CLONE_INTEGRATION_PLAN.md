# YO CLONE — INTEGRATION PLAN (por etapas, solo con licencias verificadas y hardware)

Fecha: 2026-10-09T17:35:39.325772+00:00Z

## DECISIÓN (con evidencia)
- **Candidato principal: ai-avatar-system (MIT)** — plataforma completa (avatar real-time + TTS + frontend), arquitectura modular compatible con nuestros gates, licencia permisiva VERIFICADA, mantenimiento activo.
- **Complemento opcional: LiveTalking (Apache-2.0)** — motor WebRTC de streaming si se requiere menor latencia que la pila de ai-avatar; condición: TTS soberano (edge_tts es externo).
- **DESCARTADO: twin-mind-mirror** — sin licencia, sin capacidad visual, prácticas de seguridad deficientes.

## Etapas (cada una verificable, ninguna simulada)
0. **AUDITORÍA DE SEGURIDAD** del repo elegido (deps, auth, exposición de endpoints). Bloqueante antes de todo.
1. **VERIFICACIÓN DE LICENCIAS DE PESOS** (musetalk/wav2lip/er-nerf y voces): sin licencia compatible → BLOQUEADO.
2. **ENTORNO AISLADO**: contenedor sin red saliente excepto lo estricto; GPU (CUDA) — HARDWARE_BLOCKED en sandbox.
3. **ADAPTADOR** `yoclone/providers/avatar_engine.py`: implementa la interfaz de `CloneBuilder.generate()` + `TTSEngine`/`LipSyncEngine` (ya existentes, reportan BLOCKED hoy). El adaptador traduce: capturas autorizadas (onboarding) → motor externo; respuestas del Runtime → TTS → streaming.
4. **GATES**: toda llamada al motor pasa por `authorize_provider_transfer` (R1) ya probada. Latencia/interrupciones medidas por `LiveConversation` (ya implementado).
5. **PRUEBAS CON DATOS SINTÉTICOS** (nunca biométricos reales): fixtures sintéticos como los de la suite yoclone.
6. **PRUEBA DE CONVERSACIÓN REAL**: solo cuando 0-5 verdes en hardware real → entonces y solo entonces se podrá declarar el clon funcional.
7. **SOAK + DURABILIDAD**: 72h en infraestructura real (EXTERNAL).

## Bloqueos actuales (EXTERNAL/HARDWARE)
GPU/CUDA · pesos de modelos (licencia + descarga) · TTS soberano · credenciales. Nada se integra ni copia antes de etapa 1.

## Tareas locales pendientes (independientes, continuables)
- Tests del landing_yoclone (harness node pendiente).
- ZIP PARCIAL de entrega con manifiestos (FASE 3 de la sesión anterior).
