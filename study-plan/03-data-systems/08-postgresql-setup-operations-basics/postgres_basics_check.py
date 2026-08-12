"""Offline arithmetic and policy checks; optional SQL in setup.sql runs on PostgreSQL."""
from dataclasses import dataclass

@dataclass(frozen=True)
class PoolBudget:
    max_connections: int
    reserved: int
    replicas: int

    def application_connections(self):
        if self.max_connections <= self.reserved or self.replicas <= 0:
            raise ValueError("invalid connection budget")
        return self.max_connections - self.reserved

    def per_replica(self):
        return self.application_connections() // self.replicas

def meets_recovery(backup_interval_minutes, measured_restore_minutes, rpo, rto):
    return backup_interval_minutes <= rpo and measured_restore_minutes <= rto

budget = PoolBudget(240, 40, 40)
assert budget.application_connections() == 200
assert budget.per_replica() == 5
assert PoolBudget(200, 20, 30).per_replica() == 6
assert not meets_recovery(24 * 60, 20, 5, 30)
assert meets_recovery(5, 24, 5, 30)

required_restore_evidence = {
    "schema", "constraints", "row_evidence", "privileges",
    "sequence_state", "application_smoke", "recovery_point", "elapsed_time"
}
assert len(required_restore_evidence) == 8
print("PASS: global pool budgets, recovery gates, and restore evidence policy")
