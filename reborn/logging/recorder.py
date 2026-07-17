"""Appends state transitions and safety events to a JSONL log file.

One event per line, flushed immediately — logs must survive a crash of the
control loop, since a near-miss is exactly the moment the log matters most.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LogEvent:
    timestamp: float
    kind: str  # e.g. "state_transition", "safety_event"
    data: dict[str, Any] = field(default_factory=dict)


class Recorder:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a", encoding="utf-8")

    def record(self, kind: str, **data: Any) -> None:
        event = LogEvent(timestamp=time.time(), kind=kind, data=data)
        self._file.write(json.dumps(asdict(event)) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> Recorder:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
