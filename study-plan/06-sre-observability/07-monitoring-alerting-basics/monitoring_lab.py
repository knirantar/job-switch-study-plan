from dataclasses import dataclass

def error_ratio(bad, total):
    if total <= 0 or not 0 <= bad <= total: raise ValueError("invalid counts")
    return bad / total

def series_count(**dimensions):
    count = 1
    for values in dimensions.values(): count *= values
    return count

def queue_growth(arrival, service, seconds): return max(0, arrival-service)*seconds

@dataclass
class AlertState:
    required_true_evaluations: int
    consecutive: int = 0
    firing: bool = False

    def evaluate(self, condition):
        self.consecutive = self.consecutive + 1 if condition else 0
        self.firing = self.consecutive >= self.required_true_evaluations
        return self.firing

assert error_ratio(3_000, 600_000) == .005
assert series_count(service=20, route=40, status=5, region=4, version=8) == 128_000
assert queue_growth(2_000, 1_600, 900) == 360_000

alert = AlertState(5)
assert [alert.evaluate(v) for v in [True]*4] == [False]*4
assert not alert.evaluate(False)
assert [alert.evaluate(v) for v in [True]*5] == [False, False, False, False, True]

bucket_counts = {100: 900, 250: 980, 500: 995, 1000: 1000}
rank = .99 * max(bucket_counts.values())
bucket = next(limit for limit, cumulative in bucket_counts.items() if cumulative >= rank)
assert bucket == 500  # p99 is within (250, 500], not an exact 500 ms observation
print("PASS: error ratio, cardinality, queue trend, alert persistence, and histogram bound")
