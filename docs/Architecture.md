# Analytics Execution Agent - Architecture

## Purpose

The Analytics Execution Agent automates dataset discovery, schema validation, onboarding recommendation, and change detection for analytics ingestion workloads.

The current implementation focuses on detection, governance, and decision-making.

Execution workflows (Bronze loading, metadata updates, etc.) are planned for Phase 2.

---

# High-Level Flow

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

# Component Overview

## 1. scan_source.py

Purpose:

- Scan source directory
- Discover datasets
- Discover files
- Capture metadata

Output:

```text
outputs/discovered_datasets.json
```

---

## 2. detect_changes.py

Purpose:

Compare current scan with previous scan.

Detect:

- New datasets
- New files
- Modified files
- Deleted files

Uses:

```text
state/last_scan.json
```

Outputs:

```text
outputs/change_report.json
```

---

## 3. infer_schema.py

Purpose:

Infer dataset schemas from source files.

Detect:

- Column names
- Data types

Output:

```text
outputs/inferred_schema.json
```

---

## 4. detect_schema_changes.py

Purpose:

Compare detected schema against approved schema.

Uses:

```text
state/approved_schema.json
```

Detects:

- Added columns
- Removed columns
- Data type changes
- New datasets requiring approval

Output:

```text
outputs/schema_change_report.json
```

---

## 5. decision_engine.py

Purpose:

Convert detected changes into business actions.

Inputs:

```text
outputs/change_report.json
outputs/schema_change_report.json
state/approved_schema.json
```

Output:

```text
outputs/action_plan.json
```

---

## 6. orchestrator.py

Purpose:

Run the entire workflow in the correct sequence.

Flow:

```text
scan_source.py
     ↓
detect_changes.py
     ↓
No Changes?
    ├─ Yes → Stop
    └─ No
            ↓
        infer_schema.py
            ↓
        detect_schema_changes.py
            ↓
        decision_engine.py
```

---

# State Files

## approved_schema.json

Source of truth.

Contains:

- Approved datasets
- Approved columns
- Approved datatypes

Used for governance decisions.

Human approval updates this file.

---

## last_scan.json

Runtime tracking state.

Contains:

- Dataset names
- File names
- Hash values
- Modified timestamps

Used to detect new, modified, and deleted files.

---

# Decision Logic

## NO_ACTION

No change detected.

---

## LOAD_NEW_FILE

Conditions:

- Existing approved dataset
- New file
- Schema matches approved schema

Approval Required:

```text
No
```

---

## REPROCESS_FILE

Conditions:

- File modified
- Schema unchanged

Approval Required:

```text
No
```

---

## REVIEW_SCHEMA_CHANGE

Conditions:

- Added column
- Removed column
- Datatype changed

Approval Required:

```text
Yes
```

---

## ONBOARD_NEW_DATASET

Conditions:

- Dataset not found in approved_schema.json

Approval Required:

```text
Yes
```

---

## REVIEW_DATASET_REMOVAL

Conditions:

- Approved dataset/file removed

Approval Required:

```text
Yes
```

---

# Control Table Generation

Current implementation:

```text
1 Dataset
    ↓
1 Control Table Entry
```

Example:

```text
Electricity/
   Jan2026.csv
   Feb2026.csv
   Mar2026.csv
```

Generates:

```sql
INSERT INTO mtd.control_table ...
```

once.

---

# Bronze DDL Generation

Current implementation:

```text
1 Dataset
    ↓
1 Bronze Table
```

Example:

```text
Electricity
    ↓
electricity_interval
```

Generated only once regardless of number of files.

---

# Phase 1 Status

Completed:

✅ Dataset Discovery

✅ Change Detection

✅ Schema Inference

✅ Schema Drift Detection

✅ Approved Schema Governance

✅ New Dataset Detection

✅ Dataset Deletion Detection

✅ Decision Engine

✅ Control Table Generation

✅ Bronze DDL Generation

✅ Orchestrator

---

# Phase 2 (Future)

Execution Layer

```text
action_plan.json
        ↓
Execution Engine
        ↓
Bronze Loader
        ↓
Metadata Updates
        ↓
Control Table Updates
        ↓
Dataset Onboarding