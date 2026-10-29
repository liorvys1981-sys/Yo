# PERCEPTION CONTRACT (FASE 2)

PERCEPTION = informacion recibida del entorno. NUNCA identidad.

Percept preserva: source, timestamp, provenance, event/data type, confidence,
uncertainty, observation_state (PRESENT/ABSENT/UNCERTAIN/INSUFFICIENT_EVIDENCE),
integrity (content_hash verificable), correlation/trace_id, evidence_reference.

Separacion estructural: OBSERVATION != INTERPRETATION != IDENTITY != TRUTH.
- observation: lo detectado (provenance OBSERVED + integrity).
- interpretation: derivacion (INFERRED, exige evidence, nunca verdad).
- identity: PROHIBIDO como salida de percepcion (structural).
- truth: ningun evento es verdad automaticamente (is_fact=False estructural).

Soberania (FASE 3): la percepcion no escribe DigitalSelf, no modifica Identity/
Constitution, no otorga permisos, no eleva privilegios, no ejecuta acciones
externas, no declara verdad absoluta. Las 6 invariantes aplican en ingest.
