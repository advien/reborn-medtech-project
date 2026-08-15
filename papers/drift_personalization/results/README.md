# Notebook 01 results — committed measurements

The manuscript-bound tables from `notebooks/01_emg_qc_and_baselines.ipynb`.
`experiments/results/` is git-ignored and regenerable; the numbers that reach the
paper are copied here, versioned, with their provenance. Every file below is the
verbatim CSV the notebook wrote — do not hand-edit; regenerate.

## Provenance

| | |
|---|---|
| **Dataset** | Ninapro DB6, subject **s01**, all 10 sessions |
| **Held-out check** | s02 rejects 0.10% under s01-derived thresholds (`experiments/configs/ninapro_db6_qc.json` → `observed`) |
| **Montage** | raw DB6 columns (0, 10) — two channels, mirroring Reborn's own hardware |
| **Config fingerprint** | `fed1e81a523e5d6e` (resample 2 kHz→1 kHz, band-pass 20–450 Hz, notch 50 Hz, 200 ms window / 50 ms stride, pure windows) |
| **QC thresholds** | data-derived, `experiments/configs/ninapro_db6_qc.json` |
| **Corruption severity** | 3.0 (amplitudes scaled to the dataset; see notebook §4) |
| **Windows assessed** | 136 234 (QC rejection); 2000 fit / 2000 calibrate / 500 test (anomaly) |
| **Run date** | 2026-08-13 |
| **Code** | commit that adds this file; phase B3 / B3a / B3b |

## Files

| File | Notebook § | What it holds |
|---|---|---|
| `nb01_qc_rejection_fed1e81a523e5d6e.csv` | §2 | Per-session QC rejection: windows, rejected, rate, reason. Overall **0.67%**, all `dropout`; `d04_t01` **3.57%**. |
| `nb01_fault_detection_fed1e81a523e5d6e.csv` | §4 | Deterministic detection per fault mode, dataset-scaled vs. default injection. Scaled: dropout/saturation/clipping/baseline_offset **100%**, noise_burst **0%**. |
| `nb01_anomaly_fed1e81a523e5d6e.csv` | §5 | Advisory-detector flag rate + mean score per mode (10 fault-sensitive features). saturation/clipping/baseline_offset **100%**, noise_burst **17%**, clean **5.0%**. |
| `nb01_noise_burst_sweep_fed1e81a523e5d6e.csv` | §5 | noise_burst detection vs. burst energy (severity × length). ~8% at severity 1 → **100%** by severity 8. |
| `nb01_fp_calibration_fed1e81a523e5d6e.csv` | §5 | B3b false-positive: **time-ordered 5.0%** vs. **shuffled control 2.8%** — the gap is within-session drift. |
| `nb03_adaptive_threshold_fed1e81a523e5d6e.csv` | nb03 (B3c) | Per-session **fixed vs. adaptive** threshold, all 10 s01 sessions. Benign FP mean 5.3%→**2.6%**; degraded `d04` stays 4.2% (not masked). |

## Headline numbers (for quick citation; source of truth is the CSVs)

- **QC rejection (s01):** 0.67% overall; episodic — `d04_t01` 3.57% (13.5× median). Held-out s02: 0.10%.
- **Deterministic fault detection (scaled):** 100% on dropout, saturation, clipping, baseline_offset; 0% noise_burst (by design — delegated to the advisory layer).
- **Advisory detector (B3a features + B3b calibration):** saturation/clipping/baseline_offset 100%; noise_burst 17% at severity 3, rising to 100% by severity 8; clean false-positive 5.0% (time-ordered) / 2.8% (shuffled).
- **B3b finding:** the 5.0%–2.8% gap is within-session drift, motivating a per-session adaptive threshold (B3c) and bridging to notebook 03.

See `docs/research/lab-notebook.md` for why each measurement was taken, and
`docs/research/checklist.md` for status.
