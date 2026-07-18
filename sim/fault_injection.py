"""Fault injection — entry point skeleton.

TODO(phase C, docs/roadmap.md topic 10): deliberately break the loop
(dropout, saturation, desync, latency spikes — see docs/experiments.md group D2)
on a schedule, and assert that reborn.safety drives the system to
Degraded/Fallback/Emergency as designed. run_baseline_loop.py already injects
one dropout window; this script should generalize that into configurable,
repeatable fault scenarios with recorded outcomes.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError("Phase C work — see docs/roadmap.md, topic 10.")


if __name__ == "__main__":
    main()
