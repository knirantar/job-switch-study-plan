import unittest
from gateway import Gateway, QuotaExceeded, RequestRejected, TokenBucket, cache_key, redact


def fake_generate(prompt: str, max_tokens: int) -> str:
    return f"reviewed: {prompt[:max_tokens]}"


class GatewayTest(unittest.TestCase):
    def test_redacts_email_and_card(self):
        text = redact("mail a@b.com card 4111 1111 1111 1111")
        self.assertNotIn("a@b.com", text); self.assertNotIn("4111", text)

    def test_cache_key_changes_with_model_or_config(self):
        base = cache_key("sha256:a", "hello", 0.0, 10)
        self.assertNotEqual(base, cache_key("sha256:b", "hello", 0.0, 10))
        self.assertNotEqual(base, cache_key("sha256:a", "hello", 0.0, 11))

    def test_deterministic_request_is_cached(self):
        gateway = Gateway("sha256:a", fake_generate, TokenBucket(1000, 0))
        self.assertFalse(gateway.infer("check claim", 10, now=0)["cache_hit"])
        self.assertTrue(gateway.infer("check claim", 10, now=0)["cache_hit"])

    def test_sampling_request_is_not_cached(self):
        gateway = Gateway("sha256:a", fake_generate, TokenBucket(1000, 0))
        gateway.infer("check", 10, temperature=.7, now=0)
        self.assertFalse(gateway.infer("check", 10, temperature=.7, now=0)["cache_hit"])

    def test_quota_and_refill(self):
        bucket = TokenBucket(20, 2); bucket.updated_at = 0
        self.assertTrue(bucket.consume(20, now=0)); self.assertFalse(bucket.consume(1, now=0))
        self.assertTrue(bucket.consume(10, now=5))

    def test_invalid_generation_bounds_rejected(self):
        gateway = Gateway("sha256:a", fake_generate, TokenBucket(1000, 0))
        with self.assertRaises(RequestRejected): gateway.infer("x", 513)

    def test_gateway_never_returns_detected_email(self):
        gateway = Gateway("sha256:a", lambda p, n: "contact leak@example.com", TokenBucket(1000, 0))
        self.assertEqual("contact [EMAIL]", gateway.infer("hello", 10)["output"])


if __name__ == "__main__": unittest.main()
