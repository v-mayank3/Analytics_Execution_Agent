# Analytics Execution Agent - Test Cases

## TC01 - No Changes

Scenario:

No files modified.

Expected:

```json
{
  "action": "NO_ACTION"
}
```

Status:

✅ Passed

---

## TC02 - New File

Scenario:

Add:

```text
Electricity/May2026.csv
```

Schema matches approved schema.

Expected:

```json
{
  "action": "LOAD_NEW_FILE"
}
```

Status:

✅ Passed

---

## TC03 - Modified File

Scenario:

Change data value only.

Example:

```text
100 → 101
```

Schema unchanged.

Expected:

```json
{
  "action": "REPROCESS_FILE"
}
```

Status:

✅ Passed

---

## TC04 - New Dataset

Scenario:

Add:

```text
Solar/
   Jan2026.csv
```

Dataset not present in approved_schema.json.

Expected:

```json
{
  "action": "ONBOARD_NEW_DATASET"
}
```

Status:

✅ Passed

---

## TC05 - Added Column

Scenario:

Change:

```csv
Timestamp,SiteID,Units
```

To:

```csv
Timestamp,SiteID,Units,Region
```

Expected:

```json
{
  "action": "REVIEW_SCHEMA_CHANGE"
}
```

Status:

✅ Passed

---

## TC06 - Removed Column

Scenario:

Change:

```csv
Timestamp,SiteID,Units
```

To:

```csv
Timestamp,SiteID
```

Expected:

```json
{
  "action": "REVIEW_SCHEMA_CHANGE"
}
```

Status:

✅ Passed

---

## TC07 - Datatype Change

Scenario:

Approved:

```text
Units = INTEGER
```

File:

```text
Units = DECIMAL
```

Example:

```csv
100.25
200.50
300.75
```

Expected:

```json
{
  "action": "REVIEW_SCHEMA_CHANGE"
}
```

Status:

✅ Passed

---

## TC08 - Delete Unapproved Dataset

Scenario:

Solar discovered but never approved.

Solar removed.

Expected:

```json
{
  "action": "NO_ACTION"
}
```

Status:

✅ Passed

---

## TC09 - Delete Approved Dataset/File

Scenario:

Approved dataset file removed.

Example:

```text
Mobile/Jan2026.csv
```

Expected:

```json
{
  "action": "REVIEW_DATASET_REMOVAL"
}
```

Status:

✅ Passed

---

## TC10 - Re-add Approved Dataset

Scenario:

Approved dataset removed and added back.

Expected:

```json
{
  "action": "LOAD_NEW_FILE"
}
```

or

```json
{
  "action": "REPROCESS_FILE"
}
```

depending on file state.

Status:

✅ Passed

---

## TC11 - Control Table Generation

Scenario:

Dataset has multiple files.

Example:

```text
Electricity
 ├─ Jan2026.csv
 ├─ Feb2026.csv
 └─ Mar2026.csv
```

Expected:

One control table insert.

Status:

✅ Passed

---

## TC12 - Bronze DDL Generation

Scenario:

Dataset has multiple files.

Expected:

One Bronze table DDL.

Example:

```sql
CREATE TABLE electricity_interval(...)
```

generated once.

Status:

✅ Passed

---

# Test Summary

All Foundation Phase tests completed successfully.

Total Test Cases:

```text
12
```

Passed:

```text
12
```

Failed:

```text
0
```

Current Status:

✅ Phase 1 Complete

Next Phase:

```text
Execution Layer
(Bronze Loader & Metadata Execution)