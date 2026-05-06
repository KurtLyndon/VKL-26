from __future__ import annotations

import mimetypes
import re
import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
AGENT_TASK_SCRIPTS_DIR = DATA_DIR / "agent_task_scripts"
POC_REPOSITORY_DIR = DATA_DIR / "poc_repository"
FINDING_POC_FILES_DIR = DATA_DIR / "finding_poc_files"


def ensure_poc_repository() -> Path:
    POC_REPOSITORY_DIR.mkdir(parents=True, exist_ok=True)
    return POC_REPOSITORY_DIR


def ensure_agent_task_script_repository(agent_type: str) -> Path:
    target_dir = AGENT_TASK_SCRIPTS_DIR / agent_type
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def ensure_finding_poc_repository() -> Path:
    FINDING_POC_FILES_DIR.mkdir(parents=True, exist_ok=True)
    return FINDING_POC_FILES_DIR


def store_poc_copy(source_file: Path, vulnerability_code: str) -> Path:
    repository = ensure_poc_repository()
    target_dir = repository / vulnerability_code
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source_file.name
    shutil.copy2(source_file, target_path)
    return target_path


def _slugify_filename(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return normalized or "file"


def _remove_existing_files(target_dir: Path) -> None:
    if not target_dir.exists():
        return
    for item in target_dir.iterdir():
        if item.is_file():
            item.unlink()


def store_finding_poc_file(finding_id: int, original_name: str, content: bytes) -> dict[str, str | int | None]:
    repository = ensure_finding_poc_repository()
    target_dir = repository / f"finding-{finding_id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    _remove_existing_files(target_dir)

    source_path = Path(original_name)
    extension = source_path.suffix.lower()[:16]
    stem = _slugify_filename(source_path.stem)
    stored_name = f"finding-{finding_id}-{stem}{extension}"
    stored_path = target_dir / stored_name
    stored_path.write_bytes(content)

    mime_type = mimetypes.guess_type(stored_name)[0] or "application/octet-stream"
    return {
        "poc_file_name": original_name,
        "poc_file_path": str(stored_path.relative_to(DATA_DIR)).replace("\\", "/"),
        "poc_file_mime_type": mime_type,
        "poc_file_size": len(content),
    }


def resolve_finding_poc_path(relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    candidate = (DATA_DIR / relative_path).resolve()
    data_root = DATA_DIR.resolve()
    if data_root not in candidate.parents and candidate != data_root:
        raise ValueError("Duong dan POC khong hop le.")
    if not candidate.exists() or not candidate.is_file():
        return None
    return candidate


def delete_finding_poc_file(relative_path: str | None) -> None:
    file_path = resolve_finding_poc_path(relative_path)
    if file_path is None:
        return
    file_path.unlink(missing_ok=True)
    parent = file_path.parent
    if parent.exists() and parent.is_dir():
        try:
            parent.rmdir()
        except OSError:
            pass
