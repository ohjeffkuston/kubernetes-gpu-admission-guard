GPU workloads can be valid Kubernetes manifests and still be unsafe to admit.

The hard production questions begin after schema validation: Is the requested accelerator class approved? Is the driver healthy? Does the tenant have quota? Can the job start within its queue SLO? Will admission erase the platform's last capacity headroom?

I built a Kubernetes GPU Admission Guard to turn those questions into deterministic evidence before an AI workload consumes scarce accelerator capacity.

It evaluates DRA usage, DeviceClass policy, tenant quota, GPU memory fit, driver and device health, queue delay, headroom, and unit cost. The result is an explainable ADMIT, WARN, QUEUE, or BLOCK decision with stable reason codes, recommended actions, and an evidence fingerprint.

The project includes:

• A testable Python policy engine
• Kubernetes DRA and GPU scheduling concepts
• Eleven unit tests and GitHub Actions CI
• A hardened audit-only CronJob example
• Security, failure-mode, and deployment guidance
• Metrics for queue delay, policy coverage, utilization, cost, and false blocks

The most useful AI infrastructure automation is not the automation that acts fastest. It is the automation that can prove why a scarce production resource should be allocated.

Project: https://github.com/ohjeffkuston/kubernetes-gpu-admission-guard

Follow my profile for practical Cloud, DevOps, SRE, Platform Engineering, and AI-infrastructure projects.
