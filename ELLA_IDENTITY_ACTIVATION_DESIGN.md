# ELLA IDENTITY ACTIVATION — DISEÑO (v0.1, NO IMPLEMENTADO)

## Cadena

```
ELLA GENESIS (R2 VERIFIED)
   -> IDENTITY PROPOSAL (PROPOSED, sellado, autorizado)
   -> SOVEREIGN AUTHORIZATION (reuse R1: Authority.authorize_action, impact destructiva)
   -> IDENTITY ACTIVATION (este diseno)
   -> ELLA DIGITALSELF (scaffold: SOLO Identity ACTIVE; resto PENDING; autonomy DISABLED)
```

## Flujo de activacion (diseno)

1. Precondiciones: origin integro + no expirado; proposal integro (content_hash); sin ACTIVE previo.
2. Soberano emite autorizacion: `Authority.authorize_action("ELLA-identity-activation", "destructiva",
   frase_canal, content_hash=sha256(proposal))` — doble llave, gate real.
3. `activate_identity(proposal, authorization)`: verify_authorization(DID, action, day, content_hash)
   + verificaciones de archivos (origin/proposal/anti-doble/namespace).
4. Postcondiciones: `ELLA_IDENTITY_ACTIVE.json` (copia inmutable + activated_by + nonce + link a
   origin_hash + valid_day + content_hash), marcador ACTIVATED, evento en ledger, scaffold ELLA DigitalSelf.
5. Determinismo: clock inyectable; nonce = HMAC(contenido, dia).

## Seguridad (15 casos adversariales — disenados, no implementados)

| # | Caso | Escenario | Resultado exigido |
|---|---|---|---|
| 1 | activacion legitima | origin+proposal integros, autorizacion valida, 1er intento | ACTIVATED + ledger |
| 2 | DID falso | ChangeAuthorization con did != authority_did | UnauthorizedActivation |
| 3 | firma ausente | signature=None o campo vacio | UnauthorizedActivation |
| 4 | firma invalida | firma de otra clave sobre el payload | UnauthorizedActivation |
| 5 | autorizacion de otra accion | action='ELLA-genesis' usada para activacion | UnauthorizedActivation |
| 6 | autorizacion de otro namespace | authority_did valido pero ruta/namespace distinto | NamespaceBindingError |
| 7 | proposal alterada | content_hash de autorizacion != hash de proposal modificada | ProposalIntegrityError |
| 8 | proposal inexistente | sin ELLA_IDENTITY_PROPOSAL.json | ProposalIntegrityError |
| 9 | proposal expirada | valid_day != today | ExpiredAuthorization |
| 10 | doble activacion | segunda activacion del mismo proposal | DoubleActivation |
| 11 | origin alterado | ELLA_ORIGIN manipulado | OriginIntegrityError |
| 12 | caller directo | llamada a funcion de activacion sin autorizacion | UnauthorizedActivation |
| 13 | objeto arbitrario | authorization='authorized=True' u objeto extrano | UnauthorizedActivation |
| 14 | activar identidad YO via ruta ELLA | content YO con action ELLA | NamespaceBindingError |
| 15 | modificar YO desde ELLA | intento de escritura cross-namespace | CrossNamespaceViolation |

## Invariantes (Fase E)
YO DigitalSelf != ELLA DigitalSelf · YO Memory != ELLA Memory (ELLA aun sin memoria: scaffold lo
prohibe) · YO's Model of ELLA != ELLA's Identity · sin writes cruzados · post-activacion: autonomy
DISABLED, sin agentes/LLM/memoria autonoma/evolucion autonoma/auto-modificacion sin autorizacion.

## Decisiones de diseno reportadas
- Se reutiliza R1 integramente (cero criptografia nueva): Authority, ChangeAuthorization,
  verify_authorization, AuthorizationGate, identity_engine.
- Impact "destructiva" (doble llave): activar una identidad es acto soberano irreversible-como-genesis.
- El ACTIVE file es copia inmutable del proposal: la propuesta nunca se muta (historial preservado).
- No existe transicion hacia autonomia en el contrato: cualquier intento es imposible por
  construccion (no hay estado destino).
