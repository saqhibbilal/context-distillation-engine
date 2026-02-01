"""Serve bundled sample chat datasets for demos."""

from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "samples"


def get_sample_names() -> list[str]:
    """Return list of available sample names (without .txt)."""
    if not SAMPLES_DIR.exists():
        return []
    return [p.stem for p in SAMPLES_DIR.glob("*.txt")]


def load_sample(name: str) -> str | None:
    """Load sample content by name. Returns None if not found."""
    path = SAMPLES_DIR / f"{name}.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
