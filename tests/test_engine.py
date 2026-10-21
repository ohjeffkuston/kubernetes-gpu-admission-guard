import copy
import json
import unittest
from pathlib import Path

from kubernetes_gpu_admission_guard import evaluate


BASE = json.loads((Path(__file__).parents[1] / "examples/cluster-snapshot.json").read_text())


class AdmissionGuardTests(unittest.TestCase):
    def test_admits_healthy_capacity(self):
        self.assertEqual(evaluate(copy.deepcopy(BASE))["decision"], "ADMIT")

    def test_blocks_missing_top_level_input(self):
        data = copy.deepcopy(BASE); del data["metrics"]
        self.assertEqual(evaluate(data)["decision"], "BLOCK")

    def test_blocks_quota_excess(self):
        data = copy.deepcopy(BASE); data["tenant_quota"]["used_gpus"] = 10
        self.assertIn("TENANT_GPU_QUOTA_EXCEEDED", evaluate(data)["reason_codes"])

    def test_requires_dra(self):
        data = copy.deepcopy(BASE); data["workload"]["uses_dra"] = False
        self.assertIn("DRA_RESOURCECLAIM_REQUIRED", evaluate(data)["reason_codes"])

    def test_blocks_disallowed_class(self):
        data = copy.deepcopy(BASE); data["workload"]["device_class"] = "unmanaged"
        self.assertIn("DEVICE_CLASS_NOT_ALLOWED", evaluate(data)["reason_codes"])

    def test_queues_when_capacity_is_tight_but_slo_allows(self):
        data = copy.deepcopy(BASE); data["workload"]["replicas"] = 3
        self.assertEqual(evaluate(data)["decision"], "QUEUE")

    def test_blocks_when_capacity_and_queue_slo_fail(self):
        data = copy.deepcopy(BASE); data["workload"]["replicas"] = 3; data["metrics"]["queue_p95_seconds"] = 700
        self.assertEqual(evaluate(data)["decision"], "BLOCK")

    def test_excludes_unhealthy_nodes(self):
        data = copy.deepcopy(BASE); data["cluster"]["nodes"][0]["healthy"] = False
        self.assertEqual(evaluate(data)["evidence"]["eligible_nodes"], ["gpu-a-2"])

    def test_warns_on_low_headroom(self):
        data = copy.deepcopy(BASE); data["policy"]["min_free_gpu_fraction"] = 0.5
        self.assertEqual(evaluate(data)["decision"], "WARN")

    def test_blocks_gpu_health_breach(self):
        data = copy.deepcopy(BASE); data["metrics"]["dcgm_error_rate"] = 0.02
        self.assertIn("GPU_HEALTH_SIGNAL_BREACH", evaluate(data)["reason_codes"])

    def test_fingerprint_is_deterministic(self):
        self.assertEqual(evaluate(copy.deepcopy(BASE))["evidence_fingerprint"], evaluate(copy.deepcopy(BASE))["evidence_fingerprint"])


if __name__ == "__main__":
    unittest.main()
