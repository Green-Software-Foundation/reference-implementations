# Sustainability Score Report

**Repository:** `tests/fixtures/sample_service`  
**Generated:** 2026-08-27T02:39:31+00:00  
**Method:** static analysis only  

## Score: 73.1/100 (Grade C)

> Confidence: **Tier 1 - Static analysis only** (directional). Inferred from source, config and manifests. No runtime or billing data. Findings indicate likely direction of impact, not measured magnitude.
>
> This report is **advisory**. Nothing here should gate a build or deploy. Every recommendation that could affect capacity or resiliency states the SLO trade-off explicitly.

Grounded in the Green Software Foundation [Software Carbon Intensity (SCI)](https://sci.greensoftware.foundation/) specification: `SCI = ((E x I) + M) / R`.

## Pillars

| Pillar | Weight | Score | Confidence |
|---|---:|---:|---|
| Code / Algorithm Efficiency | 30% | 82 | Tier 1 |
| Containerization | 15% | 72 | Tier 1 |
| CI/CD Practices | 15% | 82 | Tier 1 |
| Cloud Infrastructure Choices | 25% | 56 | Tier 1 |
| SRE / Operations | 15% | 76 | Tier 1 |

## Findings

### Code / Algorithm Efficiency
- **[MEDIUM] SELECT * pulls unused columns over the wire** (`CE-SELECT-STAR`, Tier 1)
  - Evidence: `app/handler.py:20`
  - Advice: Select only needed columns; reduces I/O, network and serialization energy per query.
- **[LOW] Nested loop may indicate super-linear work on a hot path** (`CE-NESTED-LOOP`, Tier 1)
  - Evidence: `app/handler.py:5`
  - Advice: Confirm the collection sizes; if they grow with load, consider a set/dict lookup or precomputed index to cut CPU time (lowers E).
- **[LOW] Blocking sleep() holds a worker/thread idle** (`CE-BLOCKING-SLEEP`, Tier 1)
  - Evidence: `app/handler.py:18`
  - Advice: Prefer event-driven waits or async scheduling so the worker can be reclaimed while idle.
  - SLO/resiliency note: None if replaced with an equivalent async wait; verify retry/backoff semantics are preserved.

### Containerization
- **[MEDIUM] Full-fat base image inflates embodied + transfer footprint** (`CN-HEAVY-BASE`, Tier 1)
  - Evidence: `Dockerfile:1`
  - Advice: Switch to a slim/distroless/alpine base or a multi-stage build; smaller images pull faster and use less registry storage and cold-start energy (M, E).
- **[MEDIUM] Workload has no CPU/memory requests or limits** (`CN-NO-RESOURCE-LIMITS`, Tier 1)
  - Evidence: `deploy/deployment.yaml`
  - Advice: Set requests/limits so the scheduler can bin-pack efficiently instead of stranding node capacity (M, E).
  - SLO/resiliency note: Set limits from observed p99 usage, not guesses; limits set too low can throttle or OOM-kill under load.
- **[LOW] Build toolchain shipped in the runtime image** (`CN-NO-MULTISTAGE`, Tier 1)
  - Evidence: `Dockerfile`
  - Advice: Use a multi-stage build so compilers/build deps do not ship in the final image.
- **[LOW] Container runs as root (no USER directive)** (`CN-NO-USER`, Tier 1)
  - Evidence: `Dockerfile`
  - Advice: Add a non-root USER. Sustainability-adjacent hardening; does not change carbon directly.

### CI/CD Practices
- **[MEDIUM] Workflow declares no dependency caching** (`CI-NO-CACHE`, Tier 1)
  - Evidence: `.github/workflows/ci.yml`
  - Advice: Cache dependencies (actions/cache or setup-*'s cache) so every run does not re-download and rebuild from scratch (E).
- **[LOW] Pipeline runs on every push with no path filter** (`CI-NO-PATH-FILTER`, Tier 1)
  - Evidence: `.github/workflows/ci.yml`
  - Advice: Add path filters or concurrency cancellation so docs-only or superseded commits do not trigger full builds.
- **[LOW] No concurrency control; superseded runs are not cancelled** (`CI-NO-CONCURRENCY`, Tier 1)
  - Evidence: `.github/workflows/ci.yml`
  - Advice: Add a concurrency group with cancel-in-progress so an outdated run stops when a newer commit lands.
- **[INFO] Scheduled (cron) workflow runs regardless of changes** (`CI-SCHEDULED-BUILD`, Tier 1)
  - Evidence: `.github/workflows/ci.yml`
  - Advice: Confirm the schedule is needed; nightly builds on quiet repos burn compute with no functional output.

### Cloud Infrastructure Choices
_Declared infrastructure found -> cloud findings evaluated at Tier 2 (static + declared infra)._

- **[HIGH] Fixed capacity with no effective autoscaling (min == max)** (`CLOUD-FIXED-CAPACITY`, Tier 2)
  - Evidence: `deploy/main.tf:6`
  - Advice: Add a target-tracking scaling policy and let min < max so capacity follows demand instead of running peak-sized 24/7 (large E win).
  - SLO/resiliency note: Configure min capacity and scale-out cooldowns to protect availability during spikes.
  - GHG mapping: GHG Protocol Scope 3 Category 1.
- **[MEDIUM] Deploys to a relatively high-carbon region (us-east-1)** (`CLOUD-HIGH-CARBON-REGION`, Tier 2)
  - Evidence: `deploy/main.tf:2`
  - Advice: If latency/data-residency allow, prefer a lower-carbon region. Region choice directly changes carbon intensity I in SCI.
  - SLO/resiliency note: Region moves affect latency and data residency; validate compliance and RTO/RPO before relocating.
  - GHG mapping: GHG Protocol Scope 3 Category 1 (purchased cloud services).
- **[MEDIUM] Very large instance type declared (m5.12xlarge)** (`CLOUD-LARGE-INSTANCE`, Tier 2)
  - Evidence: `deploy/main.tf`
  - Advice: Confirm the workload needs this size; right-size from observed utilization, and prefer current-gen (e.g. Graviton/ARM) for better performance-per-watt.
  - GHG mapping: GHG Protocol Scope 3 Category 1.
- **[LOW] Deployment without a HorizontalPodAutoscaler** (`CLOUD-NO-HPA`, Tier 1)
  - Evidence: `deploy/deployment.yaml`
  - Advice: Add an HPA so replica count tracks load rather than sitting at a fixed count around the clock.
  - SLO/resiliency note: Set sensible min replicas and stabilization windows to avoid flapping under bursty load.

### SRE / Operations
- **[HIGH] No observability/metrics stack detected in manifests** (`SRE-NO-OBSERVABILITY`, Tier 1)
  - Evidence: `dependency manifests / k8s manifests`
  - Advice: Instrument with metrics (utilization, request rate, saturation). You cannot right-size or prove an efficiency win you cannot measure. This is the precondition for reaching Tier 3.
- **[LOW] Deployment without liveness/readiness probes** (`SRE-NO-PROBES`, Tier 1)
  - Evidence: `deploy/deployment.yaml`
  - Advice: Add probes so the platform can route around and reclaim unhealthy pods rather than wasting capacity on them.
  - SLO/resiliency note: None; probes improve resiliency. Tune thresholds to avoid premature restarts.

## Sample PR comment (advisory, non-blocking)

```markdown
Sustainability score: **73.1/100 (Grade C)** - confidence Tier 1 (directional).

This is an advisory signal, not a gate. A few directional suggestions:
- SELECT * pulls unused columns over the wire (`app/handler.py:20`)
- Full-fat base image inflates embodied + transfer footprint (`Dockerfile:1`)
- Workload has no CPU/memory requests or limits (`deploy/deployment.yaml`)

_Scores are directional from static analysis; see the full report for SLO trade-offs before acting._
```
