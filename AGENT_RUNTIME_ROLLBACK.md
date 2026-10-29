# AGENT RUNTIME ROLLBACK

Snapshot VERIFICADO (hashes confirmados contra SNAPSHOT_MANIFEST.json):
`agent_runtime/.reorg_2026-10-08/` -> runtime.py.baseline, test_runtime.py.baseline,
test_runtime_audit.py.baseline

## Procedimiento
1. cp .reorg_2026-10-08/runtime.py.baseline agent_runtime/runtime.py
2. cp .reorg_2026-10-08/test_runtime.py.baseline agent_runtime/tests/test_runtime.py
3. cp .reorg_2026-10-08/test_runtime_audit.py.baseline agent_runtime/tests/test_runtime_audit.py
4. rm -rf agent_runtime/rtpkg
5. Limpiar __pycache__ (find agent_runtime -name __pycache__ -exec rm -rf {} +)
6. Verificar: sha256sum de los 3 archivos vs SNAPSHOT_MANIFEST.json
7. Pruebas de referencia: tests.test_runtime + tests.test_runtime_audit + regresion

## Estado
NO EJECUTADO (no fue necesario: validacion completa). Disponible y verificado.
