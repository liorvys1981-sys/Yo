# CAPA_B_CROSSWALK — Arquitectura A (cognitiva) ↔ B (operacional)

24 correspondencias A↔B + 8 areas B sin correspondencia directa. Toda entrada con evidencia; ninguna equivalencia inventada. Sin carpetas vacias creadas.

| Area A | Area B | Tipo | Componentes reales | Evidencia (tests) | Gaps | Riesgo | Accion |
|---|---|---|---|---|---|---|---|
| 00_CONSTITUCION_EL_YO | 00_CORE / IDENTIDAD | COMPOSITE | 00: el_yo (constitution, gates, evidence); 01_IDENTIDAD: identity.py (DID/VC) | R1 12/12; fase2 identidad; test_gobierno | sin gap | ninguno | no |
| 01_IDENTIDAD | 00_CORE / IDENTIDAD | PARTIAL_CORRESPONDENCE | identity.py (DID, VC, revocacion) | fase2 10/10 | sin gap | baja | no |
| 02_MEMORIA | 19_PERSISTENCIA_Y_MEMORIA | COMPOSITE | persistent_memory.py; vector_memory.py; memory_model.py | G5 10/10; OM memory 7/7 | sin gap | ninguno | no |
| 03_PERCEPCION | 04_INTELIGENCIA_COGNITIVA | PARTIAL_CORRESPONDENCE | estados de percepcion embebidos en CognitiveEvent (12) | post284 suites | GAP: sin motor de percepcion standalone | media | DOCUMENTACION+gap futuro |
| 04_COGNICION | 04_INTELIGENCIA_COGNITIVA | COMPOSITE | reflection.py; insights.py | G6 14/14; G10 14/14 | sin gap | ninguno | no |
| 05_RAZONAMIENTO | 04_INTELIGENCIA_COGNITIVA | COMPOSITE | relationship_model.py (Decision/Policy/Trust) | OM decision suite | sin gap | ninguno | no |
| 06_APRENDIZAJE | 21_EVOLUCION_Y_AUTOPOIESIS | PARTIAL_CORRESPONDENCE | feedback_loop.py (observation->proposal->G8) | OM feedback tests | GAP: aprendizaje pesado (LoRA/weights) no existe; solo aprendizaje estructural | media | GAP FUTURO |
| 07_INTENCION | 05_ORQUESTACION_AGENTES | PARTIAL_CORRESPONDENCE | Goals via pipeline G8; GoalsAPI en contratos | G8 15/15 | GAP: sin modelo de intencion standalone | baja | DOCUMENTACION |
| 08_AGENCIA | 05_ORQUESTACION_AGENTES | COMPOSITE | swarm.py; Agent Runtime (00_CONSTITUCION_EL_YO/agent_runtime) | G9 12/12; runtime suites | sin gap | ninguno | no |
| 09_ACCION | 17_CORE_SYSTEM_EXEC | PARTIAL_CORRESPONDENCE | sin ejecucion externa v1 (constitucion); MCP gateway en 10 | decision NEVER test | GAP por diseno: ejecucion externa deshabilitada v1 | baja | no (constitucional) |
| 10_INTERACCION | 11_INTERFACES_USUARIO | COMPOSITE | chat.py; realtime.py (SSE/WS/Voice sin backend); interaction_to_cognition.py | OM gaps 16/16 | GAP: frontend real ausente; voz sin proveedor (BLOCKED) | media | BLOQUEO EXTERNO |
| 11_EMOCION | 18_ALQUIMIA_Y_SINTONIA | PARTIAL_CORRESPONDENCE | emotion_engine.py (senales, contradicciones, anti-manipulacion) | 7/7 | GAP: 'sintonia' relacional avanzada no implementada | media | GAP FUTURO |
| 12_AUTOCONCIENCIA | 04_INTELIGENCIA_COGNITIVA | COMPOSITE | self_awareness.py; reflective_metacognition.py | post284 18/18 + audit | sin gap | ninguno | no |
| 13_CONTEXT | 04_INTELIGENCIA_COGNITIVA | DIRECT | context_assembly.py | OM 7/7 | sin gap | ninguno | no |
| 14_DIGITAL_SELF | 00_CORE / IDENTIDAD | COMPOSITE | digital_self.py (v2.0.0 FROZEN); genome.py; genome_store.py; cognitive_api.py | 20/20; fase3; fase4 | sin gap | ninguno | no |
| 15_COGNITIVE_TWIN | 04_INTELIGENCIA_COGNITIVA | COMPOSITE | cognitive_twin_yo.py; maturity.py; ELLA (producto en APP_YO/ELLA con genesis/activation/foundation) | P10 suites | GAP: visual twin no existe (documentado) | baja | DOCUMENTACION |
| 16_APP_SPACE | 14_ECOSYSTEM_EXTERNOS | COMPOSITE | web_tools.py; APP_YO/app_space (registry/bridge/sync; FROZEN §17) | §17 14/14 REVALIDATED; app_space 23/23 | GAP: conectores externos reales BLOCKED (sin credenciales) | media | BLOQUEO EXTERNO |
| 17_SOVEREIGNTY | 03_SOBERANIA_DATOS | COMPOSITE | sovereignty.py (export/verify); authority.py (R1); privacy_classification en manifests | G11 20/20; R1 12/12 | sin gap | ninguno | no |
| 18_SECURITY | 07_SEGURIDAD_Y_PERMISOS | COMPOSITE | webhook.py (frontera HMAC); runtime SovereigntySecurity (zero-trust) | webhook tests; runtime adversarial | sin gap | ninguno | no |
| 19_GOVERNANCE | 20_GOBERNANZA_Y_POLITICAS | DIRECT | pipeline_evolution.py; evolution_engine.py; state_engine.py | G8 15/15; fase3; fase4 | sin gap | ninguno | no |
| 20_AUDIT | 12_LOGS_Y_MONITOREO + 22_DIAGNOSTICO_Y_RECOVER | COMPOSITE | observability.py (logs/metrics/tracing/health/audit); cli.py | OM gaps 16/16 | sin gap | ninguno | no |
| 21_EVIDENCE_LEDGER | 00_CORE / IDENTIDAD | PARTIAL_CORRESPONDENCE | datos fisicos en 01_GOBIERNO/evidence (inmutable); engine en 00 | ledger verify=True | GAP estructural menor: datos fuera del dir del area (documentado, inamovible) | baja | DOCUMENTACION |
| 22_TESTING_VALIDATION | 16_SIMULACION_Y_CHAOS + 22_DIAGNOSTICO_Y_RECOVER | COMPOSITE | suites distribuidas (37 archivos test_*); chaos evidence en 04_CHAOS_TESTS | 39 suites x2 457/457 det=True | sin gap | ninguno | no |
| 23_INVESTIGACION_EXPERIMENTACION_Y_EVOLUCION | 13_LABORATORIO_CREATIVO + 21_EVOLUCION_Y_AUTOPOIESIS | COMPOSITE | research_engine.py (9 lentes, reproducibilidad, evaluacion, evolucion G8+R1) | research suite; 18/18 | GAP: autopoiesis completa (auto-mantenimiento) parcial: recovery existe (chaos restart), generacion de nuevas capacidades NO (y no debe sin autorizacion) | media | GAP FUTURO |

## Areas B sin correspondencia directa

| Area B | Evidencia real | Estado |
|---|---|---|
| 01_INFRAESTRUCTURA_FISICA | EL_YO_SOBERANO 46 docs IaC; 0 desplegado | BLOCKED (hardware) |
| 02_REDES_Y_CONECTIVIDAD | EL_YO_SOBERANO capa 02 docs | BLOCKED (hardware/red) |
| 06_AUTOMATIZACION_Y_SCRIPTS | cli.py (20_AUDIT); scripts en docs | PARTIAL (docs) |
| 08_DOCUMENTACION_Y_GUIAS | docs en raiz APP_YO/EL_YO + manifests | COMPLETE (documentacion) |
| 09_MARCO_LEGAL_Y_CUMPLIMIENTO | EL_YO_SOBERANO 13 legal docs; sin codigo en el arbol 24 | PARTIAL (documentacion) |
| 10_FINANZAS_Y_TRANSACCIONES | EL_YO_SOBERANO 08 docs; sin codigo en el arbol 24 | PARTIAL (documentacion) |
| 15_RESERVAS_Y_OFF_GRID | EL_YO_SOBERANO 14 docs; 0 hardware | BLOCKED |
| 18_ALQUIMIA_Y_SINTONIA | sin correspondencia directa; parcial via 11_EMOCION | NO_DIRECT_CORRESPONDENCE |
