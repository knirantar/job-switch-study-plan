import hashlib, hmac
from dataclasses import dataclass
from datetime import datetime, timezone

def pseudonym(key: bytes, purpose: str, normalized_id: str) -> str:
    message=f"{purpose}:v1:{normalized_id}".encode()
    return hmac.new(key,message,hashlib.sha256).hexdigest()

@dataclass(frozen=True)
class Consent:
    subject: str; purpose: str; notice_version: str
    granted_at: datetime; expires_at: datetime | None; withdrawn_at: datetime | None=None
    def active(self, now, requested_purpose):
        return (requested_purpose==self.purpose and now>=self.granted_at and
                (self.expires_at is None or now<self.expires_at) and
                (self.withdrawn_at is None or now<self.withdrawn_at))

key=b"study-key-not-production"
a=pseudonym(key,"research","PAT-1")
assert a==pseudonym(key,"research","PAT-1")
assert a!=pseudonym(key,"treatment","PAT-1")
now=datetime(2026,8,12,tzinfo=timezone.utc)
c=Consent("PAT-1","research","N3",datetime(2026,1,1,tzinfo=timezone.utc),None)
assert c.active(now,"research") and not c.active(now,"marketing")
withdrawn=Consent("PAT-1","research","N3",c.granted_at,None,datetime(2026,8,1,tzinfo=timezone.utc))
assert not withdrawn.active(now,"research")

required_inventory={"subject","source","purpose","authority","classification","location",
 "access","recipients","retention","deletion","backup","owner"}
required_audit={"time","actor","action","resource","purpose","policy_version","result","trace"}
assert len(required_inventory)==12 and len(required_audit)==8
print("PASS: purpose-separated pseudonyms, versioned consent state, inventory and audit policy")
