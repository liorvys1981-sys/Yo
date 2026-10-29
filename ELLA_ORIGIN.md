# ELLA_ORIGIN — Acto de creacion de ELLA

## Cadena soberana ejecutada

```
YO Cognitive Twin  (existia)
  -> YO'S MODEL OF ELLA  (decision soberana: el YO NO contiene a ELLA)
  -> ELLA GENESIS  (ESTA FASE: acto de creacion)
  -> ELLA_ORIGIN  (registro sellado con content_hash + evidencia en ledger)
  -> ELLA Identity Proposal  (PROPOSED — requiere aprobacion soberana futura)
  -> ELLA Cognitive Twin  (PENDIENTE: no construido en genesis)
```

## Hechos del origin record

| Campo | Valor |
|---|---|
| namespace | ELLA (disjunto de YO) |
| created_by | DID soberana (SELF_REPORTED / SOVEREIGN_DECLARATION) |
| autonomy | DISABLED |
| genesis state | GENESIS_INCOMPLETE |
| evidencia | `ELLA/ELLA_ORIGIN.json` + entrada sellada en ledger |

## Reglas de separacion (enforcement estructural, no convencion)

1. ELLA **no es un modelo del YO**: el modelo del YO sobre ELLA vive en el namespace YO,
   etiquetado `provenance=INFERRED, subtype=YO_MODEL_OF_ELLA, not_ella_identity=True`.
2. ELLA **no vive dentro del YO Cognitive Twin**: self separado, raiz de almacen
   separada (`<root>/ELLA/`), modulo sin imports del self YO.
3. **Sin writes cross-namespace**: `enforce_separation` lanza `CrossNamespaceViolation`.
4. La identidad de ELLA nace de **declaracion soberana** — nunca de INFERRED/SYSTEM_DERIVED
   del sistema sobre ella.

## No implementado (deliberadamente)

Autonomia completa de ELLA, activacion de su identidad, cognitive twin de ELLA.
Genesis deja todo en PROPOSED/DISABLED hasta decision soberana explicita.
