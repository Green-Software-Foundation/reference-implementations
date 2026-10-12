#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["codecarbon>=3,<4"]
# ///
"""Measure the energy and operational carbon of shell commands with CodeCarbon.

Each --variant is NAME=COMMAND; the first one is the baseline. Every variant
runs --warmup unmeasured times, then --runs measured times, interleaved and
alternating order so drift and thermal state fall evenly on all variants.
Each measured run is one CodeCarbon task (machine tracking mode, so child
processes count). An idle task of the baseline's median duration gives the
machine's background floor.

Prints a markdown summary to stdout and writes raw per-run data to --out.

    uv run measure.py --variant before="python job.py --old" \\
                      --variant after="python job.py" --units 1000 --unit-label records
"""

import argparse
import json
import logging
import statistics
import subprocess
import sys
import time

MEASURED_CPU = {"RAPL", "Power Gadget", "Windows EMI", "PowerMetrics"}
MEASURED_GPU = {"pynvml", "amdsmi", "PowerMetrics"}
MIN_RUN_SECS = 5.0


class LogCapture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self.records = []

    def emit(self, record):
        self.records.append((record.levelname, record.getMessage()))


def parse_variant(text):
    name, sep, command = text.partition("=")
    if not sep or not name.strip() or not command.strip():
        raise argparse.ArgumentTypeError(f"expected NAME=COMMAND, got {text!r}")
    return name.strip(), command.strip()


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--variant", action="append", type=parse_variant, required=True,
                   metavar="NAME=COMMAND", help="command to measure; repeat for each variant, baseline first")
    p.add_argument("--runs", type=int, default=5, help="measured runs per variant (default 5)")
    p.add_argument("--warmup", type=int, default=1, help="unmeasured warm-up runs per variant (default 1)")
    p.add_argument("--units", type=float, help="functional units (R) one run performs, e.g. 1000 requests")
    p.add_argument("--unit-label", default="unit", help="name of the functional unit (default 'unit')")
    p.add_argument("--country", metavar="ISO3",
                   help="grid location as ISO 3166-1 alpha-3 (e.g. DEU); runs offline instead of geolocating by IP")
    p.add_argument("--sample-secs", type=float, default=1.0, help="CodeCarbon power sampling interval (default 1)")
    p.add_argument("--no-idle", action="store_true", help="skip the idle-floor measurement")
    p.add_argument("--out", default="green-measure.json", help="raw results file (default green-measure.json)")
    args = p.parse_args(argv)
    names = [n for n, _ in args.variant]
    if len(set(names)) != len(names):
        p.error("variant names must be unique")
    if args.runs < 1:
        p.error("--runs must be at least 1")
    return args


def make_tracker(args):
    from codecarbon import EmissionsTracker, OfflineEmissionsTracker

    common = dict(project_name="green-measure", measure_power_secs=args.sample_secs,
                  save_to_file=False, tracking_mode="machine", log_level="info")
    if args.country:
        tracker = OfflineEmissionsTracker(country_iso_code=args.country.upper(), **common)
    else:
        tracker = EmissionsTracker(**common)
    # CodeCarbon only logs which power source it chose, so capture its log instead of printing it.
    capture = LogCapture()
    cc_logger = logging.getLogger("codecarbon")
    cc_logger.handlers = [capture]
    cc_logger.propagate = False
    return tracker, capture


def run_command(name, command):
    proc = subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-20:])
        sys.exit(f"variant {name!r} exited {proc.returncode}; measuring a failing command is meaningless.\n{tail}")


def measure_task(tracker, task_name, work):
    tracker.start_task(task_name)
    work()
    data = tracker.stop_task()
    if data is None:
        sys.exit("CodeCarbon returned no data for a task (another CodeCarbon instance running?). "
                 "Re-run with log output to diagnose.")
    return {
        "duration_s": data.duration,
        "energy_kwh": data.energy_consumed,
        "cpu_kwh": data.cpu_energy,
        "gpu_kwh": data.gpu_energy,
        "ram_kwh": data.ram_energy,
        "emissions_kg": data.emissions,
    }, data


def tracking_methods(records):
    methods = {}
    for _, msg in records:
        for line in msg.splitlines():
            key, sep, value = line.strip().partition(" Tracking Method: ")
            if sep:
                methods[key.lower()] = value.strip()
    return methods


def classify(methods):
    cpu, gpu = methods.get("cpu", "unknown"), methods.get("gpu", "Unspecified")
    gpu_ok = gpu in MEASURED_GPU or gpu == "Unspecified"
    return "measured" if cpu in MEASURED_CPU and gpu_ok else "estimated"


def summarize(runs):
    energy = [r["energy_kwh"] for r in runs]
    return {
        "energy_kwh_median": statistics.median(energy),
        "energy_kwh_min": min(energy),
        "energy_kwh_max": max(energy),
        "duration_s_median": statistics.median(r["duration_s"] for r in runs),
        "emissions_kg_median": statistics.median(r["emissions_kg"] for r in runs),
    }


ENERGY_SCALES = [(1, "kWh"), (1e3, "Wh"), (1e6, "mWh"), (1e9, "µWh")]
MASS_SCALES = [(1, "kg"), (1e3, "g"), (1e6, "mg"), (1e9, "µg")]


def column_format(values, scales):
    """One unit per column, chosen so the smallest value reads >= 1, keeping rows comparable."""
    smallest = min(v for v in values if v > 0) if any(v > 0 for v in values) else 1
    factor, label = next(((f, l) for f, l in scales if smallest * f >= 1), scales[-1])
    return lambda v: f"{v * factor:.4g} {label}"


def render(result, args):
    m, ctx = result["method"], result["context"]
    unit = args.unit_label
    lines = [
        f"**Method:** CodeCarbon {ctx['codecarbon_version']}, **{m['label']}** "
        f"(CPU: {m['cpu']}, GPU: {m['gpu']}, RAM: {m['ram']}); "
        f"{args.runs} interleaved runs per variant after {args.warmup} warm-up",
        f"**Machine:** {ctx['cpu_model']} · {ctx['os']}",
        f"**Grid:** {ctx['grid']}, ~{ctx['intensity_g_per_kwh']:.0f} gCO₂eq/kWh (CodeCarbon)",
        "",
    ]
    per_unit = args.units is not None
    header = "| Variant | Energy per run (median, min–max) | Duration (median) |"
    rule = "|---|---|---|"
    if per_unit:
        header += f" Energy per {unit} | CO₂eq per {unit} |"
        rule += "---|---|"
    lines += [header, rule]
    summary = result["summary"].values()
    fmt_run = column_format([v for s in summary for v in (s["energy_kwh_min"], s["energy_kwh_max"])], ENERGY_SCALES)
    if per_unit:
        fmt_unit_e = column_format([s["energy_kwh_median"] / args.units for s in summary], ENERGY_SCALES)
        fmt_unit_c = column_format([s["emissions_kg_median"] / args.units for s in summary], MASS_SCALES)
    for name, s in result["summary"].items():
        row = (f"| {name} | {fmt_run(s['energy_kwh_median'])} "
               f"({fmt_run(s['energy_kwh_min'])}–{fmt_run(s['energy_kwh_max'])}) "
               f"| {s['duration_s_median']:.2f} s |")
        if per_unit:
            row += f" {fmt_unit_e(s['energy_kwh_median'] / args.units)} | {fmt_unit_c(s['emissions_kg_median'] / args.units)} |"
        lines.append(row)
    lines.append("")
    for name, cmp in result["comparison"].items():
        verdict = "separated: ranges do not overlap" if cmp["separated"] else "ranges overlap: no measurable difference at this run count"
        lines.append(f"- **{name} vs {result['baseline']}:** {cmp['energy_change_pct']:+.1f}% median energy per run ({verdict})")
    if result.get("idle"):
        idle = result["idle"]
        lines.append(f"- **Idle floor:** {idle['power_w']:.1f} W average over {idle['duration_s']:.1f} s "
                     f"(compare variant average power: {', '.join(f'{n} {p:.1f} W' for n, p in result['avg_power_w'].items())})")
    for warning in result["warnings"]:
        lines.append(f"- ⚠ {warning}")
    lines.append(f"- Raw data: `{args.out}`")
    return "\n".join(lines)


def main(argv=None):
    args = parse_args(argv)
    tracker, capture = make_tracker(args)
    variants = args.variant
    runs = {name: [] for name, _ in variants}
    last = None
    idle = None
    try:
        for _ in range(args.warmup):
            for name, command in variants:
                run_command(name, command)
        for i in range(args.runs):
            order = variants if i % 2 == 0 else list(reversed(variants))
            for name, command in order:
                record, last = measure_task(tracker, f"{name}#{i}", lambda: run_command(name, command))
                runs[name].append(record)
        if not args.no_idle:
            secs = statistics.median(r["duration_s"] for r in runs[variants[0][0]])
            record, _ = measure_task(tracker, "idle", lambda: time.sleep(secs))
            idle = {"duration_s": record["duration_s"],
                    "power_w": record["energy_kwh"] * 3.6e6 / record["duration_s"]}
    finally:
        tracker.stop()

    methods = tracking_methods(capture.records)
    summary = {name: summarize(r) for name, r in runs.items()}
    baseline = variants[0][0]
    base = summary[baseline]
    comparison = {
        name: {
            "energy_change_pct": (s["energy_kwh_median"] / base["energy_kwh_median"] - 1) * 100,
            "separated": s["energy_kwh_max"] < base["energy_kwh_min"] or s["energy_kwh_min"] > base["energy_kwh_max"],
        }
        for name, s in summary.items() if name != baseline
    }
    total_energy = sum(r["energy_kwh"] for rs in runs.values() for r in rs)
    total_emissions = sum(r["emissions_kg"] for rs in runs.values() for r in rs)
    warnings = [msg.strip() for level, msg in capture.records if level in ("WARNING", "ERROR")]
    short = [n for n, s in summary.items() if s["duration_s_median"] < MIN_RUN_SECS]
    if short:
        warnings.append(f"median run under {MIN_RUN_SECS:.0f} s for {', '.join(short)}: power sampling and "
                        "process start-up dominate; scale up the work per run")
    if args.runs < 5:
        warnings.append(f"only {args.runs} runs per variant; ranges are unreliable below 5")

    result = {
        "baseline": baseline,
        "variants": dict(variants),
        "units_per_run": args.units,
        "unit_label": args.unit_label,
        "method": {
            "label": classify(methods),
            "cpu": methods.get("cpu", "unknown"),
            "gpu": methods.get("gpu", "unknown"),
            "ram": methods.get("ram", "unknown"),
        },
        "context": {
            "codecarbon_version": last.codecarbon_version,
            "cpu_model": last.cpu_model,
            "os": last.os,
            "grid": ", ".join(x for x in (last.country_name, last.region, last.cloud_provider, last.cloud_region) if x),
            "intensity_g_per_kwh": total_emissions / total_energy * 1000 if total_energy else float("nan"),
            "tracking_mode": last.tracking_mode,
        },
        "summary": summary,
        "comparison": comparison,
        "avg_power_w": {n: s["energy_kwh_median"] * 3.6e6 / s["duration_s_median"] for n, s in summary.items()},
        "idle": idle,
        "warnings": warnings,
        "runs": runs,
    }
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(render(result, args))


if __name__ == "__main__":
    main()
