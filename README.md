# Analytics Execution Agent

## Overview

The Analytics Execution Agent is a metadata-driven onboarding and change-detection framework for analytics datasets.

The current implementation focuses on:

- Dataset discovery
- File change detection
- Schema inference
- Schema drift detection
- Human-in-the-loop approval workflow
- Decision engine
- Dataset onboarding recommendations

Execution (Bronze loading, metadata updates, DDL execution, etc.) is planned for Phase 2.

---

# Project Structure

```text
Analytics_Execution_Agent/

├── orchestrator.py

├── scripts/
│   ├── scan_source.py
│   ├── detect_changes.py
│   ├── infer_schema.py
│   ├── detect_schema_changes.py
│   ├── decision_engine.py
│   ├── generate_bronze_ddl.py
│   └── generate_control_table_sql.py

├── source/
│   ├── Electricity/
│   ├── Mobile/
│   └── ...

├── outputs/
│   ├── discovered_datasets.json
│   ├── change_report.json
│   ├── inferred_schema.json
│   ├── schema_change_report.json
│   ├── action_plan.json
│   ├── bronze_ddl.sql
│   └── control_table_inserts.sql

├── state/
│   ├── approved_schema.json
│   └── last_scan.json
```

---

# State Files

## approved_schema.json

Human-approved source of truth.

Example:

```json
{
  "dataset_name": "Electricity",
  "columns": [
    { "name": "Timestamp", "data_type": "DATETIME" },
    { "name": "SiteID", "data_type": "STRING" },
    { "name": "Units", "data_type": "INTEGER" }
  ]
}
```

The schema validation engine compares files against this file.

---

## last_scan.json

Stores:

- Dataset names
- File names
- File hashes
- Modified dates

Used for:

- New file detection
- Modified file detection
- Deleted file detection

---

# Workflow

```text
Source Files
    ↓
scan_source.py
    ↓
detect_changes.py
    ↓
infer_schema.py
    ↓
detect_schema_changes.py
    ↓
decision_engine.py
    ↓
action_plan.json
```

---

# Running the Agent

Run:

```powershell
python orchestrator.py
```

The orchestrator automatically executes all required scripts.

If no changes are detected, processing stops early.

---

# Action Types

## NO_ACTION

No changes detected.

```json
{
  "action": "NO_ACTION"
}
```

---

## LOAD_NEW_FILE

Existing approved dataset received a new file.

Example:

```text
Electricity/
 ├─ Jan2026.csv
 ├─ Feb2026.csv
 └─ Mar2026.csv
```

New file:

```text
Apr2026.csv
```

Result:

```json
{
  "action": "LOAD_NEW_FILE"
}
```

Human approval not required.

---

## REPROCESS_FILE

File contents changed but schema remained unchanged.

Human approval not required.

---

## REVIEW_SCHEMA_CHANGE

Triggered when:

- New column detected
- Column removed
- Datatype changed

Example:

```text
Units: INTEGER → DECIMAL
```

Human approval required.

---

## ONBOARD_NEW_DATASET

Triggered when a dataset does not exist in approved_schema.json.

Example:

```text
Solar/
 └─ Jan2026.csv
```

Result:

```json
{
  "action": "ONBOARD_NEW_DATASET"
}
```

Human approval required.

---

## REVIEW_DATASET_REMOVAL

Triggered when an approved dataset/file is removed.

Human approval required.

---

# Human Approval Process

The agent does NOT automatically update approved_schema.json.

Process:

1. Agent detects change.
2. schema_change_report.json is generated.
3. Human reviews the change.
4. Human updates approved_schema.json if approved.
5. Agent uses the updated schema as the new baseline.

---

# Current Phase

Phase 1 Complete:

✅ Dataset Discovery

✅ Schema Inference

✅ File Change Detection

✅ Hash-Based Tracking

✅ Dataset Onboarding Detection

✅ Schema Drift Detection

✅ Human Approval Workflow

✅ Decision Engine

✅ Control Table Generation

✅ Bronze DDL Generation

✅ Orchestrator

---

# Phase 2 (Future)

Execution Layer

The Decision Engine currently recommends actions.

Future implementation will execute actions automatically:

```text
action_plan.json
        ↓
Execution Layer
        ↓
Bronze Loader
        ↓
Metadata Updates
        ↓
Control Table Updates
        ↓
Dataset Onboarding Workflow
```

The foundation layer must remain stable before Phase 2 development begins.
