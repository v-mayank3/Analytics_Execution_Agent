#!/usr/bin/env python3
"""Generate simple Bronze table DDL from inferred schema information.

This script reads the schema report created by infer_schema.py. For each
source dataset, it creates a beginner-friendly CREATE TABLE statement using
simple SQL data types.
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
    """Convert a dataset name into a simple Bronze table name.

    Examples:
    - Electricity -> electricity_interval
    - Mobile -> mobile_traffic
    - Price -> spot_price

    This function uses a small rule-based approach so it stays easy to follow.
    """
    name = dataset_name.strip().lower()

    if name == "electricity":
        return "electricity_interval"
    if name == "mobile":
        return "mobile_traffic"
    if name == "price":
        return "spot_price"

    # Default fallback: use the dataset name plus a generic suffix.
    return f"{name}_bronze"


def sql_type_for(data_type: str) -> str:
    """Map the inferred Python-friendly type to a SQL type."""
    mapping = {
        "STRING": "NVARCHAR(4000)",
        "INTEGER": "INT",
        "DECIMAL": "DECIMAL(18,2)",
        "DATETIME": "DATETIME2",
        "BOOLEAN": "BIT",
    }
    return mapping.get(data_type.upper(), "NVARCHAR(4000)")


def build_create_table_sql(dataset_name: str, columns: List[Dict[str, Any]]) -> str:
    """Build a CREATE TABLE statement for one dataset."""
    table_name = to_table_name(dataset_name)

    lines = []
    lines.append(f"CREATE TABLE {table_name} (")

    # Add the inferred columns first.
    for column in columns:
        column_name = column.get("name", "")
        data_type = column.get("data_type", "STRING")
        lines.append(f"    {column_name} {sql_type_for(data_type)},")

    # Add the required metadata columns.
    lines.append("    _source_file NVARCHAR(500),")
    lines.append("    _ingestion_timestamp DATETIME2")
    lines.append(");")

    return "\n".join(lines)


def generate_ddl(schema_path: Path) -> str:
    """Read the inferred schema JSON and create one SQL statement per dataset."""
    if not schema_path.exists():
        return "-- Schema file not found."

    with schema_path.open("r", encoding="utf-8") as handle:
        schema_data = json.load(handle)

    statements = []
    statements.append("-- Bronze table DDL generated from inferred schema")
    statements.append("")

    datasets: dict[str, List[Dict[str, Any]]] = {}
    for item in schema_data.get("files", []):
        dataset_name = str(item.get("dataset_name", "")).strip()
        if not dataset_name:
            continue

        if dataset_name not in datasets:
            datasets[dataset_name] = []

        for column in item.get("columns", []):
            column_name = str(column.get("name", "")).strip()
            if not column_name:
                continue

            if not any(existing.get("name", "") == column_name for existing in datasets[dataset_name]):
                datasets[dataset_name].append(column)

    for dataset_name in sorted(datasets):
        columns = datasets[dataset_name]
        statements.append(build_create_table_sql(dataset_name, columns))
        statements.append("")

    return "\n".join(statements).strip() + "\n"


def main() -> None:
    """Run the DDL generation process and save the SQL output."""
    root_dir = get_project_root()
    schema_path = root_dir / "outputs" / "inferred_schema.json"
    output_path = root_dir / "outputs" / "bronze_ddl.sql"

    ddl_sql = generate_ddl(schema_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ddl_sql, encoding="utf-8")

    print(f"Bronze DDL saved to {output_path}")


if __name__ == "__main__":
    main()
