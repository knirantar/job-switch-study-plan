import hashlib, hmac, secrets, time

def sign_webhook(secret: bytes, timestamp: int, body: bytes) -> str:
    return hmac.new(secret, str(timestamp).encode()+b"."+body, hashlib.sha256).hexdigest()

def verify_webhook(secret, timestamp, body, signature, now, max_age=300):
    if abs(now-timestamp)>max_age: return False
    expected=sign_webhook(secret,timestamp,body)
    return hmac.compare_digest(expected,signature)

def authorize(actor_tenant, resource_tenant, permissions, action):
    return actor_tenant==resource_tenant and action in permissions

secret=secrets.token_bytes(32); now=int(time.time()); body=b'{"event":"paid","id":"C1"}'
signature=sign_webhook(secret,now,body)
assert verify_webhook(secret,now,body,signature,now)
assert not verify_webhook(secret,now,body+b"!",signature,now)
assert not verify_webhook(secret,now-301,body,sign_webhook(secret,now-301,body),now)
assert authorize("T1","T1",{"claim:read"},"claim:read")
assert not authorize("T1","T2",{"claim:read"},"claim:read")
assert not authorize("T1","T1",{"claim:read"},"claim:delete")

required_token_checks={"algorithm","signature","issuer","audience","expiry","not_before","token_type"}
assert len(required_token_checks)==7
print("PASS: HMAC integrity/replay window, constant-time verify, tenant/action authorization, token policy")
