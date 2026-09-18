"""Resolve ThermoGuard dataset paths without a single-machine hardcode.

Search order:
1. THERMOGUARD_DATA_ROOT (processed dir, or a repo-style root that contains it)
2. <this repository>/data/satellite/processed
3. <parent of this repository>/data/satellite/processed
4. Legacy local layout C:\\AWS Hackathon\\data\\satellite\\processed, if present
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parent
PROCESSED_REL = Path("data") / "satellite" / "processed"
LEGACY_PROCESSED = Path(r"C:\AWS Hackathon") / "data" / "satellite" / "processed"


def _unique(paths: Iterable[Path]) -> List[Path]:
    seen = set()
    out: List[Path] = []
    for path in paths:
        resolved = path.expanduser()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        out.append(resolved)
    return out


def processed_dir_candidates() -> List[Path]:
    env = os.environ.get("THERMOGUARD_DATA_ROOT", "").strip()
    candidates: List[Path] = []
    if env:
        env_path = Path(env)
        candidates.append(env_path)
        candidates.append(env_path / PROCESSED_REL)
    candidates.append(REPO_ROOT / PROCESSED_REL)
    candidates.append(REPO_ROOT.parent / PROCESSED_REL)
    candidates.append(LEGACY_PROCESSED)
    return _unique(candidates)


def find_processed_file(filename: str) -> Optional[Path]:
    for directory in processed_dir_candidates():
        path = directory / filename
        if path.is_file():
            return path
    return None


def require_processed_file(filename: str) -> Path:
    found = find_processed_file(filename)
    if found is None:
        tried = [str(d / filename) for d in processed_dir_candidates()]
        raise FileNotFoundError(
            f"Could not find {filename}. Set THERMOGUARD_DATA_ROOT or place the "
            f"file under data/satellite/processed. Tried: {tried}"
        )
    return found


def find_processed_dir_with(*filenames: str) -> Optional[Path]:
    for directory in processed_dir_candidates():
        if all((directory / name).is_file() for name in filenames):
            return directory
    return None
