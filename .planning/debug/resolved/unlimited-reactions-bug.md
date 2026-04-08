---
status: awaiting_human_verify
trigger: "Usuarios pueden reaccionar múltiples veces a un mensaje de broadcast sin límite. El UniqueConstraint nunca fue creado."
created: 2026-04-07T00:00:00Z
updated: 2026-04-07T00:00:00Z
---

## Current Focus
hypothesis: "Fix aplicado y verificado internamente. Esperando confirmación del usuario."
test: "Verificar que el constraint existe y que IntegrityError se lanza en duplicados"
expecting: "Constraint uq_broadcast_user_reaction existe en BD, IntegrityError es capturado por check_and_register_reaction"
next_action: "Usuario debe confirmar que el fix funciona en su entorno"

## Symptoms
expected: "Un usuario solo puede reaccionar una vez por mensaje de broadcast"
actual: "Usuarios pueden reaccionar múltiples veces sin límite"
errors: []
reproduction: "Usuario reacciona varias veces al mismo mensaje de broadcast"
started: "El constraint nunca fue creado"

## Eliminated

## Evidence
- timestamp: 2026-04-07
  checked: "models/models.py líneas 264-268"
  found: "Constraint único agregado: UniqueConstraint('broadcast_id', 'user_id', name='uq_broadcast_user_reaction')"
  implication: "Modelo ahora refleja el constraint"

- timestamp: 2026-04-07
  checked: "BD broadcast_reactions"
  found: "Constraint uq_broadcast_user_reaction creado, 0 grupos de duplicados restantes"
  implication: "Fix aplicado correctamente en BD"

- timestamp: 2026-04-07
  checked: "IntegrityError test"
  found: "IntegrityError capturado correctamente al intentar insertar duplicado"
  implication: "check_and_register_reaction capturará el error"

- timestamp: 2026-04-07
  checked: "tests/unit/test_broadcast_service.py"
  found: "14 passed"
  implication: "Fix no rompe funcionalidad existente"

## Resolution
root_cause: "El UniqueConstraint (broadcast_id, user_id) nunca fue creado ni en el modelo Python ni en la BD. La migración existente f7d08ca1ce1a tenía dependencia incorrecta y nunca se aplicó."
fix: "1) Actualizar BroadcastReaction.__table_args__ con UniqueConstraint, 2) Crear nueva migración 20250407_add_unique_to_broadcast_reactions que depende de 7c158f7483f5"
verification: "Constraint existe en BD, IntegrityError se lanza en duplicados, tests pasan"
files_changed:
  - "models/models.py": Agregado UniqueConstraint a BroadcastReaction
  - "alembic/versions/20250407_add_unique_to_broadcast_reactions.py": Nueva migración creada y aplicada
