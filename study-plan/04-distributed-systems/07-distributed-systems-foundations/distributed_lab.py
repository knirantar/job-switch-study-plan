from math import comb

def majority(nodes):
    if nodes <= 0:
        raise ValueError("nodes must be positive")
    return nodes // 2 + 1

def crash_tolerance(nodes):
    return nodes - majority(nodes)

def quorum_overlap(n, w, r):
    return w + r > n

def quorum_availability(n, required, independent_reachability):
    p = independent_reachability
    return sum(comb(n, k) * p**k * (1-p)**(n-k)
               for k in range(required, n + 1))

class FencedResource:
    def __init__(self):
        self.highest_token = 0
        self.value = None

    def write(self, token, value):
        if token < self.highest_token:
            return False
        self.highest_token = token
        self.value = value
        return True

assert [majority(n) for n in (3, 4, 5, 7)] == [2, 3, 3, 4]
assert [crash_tolerance(n) for n in (3, 4, 5, 7)] == [1, 1, 2, 3]
assert quorum_overlap(3, 2, 2)
assert not quorum_overlap(5, 2, 3)
assert round(quorum_availability(3, 2, .99), 6) == .999702

resource = FencedResource()
assert resource.write(41, "A-started")
assert resource.write(42, "B-authoritative")
assert not resource.write(41, "A-resumed-stale")
assert resource.value == "B-authoritative"
print("PASS: majority, quorum overlap, reachability model, and fencing")
