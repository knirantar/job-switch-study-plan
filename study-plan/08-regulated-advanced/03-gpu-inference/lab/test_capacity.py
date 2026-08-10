import unittest
from capacity import GIB, Transformer, kv_bytes_per_token, max_sequences, required_replicas, weight_bytes

MODEL=Transformer(parameters=7_000_000_000,layers=32,kv_heads=8,head_dim=128)

class CapacityTest(unittest.TestCase):
    def test_fp16_weights(self): self.assertEqual(14_000_000_000,weight_bytes(MODEL))
    def test_gqa_kv_per_token(self): self.assertEqual(131_072,kv_bytes_per_token(MODEL))
    def test_mha_has_four_times_gqa_kv(self):
        mha=Transformer(7_000_000_000,32,32,128)
        self.assertEqual(4*kv_bytes_per_token(MODEL),kv_bytes_per_token(mha))
    def test_sequence_capacity(self):
        # 24 GiB, 90% usable, 2 GiB fixed overhead, 4096 tokens/sequence
        self.assertEqual(13,max_sequences(MODEL,24,.9,4096,2))
    def test_no_capacity_when_weights_exceed_budget(self): self.assertEqual(0,max_sequences(MODEL,12,.9,4096,1))
    def test_replica_headroom(self): self.assertEqual(9,required_replicas(120,25,.6,1))
    def test_invalid_utilization(self):
        with self.assertRaises(ValueError): required_replicas(10,5,1.1)

if __name__ == "__main__": unittest.main()
