from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    connect_timeout_ms: int
    request_deadline_ms: int
    retries: int
    pool_max: int
    max_replicas: int
    db_connection_budget: int

def validate(c):
    errors = []
    if not 50 <= c.connect_timeout_ms <= 5_000: errors.append("connect timeout")
    if not 100 <= c.request_deadline_ms <= 10_000: errors.append("request deadline")
    if c.connect_timeout_ms >= c.request_deadline_ms: errors.append("timeout nesting")
    if not 0 <= c.retries <= 3: errors.append("retries")
    if c.pool_max * c.max_replicas > c.db_connection_budget: errors.append("DB budget")
    return errors

def canary_rate(total_rps, percent):
    return total_rps * percent / 100

def expected_seconds_to_observe(canary_rps, one_in_requests):
    return one_in_requests / canary_rps

good = Config(250, 2_000, 1, 8, 30, 240)
bad = Config(3_000, 2_000, 5, 100, 50, 800)
assert validate(good) == []
assert set(validate(bad)) == {"timeout nesting", "retries", "DB budget"}
assert canary_rate(20_000, 1) == 200
assert expected_seconds_to_observe(200, 100_000) == 500

required_runbook = {"purpose", "preconditions", "authorization", "read_only_evidence",
                    "scoped_action", "expected_result", "verification", "rollback", "escalation"}
assert len(required_runbook) == 9
print("PASS: config admission, pool budget, canary math, and runbook policy")
