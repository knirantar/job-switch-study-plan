import ipaddress
import math

def ideal_transfer_seconds(megabytes, megabits_per_second):
    if megabytes < 0 or megabits_per_second <= 0:
        raise ValueError("invalid transfer")
    return megabytes * 8 / megabits_per_second

def in_flight(requests_per_second, latency_ms):
    return requests_per_second * latency_ms / 1000

def per_instance(rate, healthy_instances):
    if healthy_instances <= 0:
        raise ValueError("no capacity")
    return rate / healthy_instances

net = ipaddress.ip_network("10.20.32.0/20")
assert net.num_addresses == 4096
assert str(net.broadcast_address) == "10.20.47.255"
assert ideal_transfer_seconds(250, 500) == 4
assert in_flight(5_000, 240) == 1_200
assert math.isclose(per_instance(16_000, 15), 1066.6666666666667)
assert per_instance(12_000, 9) / per_instance(12_000, 12) == 4 / 3

bandwidth_delay_product_bytes = 1_000_000_000 * 0.1 / 8
assert bandwidth_delay_product_bytes == 12_500_000
print("PASS: CIDR, transfer, Little's Law, failure load, and BDP")
