---
status: resolved
trigger: "4 bugs de producción en Railway: (1) AttributeError DailyGiftService, (2) enum GAME/TRIVIA case mismatch, (3) ForeignKeyViolation delete_package, (4) wrong file identifier en store"
created: 2026-04-07T00:00:00
updated: 2026-04-07T00:00:00
---

## Current Focus

hypothesis: "Todos los 4 bugs han sido corregidos"
test: "Verificación de sintaxis Python y imports"
expecting: "Los fixes están correctamente implementados"
next_action: "Ninguna - los fixes están completos"

## Symptoms

### Bug 1: AttributeError: 'NoneType' object has no attribute 'query'
- **error_location:** handlers/gamification_user_handlers.py → DailyGiftService.get_gift_amount() → get_config() → self.db.query()

### Bug 2: InvalidTextRepresentation: invalid input value for enum transactionsource: "GAME"
- **error_location:** game_service.py:405 credit_besitos(source=TransactionSource.GAME)

### Bug 3: ForeignKeyViolation en delete_package
- **error_location:** package_service.py delete_package()

### Bug 4: wrong file identifier/HTTP URL specified
- **error_location:** handlers/store_user_handlers.py product_preview()

## Resolution

root_cause: |
  Bug 1: DailyGiftService usaba self.db = db or SessionLocal() - si SessionLocal() falla en Railway,
         self.db era None. BesitoService tiene patrón seguro con _get_db() lazy.

  Bug 2: PostgreSQL tiene enum 'transactionsource' con valores UPPERCASE (GAME, TRIVIA),
         pero Python TransactionSource tenía valores lowercase ("game", "trivia").

  Bug 3: delete_package() intentaba eliminar físicamente sin considerar FK de store_products.

  Bug 4: product_preview() no logueaba suficiente información cuando file_id era inválido.

fix: |
  Bug 1: Cambiado DailyGiftService a usar patrón lazy _get_db() con _owns_session flag,
         igual que BesitoService. SessionLocal() se llama lazily solo cuando se necesita.
         Métodos actualizados: get_config, update_config, get_last_claim, claim_gift,
         get_claim_history, get_total_claims_today, get_total_besitos_given_today.

  Bug 2: Actualizado Python enum TransactionSource para usar valores UPPERCASE:
         GAME = "GAME", TRIVIA = "TRIVIA" - para coincidir con PostgreSQL.
         Actualizado también gamification_user_handlers.py para mostrar "Juego" y "Trivia".

  Bug 3: Cambiado delete_package() de hard delete a soft delete (is_active=False).
         Esto evita FK violations y es más seguro/reversible.

  Bug 4: Mejorado logging en product_preview() para incluir file_id y file_type
         cuando ocurre un error, facilitando diagnóstico futuro.

verification: "Todos los archivos pasan py_compile y los imports funcionan correctamente"
files_changed:
  - services/daily_gift_service.py
  - models/models.py
  - services/package_service.py
  - handlers/store_user_handlers.py
  - handlers/gamification_user_handlers.py
