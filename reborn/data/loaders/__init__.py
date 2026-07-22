"""Dataset backends. One per public dataset, all returning `EmgRecording`."""

from .base import DatasetLoader
from .ninapro_db6 import NinaproDB6Loader
from .synthetic import SyntheticDriftLoader

__all__ = ["DatasetLoader", "NinaproDB6Loader", "SyntheticDriftLoader"]
