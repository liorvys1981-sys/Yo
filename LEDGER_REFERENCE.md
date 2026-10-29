# EVIDENCE LEDGER — referencia arquitectonica (GAP-21 estructural)

Los DATOS de la cadena de evidencia viven fisicamente en
`EL_YO/01_GOBIERNO/evidence/ledger.jsonl`. RAZON DE ARQUITECTURA/INMUTABILIDAD:
la cadena es append-only con hash encadenado desde GENESIS; mover el archivo
romperia la continuidad historica y todos los hashes sellados. NO se duplica;
NO se crea una segunda fuente de verdad.

Este directorio (21) es el AREA CANONICA del concepto Evidence Ledger:
- engine: 00_CONSTITUCION_EL_YO/el_yo/evidence.py (EvidenceLedger)
- datos: 01_GOBIERNO/evidence/ledger.jsonl (referencia, inmutable)
- verificacion: ledger.verify() == True (test en test_ledger_reference.py)

Estado: COMPLETE via referencias/manifests/contratos, sin duplicar el Ledger.
