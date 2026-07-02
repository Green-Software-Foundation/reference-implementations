# GSF Architecture Patterns Reference

All 17 patterns from the GSF Architecture category. Each entry includes the problem, detection signals to scan for in review, the fix approach for generation/design, the SCI term it reduces, and the canonical URL.

> The Architecture category covers system-level decisions — topology, technology selection, deployment shape. These are often the highest-leverage interventions because they compound across every request.

## Table of contents

- System topology: [Adopt serverless for AI/ML](#adopt-serverless-architecture-for-aiml-workload-processes), [Choose region closest to users](#choose-the-region-that-is-closest-to-users), [Containerize workloads](#containerize-your-workloads), [Implement stateless design](#implement-stateless-design), [Queue non-urgent requests](#queue-non-urgent-processing-requests), [Reduce VM network traversal](#reduce-network-traversal-between-vms), [Run AI models at the edge](#run-ai-models-at-the-edge), [Scale logical components independently](#scale-logical-components-independently), [Use a service mesh only if needed](#use-a-service-mesh-only-if-needed)
- Technology selection: [Evaluate other CPU architectures](#evaluate-other-cpu-architectures), [Optimize AI/ML model size](#optimize-the-size-of-aiml-models), [Select efficient AI/ML framework](#select-a-more-energy-efficient-aiml-framework), [Right hardware for AI/ML training](#select-the-right-hardwarevm-instance-types-for-aiml-training), [Cloud-native processor VMs](#use-cloud-native-processor-vms), [Efficient file formats for AI/ML](#use-efficient-file-formats-for-aiml-development), [Energy-efficient AI/ML models](#use-energy-efficient-aiml-models), [Use serverless cloud services](#use-serverless-cloud-services)

---

## System Topology

### Adopt serverless architecture for AI/ML workload processes
- **Problem:** Always-on inference servers waste energy and embodied carbon during idle periods.
- **Detection signals:** GPU instances reserved 24×7 for sporadic inference, dedicated VMs for training jobs that run weekly, no autoscaling on AI endpoints.
- **Fix:** Use serverless inference platforms (Vertex AI endpoints with scale-to-zero, SageMaker Serverless, Modal, Replicate), or scale-to-zero K8s with KEDA for AI workloads with bursty traffic.
- **SCI:** Reduces M (shared hardware) and E (no idle GPU draw).
- **Trade-off:** Cold-start latency. Don't apply to latency-sensitive inference.
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/serverless-model-development

### Choose the region that is closest to users
- **Problem:** Long network distances mean more router hops, more energy in transit, and embodied carbon spread across more equipment.
- **Detection signals:** Single-region deployment serving global users, no CDN edge presence near user clusters, region chosen by developer convenience rather than user geography.
- **Fix:** Deploy multi-region or use a global CDN/edge layer; route users to the nearest healthy region.
- **SCI:** Reduces E (shorter transit) and M (less networking hardware traversed). Can indirectly help I if nearer region also has cleaner grid.
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/choose-region-closest-to-users

### Containerize your workloads
- **Problem:** Full VMs carry guest OS overhead per workload; containers share the kernel and pack more workloads onto the same hardware.
- **Detection signals:** One-VM-per-app deployments, low VM utilization (<30%), workloads that don't need OS-level isolation running on full VMs.
- **Fix:** Containerize and run on a shared orchestrator (K8s, ECS, Cloud Run). Right-size requests/limits to enable bin-packing.
- **SCI:** Reduces M (denser packing per hardware unit).
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/containerize-your-workload-where-applicable

### Implement stateless design
- **Problem:** Stateful services need bigger VMs (memory, disk) and resist horizontal scaling, locking in oversized hardware.
- **Detection signals:** In-memory session state, file uploads written to local disk, sticky-session load balancing required, services that can't be killed without data loss.
- **Fix:** Externalize state (Redis for sessions, object storage for files, durable queues for in-flight work); design services so any replica can serve any request.
- **SCI:** Reduces M (smaller, fungible instances) and improves R (better scaling).
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/implement-stateless-design

### Queue non-urgent processing requests
- **Problem:** Peak-sized infrastructure handling spiky workloads wastes capacity during troughs, inflating both E (idle draw) and M (oversized hardware).
- **Detection signals:** Sync API endpoints doing heavy work that doesn't need a sync response, oversized worker pools to handle peak loads, no batch path for cost-tolerant operations.
- **Fix:** Accept-then-queue pattern (SQS, Pub/Sub, RabbitMQ, Celery, Sidekiq); workers consume at steady rate; enables carbon-aware scheduling later.
- **SCI:** Reduces M (lower peak hardware) and enables I improvement via time-shifted execution.
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/queue-non-urgent-requests

### Reduce network traversal between VMs
- **Problem:** Cross-AZ or cross-region service-to-service calls cost energy on every hop and add latency that often hides further inefficiency.
- **Detection signals:** Microservices in different regions calling each other on hot paths, no awareness of placement in topology, chatty service-mesh patterns crossing AZ boundaries.
- **Fix:** Co-locate tightly coupled services in the same AZ/region; use placement groups; reduce chattiness with batched or aggregate calls.
- **SCI:** Reduces E.
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/reduce-network-traversal-between-VMs

### Run AI models at the edge
- **Problem:** Sending raw data (especially video, audio, sensor streams) to the cloud for inference costs network energy and centralized compute.
- **Detection signals:** Mobile/IoT clients streaming raw sensor data to cloud for classification, real-time video pipelines round-tripping to inference endpoints.
- **Fix:** Quantize and deploy models to edge devices (CoreML, TFLite, ONNX Runtime Mobile, TensorRT on edge boxes); use cloud only for aggregation/training.
- **SCI:** Reduces E (no transit) and centralized M.
- **Trade-off:** Shifts M to client devices; may shorten device life through heavier use. Name this trade-off when recommending.
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/energy-efficent-ai-edge

### Scale logical components independently
- **Problem:** Monoliths force you to scale everything when only one component is the bottleneck — over-provisioning the rest.
- **Detection signals:** A single deployment unit containing components with wildly different resource profiles, full-app scaling to handle one hot endpoint.
- **Fix:** Decompose into microservices or independent functions, scale each on its own metric. Don't shatter cohesive code just for this — apply where component load profiles actually differ.
- **SCI:** Reduces M (right-size per component).
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/scale-logical-components-independently

### Use a service mesh only if needed
- **Problem:** Service meshes add sidecar containers and extra network hops to every request, costing real energy.
- **Detection signals:** Istio/Linkerd deployed mesh-wide for features only a handful of services use, no measurable benefit vs without-mesh.
- **Fix:** Apply mesh selectively to services that need its features (mTLS, traffic splitting, observability); use lighter alternatives (per-service libraries) elsewhere.
- **SCI:** Reduces E (no sidecar overhead) and M (fewer containers per pod).
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/evaluate-using-a-service-mesh

---

## Technology Selection

### Evaluate other CPU architectures
- **Problem:** x86 is not always the most energy-efficient option for a given workload; ARM and other specialized cores can do the same work with less power.
- **Detection signals:** Default x86 instance choice without benchmarking, scale-out workloads on general-purpose CPUs.
- **Fix:** Benchmark on ARM (AWS Graviton, Azure Cobalt, GCP Axion) and on specialized accelerators where applicable; switch where the energy/cost ratio justifies.
- **SCI:** Reduces E and (often) M.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/evaluate-other-cpu-architectures

### Optimize the size of AI/ML models
- **Problem:** Large models cost more energy per inference and per training step than necessary.
- **Detection signals:** Full-precision FP32 inference, no quantization, fine-tunes shipped at full base-model size, no distillation considered.
- **Fix:** Quantize (INT8, INT4, FP8), prune, distill to smaller student models, use LoRA adapters instead of full fine-tunes.
- **SCI:** Reduces E (every inference) and improves R.
- **URL:** https://patterns.greensoftware.foundation/architecture/compress-ml-models-for-inference

### Select a more energy efficient AI/ML framework
- **Problem:** Frameworks differ significantly in throughput per watt for the same model on the same hardware.
- **Detection signals:** Inference still on the training framework (eager-mode PyTorch) in production; no consideration of optimized runtimes.
- **Fix:** For inference: ONNX Runtime, TensorRT, vLLM, TGI, llama.cpp, MLX. For training: pick framework matched to hardware (PyTorch+CUDA, JAX+TPU). Benchmark.
- **SCI:** Reduces E.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/energy-efficent-framework

### Select the right hardware/VM instance types for AI/ML training
- **Problem:** Default GPU choice often over- or under-provisions for the model size, leaving the gap as wasted energy.
- **Detection signals:** A100/H100 chosen by default for small models, no profiling of GPU utilization, no consideration of multi-instance GPU (MIG).
- **Fix:** Profile actual GPU utilization, right-size to the smallest GPU that fits the model and target throughput, consider MIG/fractional GPUs for small jobs.
- **SCI:** Reduces M.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/right-hardware-type

### Use cloud native processor VMs
- **Problem:** Cloud-native ARM processors (Graviton, Cobalt, Axion) are designed for scale-out workloads and use less energy per unit of work for compatible workloads.
- **Detection signals:** Default Intel/AMD x86 selection for workloads that compile cleanly on ARM.
- **Fix:** Try ARM-based VMs for scale-out services (web, microservices, caches, databases with ARM support); benchmark before committing.
- **SCI:** Reduces E and M.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/use-energy-efficient-hardware

### Use efficient file formats for AI/ML development
- **Problem:** CSV/JSON for training data and full checkpoint formats inflate storage and slow I/O, costing energy on every epoch read.
- **Detection signals:** Training pipelines reading CSV/JSON, full checkpoints stored uncompressed, no use of Parquet/Arrow/TFRecord/WebDataset.
- **Fix:** Parquet/Arrow for tabular, WebDataset/TFRecord for image/audio, safetensors for checkpoints; compress where appropriate.
- **SCI:** Reduces E (less I/O) and M (less storage).
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/efficent-format-for-model-training

### Use energy efficient AI/ML models
- **Problem:** Choosing the biggest available model when a smaller one suffices wastes energy per inference and per training step, forever.
- **Detection signals:** GPT-class model used for tasks a small classifier solves, default to largest model in family without ablation.
- **Fix:** Match model size to task difficulty; use routing patterns to send easy queries to small models and hard queries to large ones; benchmark.
- **SCI:** Reduces E and M.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/energy-efficent-models

### Use serverless cloud services
- **Problem:** Always-on VMs and managed services running below their capacity pay full M and full idle E.
- **Detection signals:** Low-utilization VMs left running, dedicated database clusters for low-traffic apps, custom-built services for things serverless platforms solve.
- **Fix:** Use FaaS (Lambda, Cloud Functions), serverless containers (Cloud Run, App Runner), serverless databases (DynamoDB, Aurora Serverless, Cosmos serverless) where workload profile fits.
- **SCI:** Reduces M (shared infra) and E (no idle draw).
- **Trade-off:** Cold starts, vendor lock-in. Not for ultra-low-latency or steady-state high-throughput workloads.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/use-serverless
