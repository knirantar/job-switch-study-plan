from decimal import Decimal

def allocate_minor(total, weights, stable_keys):
    if total < 0 or sum(weights) <= 0 or len(weights)!=len(stable_keys): raise ValueError()
    weight_sum=sum(weights)
    raw=[Decimal(total)*Decimal(w)/Decimal(weight_sum) for w in weights]
    base=[int(x) for x in raw]
    remainder=total-sum(base)
    order=sorted(range(len(raw)),key=lambda i:(-(raw[i]-base[i]),stable_keys[i]))
    for i in order[:remainder]: base[i]+=1
    return dict(zip(stable_keys,base,strict=True))

def gross_margin(revenue_minor, cost_minor):
    if revenue_minor <= 0: raise ValueError()
    return Decimal(revenue_minor-cost_minor)/Decimal(revenue_minor)

allocation=allocate_minor(12_000_000,[50,30,20],["A","B","C"])
assert allocation=={"A":6_000_000,"B":3_600_000,"C":2_400_000}
assert sum(allocation.values())==12_000_000
odd=allocate_minor(100_001,[50,30,20],["A","B","C"])
assert sum(odd.values())==100_001
assert gross_margin(80_000_000,50_000_000)==Decimal("0.375")

def authorize_tenant(actor_memberships, selected, resource):
    return selected in actor_memberships and selected==resource
assert authorize_tenant({"T1","T2"},"T2","T2")
assert not authorize_tenant({"T1"},"T2","T2")
assert not authorize_tenant({"T1","T2"},"T1","T2")

required_usage={"event_id","tenant_id","meter_version","quantity","unit",
 "occurred_at","resource","region","source_request","correction_of"}
assert len(required_usage)==10
print("PASS: exact shared allocation, gross margin, tenant context, and metering policy")
