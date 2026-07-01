#!/usr/bin/env python3
"""Run the analytics onboarding workflow step by step."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent
CHANGE_REPORT_PATH = ROOT_DIR / "outputs" / "change_report.json"
ACTION_PLAN_PATH = ROOT_DIR / "outputs" / "action_plan.json"


def run_step(script_name: str) -> None:
    """Run a Python script and stop immediately if it fails."""
    print(f"[INFO] Running {script_name}...")

    result = subprocess.run(
        [sys.executable, script_name],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")


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


def main() -> None:
    """Run the full onboarding workflow in sequence."""
    print("[INFO] Starting analytics onboarding workflow")

    run_step("scripts/scan_source.py")
    run_step("scripts/detect_changes.py")

    change_report = read_json(CHANGE_REPORT_PATH, {})
    status = change_report.get("status", "")

    if status == "no_changes":
        no_action_plan = {
            "action": "NO_ACTION",
            "human_approval": False,
            "reason": "No new datasets, files, or schema changes were detected.",
            "summary": {
                "new_dataset_count": 0,
                "new_file_count": 0,
                "modified_file_count": 0,
                "schema_change_count": 0,
            },
        }
        save_json(ACTION_PLAN_PATH, no_action_plan)
        print("[INFO] No changes detected")
        print("[INFO] Action plan updated to NO_ACTION")
        print("[INFO] Stopping workflow")
        return

    run_step("scripts/infer_schema.py")
    run_step("scripts/detect_schema_changes.py")
    run_step("scripts/decision_engine.py")

    action_plan = read_json(ACTION_PLAN_PATH, {})
    print("[FINAL] Decision:")
    print(json.dumps(action_plan, indent=2))


if __name__ == "__main__":
    main()
