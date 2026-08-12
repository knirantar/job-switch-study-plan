from math import prod, ceil

def observed_availability(period_minutes, unavailable_minutes):
    return 1 - unavailable_minutes / period_minutes

def mtbf_availability(mtbf_hours, mttr_hours):
    return mtbf_hours / (mtbf_hours + mttr_hours)

def serial(*values): return prod(values)
def either(*values): return 1 - prod(1-v for v in values)

def zone_total(required_healthy, zones, tolerated_zone_failures=1):
    return ceil(required_healthy/(zones-tolerated_zone_failures))*zones

def backlog(arrival, service, seconds): return max(0, arrival-service)*seconds

assert abs(observed_availability(43_200, 45)-.9989583333333333) < 1e-12
assert abs(mtbf_availability(720, 2)-.997229916897507) < 1e-12
assert round(serial(.999, .9995, .9999), 7) == .9984006
assert either(.99, .99) == .9999
assert zone_total(15, 3) == 24
assert backlog(1_500, 1_200, 600) == 180_000
assert int((1-.9995)*10_000_000) == 4_999  # float is unsuitable for exact budget
assert 10_000_000 * 5 // 10_000 == 5_000  # exact integer policy: 5 bad per 10k
print("PASS: availability, MTBF/MTTR, dependency, zone, backlog, and exact budget math")
