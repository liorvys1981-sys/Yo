# PROTECTED ZONES — protocolo de cambio (baseline EL_YO-BASELINE-VERIFIED-2026-10-08-001)

Zonas protegidas (41 archivos, hashes en BASELINE_VERIFIED.json): Constitucion,
Identity, DigitalSelf, CognitiveTwin, Sovereignty, Security, Governance,
EvidenceLedger(datos), §17 AppSpace, AgentRuntime, Memory, Cognition, Reasoning,
Autoconciencia, Emocion, Interaccion, Investigacion, Context, Agencia,
AppSpaceWebTools, Audit.

## Protocolo obligatorio para cualquier cambio en zona protegida
CAMBIO -> JUSTIFICACION -> IMPACTO -> RIESGO -> TEST -> REVALIDACION -> EVIDENCIA -> NUEVO HASH

1. Entrada previa en Evidence Ledger (type=protected_change_request).
2. Cambio minimo + test especifico de la zona.
3. Regresion completa x2 (0 FAIL, deterministic) + suites de la zona.
4. Si toca §17: revalidacion §17 completa obligatoria.
5. Sello posterior con nuevos hashes; baseline version bump (002...).

La proteccion NO impide evolucion legitima: exige disciplina de evidencia.
Cambios fuera de zonas protegidas (nuevos modulos, docs, gaps) siguen el ciclo
normal IMPLEMENT->TEST->EVIDENCE.
