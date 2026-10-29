# AGENT RUNTIME TEST REPORT

Generado: 2026-10-09T07:30:36.216228+00:00Z

## Suites del runtime (recuentos REALES, ejecutados esta sesion)
- tests.test_runtime: rc=0 (17 tests, 0 FAIL/0 ERROR)
- tests.test_runtime_audit: rc=0 (10 tests, 0 FAIL/0 ERROR)
Nota: recuentos reales 17/10 (la referencia historica 16/15 correspondia a la
variante pre-reorg; los numeros actuales fueron verificados por ejecucion).

## Regresion completa
RUN1: 537 tests / 0 FAIL · RUN2: 537 tests / 0 FAIL ·
deterministic=True · suites=47

## §17
REVALIDATED. Zonas protegidas byte-identicas: {"constitution": true, "identity": true, "digital_self": true, "app_space": true}

## Cambios en tests (legitimos, documentados)
test_runtime_audit.py: header (RT_SRC = facade + rtpkg/*.py) y 4 aserciones
estructurales ajustadas al paquete (scans de seguridad: requests/openai/ollama/
did:key/set_constitution sobre codigo ejecutable real). Ninguna assertion
reducida; cobertura ampliada. test_runtime.py sin cambios.

## Controles ejecutados
Imports/excepciones/contratos (smoke 6 rutas + memoria + circuito): OK.
