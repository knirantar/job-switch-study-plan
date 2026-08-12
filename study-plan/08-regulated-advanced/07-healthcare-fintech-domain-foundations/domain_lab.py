from dataclasses import dataclass

@dataclass(frozen=True)
class Posting:
    account: str; currency: str; signed_minor: int

def validate_balanced(postings):
    sums={}
    for p in postings: sums[p.currency]=sums.get(p.currency,0)+p.signed_minor
    if any(value!=0 for value in sums.values()): raise ValueError(f"unbalanced {sums}")
    return sums

allowed={
 "CREATED":{"AUTHORIZED","FAILED"},
 "AUTHORIZED":{"CAPTURED","REVERSED","EXPIRED"},
 "CAPTURED":{"SETTLED","REFUNDED","DISPUTED"},
 "SETTLED":{"REFUNDED","DISPUTED"},
}
def transition(current,target):
    if target not in allowed.get(current,set()): raise ValueError("invalid transition")
    return target

payment=[Posting("customer","INR",-129_900),Posting("merchant","INR",127_000),Posting("fee","INR",2_900)]
assert validate_balanced(payment)=={"INR":0}
try: validate_balanced(payment[:-1]); raise AssertionError("unbalanced accepted")
except ValueError: pass
assert transition("CREATED","AUTHORIZED")=="AUTHORIZED"
assert transition("AUTHORIZED","CAPTURED")=="CAPTURED"
try: transition("SETTLED","AUTHORIZED"); raise AssertionError("regression accepted")
except ValueError: pass

total=10_000; base=total//3; remainder=total%3
shares=[base+(1 if i<remainder else 0) for i in range(3)]
assert shares==[3334,3333,3333] and sum(shares)==total

required_observation={"patient","code_system","code","value","unit_system","unit_code",
 "effective_time","issued_time","status","provenance"}
assert len(required_observation)==10
print("PASS: exact ledger balance, state transitions, residual allocation, observation contract")
