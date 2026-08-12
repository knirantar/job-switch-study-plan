from collections import Counter, deque
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True, slots=True)
class Money:
    amount_paise: int
    currency: str
    def __post_init__(self):
        if self.amount_paise < 0: raise ValueError("negative")
        if self.currency not in {"INR", "USD"}: raise ValueError("currency")
    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency: raise ValueError("currency mismatch")
        return Money(self.amount_paise + other.amount_paise, self.currency)

class Predictor(Protocol):
    def predict(self, features: tuple[float, ...]) -> float: ...

class FixedPredictor:
    def predict(self, features): return sum(features) / len(features)

def positive_amounts(values):
    for value in values:
        if value > 0: yield value

class FakeConnection:
    def __init__(self): self.actions=[]
    def commit(self): self.actions.append("commit")
    def rollback(self): self.actions.append("rollback")

@contextmanager
def transaction(connection):
    try: yield connection
    except Exception:
        connection.rollback(); raise
    else: connection.commit()

q=deque(["J1","J2"]); q.append("J3"); assert q.popleft()=="J1"
assert Counter(["PAID","PAID","REJECTED"]) == {"PAID":2,"REJECTED":1}
g=positive_amounts([-1,2,0,3]); assert list(g)==[2,3]; assert list(g)==[]
assert Money(100,"INR").add(Money(50,"INR")) == Money(150,"INR")
try: Money(1,"INR").add(Money(1,"USD")); raise AssertionError()
except ValueError: pass
assert abs(FixedPredictor().predict((.2,.4)) - .3) < 1e-12
c=FakeConnection()
with transaction(c): pass
assert c.actions==["commit"]
c=FakeConnection()
try:
    with transaction(c): raise RuntimeError("fail")
except RuntimeError: pass
assert c.actions==["rollback"]
print("PASS: deque, Counter, lazy generator, value object, protocol, and context transaction")
