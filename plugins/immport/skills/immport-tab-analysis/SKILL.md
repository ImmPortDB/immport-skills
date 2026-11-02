---
name: immport-tab-analysis
description: Analyse ImmPort study data from downloaded Tab.zip packages (files named like SDY180-DR58_Tab.zip) by loading them into SQLite and querying with SQL joins from the ImmPort data model. Use when the user has, or is about to download, an ImmPort Tab.zip or extracted Tab folder and wants tables joined, subjects linked to arms, samples or assay results (HAI, ELISA, flow cytometry, MBAA, lab tests…), summary statistics, or a cross-study dataset. For finding and comparing studies first, use immport-study-explorer.
---

# Analyse ImmPort Tab.zip data

A study's Tab.zip (`<SDY>-DR<n>_Tab.zip`) contains its complete parsed data: one tab-separated
file per ImmPort table in `<SDY>-DR<n>_Tab/Tab/<table>.txt`, with an uppercase header row.
`Tab/protocols/` holds the study's protocol documents. It's the right source when the API would
need many calls or a table is large.

## 1. Get the file

If the user doesn't have it yet, use the ImmPort MCP tools:
`get_study_files(action="manifest", study_accession="SDY180", file_type="release_file")`, find the
`_Tab.zip` entry, then `get_study_files(action="download", file_uuid=...)`. That returns a signed,
time-limited link. Give it to the user to download; never try to fetch it yourself, because it
fails from a sandbox. Ask the user to upload the zip, or give its path if you're running locally.

## 2. Load it into SQLite

```bash
python3 scripts/load_tab.py SDY180-DR58_Tab.zip --db immport.db
python3 scripts/load_tab.py SDY180-DR58_Tab.zip SDY269-DR58_Tab.zip --db flu.db   # several studies
```

The script is in this skill's `scripts/` folder and uses only the Python standard library. Table
and column names become lowercase (they match the data model), numbers are stored as numbers, and
empty values become NULL. It prints the row count of each table; use that to see what the study
contains. Tables listed with 0 rows, or missing, have no parsed data in this study.

## 3. Find the joins: don't guess them

Use the ImmPort MCP data model tool, which needs no login:
- `get_data_model()` lists every table with a description
- `get_data_model(table="hai_result")` gives columns, primary key, foreign keys and the tables
  that reference it

Build joins from the foreign keys. Common paths:

| From | To | Join on |
|---|---|---|
| `subject` | arm | `arm_2_subject.subject_accession` → `arm_or_cohort.arm_accession` (a subject can be in more than one arm) |
| `arm_or_cohort` | study | `arm_or_cohort.study_accession` |
| `biosample` | subject, visit | `biosample.subject_accession`, `biosample.planned_visit_accession` → `planned_visit` |
| assay results (`hai_result`, `elisa_result`, `mbaa_result`, `fcs_analyzed_result`, …) | subject, arm, sample | `subject_accession`, `arm_accession`, `biosample_accession`, `expsample_accession` are on the result row |
| `expsample` | biosample | `expsample_2_biosample` |
| `lab_test` | biosample | `lab_test.biosample_accession` |
| `assessment_component` | panel → study | `assessment_component.assessment_panel_accession` → `assessment_panel.study_accession` |

Time points: results and biosamples carry `study_time_collected` and `study_time_collected_unit`
(days relative to the study's reference event, e.g. vaccination).

## 4. Analyse

Query with Python's `sqlite3` (or pandas `read_sql`). For example, HAI titers per arm, strain and
day:

```sql
SELECT a.name AS arm, h.virus_strain_preferred AS strain, h.study_time_collected AS day,
       COUNT(DISTINCT h.subject_accession) AS subjects, AVG(h.value_preferred) AS mean_titer
  FROM hai_result h
  JOIN arm_or_cohort a ON a.arm_accession = h.arm_accession
 GROUP BY arm, strain, day
 ORDER BY arm, strain, day;
```

Good practice:
- Use the `*_preferred` columns (standardised values and units) over `*_reported`, and say which
  you used.
- Check units (`unit_preferred`) before combining values, and say when a study has mixed units.
- Count distinct subjects, not rows. Assay tables have several rows per subject (time points,
  analytes, replicates).
- For seroconversion or fold change, pair each subject's baseline (day ≤ 0) with a post-dose
  value of the same strain, and say which baseline and day you chose.
- With several studies in one database, group by `study_accession` (directly on most research
  tables, or through `arm_or_cohort`) and don't pool studies without saying so.

## Reporting

Give the SQL you ran with the results, so the analysis can be repeated. Cite the study accessions
and the data release from the file name (e.g. SDY180, DR58).
