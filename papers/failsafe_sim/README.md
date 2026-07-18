# Fail-safe architecture under simulated fault injection

**Phase C, topic 10** (docs/roadmap.md). Deliberate fault injection (EMG
dropout, actuator saturation, desync, latency spikes) against the Reborn
simulation stand, validating that `reborn.safety` drives the system to
Degraded/Fallback/Emergency as designed. Built on `sim/fault_injection.py`.

Not started (phase C hasn't begun). Once written, this paper should cite the
specific code and data git tag its figures were generated from.
