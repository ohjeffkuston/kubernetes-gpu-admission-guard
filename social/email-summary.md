# To: ohjeffkuston@yahoo.ca
# Subject: Day 15 — Kubernetes GPU Admission Guard learning and deployment guide

Today’s project is a deterministic admission-evidence engine for Kubernetes AI workloads. It evaluates GPU DeviceClass policy, DRA use, tenant quota, device health, memory fit, queue SLO, capacity headroom, and GPU-hour cost.

## How to explain it

The production problem is that a valid AI workload can still remain pending, violate tenant governance, consume the last reliable GPU capacity, or use an unhealthy or unapproved device pool. The guard creates an auditable decision before enforcement.

The input is a bounded snapshot. The engine filters eligible GPU nodes and returns ADMIT, WARN, QUEUE, or BLOCK with stable reason codes and actions. It is intentionally advisory-only; a separate authenticated controller and human approval gate own mutations.

## Deploy repeatedly

1. Clone the repository and create a Python 3.11+ virtual environment.
2. Install with `python -m pip install -e .`.
3. Run all tests with `python -m unittest discover -s tests -v`.
4. Copy the sample snapshot and replace it with sanitized, read-only inventory and telemetry.
5. Version the policy alongside the platform configuration.
6. Run in shadow mode and measure false blocks and missed unschedulable jobs.
7. Build and scan the container, pin its digest, and use the CronJob only as an audit example.
8. Store signed evidence; connect enforcement only through a separate least-privilege approval system.

## Interview story

Lead with the difference between GPU availability and safe workload admission. Describe why you combined Kubernetes DRA, tenant quota, queue SLO, driver health, cost, and headroom. Explain the deterministic design, the fail-closed boundary, and the metrics you would use to prove value. This positions the project for Cloud, DevOps, SRE, Platform Engineering, and AI-infrastructure conversations.

Repository: https://github.com/ohjeffkuston/kubernetes-gpu-admission-guard
