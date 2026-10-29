# EVALUACION CONSTITUCIONAL — GEMELO COGNITIVO
Regla: ningun componente entra sin justificar capacidad concreta necesaria para el Gemelo Cognitivo.
## I. COMPONENTES PROPIOS (8)
| Componente | Contribucion al Gemelo | Areas | Verificacion | Decision |
|---|---|---|---|---|
| constitution_engine | Define autoridad y niveles del gemelo; sin ello el gemelo no tiene identidad normativa | 06/17 | 5 pytest PASS | **ENTRA** |
| authorization_gate | Ejecuta la autoridad: quien puede hacer que; protege capacidades del gemelo | 06 | 10 pytest PASS | **ENTRA** |
| evidence_ledger | Memoria de hechos del gemelo: que sabia, decidio, hizo; demostrable ante terceros | 11 | 13 tests (3+chaos) | **ENTRA** |
| webhook_gateway | Piel del gemelo: filtra todo lo que entra del mundo exterior | 06/08 | 6 pytest PASS | **ENTRA** |
| identity_engine | Quien es el gemelo: DID propio, credenciales, revocacion | 19 | 10 unittest PASS | **ENTRA** |
| state_engine | Estado declarativo de componentes: honestidad del sistema sobre si mismo | 17/20 | 6 unittest PASS | **ENTRA** |
| chaos_recovery | El gemelo puede demostrar que sobrevive: mid-write, tamper, concurrencia | 16 | 5 unittest PASS (encontro bug real) | **ENTRA** |
| cli_el_yo | Ventana del operador sobre el gemelo: status/verify/gate-check | 17/11 | 5 unittest PASS | **ENTRA** |

## II. REPOS DE OPEN_SOURCE_MATRIX (12)

### Division Swarm [Apache-2.0] P0
2. **FUNCION**: State machine durable con routing determinista, transiciones atomicas, crash recovery, replay/fork
3. **CONTRIBUCION AL GEMELO**: ES EL CORAZON DEL ESTADO DEL GEMELO: sin estado durable no hay gemelo persistente, solo chat efimero
4. **AREA**: 05 Memory / 20 Recovery / 07 Pipelines
5. **CAPACIDAD**: Mantiene OBJETIVOS del gemelo como estado maquina; recovers interrumpciones; replay audita 'que decidi'
6. **DATOS/MEMORIA**: Estado de ejecucion de cada objetivo/tarea del gemelo con historial replayable
7. **INTERACCION**: SoC: kernel (OpenFang) pide transiciones; Autonomic Kernel media efectos; evidence_ledger sella decisiones
8. **VERIFICACION**: Tests de crash/replay del propio repo + chaos suite (16) + SAOS gates al vendorar
9. **RIESGO**: Vendoring bloqueado por red; verificar test coverage real al clonar
10. **DECISION**: **ENTRA (ganador de capacidad Estado Durable)**

### OpenFang [MIT] P0
2. **FUNCION**: Runtime/kernel de agentes en Rust: kernel/runtime/memory/security, agentes continuos, test discipline fuerte
3. **CONTRIBUCION AL GEMELO**: EL CUERPO EJECUTOR DEL GEMELO: donde viven los agentes continuos que forman el gemelo
4. **AREA**: 04 Cognitive/Agents
5. **CAPACIDAD**: Ejecucion continua, aislamiento, runtime seguro de los procesos cognitivos
6. **DATOS/MEMORIA**: Contexto de ejecucion, memoria de trabajo de agentes, eventos de runtime
7. **INTERACCION**: Recibe politicas de Autonomic Kernel; persiste estado en Division Swarm; expone observabilidad a 11/21
8. **VERIFICACION**: Su 'strong test discipline' + nuestra suite 16 + gates SAOS
9. **RIESGO**: Rust toolchain; tamano del workspace al vendorar
10. **DECISION**: **ENTRA (ganador de capacidad Runtime de Agentes)**

### Autonomic Kernel [MIT] P0
2. **FUNCION**: Control plane confiable: sandbox, mediacion politica/efectos, epoch fencing, verificacion, recovery, audit
3. **CONTRIBUCION AL GEMELO**: EL CEREBRO INMUNE DEL GEMELO: sin mediacion de efectos, el gemelo puede ser secuestrado por un prompt
4. **AREA**: 06 Security
5. **CAPACIDAD**: Autoridad, capacidades y herramientas del gemelo protegidas por politica determinista
6. **DATOS/MEMORIA**: Politicas vigentes, epoch de ejecucion, registro de efectos autorizados/denegados
7. **INTERACCION**: Toda accion del runtime (OpenFang) pasa por su mediacion; alimenta evidence_ledger; compone con gates
8. **VERIFICACION**: Verificacion formal/epoch fencing del repo + adversarial tests + SAOS gates
9. **RIESGO**: Vendoring pendiente (red); complejidad de integracion
10. **DECISION**: **ENTRA (ganador de capacidad Control Plane de Seguridad)**

### SOVEREIGN [MIT] P1
2. **FUNCION**: Inferencia local-first, gobernanza, audit append-only, provenance, generacion determinista, memoria grafo+vector
3. **CONTRIBUCION AL GEMELO**: LA MEMORIA BIOGRAFICA DEL GEMELO: conocimiento con procedencia — sin ella el gemelo no sabe que sabe ni de donde
4. **AREA**: 05 Memory / 17 Governance / 11 Audit
5. **CAPACIDAD**: Memoria persistente con procedencia; distingue memoria derivada de fuente original
6. **DATOS/MEMORIA**: Grafo+vector de conocimiento, cadenas de provenance, auditoria append-only
7. **INTERACCION**: Runtime (OpenFang) consulta/memoria; Division Swarm guarda estado de procesos; Autonomic Kernel protege escrituras
8. **VERIFICACION**: Determinism tests + provenance verification + nuestra chaos suite
9. **RIESGO**: P1 (no P0): memoria interina puede cubrirse con evidence_ledger hasta vendorar
10. **DECISION**: **ENTRA (ganador de capacidad Memoria con Procedencia)**

### Oxios [MIT] P0
2. **FUNCION**: Supervisor+scheduler+state+memory+RBAC+Merkle audit+circuit breaker+MCP/A2A+budgets
3. **CONTRIBUCION AL GEMELO**: Capacidades parcialmente duplicadas: scheduler/state/memory solapan con Division Swarm y OpenFang
4. **AREA**: 06/08/21 (mapeo original)
5. **CAPACIDAD**: Circuit breaker y presupuestos NO cubiertos por el ganador
6. **DATOS/MEMORIA**: Interfaces MCP/A2A como puerta de herramientas
7. **INTERACCION**: Seria SEGUNDO kernel: viola regla anti-Frankenstein
8. **VERIFICACION**: n/a (no se vendoriza)
9. **RIESGO**: Duplicacion de kernel = incoherencia arquitectonica
10. **DECISION**: **ADAPTAR (extraer: circuit breaker, presupuestos, interfaz MCP/A2A; NO vendorizar como kernel)**

### AIOS [Licencia: auditoria requerida] P0
2. **FUNCION**: Conceptos kernel de agentes: scheduling, contexto, memoria/almacenamiento, herramientas, separacion kernel/SDK
3. **CONTRIBUCION AL GEMELO**: Conceptos ya cubiertos por OpenFang (kernel) + Division Swarm (scheduling de estado)
4. **AREA**: 04/23 (conceptual)
5. **CAPACIDAD**: Separacion kernel/SDK como principio de diseno
6. **DATOS/MEMORIA**: n/a
7. **INTERACCION**: Influencia de diseno en interfaces del runtime
8. **VERIFICACION**: n/a
9. **RIESGO**: Licencia no aclarada: bloquea vendoring
10. **DECISION**: **REFERENCIA (principios de separacion kernel/SDK; sin codigo)**

### Astra [Verificar antes de vendorar] P1
2. **FUNCION**: Microkernel multi-tenant, RBAC/OPA, DAG de tareas, Redis Streams, approvals, LLM routing, cost tracking
3. **CONTRIBUCION AL GEMELO**: Multi-tenancy y Redis Streams = peso operativo para un gemelo single-operator; DAG cubierto por Division Swarm
4. **AREA**: 07/21/08 (mapeo original)
5. **CAPACIDAD**: Cost tracking LLM (parcial, cubierto por presupuestos adaptados de Oxios)
6. **DATOS/MEMORIA**: n/a
7. **INTERACCION**: Redundante con ganadores
8. **VERIFICACION**: n/a
9. **RIESGO**: Licencia sin verificar + solapamiento alto
10. **DECISION**: **DESCARTAR**

### AOS Agentic OS [Verificar componente a componente] P1
2. **FUNCION**: Trust ramp por capacidades: niveles shadow/approval/autonomous; roles orchestrator/health/advisor
3. **CONTRIBUCION AL GEMELO**: El TRUST RAMP es la capacidad unica: el gemelo gana autonomia por evidencia, no por defecto
4. **AREA**: 17 Governance (conceptual)
5. **CAPACIDAD**: Promocion/degradacion de niveles de autonomia basada en historial verificado
6. **DATOS/MEMORIA**: Nivel de confianza actual por capacidad, con evidencia acumulada
7. **INTERACCION**: Se integra como POLITICA sobre nuestro AuthorizationGate (ya implementa niveles): degradacion automatica
8. **VERIFICACION**: Tests de degradacion/promocion deterministas
9. **RIESGO**: Licencia sin verificar: se adopta el MODELO, no el codigo
10. **DECISION**: **ADAPTAR (modelo trust-ramp como politica del gate; sin vendoring)**

### Autonomous Multi-Agent Software Factory [Verificar] P0
2. **FUNCION**: FSM, gates deterministas, presupuestos de ejecucion, aislamiento worktree, SAST, invariantes, recovery/resume
3. **CONTRIBUCION AL GEMELO**: El GEMELO QUE SE AUTO-MEJORA: pipeline determinista para que el gemelo evolucione su propio codigo con gates
4. **AREA**: 07 Pipelines / 23 Research-Evolution
5. **CAPACIDAD**: Evolucion controlada del gemelo: cambios de software pasan por gates ejecutables, no por fe
6. **DATOS/MEMORIA**: Artefactos de build, resultados SAST, invariantes verificados por release
7. **INTERACCION**: Consumido por SAOS17 como disciplina de fases; compone con Division Swarm (estado) y gates (16/17)
8. **VERIFICACION**: Sus gates deterministas + SAOS17 20 gates + chaos suite
9. **RIESGO**: Solapa FSM con Division Swarm: se usan SUS GATES, no su FSM
10. **DECISION**: **ADAPTAR (gates deterministas + worktree isolation + invariantes; FSM queda en Division Swarm)**

### AAiOS [Verificar] P1
2. **FUNCION**: GenericAgent, capability manifests, DAG, checkpoint/crash-resume, aprobacion humana, model router, memoria por capas
3. **CONTRIBUCION AL GEMELO**: Toda capacidad listada cubierta por ganadores (OpenFang, Division Swarm, Autonomic Kernel, SOVEREIGN)
4. **AREA**: 04/20/21 (mapeo original)
5. **CAPACIDAD**: n/a (redundante)
6. **DATOS/MEMORIA**: n/a
7. **INTERACCION**: Frankenstein si se suma
8. **VERIFICACION**: n/a
9. **RIESGO**: Licencia sin verificar + redundancia total
10. **DECISION**: **DESCARTAR**

### Sovereign AI [Dual; uso enterprise requiere licencia comercial] P1
2. **FUNCION**: Identidad criptografica, memoria hash-chained, inferencia/auditoria firmada, patrones de soberania
3. **CONTRIBUCION AL GEMELO**: Capacidad YA IMPLEMENTADA en identity_engine (DID did:key, VC, revocacion) + evidence_ledger (hash chain)
4. **AREA**: 19 (mapeo original)
5. **CAPACIDAD**: n/a (cubierto in-house)
6. **DATOS/MEMORIA**: n/a
7. **INTERACCION**: nuestros modulos 01_GOBIERNO/02_IDENTIDAD ya cubren
8. **VERIFICACION**: nuestros 10 tests de identidad + chaos
9. **RIESGO**: LICENCIA COMERCIAL: incompatible con vendoring sin coste
10. **DECISION**: **DESCARTAR (capacidad cubierta in-house con licencia libre)**

### Sovereign Knowledge Compiler [Verificar] P1
2. **FUNCION**: Pipeline de conocimiento determinista, sync CRDT, ledger de conflictos, memoria orientada a provenance
3. **CONTRIBUCION AL GEMELO**: Capacidad UNICA no cubierta: sincronizacion de memoria entre nodos con resolucion de conflictos
4. **AREA**: 05 Memory / 23 (extension)
5. **CAPACIDAD**: Cuando el gemelo sea multi-nodo: memoria consistente con provenance entre ubicaciones
6. **DATOS/MEMORIA**: Conflictos de conocimiento resueltos con trazabilidad
7. **INTERACCION**: Futuro: capa sobre SOVEREIGN cuando haya segundo nodo (Capa 05 docs)
8. **VERIFICACION**: CRDT convergence tests (del repo) al vendorar
9. **RIESGO**: NO necesario ahora (single-node): violaria 'minimo pero suficiente' si entra hoy
10. **DECISION**: **ADAPTAR DIFERIDO (solo cuando exista segundo nodo; hoy REFERENCIA)**

## III. ARQUITECTURA MINIMA RESULTANTE (anti-Frankenstein)

```
Nucleo cognitivo (gemelo):
  Division Swarm  = estado durable (objetivos, recuperacion, replay)   [ENTRA]
  OpenFang        = runtime/kernel de agentes                          [ENTRA]
  Autonomic Kernel= mediacion de efectos, sandbox, politicas           [ENTRA]
  SOVEREIGN       = memoria grafo+vector con procedencia               [ENTRA]
In-house (ya implementado + probado):
  constitution + gates + evidence_ledger + identity + state + webhook + chaos + cli
Adaptado (patrones, no codigo):
  Oxios      -> circuit breaker, budgets, interfaz MCP/A2A
  AOS        -> trust-ramp (promocion de autonomia por evidencia) sobre el gate
  SoftFactory-> gates deterministas + worktree isolation (disciplina SAOS17)
  AIOS       -> separacion kernel/SDK (principio)
  Knowledge Compiler -> diferido a segundo nodo (hoy: nada)
Descartados:
  Astra (redundante, licencia), AAiOS (redundante, licencia),
  Sovereign AI (licencia comercial + capacidad cubierta in-house)
Regla aplicada: 1 ganador por capacidad; criterios: licencia, determinismo,
ajuste al gemelo, mantenibilidad, soberania, coste.
