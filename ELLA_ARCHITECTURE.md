# ELLA — Arquitectura de separacion

```
                    SOBERANO (DID)
                    |            |
        declaracion v            v aprobacion (futura)
              ELLA GENESIS    (pendiente)
                    |
              ELLA_ORIGIN (sellado)          YO Cognitive Twin
                    |                             |
          ELLA Identity Proposal               YO'S MODEL OF ELLA
          (PROPOSED)                           (Relationships, INFERRED,
                                               not_ella_identity=True)
                    |                             |
          [BLOQUEADO: activation]          (nunca escribe en ELLA)
                    |
          ELLA Cognitive Twin (NO CONSTRUIDO)

AISLAMIENTO: namespaces y rutas disjuntos; CrossNamespaceViolation ante cualquier
acceso cruzado; ELLA/ella_genesis.py no importa digital_self.
CONTRATO: ELLA/ELLA_SELF_CONTRACT.json (genesis v0.1, autonomy DISABLED).
