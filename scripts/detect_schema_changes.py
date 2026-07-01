#!/usr/bin/env python3
"""Detect schema changes for changed files and save a schema history snapshot."""

from __future__ import annotations

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
CHANGE_REPORT_PATH = ROOT_DIR / "outputs" / "change_report.json"
SCHEMA_PATH = ROOT_DIR / "outputs" / "inferred_schema.json"
APPROVED_SCHEMA_PATH = ROOT_DIR / "state" / "approved_schema.json"
STATE_SCHEMA_PATH = ROOT_DIR / "state" / "last_schema.json"
SCHEMA_CHANGE_REPORT_PATH = ROOT_DIR / "outputs" / "schema_change_report.json"


def read_json(path: Path, default: Any) -> Any:
    """Read a JSON file and return a default value if the file does not exist."""
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, content: dict) -> None:
    """Write a Python object to a JSON file with clear formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(content, handle, indent=2)
        handle.write("\n")


def build_file_key(dataset_name: str, file_name: str) -> str:
    """Create a simple identifier for a file entry."""
    return f"{dataset_name}/{file_name}"


def get_schema_entry(schema_data: dict, dataset_name: str, file_name: str) -> dict | None:
    """Find a schema entry for a specific dataset and file."""
    for entry in schema_data.get("files", []):
        if entry.get("dataset_name") == dataset_name and entry.get("file_name") == file_name:
            return entry

    return None


def get_dataset_approved_schema(schema_data: dict, dataset_name: str) -> dict | None:
    """Find the approved schema definition for a dataset."""
    datasets = schema_data.get("schemas") or schema_data.get("datasets") or []

    for entry in datasets:
        if entry.get("dataset_name") == dataset_name:
            return entry

    return None


def build_column_map(columns: list[dict]) -> dict[str, str]:
    """Convert a list of column definitions into a simple name-to-type map."""
    column_map: dict[str, str] = {}

    for column in columns:
        name = str(column.get("name", "")).strip()
        if name:
            column_map[name] = str(column.get("data_type", "")).strip()

    return column_map


def compare_schema(approved_columns: dict[str, str], current_columns: dict[str, str]) -> dict:
    """Compare the approved dataset columns with the current file columns."""
    extra_columns_in_file = [
        {"name": column_name, "data_type": current_columns[column_name]}
        for column_name in sorted(set(current_columns) - set(approved_columns))
    ]
    missing_columns_in_file = [
        {"name": column_name, "data_type": approved_columns[column_name]}
        for column_name in sorted(set(approved_columns) - set(current_columns))
    ]
    data_type_changes = [
        {
            "name": column_name,
            "approved_data_type": approved_columns[column_name],
            "current_data_type": current_columns[column_name],
        }
        for column_name in sorted(set(approved_columns) & set(current_columns))
        if approved_columns[column_name] != current_columns[column_name]
    ]

    return {
        "extra_columns_in_file": extra_columns_in_file,
        "missing_columns_in_file": missing_columns_in_file,
        "data_type_changes": data_type_changes,
    }


def detect_schema_changes(change_report: dict, current_schema: dict, approved_schema: dict | None) -> dict:
    """Compare the current schema of changed files with the approved dataset schema."""
    relevant_files = []

    for item in change_report.get("modified_files", []):
        relevant_files.append((item.get("dataset_name", ""), item.get("file_name", "")))

    for item in change_report.get("new_files", []):
        relevant_files.append((item.get("dataset_name", ""), item.get("file_name", "")))

    # Remove duplicates while keeping the order.
    seen = set()
    unique_files = []
    for dataset_name, file_name in relevant_files:
        key = build_file_key(str(dataset_name), str(file_name))
        if key not in seen:
            seen.add(key)
            unique_files.append((str(dataset_name), str(file_name)))

    changes = []
    for dataset_name, file_name in unique_files:
        current_entry = get_schema_entry(current_schema, dataset_name, file_name)
        current_columns = build_column_map(current_entry.get("columns", []) if current_entry else [])

        if approved_schema is None:
            # If the approved schema file is missing, treat this as a new dataset.
            changes.append(
                {
                    "dataset_name": dataset_name,
                    "file_name": file_name,
                    "status": "NEW_DATASET_REQUIRES_APPROVAL",
                    "extra_columns_in_file": [],
                    "missing_columns_in_file": [],
                    "data_type_changes": [],
                }
            )
            continue

        approved_dataset_schema = get_dataset_approved_schema(approved_schema, dataset_name)
        if approved_dataset_schema is None:
            # Only the dataset itself being missing triggers the new-dataset approval path.
            changes.append(
                {
                    "dataset_name": dataset_name,
                    "file_name": file_name,
                    "status": "NEW_DATASET_REQUIRES_APPROVAL",
                    "extra_columns_in_file": [],
                    "missing_columns_in_file": [],
                    "data_type_changes": [],
                }
            )
            continue

        approved_columns = build_column_map(approved_dataset_schema.get("columns", []))
        file_changes = compare_schema(approved_columns, current_columns)

        if not any(file_changes.values()):
            continue

        changes.append(
            {
                "dataset_name": dataset_name,
                "file_name": file_name,
                "status": "SCHEMA_CHANGE_DETECTED",
                **file_changes,
            }
        )

    status = "first_run" if not approved_schema else ("changes_detected" if changes else "no_changes")

    summary = {
        "files_checked": len(unique_files),
        "files_with_changes": len(changes),
        "extra_column_count": sum(len(item.get("extra_columns_in_file", [])) for item in changes),
        "missing_column_count": sum(len(item.get("missing_columns_in_file", [])) for item in changes),
        "data_type_change_count": sum(len(item.get("data_type_changes", [])) for item in changes),
    }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "processed_files": [
            {"dataset_name": dataset_name, "file_name": file_name}
            for dataset_name, file_name in unique_files
        ],
        "changes": changes,
        "summary": summary,
    }


def main() -> None:
    """Read the current schema report, compare it to the previous saved snapshot, and save the result."""
    if not CHANGE_REPORT_PATH.exists():
        raise FileNotFoundError(f"Change report was not found: {CHANGE_REPORT_PATH}")

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Inferred schema file was not found: {SCHEMA_PATH}")

    change_report = read_json(CHANGE_REPORT_PATH, {})
    current_schema = read_json(SCHEMA_PATH, {"files": []})
    approved_schema = read_json(APPROVED_SCHEMA_PATH, None)

    schema_change_report = detect_schema_changes(change_report, current_schema, approved_schema)

    save_json(SCHEMA_CHANGE_REPORT_PATH, schema_change_report)

    print(f"Schema change report saved to {SCHEMA_CHANGE_REPORT_PATH}")


if __name__ == "__main__":
    main()
