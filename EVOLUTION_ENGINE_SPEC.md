# EVOLUTION ENGINE — Especificación

## Pipeline obligatorio

```
EXPERIENCES → PATTERN → HYPOTHESIS → REFLECTION → PROPOSED CHANGE → REVIEW → APPROVAL
            → VERSIONED UPDATE → EVIDENCE
```

Ninguna etapa se salta. Ninguna modificación automática de elementos fundamentales de identidad (values, purpose, beliefs core) sin APPROVAL humano con frase-canal.

## Tipos de cambio y gates

| Cambio | Ejemplos | Gate |
|---|---|---|
| Menor (preferencias, fortalezas) | añadir preferencia | Evolution Engine autónomo + registro (AGENTE_CON_REGISTRO) |
| Mayor (objetivos, rasgos) | nuevo objetivo anual | humano (frase-canal) |
| Fundamental (values, purpose) | cambio de propósito declarado | humano × 2 (doble llave) + reversión garantizada |

## Reversibilidad

Todo cambio versionado es reversible: `revert(genome_element, to_version)` crea nueva versión restauradora (nunca edita historial). Estado EVOLUTION_LOCKED bloquea escrituras sobre el elemento durante revisión.

## Evidencia

Cada transición del pipeline produce evento en evidence_ledger con: patrón origen, hipótesis, reflexión, diff propuesto, aprobador, hash de versión resultante.

## Anti-deriva

El sistema compara el genoma cada N experiencias contra su estado v-1: divergencia no explicada por evoluciones aprobadas = incidente (Safety Agent audita).
