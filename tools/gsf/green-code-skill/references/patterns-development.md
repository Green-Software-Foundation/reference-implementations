# GSF Development Patterns Reference

All 23 patterns from the GSF Development category. Each entry includes the problem, what to scan for in code review (detection signals), the fix approach for generation, the SCI term it reduces, and the canonical URL.

> The Development category covers code-level patterns — things a developer changes inside a file, not architecture or ops choices.

## Table of contents

- Data handling: [Avoid tracking unnecessary data](#avoid-tracking-unnecessary-data), [Cache static data](#cache-static-data), [Compress stored data](#compress-stored-data), [Compress transmitted data](#compress-transmitted-data), [Reduce transmitted data](#reduce-transmitted-data)
- Media & code efficiency: [Defer offscreen images](#defer-offscreen-images), [Deprecate GIFs](#deprecate-gifs-for-animated-content), [Optimize image size](#optimize-image-size), [Remove unused CSS](#remove-unused-css-definitions), [Serve images in modern formats](#serve-images-in-modern-formats), [Use compiled languages](#use-compiled-languages)
- Web performance: [Avoid excessive DOM size](#avoid-an-excessive-dom-size), [Avoid chaining critical requests](#avoid-chaining-critical-requests), [Enable text compression](#enable-text-compression), [Keep request counts low](#keep-request-counts-low), [Minify web assets](#minify-web-assets), [Minimize main thread work](#minimize-main-thread-work), [Use server-side rendering for high-traffic pages](#use-server-side-rendering-for-high-traffic-pages)
- Cloud & deployment: [Minimize deployed environments](#minimize-the-total-number-of-deployed-environments), [Terminate TLS at border gateway](#terminate-tls-at-border-gateway), [Use async network calls](#use-asynchronous-network-calls-instead-of-synchronous)
- AI/ML (also see `patterns-ai-ml.md`): [Pre-trained models & transfer learning](#leverage-pre-trained-models-and-transfer-learning), [Use sustainable regions for AI/ML training](#use-sustainable-regions-for-aiml-training)

---

## Data Handling

### Avoid tracking unnecessary data
- **Problem:** User tracking, analytics, and ad-targeting code generate significant emissions across every page load and every backend write.
- **Detection signals:** Multiple analytics SDKs loaded, third-party tracker scripts, event-logging fired on every interaction, full-event payloads stored when only aggregates are needed.
- **Fix:** Remove unused trackers, sample events instead of capturing all, aggregate at the edge, store only the fields actually consumed downstream.
- **SCI:** Reduces E (less network, less storage write, less downstream processing) and M (less storage hardware).
- **URL:** https://patterns.greensoftware.foundation/development/data-handling/avoid-tracking-unnecessary-data

### Cache static data
- **Problem:** Re-fetching data that rarely changes over the network wastes energy on every transit hop.
- **Detection signals:** HTTP requests inside loops, no `Cache-Control` headers, repeated fetches of the same resource within a session, missing CDN in front of static assets.
- **Fix:** Add HTTP caching headers, use a CDN, cache in-memory with TTL, prefer client-side caches for truly static config.
- **SCI:** Reduces E (less network transit) and M (less server hardware needed for repeat reads).
- **URL:** https://patterns.greensoftware.foundation/development/data-handling/cache-static-data

### Compress stored data
- **Problem:** Uncompressed at-rest data wastes storage and increases the energy of every read/write.
- **Detection signals:** Plain-text JSON/XML stored in databases or object stores, no compression on log files, raw images in storage when WebP/AVIF would suffice.
- **Fix:** Enable database column compression, gzip/zstd object-store contents, choose compressed serialization formats (Parquet, Avro) for analytical data.
- **SCI:** Reduces M (less storage hardware) and E (less I/O energy per row).
- **URL:** https://patterns.greensoftware.foundation/development/data-handling/compress-stored-data

### Compress transmitted data
- **Problem:** Sending uncompressed payloads over the network wastes energy on every hop.
- **Detection signals:** API responses without `Content-Encoding: gzip` or `br`, large JSON payloads with no compression, file uploads in raw form.
- **Fix:** Enable gzip or Brotli at the server / API gateway / CDN; compress request bodies in clients where bandwidth-bound.
- **SCI:** Reduces E (less network transit energy).
- **URL:** https://patterns.greensoftware.foundation/development/data-handling/compress-transmitted-data

### Reduce transmitted data
- **Problem:** Over-fetching (whole resources when fields would do) costs network energy on every transit.
- **Detection signals:** `SELECT *` patterns in code-generated queries, REST endpoints that return whole objects for list views, no pagination, no field-selection (GraphQL/sparse fieldsets).
- **Fix:** Field selection, pagination, projection at the database level, dedicated list-view DTOs.
- **SCI:** Reduces E (network + serialization cost).
- **URL:** https://patterns.greensoftware.foundation/development/data-handling/reduce-transmitted-data

---

## Media & Code Efficiency

### Defer offscreen images
- **Problem:** Loading images that aren't visible on first paint wastes bandwidth and CPU.
- **Detection signals:** `<img>` tags without `loading="lazy"`, JS that eager-loads gallery images, no Intersection Observer pattern in image-heavy pages.
- **Fix:** `loading="lazy"` on non-critical images, Intersection Observer for custom lazy loading, defer below-the-fold media.
- **SCI:** Reduces E (less network + decode work for content never seen).
- **URL:** https://patterns.greensoftware.foundation/development/media-and-code-efficiency/defer-offscreen-images

### Deprecate GIFs for animated content
- **Problem:** Animated GIFs are 5–10× larger than equivalent MP4/WebM and have lower visual quality.
- **Detection signals:** `.gif` files with animation, `<img src="*.gif">` for motion content.
- **Fix:** Encode as MP4 (H.264) or WebM (VP9/AV1), use `<video autoplay muted loop playsinline>`.
- **SCI:** Reduces E (much smaller payloads → less network and decode).
- **URL:** https://patterns.greensoftware.foundation/development/media-and-code-efficiency/deprecate-gifs

### Optimize image size
- **Problem:** Serving images larger than the rendered display wastes bandwidth and decode CPU.
- **Detection signals:** No `srcset`, fixed-large images for responsive layouts, intrinsic image dimensions far exceeding display dimensions.
- **Fix:** `srcset` + `sizes` for responsive delivery, resize at build time or via image CDN, match output to display pixels.
- **SCI:** Reduces E.
- **URL:** https://patterns.greensoftware.foundation/development/media-and-code-efficiency/properly-sized-images

### Remove unused CSS definitions
- **Problem:** Dead CSS still has to be parsed, kept in memory, and re-evaluated on every layout pass.
- **Detection signals:** Unused selectors flagged by Coverage tool, unused utility classes from CSS frameworks shipped in full, no PurgeCSS / Tailwind JIT configured.
- **Fix:** Tree-shake CSS with PurgeCSS, Tailwind JIT, or framework-native dead-code elimination; remove unused rule blocks in code review.
- **SCI:** Reduces E (less network, less parsing CPU).
- **URL:** https://patterns.greensoftware.foundation/development/media-and-code-efficiency/remove-unused-css

### Serve images in modern formats
- **Problem:** JPEG and PNG are 25–50% larger than WebP / AVIF for equivalent quality.
- **Detection signals:** No `<picture>` element with format fallbacks, `.jpg`/`.png` only, no `Accept`-header negotiation at the image CDN.
- **Fix:** Use `<picture>` with AVIF → WebP → JPEG fallback, or an image CDN that negotiates format from `Accept`.
- **SCI:** Reduces E.
- **URL:** https://patterns.greensoftware.foundation/development/media-and-code-efficiency/serve-images-in-modern-formats

### Use compiled languages
- **Problem:** Interpreted languages re-parse and re-compile on every execution, consuming more energy than ahead-of-time-compiled binaries for equivalent work.
- **Detection signals:** Hot-path code in pure Python/Ruby/JS without JIT or native acceleration where Go/Rust/C# would fit; long-running interpreted workers; CPU-bound batch jobs in interpreted languages.
- **Fix:** For CPU-bound hot paths, prefer compiled languages (Go, Rust, .NET AOT, GraalVM); use native extensions (NumPy, Cython, PyO3) where appropriate; do not rewrite cold paths just for this.
- **SCI:** Reduces E.
- **Trade-off:** Developer velocity, ecosystem fit. Do not apply to non-hot-path code.
- **URL:** https://patterns.greensoftware.foundation/development/media-and-code-efficiency/use-compiled-languages

---

## Web Performance

### Avoid an excessive DOM size
- **Problem:** Larger DOMs cost more CPU and memory on every layout, style, and paint pass — paid by the user device.
- **Detection signals:** Pages with >1500 DOM nodes, deeply nested structures (>32 levels), rendering thousands of list items without virtualization.
- **Fix:** Virtualize long lists, paginate, collapse non-visible regions, avoid wrapping divs purely for layout (use CSS Grid/Flex).
- **SCI:** Reduces E on the client device.
- **URL:** https://patterns.greensoftware.foundation/development/web-performance/avoid-excessive-dom-size

### Avoid chaining critical requests
- **Problem:** Each waterfall step (CSS waits for HTML, JS waits for CSS, fonts wait for CSS) extends time-to-render and total energy spent processing.
- **Detection signals:** Long critical-path chains in Lighthouse, dynamic `<link>` injection, late-discovered fonts, `@import` in CSS.
- **Fix:** `rel="preload"` for critical fonts/scripts, inline critical CSS, avoid `@import` chains, eliminate render-blocking resources.
- **SCI:** Reduces E and improves R (more useful renders per unit energy).
- **URL:** https://patterns.greensoftware.foundation/development/web-performance/avoid-chaining-critical-requests

### Enable text compression
- **Problem:** HTML/JS/CSS/JSON sent uncompressed wastes bandwidth on every page view.
- **Detection signals:** No `Content-Encoding` on text responses, server config with gzip disabled, CDN without compression at edge.
- **Fix:** Enable gzip or Brotli at the server, API gateway, or CDN — most platforms support this with one toggle.
- **SCI:** Reduces E.
- **URL:** https://patterns.greensoftware.foundation/development/web-performance/enable-text-compression

### Keep request counts low
- **Problem:** Each request has fixed overhead (DNS, TLS handshake, headers). High request counts amplify that overhead per page.
- **Detection signals:** Many small JS/CSS files, no bundling, separate requests per icon (use SVG sprites or icon font), one image per small asset.
- **Fix:** Bundle (with care — see trade-offs.md on bundle bloat), use HTTP/2 or HTTP/3 multiplexing, SVG sprite sheets, inline tiny resources.
- **SCI:** Reduces E.
- **URL:** https://patterns.greensoftware.foundation/development/web-performance/keep-request-counts-low

### Minify web assets
- **Problem:** Whitespace and comments in production JS/CSS/HTML waste bandwidth.
- **Detection signals:** Production assets containing readable formatting, source maps shipped to clients, no build-time minifier configured.
- **Fix:** Configure minification in build pipeline (esbuild, terser, swc, htmlnano, cssnano); don't ship source maps to end users.
- **SCI:** Reduces E (small but compounds at scale).
- **URL:** https://patterns.greensoftware.foundation/development/web-performance/minify-web-assets

### Minimize main thread work
- **Problem:** Long-running JS on the browser main thread underutilizes multi-core CPUs and burns user-device energy.
- **Detection signals:** Long-task warnings in Performance tab, parsing/processing >50ms on main thread, heavy work in event handlers, synchronous JSON parsing of large payloads.
- **Fix:** Move heavy work to Web Workers, break work into `requestIdleCallback` chunks, push computation server-side where appropriate.
- **SCI:** Reduces E on the user device.
- **URL:** https://patterns.greensoftware.foundation/development/web-performance/minimize-main-thread-work

### Use server-side rendering for high-traffic pages
- **Problem:** Re-rendering the same page client-side for every visitor wastes total energy across the user base.
- **Detection signals:** Marketing/landing pages built as SPA-only with no SSR, high-traffic pages re-fetching identical content per session.
- **Fix:** SSR or SSG with hydration for high-traffic pages; keep CSR for interactive app shells.
- **SCI:** Improves R (one render serves many) — most powerful at high traffic; reduces aggregate E.
- **Trade-off:** SSR costs server CPU per request. Only worth it when traffic is high enough that one server render is cheaper than N client renders. Don't apply to low-traffic admin tools.
- **URL:** https://patterns.greensoftware.foundation/development/web-performance/use-server-side-rendering

---

## Cloud & Deployment

### Minimize the total number of deployed environments
- **Problem:** Each environment (dev, test, staging, perf, UAT, prod-eu, prod-us…) has running cost and embodied carbon, even when idle.
- **Detection signals:** Long-lived dev environments per developer, staging clones that mirror production size, perf environments running 24×7.
- **Fix:** Ephemeral preview environments per PR, scale staging to a fraction of production, shut down non-prod nightly and on weekends, consolidate test environments where isolation isn't required.
- **SCI:** Reduces M (less always-on hardware) and E (less idle compute).
- **URL:** https://patterns.greensoftware.foundation/development/minimizing-deployed-environments

### Terminate TLS at border gateway
- **Problem:** Terminating and re-establishing TLS at every hop inside a trusted network adds CPU cycles for no security benefit.
- **Detection signals:** Service-to-service mTLS inside a closed VPC where it's not actually required, double-TLS through load balancer plus service.
- **Fix:** Terminate TLS once at the border (load balancer, ingress, API gateway) and use plain HTTP within the trusted boundary, *if* threat model allows.
- **SCI:** Reduces E.
- **Trade-off:** Loses defense-in-depth. Don't apply if zero-trust is required or compliance demands end-to-end encryption (PCI, HIPAA may, depending on data).
- **URL:** https://patterns.greensoftware.foundation/development/evaluate-whether-to-use-TLS-termination

### Use Asynchronous network calls instead of synchronous
- **Problem:** Blocking on synchronous I/O pins a thread and prevents the CPU from doing other useful work, inflating compute needed per request.
- **Detection signals:** `requests` (Python sync), `RestTemplate` (Java blocking), `fetch` without `await` chained badly, sequential `await`s where parallel would work, sync DB drivers in async frameworks.
- **Fix:** Use async clients (`httpx`/`aiohttp`, `WebClient`, `HttpClient.SendAsync`), `Promise.all` / `asyncio.gather` for parallelizable calls.
- **SCI:** Reduces E (higher throughput per server → less hardware), improves R.
- **URL:** https://patterns.greensoftware.foundation/development/use-async-instead-of-sync

---

## AI/ML (Development category)

Detailed AI/ML treatment lives in `patterns-ai-ml.md`. These two patterns sit in the Development category in the GSF catalog.

### Leverage pre-trained models and transfer learning
- **Problem:** Training a model from scratch costs orders of magnitude more energy than fine-tuning a pre-trained one.
- **Detection signals:** Training pipelines that start from random weights for tasks where a foundation model exists; teams reinventing embeddings, image classifiers, or LLMs.
- **Fix:** Start from a pre-trained checkpoint (Hugging Face, model zoos), use LoRA / QLoRA / adapter-based fine-tuning, freeze backbone layers where appropriate.
- **SCI:** Massive reduction in E (training energy amortized across many users); improves R.
- **URL:** https://patterns.greensoftware.foundation/development/pre-trained-transfer-learning

### Use sustainable regions for AI/ML training
- **Problem:** Training is energy-intensive; running it in a high-carbon-intensity region wastes the chance to do the same work on cleaner electricity.
- **Detection signals:** Training jobs hard-coded to a single region, no consideration of grid mix or time-of-day in scheduling.
- **Fix:** Choose cloud regions with lower carbon intensity (cloud providers publish this); schedule non-urgent training for low-intensity windows.
- **SCI:** Reduces I (this is one of the few code-adjacent ways to move I — and only by *enabling* the deploy/ops decision).
- **URL:** https://patterns.greensoftware.foundation/development/leverage-sustainable-regions
