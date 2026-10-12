# Measure mode

Energy and operational carbon of real runs, measured with [CodeCarbon](https://github.com/mlco2/codecarbon). Usually a before/after comparison: a **baseline** and one or more **variants** doing the same work.

CodeCarbon sees **this machine only**. Work done elsewhere, such as LLM API inference, a remote database, or other services, does not appear in its numbers. For API-bound code, the measurement covers the client side; use call and token counts as the proxy for the remote side and say so in the report.

## Steps

1. **Fix R and the variants.** Agree with the user on the code path, the functional unit R (per request, per 1k records, per inference), and how many units one run performs. Done when each variant is one shell command that performs the same R units of work, exits 0, and is safe to repeat.
   - A Python function gets a small driver script that imports it and calls it in a loop; the command is `python driver.py`.
   - Use the same inputs and fixtures for every variant, with a fixed seed, local data, and no network: network latency is noise.
   - Size the work so each run lasts **10 s or more**. CodeCarbon samples power periodically, so in short runs sampling error and process start-up dominate.
   - Each command runs `(warmup + runs)` times. Before measuring commands that write external state or call paid APIs, confirm with the user.

2. **Run the harness** from the project directory. [`scripts/measure.py`](../scripts/measure.py) interleaves the variants, discards warm-up runs, measures an idle floor, prints a markdown summary, and writes raw per-run data to `--out`.

   ```bash
   uv run <skill-dir>/scripts/measure.py \
     --variant baseline="python driver.py --impl current" \
     --variant batched="python driver.py --impl batched" \
     --units 1000 --unit-label record --country DEU
   ```

   - `uv run` installs CodeCarbon ephemerally from the script's inline metadata. Without uv, install into a scratch venv (`python -m venv .gcs-venv && .gcs-venv/bin/pip install 'codecarbon>=3,<4'`) and run with that interpreter. Leave the project's dependency files untouched unless the user asks.
   - Pass `--country` (ISO 3166-1 alpha-3) for the grid where the code runs. Without it CodeCarbon geolocates by IP, and a VPN or remote dev box reports the wrong grid.
   - `--runs` defaults to 5. Add runs when the ranges overlap.

   Done when the harness exits 0 and prints its summary. A failing variant aborts the run: fix the command, then re-run.

3. **Read the Method line before the numbers.** The harness labels the run **measured** (hardware energy counters: RAPL, Windows EMI, PowerMetrics, NVML, AMDSMI) or **estimated** (CodeCarbon's CPU-load or TDP power models). Carry that label onto every number you report. An estimated run models power from CPU utilization, so its energy differences track runtime and load and miss efficiency gains at equal load. When the run is estimated, tell the user what would make it measured: a Linux host with readable RAPL files under `/sys/class/powercap/intel-rapl`, Windows 11 on bare metal, or NVIDIA/AMD GPUs for GPU work.

4. **Judge the difference.**
   - Compare **energy**, not emissions. Every variant ran under the same I, so energy is the code's signal, and emissions add only the grid factor.
   - A difference counts when the harness reports the ranges as **separated** (min–max ranges do not overlap). Overlapping ranges mean "no measurable difference at this run count". Report that plainly, or re-run with more runs.
   - Compare each variant's average power with the idle floor. When the two are close, the workload barely loads the machine, and the measured difference is mostly runtime.

   Done when every harness warning (short runs, few runs, CodeCarbon fallbacks) is resolved by a re-run or carried into the report.

5. **Report** with the template below.

## Report template

```
## Green Measurement

**Workload:** <code path> · **R:** <functional unit>, <N> per run
**Variants:** <name: what changed>, baseline first

<harness summary, pasted unchanged: Method, Machine, Grid, table, comparison lines, warnings>

**Result:** <variant> uses <X>% less energy per <unit> than <baseline> (<measured|estimated>, ranges separated) | no measurable difference at <runs> runs.
**Scope:** operational carbon only (E × I) on this machine and grid. Embodied hardware emissions (M) are not measured; a full SCI score needs embodied data for the hardware. Production hardware, load, and grid will differ. <Remote work not captured, if any.>
```
