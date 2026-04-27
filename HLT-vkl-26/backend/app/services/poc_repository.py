from __future__ import annotations

import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
POC_REPOSITORY_DIR = ROOT_DIR / "data" / "poc_repository"


def ensure_poc_repository() -> Path:
    POC_REPOSITORY_DIR.mkdir(parents=True, exist_ok=True)
    return POC_REPOSITORY_DIR


def store_poc_copy(source_file: Path, vulnerability_code: str) -> Path:
    repository = ensure_poc_repository()
    target_dir = repository / vulnerability_code
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source_file.name
    shutil.copy2(source_file, target_path)
    return target_path
