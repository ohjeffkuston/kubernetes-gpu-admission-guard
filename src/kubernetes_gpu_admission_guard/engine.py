"""Pure, deterministic Kubernetes GPU admission evaluation."""

from __future__ import annotations

import hashlib
import json
from typing import Any


REQUIRED_TOP_LEVEL = {"policy", "cluster", "workload", "tenant_quota", "metrics"}


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_TOP_LEVEL - payload.keys())
    if missing:
        return _result("BLOCK", [f"MISSING_{name.upper()}" for name in missing], [], payload, {})

    policy = payload["policy"]
    workload = payload["workload"]
    quota = payload["tenant_quota"]
    metrics = payload["metrics"]
    nodes = payload["cluster"].get("nodes", [])
    reasons: list[str] = []
    actions: list[str] = []

    requested = int(workload["replicas"]) * int(workload["gpus_per_replica"])
    quota_remaining = int(quota["max_gpus"]) - int(quota["used_gpus"])
    if requested > quota_remaining:
        reasons.append("TENANT_GPU_QUOTA_EXCEEDED")
        actions.append("Reduce replicas or obtain an approved tenant quota increase.")

    if policy.get("require_dra") and not workload.get("uses_dra"):
        reasons.append("DRA_RESOURCECLAIM_REQUIRED")
        actions.append("Use an approved DeviceClass through a ResourceClaim or ResourceClaimTemplate.")

    allowed_classes = set(policy.get("allowed_device_classes", []))
    if allowed_classes and workload.get("device_class") not in allowed_classes:
        reasons.append("DEVICE_CLASS_NOT_ALLOWED")
        actions.append("Select a platform-approved GPU DeviceClass.")

    eligible = []
    for node in nodes:
        free = max(0, int(node["total_gpus"]) - int(node["allocated_gpus"]))
        if not node.get("driver_ready", False) or not node.get("healthy", False):
            continue
        if node.get("device_class") != workload.get("device_class"):
            continue
        if float(node.get("gpu_memory_gib", 0)) < float(workload.get("required_gpu_memory_gib", 0)):
            continue
        eligible.append({**node, "free_gpus": free})

    eligible.sort(key=lambda n: (-n["free_gpus"], float(n["cost_per_gpu_hour"]), n["name"]))
    free_gpus = sum(n["free_gpus"] for n in eligible)
    total_gpus = sum(int(n["total_gpus"]) for n in eligible)
    max_cost = max((float(n["cost_per_gpu_hour"]) for n in eligible), default=0.0)

    if not eligible:
        reasons.append("NO_ELIGIBLE_GPU_POOL")
        actions.append("Restore driver health or provision a pool matching the requested DeviceClass and memory.")
    elif free_gpus < requested:
        if float(metrics["queue_p95_seconds"]) > float(workload["max_start_delay_seconds"]):
            reasons.append("GPU_CAPACITY_AND_QUEUE_SLO_BREACH")
            actions.append("Provision capacity or route to an approved alternate DeviceClass before admission.")
        else:
            reasons.append("GPU_CAPACITY_QUEUED")
            actions.append("Keep the workload queued and re-evaluate when capacity changes.")

    free_fraction = (free_gpus / total_gpus) if total_gpus else 0.0
    warnings: list[str] = []
    if eligible and free_gpus >= requested and free_fraction < float(policy["min_free_gpu_fraction"]):
        warnings.append("LOW_GPU_HEADROOM")
        actions.append("Add GPU headroom or lower-priority capacity before the next demand spike.")
    if eligible and max_cost > float(policy["max_cost_per_gpu_hour"]):
        warnings.append("GPU_UNIT_COST_ABOVE_POLICY")
        actions.append("Prefer a lower-cost eligible pool or document the performance-cost exception.")
    if float(metrics.get("dcgm_error_rate", 0)) > float(policy["max_dcgm_error_rate"]):
        reasons.append("GPU_HEALTH_SIGNAL_BREACH")
        actions.append("Quarantine unhealthy devices and investigate DCGM/Xid evidence.")

    blocking = [r for r in reasons if r != "GPU_CAPACITY_QUEUED"]
    if blocking:
        decision = "BLOCK"
    elif "GPU_CAPACITY_QUEUED" in reasons:
        decision = "QUEUE"
    elif warnings:
        decision = "WARN"
    else:
        decision = "ADMIT"

    evidence = {
        "requested_gpus": requested,
        "quota_remaining_gpus": quota_remaining,
        "eligible_nodes": [n["name"] for n in eligible],
        "eligible_free_gpus": free_gpus,
        "eligible_free_fraction": round(free_fraction, 4),
        "candidate_node": eligible[0]["name"] if eligible and eligible[0]["free_gpus"] else None,
        "max_eligible_unit_cost": max_cost,
        "queue_p95_seconds": float(metrics["queue_p95_seconds"]),
    }
    return _result(decision, reasons + warnings, actions, payload, evidence)


def _result(decision: str, reasons: list[str], actions: list[str], payload: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": decision,
        "reason_codes": sorted(set(reasons)),
        "recommended_actions": list(dict.fromkeys(actions)),
        "evidence": evidence,
        "evidence_fingerprint": _fingerprint(payload),
        "safety_boundary": "advisory-only; no Kubernetes or cloud mutations",
    }
