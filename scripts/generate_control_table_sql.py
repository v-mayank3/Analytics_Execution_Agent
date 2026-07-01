#!/usr/bin/env python3
"""Generate SQL insert statements for a control table.

This script reads the inferred schema JSON and creates simple SQL INSERT
statements for the mtd.control_table table. The output is meant for learning
and can be adapted to your own database environment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def get_project_root() -> Path:
    """Return the project root even when this script lives in the scripts folder."""
    current_path = Path(__file__).resolve()
    if current_path.parent.name == "scripts":
        return current_path.parent.parent
    return current_path.parent


def to_table_name(dataset_name: str) -> str:
    """Create a Bronze table name from the dataset name.

    This mirrors the naming logic from the Bronze DDL generator so the control
    table stays consistent with the DDL output.
    """
    name = dataset_name.strip().lower()

    if name == "electricity":
        return "electricity_interval"
    if name == "mobile":
        return "mobile_traffic"
    if name == "price":
        return "spot_price"

    return f"{name}_bronze"


def build_insert_statement(dataset_name: str, source_folder: str) -> str:
    """Build one INSERT statement for mtd.control_table."""
    bronze_table = to_table_name(dataset_name)

    # The values below use the defaults requested by the user.
    # We keep the SQL simple and easy to read for beginners.
    return (
        "INSERT INTO mtd.control_table "
        "(DatasetName, SourceFolder, BronzeTable, IsActive, Status, CreatedDate) "
        f"VALUES ('{dataset_name}', '{source_folder}', '{bronze_table}', 0, 'PendingApproval', CURRENT_TIMESTAMP);"
    )


def generate_control_sql(schema_path: Path) -> str:
    """Read the inferred schema JSON and build one control-table row per dataset."""
    if not schema_path.exists():
        return "-- Schema file not found."

    with schema_path.open("r", encoding="utf-8") as handle:
        schema_data = json.load(handle)

    statements = []
    statements.append("-- Control table insert statements generated from inferred schema")
    statements.append("")

    dataset_names = sorted({str(item.get("dataset_name", "")).strip() for item in schema_data.get("files", []) if item.get("dataset_name")})
    for dataset_name in dataset_names:
        source_folder = f"source/{dataset_name}"
        statements.append(build_insert_statement(dataset_name, source_folder))
        statements.append("")

    return "\n".join(statements).strip() + "\n"


def main() -> None:
    """Run the control-table SQL generation and save the output file."""
    root_dir = get_project_root()
    schema_path = root_dir / "outputs" / "inferred_schema.json"
    output_path = root_dir / "outputs" / "control_table_inserts.sql"

    sql_text = generate_control_sql(schema_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sql_text, encoding="utf-8")

    print(f"Control table SQL saved to {output_path}")


if __name__ == "__main__":
    main()
