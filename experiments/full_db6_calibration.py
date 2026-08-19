"""PRIORITY 0 — validate the central finding on all 10 DB6 subjects.

Central claim under test (from n=2): under cross-session sEMG drift, confidence
CALIBRATION deteriorates substantially more than CLASSIFICATION PERFORMANCE.

Preserves the exact existing pipeline: the frozen config in
experiments/configs/ninapro_db6_qc.json, the two-channel montage, QC-gated
windowing (reborn.data), the repetition-aware within-session and time-ordered
cross-session splits (reborn.data.splits), and the ConfidenceGate-based
unsafe-assist / availability metrics (reborn.data.evaluation). Processes one
subject at a time (memory-safe on 15 GB RAM), which is also the natural grain for
the per-subject deltas.

Run:  py -3.11 experiments/full_db6_calibration.py
Writes per-subject and aggregate CSVs to experiments/results/.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.linear_model import LogisticRegression

from reborn.data.evaluation import evaluate_splits, summarize
from reborn.data.features import feature_matrix, standardize
from reborn.data.loaders import NinaproDB6Loader
from reborn.data.pipeline import PreprocessConfig, build_window_set
from reborn.data.splits import cross_session_splits, within_session_splits

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "experiments" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)
CONFIG = json.loads((REPO / "experiments" / "configs" / "ninapro_db6_qc.json").read_text())
QC_KWARGS = CONFIG["qc_kwargs"]
MONTAGE = tuple(CONFIG["channels"]["montage"])
PRE = CONFIG["preprocess"]

config = PreprocessConfig(
    target_sample_rate=PRE["target_sample_rate_hz"],
    bandpass_hz=tuple(PRE["bandpass_hz"]),
    notch_hz=PRE["notch_hz"],
    window_ms=PRE["window_ms"],
    stride_ms=PRE["stride_ms"],
    pure_windows=PRE["pure_windows"],
    qc_kwargs=QC_KWARGS,
)


def make_fit_predict(factory):
    def fit_predict(X_train, y_train, X_test):
        X_train, X_test = standardize(X_train, X_test)
        model = factory().fit(X_train, y_train)
        proba = model.predict_proba(X_test)
        return model.classes_[np.argmax(proba, axis=1)], np.max(proba, axis=1)

    return fit_predict


MODELS = {"lda": make_fit_predict(LinearDiscriminantAnalysis),
          "logreg": make_fit_predict(lambda: LogisticRegression(max_iter=2000))}
COMBOS = [(t, m) for t in ("binary", "multi") for m in MODELS]


def main() -> None:
    loader = NinaproDB6Loader(REPO / "data" / "ninapro_db6", channels=MONTAGE)
    subjects = loader.subjects()
    print(f"subjects: {subjects}\n")

    per_subject = []   # one row per (subject, task, model)
    qc_rows = []       # one row per subject
    t0 = time.time()

    for subj in subjects:
        ts = time.time()
        ws = build_window_set(loader.load(subjects=[subj]), config)
        X, _ = feature_matrix(ws)
        labels = {"binary": ws.binary_labels(), "multi": ws.labels}
        within = within_session_splits(ws)
        cross = cross_session_splits(ws, n_train_sessions=1)
        qc_rows.append({"subject": subj, "n_windows": ws.n_windows,
                        "qc_rejection_rate": ws.qc.rejection_rate,
                        "n_sessions": len(set(map(str, ws.session_ids)))})

        for task, model in COMBOS:
            y = labels[task]
            fp = MODELS[model]
            w = summarize(evaluate_splits(X, y, within, fp))
            c = summarize(evaluate_splits(X, y, cross, fp))
            per_subject.append({
                "subject": subj, "task": task, "model": model,
                "within_bal": w["balanced_accuracy_mean"], "cross_bal": c["balanced_accuracy_mean"],
                "within_ece": w["ece_mean"], "cross_ece": c["ece_mean"],
                "within_unsafe": w["unsafe_assist_rate_mean"], "cross_unsafe": c["unsafe_assist_rate_mean"],
                "within_avail": w["assist_availability_mean"], "cross_avail": c["assist_availability_mean"],
                "d_bal": w["balanced_accuracy_mean"] - c["balanced_accuracy_mean"],
                "d_ece": c["ece_mean"] - w["ece_mean"],
                "ece_ratio": (c["ece_mean"] / w["ece_mean"]) if w["ece_mean"] > 0 else float("nan"),
            })
        print(f"{subj}: {ws.n_windows} win, QC {ws.qc.rejection_rate:.2%}, "
              f"{len(within)} within / {len(cross)} cross splits  ({time.time()-ts:.0f}s)")
        del ws, X

    # write per-subject + QC
    _write(RESULTS / "fulldb6_per_subject.csv", per_subject)
    _write(RESULTS / "fulldb6_qc_per_subject.csv", qc_rows)

    # aggregate across subjects, per combo, with spread
    print(f"\n{'combo':<16}{'within_bal':>11}{'cross_bal':>11}{'d_bal':>9}"
          f"{'within_ece':>12}{'cross_ece':>11}{'ece_ratio':>11}")
    print("-" * 81)
    agg_rows = []
    for task, model in COMBOS:
        rows = [r for r in per_subject if r["task"] == task and r["model"] == model]
        agg = {"task": task, "model": model, "n_subjects": len(rows)}
        for k in ("within_bal", "cross_bal", "d_bal", "within_ece", "cross_ece", "d_ece", "ece_ratio",
                  "within_unsafe", "cross_unsafe", "within_avail", "cross_avail"):
            vals = np.array([r[k] for r in rows], dtype=float)
            vals = vals[np.isfinite(vals)]
            agg[f"{k}_mean"] = float(np.mean(vals))
            agg[f"{k}_sd"] = float(np.std(vals))
        agg_rows.append(agg)
        print(f"{task+'/'+model:<16}{agg['within_bal_mean']:>11.3f}{agg['cross_bal_mean']:>11.3f}"
              f"{agg['d_bal_mean']:>9.3f}{agg['within_ece_mean']:>12.3f}{agg['cross_ece_mean']:>11.3f}"
              f"{agg['ece_ratio_mean']:>11.2f}")
    _write(RESULTS / "fulldb6_aggregate.csv", agg_rows)

    # the central test, stated in relative terms per subject
    print("\ncentral test — calibration deterioration vs performance deterioration:")
    for task, model in COMBOS:
        rows = [r for r in per_subject if r["task"] == task and r["model"] == model]
        rel_acc = np.array([(r["d_bal"] / r["within_bal"]) for r in rows if r["within_bal"] > 0])
        ratios = np.array([r["ece_ratio"] for r in rows if np.isfinite(r["ece_ratio"])])
        n_ece_worse = int(np.sum(ratios > 1.0))
        n_big = int(np.sum(ratios >= 1.5))
        print(f"  {task+'/'+model:<14} rel. acc drop {np.mean(rel_acc):+.1%} (sd {np.std(rel_acc):.1%})  |  "
              f"ECE ratio mean x{np.mean(ratios):.2f} (median x{np.median(ratios):.2f}); "
              f"worse in {n_ece_worse}/{len(ratios)}, >=1.5x in {n_big}/{len(ratios)}")

    print(f"\nQC rejection across subjects: "
          f"mean {np.mean([r['qc_rejection_rate'] for r in qc_rows]):.2%}  "
          f"range {min(r['qc_rejection_rate'] for r in qc_rows):.2%}"
          f"-{max(r['qc_rejection_rate'] for r in qc_rows):.2%}")
    print(f"\ntotal {time.time()-t0:.0f}s. wrote fulldb6_per_subject / _aggregate / _qc_per_subject.csv")


def _write(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
