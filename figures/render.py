"""Render the public-track figures from persisted result CSVs.

Contract (docs/research/phase-b-plan.md §8): a figure is a deterministic function of a
committed CSV and a config fingerprint. Nothing here reads a live kernel, a cache, or a
dataset. Run `python figures/render.py --fingerprint <stamp>` to rebuild every figure, or
import `render_nb1` / `render_nb2` / `render_nb3` from a notebook's last cell.

Every caption restates the scope the audit fixed for it: offline, pilot, and what the panel
must not be read as. Those lines are part of the figure, not decoration.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "experiments" / "results"
FIGURES = REPO / "figures"

SUBJECT_COLOURS = {"s01": "#1f77b4", "s02": "#d62728"}
NEUTRAL = "#4d4d4d"
ACCENT = "#e6550d"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _f(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return float(value) if value not in ("", None) else math.nan


def _wilson(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _caption(fig, text: str) -> None:
    fig.text(0.01, 0.01, text, fontsize=7.5, color=NEUTRAL, va="bottom", ha="left", wrap=True)


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# NB1 — signal trust
# --------------------------------------------------------------------------- #


def fig_1_1_qc_rejection(results: Path, out: Path, stamp: str) -> Path:
    rows = _read(results / f"nb01_qc_rejection_{stamp}.csv")
    sessions = [r["session"] for r in rows]
    rates = [_f(r, "rejection_rate") * 100 for r in rows]
    reason_keys = [k for k in rows[0] if k.startswith("reason_")]
    dominant = []
    for r in rows:
        counts = {k[7:]: _f(r, k) for k in reason_keys if r.get(k, "") != ""}
        dominant.append(max(counts, key=counts.get) if counts else "none")
    median = sorted(rates)[len(rates) // 2]

    fig, ax = plt.subplots(figsize=(8, 3.8))
    palette = {"dropout": "#3182bd", "saturation": "#e6550d", "clipping": "#756bb1", "baseline_offset": "#31a354",
               "amplitude_high": "#fd8d3c", "amplitude_low": "#9ecae1", "none": "#bdbdbd"}
    ax.bar(sessions, rates, color=[palette.get(d, NEUTRAL) for d in dominant])
    ax.axhline(median, color=NEUTRAL, ls="--", lw=1, label=f"median {median:.2f}%")
    ax.set_ylabel("windows rejected by deterministic QC (%)")
    ax.set_xlabel("session (chronological)")
    ax.set_title(f"F1.1  Per-session QC rejection — {rows[0]['subject']}, Ninapro DB6 (offline, pilot)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=palette[d]) for d in sorted(set(dominant))]
    ax.legend(handles + [ax.lines[0]], [f"dominant reason: {d}" for d in sorted(set(dominant))] + [ax.lines[0].get_label()],
              fontsize=8, frameon=False)
    ax.tick_params(axis="x", rotation=45)
    _caption(fig, "Answers: is signal rejection stationary or episodic? One subject, ten sessions, per-session bars, no pooling. "
                  "Must not be read as a rejection rate to expect from a worn device, or as a hardware expectation.")
    fig.subplots_adjust(bottom=0.32)
    return _save(fig, out / f"F1_1_qc_rejection_{stamp}.png")


def fig_1_2_fault_detection(results: Path, out: Path, stamp: str) -> Path:
    qc = {r["mode"]: r for r in _read(results / f"nb01_fault_detection_{stamp}.csv")}
    an = {r["mode"]: r for r in _read(results / f"nb01_anomaly_{stamp}.csv")}
    modes = [m for m in qc]
    series = [
        ("deterministic QC, dataset-scaled severity", [_f(qc[m], "detection_scaled") for m in modes], "#3182bd"),
        ("deterministic QC, unscaled defaults (describes the injection)", [_f(qc[m], "detection_defaults") for m in modes], "#9ecae1"),
        ("advisory anomaly detector, dataset-scaled severity", [_f(an[m], "flag_rate") for m in modes], ACCENT),
    ]
    n_qc = int(_f(qc[modes[0]], "n_windows")) if "n_windows" in qc[modes[0]] else 0
    n_an = int(_f(an[modes[0]], "n_windows")) if "n_windows" in an[modes[0]] else 0
    ns = [n_qc, n_qc, n_an]

    fig, ax = plt.subplots(figsize=(11, 4))
    width = 0.26
    xs = range(len(modes))
    for k, (label, values, colour) in enumerate(series):
        pos = [x + (k - 1) * width for x in xs]
        errs = [[max(0.0, v - _wilson(v, ns[k])[0]) for v in values], [max(0.0, _wilson(v, ns[k])[1] - v) for v in values]]
        ax.bar(pos, [v * 100 for v in values], width, label=label, color=colour,
               yerr=[[e * 100 for e in errs[0]], [e * 100 for e in errs[1]]], capsize=2, error_kw={"lw": 0.8})
    clean = _f(an["clean"], "flag_rate") * 100 if "clean" in an else math.nan
    if not math.isnan(clean):
        ax.axhline(clean, color=ACCENT, ls=":", lw=1, label=f"advisory clean flag rate {clean:.1f}%")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(modes)
    ax.set_ylabel("windows flagged (%)")
    ax.set_ylim(0, 105)
    ax.set_title("F1.2  What each monitor layer catches, by injected fault mode (offline, pilot)")
    ax.legend(fontsize=7.5, frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    _caption(fig, f"Answers: what does each layer actually catch? Rates over n={n_qc} (QC) / n={n_an} (advisory) injected windows, "
                  "Wilson 95% intervals. Must not be read as: injected faults reproduce real worn-device failures, or detection rates "
                  "transfer to hardware.")
    fig.subplots_adjust(bottom=0.22)
    return _save(fig, out / f"F1_2_fault_detection_{stamp}.png")


def fig_1_3_adaptive_threshold(results: Path, out: Path, stamp: str) -> Path:
    rows = _read(results / f"nb01_adaptive_threshold_{stamp}.csv")
    designs = list(dict.fromkeys(r["design"] for r in rows))
    fig, axes = plt.subplots(1, len(designs), figsize=(5.2 * len(designs), 4), sharey=True)
    axes = [axes] if len(designs) == 1 else list(axes)
    for ax, design in zip(axes, designs):
        sub = [r for r in rows if r["design"] == design]
        sessions = [r["session"] for r in sub]
        fixed = [_f(r, "fixed_fp") * 100 for r in sub]
        adapt = [_f(r, "adaptive_fp") * 100 for r in sub]
        flagged = [r["qc_flagged_session"].lower() == "true" for r in sub]
        xs = list(range(len(sub)))
        for x, f_, a_, fl in zip(xs, fixed, adapt, flagged):
            ax.plot([x, x], [f_, a_], color="#bbbbbb", lw=1, zorder=1)
        ax.scatter(xs, fixed, marker="o", color=NEUTRAL, label="fixed threshold (calibrated once, session 1)", zorder=2)
        ax.scatter(xs, adapt, marker="s", color="#3182bd", label="adaptive threshold (per session)", zorder=3)
        for x, fl in zip(xs, flagged):
            if fl:
                ax.axvspan(x - 0.4, x + 0.4, color=ACCENT, alpha=0.12, lw=0)
        target = 2.5
        ax.axhline(target, color="#31a354", ls="--", lw=1, label=f"target clean flag rate {target:.1f}%")
        ax.set_xticks(xs)
        ax.set_xticklabels(sessions, rotation=45, fontsize=8)
        ax.set_title(f"{design} halves", fontsize=10)
        ax.set_xlabel("session")
    axes[0].set_ylabel("clean-window flag rate (%)")
    axes[0].legend(fontsize=7.5, frameon=False)
    fig.suptitle("F1.3  Advisory detector: fixed vs. per-session adaptive threshold across sessions (offline, pilot)", fontsize=10)
    _caption(fig, "Answers: does a per-session threshold hold the advisory false-positive rate at target? Shaded = the session the "
                  "deterministic QC flagged for dropout (d04); it is marked, not claimed as separated. Must not be read as: adaptivity "
                  "preserves visibility of a degraded session, or replaces the deterministic floor.")
    fig.subplots_adjust(bottom=0.30, top=0.85)
    return _save(fig, out / f"F1_3_adaptive_threshold_{stamp}.png")


def render_nb1(results: Path = RESULTS, out: Path = FIGURES, stamp: str = "") -> list[Path]:
    return [
        fig_1_1_qc_rejection(results, out, stamp),
        fig_1_2_fault_detection(results, out, stamp),
        fig_1_3_adaptive_threshold(results, out, stamp),
    ]


# --------------------------------------------------------------------------- #
# NB2 — confidence under shift
# --------------------------------------------------------------------------- #

PROTOCOL_ORDER = ["within-session", "cross-session", "cross-subject", "random-shuffle"]
PROTOCOL_COLOURS = {"within-session": "#3182bd", "cross-session": ACCENT, "cross-subject": "#756bb1", "random-shuffle": "#bdbdbd"}


def fig_2_1_reliability(results: Path, out: Path, stamp: str) -> Path:
    models = ["lda", "logreg"]
    fig, axes = plt.subplots(1, len(models), figsize=(5 * len(models), 4.4), sharey=True)
    for ax, model in zip(axes, models):
        rows = _read(results / f"nb02_reliability_binary_{model}_{stamp}.csv")
        ax.plot([0, 1], [0, 1], color="#bbbbbb", lw=1, ls="--", label="perfect calibration")
        for protocol in ("within-session", "cross-session"):
            sub = [r for r in rows if r["protocol"] == protocol and int(_f(r, "n")) > 0]
            conf = [_f(r, "mean_confidence") for r in sub]
            acc = [_f(r, "accuracy") for r in sub]
            ns = [int(_f(r, "n")) for r in sub]
            total = sum(ns)
            sizes = [20 + 300 * n / total for n in ns]
            ax.plot(conf, acc, color=PROTOCOL_COLOURS[protocol], lw=1, zorder=2)
            ax.scatter(conf, acc, s=sizes, color=PROTOCOL_COLOURS[protocol], alpha=0.8, zorder=3,
                       label=f"{protocol} (marker area ∝ windows in bin, n={total})")
        ax.set_xlim(0.45, 1.02)
        ax.set_ylim(0.45, 1.02)
        ax.set_xlabel("mean predicted-class confidence in bin")
        ax.set_title(f"binary rest-vs-movement, {model}", fontsize=10)
        ax.legend(fontsize=7, frameon=False, loc="upper left")
    axes[0].set_ylabel("observed accuracy in bin")
    fig.suptitle("F2.1  Reliability diagrams, pooled over splits per protocol (offline, pilot, 2 subjects)", fontsize=10)
    _caption(fig, "Answers: does the probability stay honest under shift? Bins pooled across splits per protocol; empty bins omitted. "
                  "Must not be read as: probability is a validated control signal, or any specific threshold is safe.")
    fig.subplots_adjust(bottom=0.2, top=0.86)
    return _save(fig, out / f"F2_1_reliability_{stamp}.png")


def fig_2_2_metrics_by_protocol(results: Path, out: Path, stamp: str) -> Path:
    rows = [r for r in _read(results / f"nb02_summary_{stamp}.csv") if r["task"] == "binary"]
    metrics = [("balanced_accuracy", "balanced accuracy (higher is better)"), ("ece", "ECE (lower is better)"),
               ("brier", "Brier, one-column binary form (lower is better)"), ("nll", "NLL / log loss (lower is better)")]
    models = ["lda", "logreg"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(4.2 * len(metrics), 4))
    width = 0.38
    for ax, (metric, label) in zip(axes, metrics):
        for k, model in enumerate(models):
            protocols = [p for p in PROTOCOL_ORDER if any(r["model"] == model and r["protocol"] == p for r in rows)]
            xs = [i + (k - 0.5) * width for i in range(len(protocols))]
            means, lo, hi = [], [], []
            for p in protocols:
                r = next(r for r in rows if r["model"] == model and r["protocol"] == p)
                m, mn, mx = _f(r, f"{metric}_mean"), _f(r, f"{metric}_min"), _f(r, f"{metric}_max")
                means.append(m)
                lo.append(max(0.0, m - mn))
                hi.append(max(0.0, mx - m))
            ax.bar(xs, means, width, yerr=[lo, hi], capsize=2, error_kw={"lw": 0.8},
                   color=[PROTOCOL_COLOURS[p] for p in protocols], alpha=0.55 if model == "lda" else 0.95,
                   edgecolor="black", lw=0.5, label=model)
            ax.set_xticks(range(len(protocols)))
            ax.set_xticklabels(protocols, rotation=30, fontsize=8, ha="right")
        ax.set_title(label, fontsize=9)
        ax.legend(fontsize=7, frameon=False)
    fig.suptitle("F2.2  Discrimination and probability quality by protocol — each metric on its own scale "
                 "(binary task; bars = mean over splits, whiskers = min–max)", fontsize=9.5)
    _caption(fig, "Answers: how do prediction quality and probability quality each behave under each protocol? Separate panels, "
                  "separate scales: magnitudes across panels are NOT commensurate and must not be compared. Whiskers are the spread "
                  "over splits; cross-session splits share one training session per subject (2 subjects) and are not independent "
                  "replications. random-shuffle is a leaky control, not a result. Must not be read as: causal session drift; or a "
                  "benchmark comparable to multi-channel literature.")
    fig.subplots_adjust(bottom=0.36, top=0.86, wspace=0.35)
    return _save(fig, out / f"F2_2_metrics_by_protocol_{stamp}.png")


def fig_2_3_per_split(results: Path, out: Path, stamp: str) -> Path:
    models = ["lda", "logreg"]
    metrics = [("balanced_accuracy", "balanced accuracy"), ("nll", "NLL / log loss")]
    fig, axes = plt.subplots(len(metrics), len(models), figsize=(5 * len(models), 3.4 * len(metrics)), sharex=True)
    n_total = 0
    subjects = set()
    for j, model in enumerate(models):
        rows = [r for r in _read(results / f"nb02_splits_binary_{model}_{stamp}.csv") if r["protocol"] == "cross-session"]
        n_total = len(rows)
        for i, (metric, label) in enumerate(metrics):
            ax = axes[i][j]
            for r in rows:
                subj = r.get("meta_subject", "")
                subjects.add(subj)
                ax.scatter(_f(r, "meta_sessions_elapsed"), _f(r, metric), color=SUBJECT_COLOURS.get(subj, NEUTRAL),
                           s=28, alpha=0.85, label=subj)
            ax.set_ylabel(label)
            if i == 0:
                ax.set_title(f"binary, {model}", fontsize=10)
            if i == len(metrics) - 1:
                ax.set_xlabel("sessions elapsed since the (single) training session")
            handles, labels = ax.get_legend_handles_labels()
            seen = dict(zip(labels, handles))
            ax.legend(seen.values(), seen.keys(), fontsize=7.5, frameon=False, title="held-out subject", title_fontsize=7.5)
    fig.suptitle(f"F2.3  Per-split cross-session variability — {n_total} splits = {len(subjects)} subjects × "
                 f"{n_total // max(1, len(subjects))} held-out sessions, one training session per subject", fontsize=9.5)
    _caption(fig, "Answers: is degradation uniform, or carried by particular sessions? One point per held-out session; 2 splits per "
                  "elapsed value (one per subject). All splits of a subject share the same training session, so this is "
                  "test-session variability, not independent replication. Must not be read as: a trend in elapsed time, or a "
                  "conclusion drawn from any single collapsed session beyond 'one such case exists'.")
    fig.subplots_adjust(bottom=0.2, top=0.88, hspace=0.15)
    return _save(fig, out / f"F2_3_per_split_{stamp}.png")


def render_nb2(results: Path = RESULTS, out: Path = FIGURES, stamp: str = "") -> list[Path]:
    return [
        fig_2_1_reliability(results, out, stamp),
        fig_2_2_metrics_by_protocol(results, out, stamp),
        fig_2_3_per_split(results, out, stamp),
    ]


# --------------------------------------------------------------------------- #
# NB3 — when not to help
# --------------------------------------------------------------------------- #


def fig_3_1_risk_coverage(results: Path, out: Path, stamp: str) -> Path:
    pooled = _read(results / f"nb03_risk_coverage_pooled_{stamp}.csv")
    per_split = _read(results / f"nb03_risk_coverage_per_split_{stamp}.csv")
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for protocol in ("within-session", "cross-session"):
        colour = PROTOCOL_COLOURS[protocol]
        splits = sorted({r["split"] for r in per_split if r["protocol"] == protocol})
        for split in splits:
            sub = [r for r in per_split if r["split"] == split]
            sub.sort(key=lambda r: _f(r, "tau"))
            ax.plot([_f(r, "coverage") for r in sub], [_f(r, "selective_risk") for r in sub], color=colour, lw=0.6, alpha=0.25)
        sub = sorted((r for r in pooled if r["protocol"] == protocol), key=lambda r: _f(r, "tau"))
        ax.plot([_f(r, "coverage") for r in sub], [_f(r, "selective_risk") for r in sub], color=colour, lw=2.2,
                marker="o", ms=3, label=f"{protocol}, pooled ({len(splits)} splits faint)")
    ax.set_xlabel("coverage = fraction of windows the gate lets the model act on")
    ax.set_ylabel("selective risk = error rate among covered windows")
    ax.set_title("F3.1  Risk–coverage of the confidence rejector, binary task (offline, pilot)", fontsize=9.5)
    ax.legend(fontsize=8, frameon=False)
    ax.invert_xaxis()
    _caption(fig, "Answers: what error reduction does abstaining buy per unit of coverage given up? Sweep of a hard gate on "
                  "predicted-class probability; coverage falls left to right as tau rises. Must not be read as: any point is a safe "
                  "operating point for a wearer.")
    fig.subplots_adjust(bottom=0.22)
    return _save(fig, out / f"F3_1_risk_coverage_{stamp}.png")


def fig_3_2_unsafe_vs_availability(results: Path, out: Path, stamp: str) -> Path:
    pooled = _read(results / f"nb03_gate_sweep_pooled_{stamp}.csv")
    per_split = _read(results / f"nb03_gate_sweep_per_split_{stamp}.csv")
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for protocol in ("within-session", "cross-session"):
        colour = PROTOCOL_COLOURS[protocol]
        sub_s = [r for r in per_split if r["protocol"] == protocol]
        ax.scatter([_f(r, "assist_availability") * 100 for r in sub_s], [_f(r, "unsafe_assist_rate") * 100 for r in sub_s],
                   color=colour, s=8, alpha=0.25)
        sub = sorted((r for r in pooled if r["protocol"] == protocol), key=lambda r: _f(r, "tau"))
        ax.plot([_f(r, "assist_availability") * 100 for r in sub], [_f(r, "unsafe_assist_rate") * 100 for r in sub],
                color=colour, lw=2.2, marker="o", ms=3, label=f"{protocol}, pooled (per-split points faint)")
        first, last = sub[0], sub[-1]
        ax.annotate(f"τ={_f(first, 'tau'):.2f}", (_f(first, "assist_availability") * 100, _f(first, "unsafe_assist_rate") * 100),
                    fontsize=7, color=colour, xytext=(6, -2 if protocol == "within-session" else 8), textcoords="offset points")
        ax.annotate(f"τ={_f(last, 'tau'):.2f}", (_f(last, "assist_availability") * 100, _f(last, "unsafe_assist_rate") * 100),
                    fontsize=7, color=colour, xytext=(-4, 8 if protocol == "within-session" else -10), textcoords="offset points",
                    ha="right")
    ax.set_xlabel("assist availability (%) — denominator: true-movement windows")
    ax.set_ylabel("unsafe-assist rate (%) — denominator: all windows")
    ax.set_title("F3.2  Unsafe assist vs. assist availability under an explicit hard gate (offline, pilot)", fontsize=9.5)
    ax.legend(fontsize=8, frameon=False)
    _caption(fig, "Answers: what does refusing cost, and what does it buy? tau rises from the ungated reference (0.50, right end) to "
                  "0.99 (left end) along each curve. Denominators differ between axes (stated on each), so this is a trade-off plot, "
                  "not a risk–coverage curve (see F3.1). Must not be read as: a recommended tau, a safety threshold, or closed-loop "
                  "behaviour.")
    fig.subplots_adjust(bottom=0.22)
    return _save(fig, out / f"F3_2_unsafe_vs_availability_{stamp}.png")


def fig_3_3_monitors(results: Path, out: Path, stamp: str) -> Path:
    rows = _read(results / f"nb03_decision_monitors_{stamp}.csv")
    sessions = [r["session"] for r in rows]
    train = [r.get("is_train", "").lower() == "true" for r in rows]
    highlight = [r.get("is_highlighted", "").lower() == "true" for r in rows]
    panels = [
        ("anom_flag_ch0", "input monitor: advisory anomaly flag rate, ch0 (%)", 100),
        ("anom_flag_ch1", "input monitor: advisory anomaly flag rate, ch1 (%)", 100),
        ("balanced_accuracy", "classifier outcome (needs labels — not a monitor): balanced accuracy", 1),
        ("mean_conf", "decision monitor: mean predicted-class confidence", 1),
        ("disagreement", "decision monitor: LDA vs logreg disagreement (%)", 100),
        ("move_pred_share", "decision monitor: predicted-movement share (%)", 100),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14, 6.4), sharex=True)
    xs = list(range(len(sessions)))
    for ax, (key, label, scale) in zip(axes.ravel(), panels):
        values = [_f(r, key) * scale for r in rows]
        colours = ["#bdbdbd" if t else (ACCENT if h else "#3182bd") for t, h in zip(train, highlight)]
        ax.bar(xs, values, color=colours)
        ax.set_title(label, fontsize=9)
        ax.set_xticks(xs)
        ax.set_xticklabels(sessions, rotation=45, fontsize=8)
    subject = rows[0].get("subject", "")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ("#3182bd", ACCENT, "#bdbdbd")]
    fig.legend(handles, ["held-out session", "held-out session with the lowest balanced accuracy (illustrative case)",
                         "training session (in-sample; excluded from comparison)"],
               loc="upper center", bbox_to_anchor=(0.5, 0.94), fontsize=8, frameon=False, ncol=3)
    fig.suptitle(f"F3.3  Input monitors vs. decision monitors per session — {subject}, one subject, one training session", fontsize=10)
    _caption(fig, "Answers: which monitor family sees which failure? One subject, ten sessions, one training session. This is existence "
                  "evidence — two illustrative cases — not coverage. Must not be read as: complementarity established in general, "
                  "disagreement validated as a detector, or any disagreement level meaning something outside this session.")
    fig.subplots_adjust(bottom=0.17, top=0.84, hspace=0.35, wspace=0.25)
    return _save(fig, out / f"F3_3_monitors_{stamp}.png")


def render_nb3(results: Path = RESULTS, out: Path = FIGURES, stamp: str = "") -> list[Path]:
    return [
        fig_3_1_risk_coverage(results, out, stamp),
        fig_3_2_unsafe_vs_availability(results, out, stamp),
        fig_3_3_monitors(results, out, stamp),
    ]


def render_all(results: Path = RESULTS, out: Path = FIGURES, stamp: str = "") -> list[Path]:
    return render_nb1(results, out, stamp) + render_nb2(results, out, stamp) + render_nb3(results, out, stamp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--fingerprint", required=True, help="config fingerprint the CSVs are stamped with")
    parser.add_argument("--results", type=Path, default=RESULTS)
    parser.add_argument("--out", type=Path, default=FIGURES)
    parser.add_argument("--only", choices=["nb1", "nb2", "nb3"], default=None)
    args = parser.parse_args()
    fn = {"nb1": render_nb1, "nb2": render_nb2, "nb3": render_nb3, None: render_all}[args.only]
    for path in fn(args.results, args.out, args.fingerprint):
        print(path.relative_to(REPO).as_posix())
