from dataclasses import dataclass
from hashlib import sha256

def backlog(arrival_per_s, service_per_s, seconds, initial=0):
    return max(0, initial + (arrival_per_s - service_per_s) * seconds)

def all_success(single_success, fanout):
    return single_success ** fanout

@dataclass
class IdempotencyStore:
    entries: dict

    def create(self, tenant, key, payload):
        fingerprint = sha256(payload.encode()).hexdigest()
        scoped = (tenant, key)
        existing = self.entries.get(scoped)
        if existing:
            if existing[0] != fingerprint:
                return "CONFLICT"
            return existing[1]
        outcome = f"CREATED-{len(self.entries) + 1}"
        self.entries[scoped] = (fingerprint, outcome)
        return outcome

assert backlog(2_000, 1_600, 600) == 240_000
assert backlog(1_000, 1_600, 400, initial=240_000) == 0
assert round(all_success(.999, 50), 4) == .9512
assert round(all_success(.995, 20), 4) == .9046

store = IdempotencyStore({})
first = store.create("T1", "K1", '{"amount":1000}')
assert first == "CREATED-1"
assert store.create("T1", "K1", '{"amount":1000}') == first
assert store.create("T1", "K1", '{"amount":2000}') == "CONFLICT"
assert store.create("T2", "K1", '{"amount":2000}') == "CREATED-2"
print("PASS: queue math, fan-out reliability, and scoped idempotency")
