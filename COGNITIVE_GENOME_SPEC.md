# COGNITIVE GENOME — Especificación

## Definición

Representación estructurada y versionada del Gemelo. Es el artefacto serializable que permite exportar, auditar y restaurar la identidad digital.

## Entidades mínimas

identidad, valores, creencias, rasgos, objetivos, roles, relaciones, conocimiento, experiencias, aprendizajes, patrones, contradicciones, preferencias, cambios_evolutivos.

## Esquema de todo elemento del genoma

```json
{
  "id": "gen:valor:franklin:001",
  "kind": "value",
  "content": {"statement": "crear valor duradero", "strength": 0.9},
  "provenance": "SELF_REPORTED | OBSERVED | INFERRED | SYSTEM_DERIVED | UNCERTAIN",
  "confidence": 0.0,
  "source": {"type": "conversation|reflection|system", "ref": "doc_id o event_id"},
  "first_seen": "ISO8601", "last_updated": "ISO8601",
  "version": 3,
  "evidence": ["ev:ledger:hash1", "ev:ledger:hash2"],
  "evolution": [{"from": 2, "to": 3, "change": "strength 0.7→0.9", "approved_by": "humano", "ts": "ISO8601"}]
}
```

## Reglas

1. **Procedencia o nada**: un elemento sin provenance es rechazado por el validador del genoma.
2. **INFERRED nunca presentado como hecho**: toda salida a INTERACTION etiqueta su origen.
3. **Versionado inmutable**: los cambios crean versiones; el historial no se edita (solo se revierte con nueva versión).
4. **Distinguibilidad**: el sistema siempre puede responder cuánto del genoma es declarado por el usuario vs inferido vs derivado del sistema.
5. **Export**: el genoma exporta completo (JSON firmado con la DID del gemelo) — soberanía de datos (SOVEREIGNTY.export).

## Validador (contrato, no implementación)

`validate_genome_element(elem) -> OK | REJECTED(reason)` — reasons: missing_provenance, invalid_confidence_range, missing_evidence_for_INFERRED, version_gap, contradicts_frozen_identity (elemento de identidad fundamental sin aprobación).
