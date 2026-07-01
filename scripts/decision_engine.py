#!/usr/bin/env python3
"""Create a simple action plan from the change and schema reports."""

from __future__ import annotations

import json
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
SCHEMA_CHANGE_REPORT_PATH = ROOT_DIR / "outputs" / "schema_change_report.json"
APPROVED_SCHEMA_PATH = ROOT_DIR / "state" / "approved_schema.json"
ACTION_PLAN_PATH = ROOT_DIR / "outputs" / "action_plan.json"


def read_json(path: Path, default: Any) -> Any:
    """Read a JSON file and return a default value if the file does not exist."""
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, content: dict) -> None:
    """Write a JSON object to disk with clear formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(content, handle, indent=2)
        handle.write("\n")


def get_approved_datasets(approved_schema: dict | None) -> set[str]:
    """Return the list of dataset names that have been approved."""
    if not approved_schema:
        return set()

    datasets = approved_schema.get("schemas") or approved_schema.get("datasets") or []
    return {str(item.get("dataset_name", "")).strip() for item in datasets if item.get("dataset_name")}


def build_action_plan(change_report: dict, schema_change_report: dict, approved_schema: dict | None) -> dict:
    """Create an action plan based on detected changes and schema changes."""
    new_datasets = change_report.get("new_datasets", [])
    new_files = change_report.get("new_files", [])
    modified_files = change_report.get("modified_files", [])
    deleted_files = change_report.get("deleted_files", [])
    schema_changes = [
        item for item in schema_change_report.get("changes", [])
        if item.get("status") != "NEW_DATASET_REQUIRES_APPROVAL"
    ]
    approved_datasets = get_approved_datasets(approved_schema)

    # Priority order: new dataset, schema change, deletion, new file, modified file, no action.
    changed_dataset_names = {
        str(item.get("dataset_name", "")).strip()
        for item in (new_files + modified_files + deleted_files)
        if item.get("dataset_name")
    }

    # If a dataset is already approved, treat it as an onboarded dataset and use the normal follow-up actions.
    is_existing_approved_dataset = bool(changed_dataset_names & approved_datasets)

    if new_datasets and not is_existing_approved_dataset:
        action = "ONBOARD_NEW_DATASET"
        human_approval = True
        reason = "A new dataset was discovered, so it needs onboarding review."
    elif schema_changes:
        action = "REVIEW_SCHEMA_CHANGE"
        human_approval = True
        reason = "A schema change was detected, so the change should be reviewed manually."
    elif deleted_files:
        deleted_dataset_names = {
            str(item.get("dataset_name", "")).strip()
            for item in deleted_files
            if item.get("dataset_name")
        }

        # Only review deletions for datasets that were previously approved.
        if deleted_dataset_names and deleted_dataset_names.issubset(approved_datasets):
            action = "REVIEW_DATASET_REMOVAL"
            human_approval = True
            reason = "Files or datasets were removed from the source and should be reviewed before metadata or downstream assets are updated."
        else:
            action = "NO_ACTION"
            human_approval = False
            reason = "Unapproved dataset was removed before onboarding."
    elif new_files:
        action = "LOAD_NEW_FILE"
        human_approval = False
        reason = "New files were found and can be loaded without human approval."
    elif modified_files:
        action = "REPROCESS_FILE"
        human_approval = False
        reason = "Files were modified, but no schema changes were detected."
    else:
        action = "NO_ACTION"
        human_approval = False
        reason = "No new datasets, files, or schema changes were detected."

    summary = {
        "new_dataset_count": len(new_datasets),
        "new_file_count": len(new_files),
        "modified_file_count": len(modified_files),
        "deleted_file_count": len(deleted_files),
        "schema_change_count": len(schema_changes),
    }

    return {
        "action": action,
        "human_approval": human_approval,
        "reason": reason,
        "summary": summary,
    }


def main() -> None:
    """Read the reports and write the action plan output."""
    change_report = read_json(CHANGE_REPORT_PATH, {})
    schema_change_report = read_json(SCHEMA_CHANGE_REPORT_PATH, {})
    approved_schema = read_json(APPROVED_SCHEMA_PATH, None)

    action_plan = build_action_plan(change_report, schema_change_report, approved_schema)
    save_json(ACTION_PLAN_PATH, action_plan)

    print(f"Action plan saved to {ACTION_PLAN_PATH}")


if __name__ == "__main__":
    main()
