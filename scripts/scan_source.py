#!/usr/bin/env python3
"""Scan folders under the source directory and discover supported files."""

from pathlib import Path
import json
from datetime import datetime


def get_project_root() -> Path:
    """Return the project root even when this script lives in the scripts folder."""
    current_path = Path(__file__).resolve()
    if current_path.parent.name == "scripts":
        return current_path.parent.parent
    return current_path.parent


# Supported file types for discovery.
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet", ".xml", ".txt"}


def discover_datasets(source_dir: Path):
    """Return a list of discovered files for each dataset folder."""
    discovered_files = []

    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        return discovered_files

    # Each folder directly under source/ is treated as one dataset.
    for dataset_dir in sorted(source_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue

        dataset_name = dataset_dir.name

        # Scan files inside the dataset folder and its subfolders.
        for file_path in sorted(dataset_dir.rglob("*")):
            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                continue

            file_stat = file_path.stat()
            discovered_files.append(
                {
                    "dataset_name": dataset_name,
                    "file_name": file_path.name,
                    "extension": extension.lstrip("."),
                    "size": file_stat.st_size,
                    "modified_date": datetime.fromtimestamp(file_stat.st_mtime).isoformat(timespec="seconds"),
                }
            )

    return discovered_files


def save_results(results, output_path: Path):
    """Write the discovery results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(results, output_file, indent=2)

    print(f"Saved {results['total_files']} discovered files to {output_path}")


def main():
    """Run the discovery process and save the output JSON file."""
    root_dir = get_project_root()
    source_dir = root_dir / "source"
    output_path = root_dir / "outputs" / "discovered_datasets.json"

    discovered_files = discover_datasets(source_dir)

    results = {
        "source_directory": str(source_dir.relative_to(root_dir)).replace("\\", "/"),
        "discovered_files": discovered_files,
        "total_files": len(discovered_files),
    }

    save_results(results, output_path)


if __name__ == "__main__":
    main()
