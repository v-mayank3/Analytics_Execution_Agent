#!/usr/bin/env python3
"""Detect changes between the latest discovery and the previous scan.

This version also calculates a SHA-256 hash for every discovered file and uses
that hash to identify modified files.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def get_project_root() -> Path:
    """Return the project root even when this script lives in the scripts folder."""
    current_path = Path(__file__).resolve()
    if current_path.parent.name == "scripts":
        return current_path.parent.parent
    return current_path.parent


ROOT_DIR = get_project_root()
DISCOVERY_PATH = ROOT_DIR / "outputs" / "discovered_datasets.json"
STATE_PATH = ROOT_DIR / "state" / "last_scan.json"
CHANGE_REPORT_PATH = ROOT_DIR / "outputs" / "change_report.json"
SOURCE_DIR = ROOT_DIR / "source"


def read_json(path: Path, default: Any) -> Any:
    """Read a JSON file and return a default value if the file does not exist."""
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, content: dict) -> None:
    """Write a Python object to a JSON file with nice formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(content, handle, indent=2)
        handle.write("\n")


def build_file_key(item: dict) -> str:
    """Create a simple identifier for a discovered file entry."""
    dataset_name = str(item.get("dataset_name", "")).strip()
    file_name = str(item.get("file_name", "")).strip()
    return f"{dataset_name}/{file_name}"


def resolve_source_file(item: dict) -> Path:
    """Find the actual source file that matches a discovery entry."""
    dataset_name = str(item.get("dataset_name", "")).strip()
    file_name = str(item.get("file_name", "")).strip()
    dataset_dir = SOURCE_DIR / dataset_name

    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset folder not found: {dataset_dir}")

    matches = list(dataset_dir.rglob(file_name))
    if matches:
        return matches[0]

    raise FileNotFoundError(f"File not found: {dataset_name}/{file_name}")


def calculate_sha256(file_path: Path) -> str:
    """Return a SHA-256 hash for the contents of a file."""
    hasher = hashlib.sha256()

    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def enrich_discovered_files(discovered_files: list[dict]) -> list[dict]:
    """Add a hash value to each discovered file entry."""
    enriched_files = []

    for item in discovered_files:
        try:
            source_file = resolve_source_file(item)
            file_hash = calculate_sha256(source_file)
        except FileNotFoundError:
            # If the source file cannot be located, keep the hash blank.
            file_hash = ""

        enriched_item = dict(item)
        enriched_item["sha256_hash"] = file_hash
        enriched_files.append(enriched_item)

    return enriched_files


def detect_changes(current_discovery: dict, previous_discovery: dict | None) -> dict:
    """Compare the current discovery with the previous scan and return a report."""
    current_files = enrich_discovered_files(current_discovery.get("discovered_files", []))

    if previous_discovery is None:
        # This is the first run, so everything looks new.
        new_datasets = sorted({item.get("dataset_name", "") for item in current_files if item.get("dataset_name")})
        new_files = current_files
        deleted_files = []
        modified_files = []
        status = "first_run"
    else:
        previous_files = previous_discovery.get("discovered_files", [])
        previous_by_key = {build_file_key(item): item for item in previous_files}
        current_by_key = {build_file_key(item): item for item in current_files}

        current_datasets = sorted({item.get("dataset_name", "") for item in current_files if item.get("dataset_name")})
        previous_datasets = sorted({item.get("dataset_name", "") for item in previous_files if item.get("dataset_name")})

        new_datasets = [dataset for dataset in current_datasets if dataset not in previous_datasets]
        new_files = [item for item in current_files if build_file_key(item) not in previous_by_key]
        deleted_files = [item for item in previous_files if build_file_key(item) not in current_by_key]

        modified_files = []
        for item in current_files:
            key = build_file_key(item)
            previous_item = previous_by_key.get(key)

            if previous_item is None:
                continue

            previous_hash = previous_item.get("sha256_hash", "")
            current_hash = item.get("sha256_hash", "")

            if previous_hash != current_hash:
                modified_files.append(
                    {
                        "dataset_name": item.get("dataset_name", ""),
                        "file_name": item.get("file_name", ""),
                        "previous_sha256_hash": previous_hash,
                        "current_sha256_hash": current_hash,
                    }
                )

        if new_datasets or new_files or deleted_files or modified_files:
            status = "changes_detected"
        else:
            status = "no_changes"

    summary = {
        "new_dataset_count": len(new_datasets),
        "new_file_count": len(new_files),
        "deleted_file_count": len(deleted_files),
        "modified_file_count": len(modified_files),
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "new_datasets": new_datasets,
        "new_files": new_files,
        "deleted_files": deleted_files,
        "modified_files": modified_files,
        "summary": summary,
    }


def main() -> None:
    """Run the change detection process and save the results."""
    if not DISCOVERY_PATH.exists():
        raise FileNotFoundError(f"Discovery file was not found: {DISCOVERY_PATH}")

    current_discovery = read_json(DISCOVERY_PATH, {})
    previous_discovery = read_json(STATE_PATH, None)

    change_report = detect_changes(current_discovery, previous_discovery)

    # Save the current discovery with hashes so the next run can compare them.
    state_payload = dict(current_discovery)
    state_payload["discovered_files"] = enrich_discovered_files(current_discovery.get("discovered_files", []))

    save_json(CHANGE_REPORT_PATH, change_report)
    save_json(STATE_PATH, state_payload)

    print(f"Change report saved to {CHANGE_REPORT_PATH}")
    print(f"Last scan state saved to {STATE_PATH}")


if __name__ == "__main__":
    main()
