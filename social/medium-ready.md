# Kubernetes GPU Admission Guard: Evidence Before AI Workloads Consume Scarce Capacity

![Kubernetes GPU Admission Guard architecture](../docs/architecture.png)

A Kubernetes manifest can be valid while the workload it describes is still unsafe to admit. This is especially true for GPU-backed AI jobs, where accelerator scarcity, driver health, memory fit, tenant quotas, queue latency, and unit cost all affect whether a deployment is operationally sensible.

## Why this matters now

Current AI-platform roles repeatedly combine Kubernetes and Terraform with GPU scheduling, multi-tenant isolation, quotas, observability, SLOs, Slurm or comparable schedulers, and Python or Go automation. Kubernetes has also matured Dynamic Resource Allocation around DeviceClasses and ResourceClaims, while the NVIDIA GPU Operator automates the device software stack and DCGM monitoring.

That creates a clear platform-engineering need: explainable admission evidence before scarce capacity is consumed.

## The architecture

The guard accepts a bounded snapshot containing an AI workload request, tenant quota, GPU-pool inventory, and queue and device-health metrics. A deterministic policy engine filters eligible nodes and evaluates:

- approved DeviceClass and DRA use;
- tenant GPU quota;
- driver and device health;
- GPU memory fit and free capacity;
- maximum start delay and queue p95;
- reserved capacity headroom;
- GPU-hour cost policy.

It returns `ADMIT`, `WARN`, `QUEUE`, or `BLOCK`, plus stable reason codes, recommended actions, placement evidence, and a fingerprint of the input.

## Implementation choices

I kept the core engine pure and deterministic. It makes no Kubernetes or cloud API calls, which makes tests reproducible and prevents an advisory result from becoming an accidental infrastructure mutation. A production collector can use read-only identities to create the evidence snapshot. A separate, authenticated policy or approval layer can enforce the signed result.

The repository includes eleven unit tests, GitHub Actions CI, sample evidence, Docker packaging, and a hardened audit-only Kubernetes CronJob example.

## Security and reliability

The guard fails closed when required evidence is absent, but it distinguishes a temporary capacity queue from a policy violation. ResourceClaim and ResourceSlice status permissions should remain least-privilege. Inputs require validation and size limits, and device health needs DCGM or equivalent evidence rather than node readiness alone.

Most importantly, the guard contains no mutation credentials. Capacity provisioning, quota changes, and workload admission remain behind a controlled approval boundary.

## Measuring the outcome

This project can be evaluated through pre-submission detection of unschedulable jobs, p95 job-start delay, queue-SLO breaches, quota coverage, false-block rate, GPU utilization, retained headroom, cost per admitted GPU-hour, and the time needed to explain a pending job.

## What I learned

GPU availability is not the same as workload admissibility. Production AI platforms need a decision that joins device compatibility, tenancy, reliability, and cost. Deterministic evidence makes that decision testable and auditable before it is connected to automation.

Repository: https://github.com/ohjeffkuston/kubernetes-gpu-admission-guard

Sources: [Kubernetes DRA](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/), [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/), [DRA hardening](https://kubernetes.io/docs/concepts/security/hardening-guide/dynamic-resource-allocation/), and [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/).
