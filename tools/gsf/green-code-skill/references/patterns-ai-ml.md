# AI/ML & Agentic AI Patterns Reference

This file consolidates AI/ML patterns across two families: model and training patterns (cross-referenced from the GSF Development and Architecture categories) and agentic AI workload patterns (covering LLM-driven orchestration, retry behavior, planning depth, model routing, and tool-call efficiency).

> Both families apply SCI principles and the three-pillar logic — energy efficiency, hardware efficiency, and carbon awareness — to the AI/ML lifecycle, from model training through agentic orchestration. The agentic patterns extend the same principles to LLM application workloads, where call counts can compound rapidly across loop iterations.

---

## AI/ML model and training patterns

### Leverage pre-trained models and transfer learning
- **Problem:** Training from scratch costs orders of magnitude more energy than fine-tuning a foundation model.
- **Detection signals:** Training pipelines starting from random weights for tasks where a pre-trained model exists; reinventing embeddings, classifiers, or LLMs in-house.
- **Fix:** Start from pre-trained checkpoints (Hugging Face, model zoos); use LoRA/QLoRA or adapter-based fine-tuning; freeze backbone layers.
- **SCI:** Massive E reduction (training amortized across users); improves R.
- **Pillar:** Energy efficiency.
- **URL:** https://patterns.greensoftware.foundation/development/pre-trained-transfer-learning

### Use sustainable regions for AI/ML training
- **Problem:** Training is energy-intensive; high-carbon-intensity regions multiply that.
- **Detection signals:** Region hard-coded to convenience, no grid-mix awareness.
- **Fix:** Choose lower-intensity regions (cloud providers publish per-region intensity); schedule training for low-intensity windows.
- **SCI:** Reduces I (one of the few code-adjacent ways to influence I, via enabling the deploy decision).
- **Pillar:** Carbon awareness.
- **URL:** https://patterns.greensoftware.foundation/development/leverage-sustainable-regions

### Adopt serverless architecture for AI/ML workload processes
- **Problem:** Always-on GPU inference servers waste energy and embodied carbon during idle periods.
- **Detection signals:** GPU instances reserved 24×7 for bursty inference, no scale-to-zero.
- **Fix:** Use scale-to-zero inference platforms (SageMaker Serverless, Vertex AI endpoints, Modal, Replicate) or KEDA-driven K8s.
- **SCI:** Reduces M and E.
- **Trade-off:** Cold starts. Avoid for strict-SLA inference.
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/serverless-model-development

### Optimize the size of AI/ML models
- **Problem:** Larger-than-necessary models cost more energy per inference and per training step.
- **Detection signals:** Full FP32 inference, no quantization, no distillation, full fine-tunes instead of adapters.
- **Fix:** Quantize (INT8/INT4/FP8), prune, distill to smaller student models, use LoRA adapters.
- **SCI:** Reduces E per inference and per training step.
- **URL:** https://patterns.greensoftware.foundation/architecture/compress-ml-models-for-inference

### Run AI models at the edge
- **Problem:** Streaming raw data to the cloud for inference costs transit energy + central compute.
- **Detection signals:** Mobile/IoT clients sending raw sensor/video streams to inference endpoints.
- **Fix:** Quantize and deploy to device (CoreML, TFLite, ONNX Runtime Mobile, TensorRT edge); cloud for aggregation/training only.
- **SCI:** Reduces transit E and central M.
- **Trade-off:** Shifts M to client devices. Name this explicitly.
- **URL:** https://patterns.greensoftware.foundation/architecture/system-topology/energy-efficent-ai-edge

### Select a more energy-efficient AI/ML framework
- **Problem:** Frameworks differ significantly in throughput per watt for the same model on the same hardware.
- **Detection signals:** Eager-mode PyTorch in production inference, no consideration of optimized runtimes.
- **Fix:** Inference — ONNX Runtime, TensorRT, vLLM, TGI, llama.cpp, MLX. Training — PyTorch+CUDA, JAX+TPU. Benchmark.
- **SCI:** Reduces E.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/energy-efficent-framework

### Select the right hardware/VM instance types for AI/ML training
- **Problem:** Defaulting to top-end GPUs for small models wastes M and E.
- **Detection signals:** A100/H100 chosen by default, no GPU utilization profiling.
- **Fix:** Profile GPU utilization, right-size to smallest GPU that hits target throughput, consider MIG/fractional GPUs.
- **SCI:** Reduces M.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/right-hardware-type

### Use efficient file formats for AI/ML development
- **Problem:** CSV/JSON for training data and uncompressed checkpoints inflate I/O on every epoch.
- **Detection signals:** CSV/JSON-based data pipelines, uncompressed checkpoints, no Parquet/Arrow/TFRecord/WebDataset.
- **Fix:** Parquet/Arrow for tabular, WebDataset/TFRecord for image/audio, safetensors for checkpoints.
- **SCI:** Reduces E (less I/O) and M (less storage).
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/efficent-format-for-model-training

### Use energy-efficient AI/ML models
- **Problem:** Defaulting to the largest model in a family when a smaller one suffices wastes energy forever after.
- **Detection signals:** GPT-class model used for tasks a small classifier handles, no ablation.
- **Fix:** Match model size to task; use a router to send easy queries to small models and hard ones to large; benchmark.
- **SCI:** Reduces E and M.
- **URL:** https://patterns.greensoftware.foundation/architecture/technology-selection/energy-efficent-models

---

## Agentic AI workload patterns

These patterns target the energy and emissions profile of agentic AI systems — LLM-driven orchestration with planning, tool calls, retries, and iterative reasoning. Each loop iteration is a model call, each call carries real energy cost, and unbounded agentic loops can compound to dozens of calls for a single user goal. Applying SCI principles at this layer delivers some of the largest available reductions in modern AI workloads.

### Right-size the model per subtask (model routing)
- **Problem:** Using a frontier model for every step of an agentic pipeline overspends energy on subtasks a small model could handle.
- **Detection signals:** Single-model agentic loops where every classification, extraction, and routing decision goes to the largest model.
- **Fix:** Implement a router. Send classification/extraction/routing to small fast models (Haiku-class, 7B local, embedders); reserve large models for synthesis, complex reasoning, and final answers.
- **SCI:** Reduces E significantly (often 5–20× per affected step).
- **Pillar:** Energy efficiency.

### Cap the retry budget
- **Problem:** Unbounded retries on LLM calls, tool calls, or API failures turn transient errors into emissions amplifiers — and into bills.
- **Detection signals:** `while True` retry loops, exponential backoff without a ceiling, retry-on-any-exception without classification, agentic chains that retry the whole plan on partial failure.
- **Fix:** Set explicit max attempts (3–5 typical), classify errors (retry only transient ones), use exponential backoff *with a hard ceiling*, fail loud and propagate so the user can intervene.
- **SCI:** Reduces E (avoids runaway calls) and improves R (faster failure → faster correct answer).
- **Pillar:** Energy efficiency.

### Bound planning and reasoning depth
- **Problem:** ReAct/CoT/agentic-planning loops without depth caps can spiral into 20+ iterations on tasks that should converge in 3.
- **Detection signals:** Agent loops with no `max_iterations` parameter, planners that re-plan after every tool call, no loop-detection on identical or near-identical thoughts.
- **Fix:** Set `max_iterations` (5–10 typical for most tasks), detect repeated states/thoughts and break, surface "I'm stuck — here's what I have" to the user rather than burning more tokens.
- **SCI:** Reduces E (cap on total calls per task) and improves R.
- **Pillar:** Energy efficiency.

### Cache LLM responses (deterministic and semantic)
- **Problem:** Repeat queries — explicit duplicates or near-duplicates — re-run inference for no new information.
- **Detection signals:** No caching layer in front of LLM calls, identical prompts hitting the API repeatedly within a session, FAQs and boilerplate generation re-running every time.
- **Fix:** Exact-match cache (hash of prompt+model+params) for deterministic calls; semantic cache (embedding similarity) for near-duplicates with a similarity threshold; respect cache TTL based on content freshness.
- **SCI:** Reduces E roughly in proportion to hit rate; improves R (cache hits are much faster).
- **Pillar:** Energy efficiency.

### Use provider prompt caching for stable context
- **Problem:** Resending the same large system prompt, document, or tool definitions on every call burns input tokens and provider compute.
- **Detection signals:** Long stable prefixes (system prompts, RAG context, tool schemas) sent fresh on every call; no use of provider prompt-cache features.
- **Fix:** Use prompt-caching APIs (Anthropic prompt caching, OpenAI cached input, equivalent) for stable prefixes; structure prompts so the cacheable portion comes first.
- **SCI:** Reduces E meaningfully on chat/agent workloads with stable context.
- **Pillar:** Energy efficiency.

### Batch tool calls and parallelize independent steps
- **Problem:** Strictly sequential agentic loops serialize work that could happen in parallel, multiplying total latency and total time servers are engaged per task.
- **Detection signals:** Agents that fetch dependencies one at a time even when independent, no parallel tool execution, plans that bottleneck on a single thread.
- **Fix:** Identify independent subtasks in the plan; dispatch tool calls in parallel where the agent framework supports it; merge results back.
- **SCI:** Improves R (more useful work per unit wall-clock and per unit of engaged compute).
- **Pillar:** Energy efficiency.

### Pre-filter retrieval before expensive reranking
- **Problem:** Running a cross-encoder reranker over thousands of candidates is wasteful when a cheap first stage can prune 95%.
- **Detection signals:** RAG pipelines feeding full vector-search results into a heavy reranker, no top-k cutoff before rerank, no metadata pre-filter.
- **Fix:** Two-stage retrieval — cheap recall (BM25 / dense vector top-k) → expensive precision (cross-encoder rerank on top-N only).
- **SCI:** Reduces E.
- **Pillar:** Energy efficiency.

### Stop generation when the answer is sufficient
- **Problem:** Generating long responses when the user only needed a short one wastes inference energy on every token.
- **Detection signals:** No `max_tokens` set, no stop sequences, agentic loops that ask for verbose outputs by default.
- **Fix:** Set `max_tokens` appropriately, use stop sequences, prompt for concise answers, allow the user to ask for elaboration if they want it.
- **SCI:** Reduces E per response.
- **Pillar:** Energy efficiency.

### Prefer structured output over multi-turn negotiation
- **Problem:** Multi-turn back-and-forth to extract structured data costs N calls when 1 well-prompted call with structured output works.
- **Detection signals:** Conversations that iterate to get JSON right, manual parsing of free-form text, no use of structured-output / JSON-mode / tool-call APIs.
- **Fix:** Use structured-output APIs (Anthropic tool use, OpenAI structured outputs, Pydantic AI, Instructor) with a clear schema; validate once; retry only if validation fails.
- **SCI:** Reduces E (fewer calls) and improves R.
- **Pillar:** Energy efficiency.

### Detect and break tool-call thrashing
- **Problem:** Agents can fall into loops where they call the same tool with the same args, or oscillate between two tool calls, burning calls without progress.
- **Detection signals:** No loop-detection on tool-call history, identical tool invocations in adjacent steps, no progress metric per iteration.
- **Fix:** Track a hash of (tool_name, args) per iteration; if the same invocation appears twice (or oscillates) within a short window, break and ask the user; consider memory of "what I already tried."
- **SCI:** Reduces E (avoids runaway tool spend).
- **Pillar:** Energy efficiency.

---

## How these compose

A well-designed agentic system typically applies many of these together. A reasonable defaults checklist for a new agentic AI codebase:

1. Model router with smallest-model-first.
2. `max_iterations` set on every agent loop.
3. Retry budget capped, transient errors only.
4. Exact + semantic LLM cache in front of inference.
5. Provider prompt caching for stable system prompts and tool schemas.
6. Parallel tool calls where the framework supports them.
7. Two-stage retrieval if RAG is in the loop.
8. Structured output for any extraction step.
9. `max_tokens` set, stop sequences where applicable.
10. Loop-detection on tool-call history.

These compose to dramatically reduce E per user goal in agentic workloads, often by 3–10× compared to naive implementations — but you should always **measure** rather than quote that range.
