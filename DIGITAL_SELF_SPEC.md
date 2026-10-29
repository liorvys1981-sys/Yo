# DIGITAL SELF — SPEC v2.0.0 (evolucion soberana de v1.0.0, historial preservado) 2026-10-08)

## Contrato fundacional del Cognitive Twin

```
DigitalSelf
├── Identity       (FUNDAMENTAL: no admite INFERRED/SYSTEM_DERIVED)
├── Values         (FUNDAMENTAL: idem)
├── Beliefs      (FUNDAMENTAL desde v2.0.0: no admite INFERRED/SYSTEM_DERIVED directo)
├── Goals
├── Traits
├── Relationships
└── Experiences
```

## Regla de capas (innegociable)

| Capa | Rol |
|---|---|
| **DigitalSelf v2.0.0** | estructura estable del YO (v1.0.0 preservado en DIGITAL_SELF_EVOLUTION_v1_to_v2.json) — lo que el gemelo ES |
| Memory | registra y conserva experiencias/contexto — NO define el YO |
| Reflection | interpreta — NO redefine |
| Evolution | propone cambios y los versiona a través del gate — NO redefine la estructura |
| Cognitive Graph | representa relaciones — NO define por sí mismo la identidad |

## Principios

1. **Una entidad por kind** (Identity ×1, Values ×1, …).
2. **Provenance o nada**: toda versión lleva procedencia; Identity/Values solo OBSERVED o SELF_REPORTED.
3. **INFERRED jamás como hecho**: exige evidence y confidence; se presenta etiquetado.
4. **Historial inmutable**: versiones selladas con `content_hash` (tamper-evidence); mutación externa detectada por `verify_integrity()`.
5. **Reconstrucción temporal**: `as_of(ts)` por entidad; `reconstruct(ts)` para el self completo.
6. **Identity/Values cambian solo con approved_by=humano** en su cadena de evolución.

## Estado

FROZEN. Cualquier cambio a este contrato = gate de evolución con versión MAYOR.
Implementación de referencia: `impl/digital_self.py` (17/17 tests, evidencia con hash).
