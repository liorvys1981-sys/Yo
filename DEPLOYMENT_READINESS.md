# DEPLOYMENT READINESS — EL_YO (baseline EL_YO-BASELINE-OPERATIONAL-2026-10-08-001)

Estado: B — OPERATIONAL_WITH_DOCUMENTED_EXTERNAL_BLOCKERS. No se certifica
produccion 24/7 desde el sandbox. El software esta listo; la infraestructura
operativa es la dependencia externa.

## Que esta listo (verificado)
47 suites / 537 tests x2 determinista · §17 REVALIDATED · 6/6 invariantes ·
supervisor 11/11 · ledger verify=True · backup/restore del ledger verificado.

## Que falta (EXTERNAL) — detalle completo en EXTERNAL_DEPENDENCIES.json
1. Supervisor persistente de plataforma (systemd/contenedor) — aceptacion:
   auto-restart <30s tras kill; preservacion de cola.
2. Redis: solo si se escala a multi-proceso (proceso unico actual no lo requiere).
3. DB persistente de produccion (Postgres/SQLite-WAL) + backups automatizados.
4. Red/credenciales/proveedores (voz, GPT-4o, conectores) con gestor de secretos.
5. Health endpoint + alertas reales.
6. Soak test 72h en infraestructura real.
7. Restore drill programado.

## Criterio de despliegue
Ningun criterio se da por cumplido sin prueba en infraestructura real.
