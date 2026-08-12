import ipaddress
from math import ceil

def most_specific(destination, routes):
    address = ipaddress.ip_address(destination)
    matches = [(ipaddress.ip_network(prefix), next_hop) for prefix, next_hop in routes
               if address in ipaddress.ip_network(prefix)]
    if not matches:
        return None
    return max(matches, key=lambda item: item[0].prefixlen)[1]

def evenly_provisioned_for_zone_loss(required_instances, zones, failures=1):
    return ceil(required_instances / (zones - failures)) * zones

def surviving_capacity(per_zone, zones, failures, per_instance_rate):
    return per_zone * (zones - failures) * per_instance_rate

routes = [("10.0.0.0/8", "A"), ("10.40.0.0/16", "B"),
          ("10.40.8.0/24", "C"), ("0.0.0.0/0", "internet")]
assert most_specific("10.40.8.7", routes) == "C"
assert most_specific("10.40.9.7", routes) == "B"
assert most_specific("8.8.8.8", routes) == "internet"

parent = ipaddress.ip_network("10.40.0.0/20")
children = list(parent.subnets(new_prefix=24))
assert parent.num_addresses == 4096 and len(children) == 16
assert evenly_provisioned_for_zone_loss(15, 3) == 24
assert surviving_capacity(8, 3, 1, 1_200) == 19_200
assert surviving_capacity(8, 3, 1, 700) == 11_200

probe_interval_s, threshold = 10, 3
assert probe_interval_s * (threshold - 1) <= 30 <= probe_interval_s * threshold
print("PASS: CIDR subdivision, route specificity, zone capacity, and probe timing")
