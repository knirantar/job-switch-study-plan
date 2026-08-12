SECONDS_PER_DAY = 86_400
MINUTES_30_DAY_MONTH = 43_200

def downtime_minutes(availability, period_minutes=MINUTES_30_DAY_MONTH):
    if not 0 <= availability <= 1:
        raise ValueError("availability must be probability")
    return period_minutes * (1 - availability)

def serial_availability(*dependencies):
    result = 1.0
    for value in dependencies:
        result *= value
    return result

def required_even_zone_instances(base_instances, zones, tolerated_zone_failures=1):
    survivors = zones - tolerated_zone_failures
    if survivors <= 0:
        raise ValueError("no surviving zone")
    per_zone = -(-base_instances // survivors)  # ceiling division
    return per_zone * zones

def daily_tib(events_per_second, kib_per_event):
    return events_per_second * SECONDS_PER_DAY * kib_per_event / (1024 ** 3)

assert abs(downtime_minutes(.999) - 43.2) < 1e-9
assert abs(downtime_minutes(.9999) - 4.32) < 1e-9
assert round(serial_availability(.999, .999, .999), 6) == .997003
assert round(1 - (1 - .99) ** 2, 4) == .9999
assert required_even_zone_instances(15, 3) == 24
assert required_even_zone_instances(18, 3) == 27
assert round(daily_tib(20_000, 1), 3) == 1.609
assert 3_000 * 16 / 1024 == 46.875
print("PASS: SLO budgets, serial/redundant availability, zone capacity, storage, and volume")
