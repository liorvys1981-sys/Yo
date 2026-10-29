# ELLA IDENTITY ACTIVATION — TEST PLAN (diseno, NO ejecutado)

## Cobertura
- Archivo nuevo: `tests/test_r3_ella_activation.py` (a crear cuando se autorice la implementacion).
- Suites existentes que deben seguir verdes tras implementar: test_ella_genesis, test_r2_ella_adversarial,
  regression completa (17 suites).
- Fixtures: Authority real (Identity seed de test + AuthorizationGate con TODAY), clock inyectable.

## Plan (mapeo 1:1 con los 15 casos adversariales del diseno)
1. test_activacion_legitima — origin+proposal validos -> ACTIVE file con copia inmutable,
   activated_by=DID, ledger event, scaffold PENDING para entidades no-Identity, determinismo x2.
2. test_did_falso_rechazado
3. test_firma_ausente_rechazada
4. test_firma_invalida_rechazada
5. test_autorizacion_otra_accion_rechazada (ej. 'ELLA-genesis')
6. test_autorizacion_otro_namespace_rechazada (ruta ajena)
7. test_proposal_alterada_rechazada (content mismatch)
8. test_proposal_inexistente_rechazada
9. test_proposal_expirada_rechazada (day freshness)
10. test_doble_activacion_rechazada
11. test_origin_alterado_rechazado
12. test_caller_directo_rechazado (sin autorizacion)
13. test_objeto_arbitrario_rechazado
14. test_activar_identidad_yo_via_ella_rechazada
15. test_modificar_yo_desde_ella_rechazada
16. test_invariantes_post_activacion: no existen APIs de autonomia/memoria/agentes (scan + llamada fallida)
17. test_ledger_verificable + evidence artifact con hash
18. test_determinismo_doble_corrida

## DoD para la futura implementacion
cadena CODIGO->EJECUCION->TEST->EVIDENCIA->HASH; regression completa verde; sin cambios a
DigitalSelf/R1/R2; ledger verify=True; prohibiciones de autonomia intactas.
