# Payment authorization saga state machine

States: `RECEIVED → RESERVED → AUTHORIZED → COMPLETED`.

Failure branches:

- Reservation rejected → `FAILED_FINAL`.
- Authorization transiently unavailable → remain `RESERVED`, retry under a deadline/attempt budget.
- Authorization definitively rejected → release reservation idempotently → `COMPENSATED`.
- Timeout after authorization request → `AUTHORIZATION_UNKNOWN`; query provider with the same operation key before compensation.
- Compensation transiently fails → `COMPENSATION_PENDING`; alert and reconcile until terminal.

Every transition stores `(saga_id, step, attempt, command_id, state_version)` under
unique constraints. Duplicate commands return the existing result. A compensation is
a new business action, not deletion of history; it may fail and must itself be idempotent.
