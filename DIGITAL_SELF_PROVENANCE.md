# DIGITAL SELF — PROVENANCE

## Cinco etiquetas obligatorias

| Etiqueta | Significado | Exige evidence |
|---|---|---|
| OBSERVED | observado por el sistema | recomendado |
| SELF_REPORTED | declarado por el usuario | no |
| INFERRED | inferido | **sí, obligatorio** |
| SYSTEM_DERIVED | derivado por proceso del sistema | no |
| UNCERTAIN | incierto | no |

## Restricciones

- Identity y Values (fundamentales): solo OBSERVED o SELF_REPORTED. INFERRED/SYSTEM_DERIVED rechazados (`FUNDAMENTAL_INFERRED`).
- INFERRED sin evidence → rechazo (`INFERRED_WITHOUT_EVIDENCE`).
- `provenance_breakdown()`: distinguibilidad — cuánto del self es declarado vs observado vs inferido vs derivado (entidades sin versiones se saltan).

## Interacción con otros componentes

- Reflection/Pattern producen INFERRED → pasan por Evolution como propuesta, nunca escriben directo.
- Memory conserva el episodio origen (source_ref) que alimenta la evidencia de la versión.
