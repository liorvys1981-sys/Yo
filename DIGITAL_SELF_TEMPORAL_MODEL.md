# DIGITAL SELF — MODELO TEMPORAL

## Estado del self en el tiempo

```
self(t) = {{ kind: version_vigente(kind, t) para kind en las 7 entidades }}
```

- Cada `EntityVersion` sella `ts` (creación).
- `as_of(ts)` selecciona la última versión con `v.ts <= ts` → **estado reconstruible en cualquier punto**.
- Consulta anterior a la primera versión → `None` (el self no existía aún así).
- Las proyecciones (YO Futuro/Potencial) NO escriben en DigitalSelf: viven en Insights y se comparan contra estados temporales reales para medir divergencia.

## Invariantes

1. El tiempo solo avanza en versiones nuevas; nunca se reescribe `ts`.
2. `reconstruct(ts)` es puramente de lectura (sin mutación del self actual).
3. Comparación v/v-1 alimenta el anti-deriva del Evolution Engine.
