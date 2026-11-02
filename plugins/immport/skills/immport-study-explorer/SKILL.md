---
name: immport-study-explorer
description: Find, compare and assess ImmPort immunology studies (SDY accessions) with the ImmPort MCP tools. Use when the user asks to find ImmPort studies on a topic (a disease, vaccine, pathogen, assay or population), compare several studies, check what data a study has, see when a study was released or updated, or pick the best study for an analysis. Not for analysing downloaded Tab.zip files; use immport-tab-analysis for that.
---

# Explore and compare ImmPort studies

ImmPort holds immunology studies from NIAID-funded research. Each study has an accession like
`SDY180`. These steps use the ImmPort MCP server's tools; they are the same whether the server is
the hosted connector (mcp.immport.org) or `uvx immport-mcp`.

## Workflow

1. **Find candidate studies.** Use `search_studies` and always set `source_fields` to just what
   you need, because full documents are very large. Look up valid filter values with
   `lookup_controlled_vocabulary` in parallel with the search, not before it. Check
   `hits.total.value`; if it's more than the page size, page with `from_record`.
   Useful fields: `study_accession`, `brief_title`, `condition_or_disease`, `research_focus`,
   `actual_enrollment`, `assay_method_count`, `pubmed`, `minimum_age`, `maximum_age`, `species`.
   The `immport://search-fields` resource lists them all.

2. **See what data each study has, for all candidates in one call.**
   `get_study_data_availability(study_accession="SDY180,SDY212,SDY269")` returns per-table record
   counts for up to 20 studies. Use them to decide what to fetch:
   - `hai_result`, `elisa_result`, `mbaa_result`, `fcs_analyzed_result`, … > 0 → that assay is
     worth fetching (`get_assay_results`)
   - `subject` gives the cohort size; `lab_test` and `assessment_component` hold clinical data
   - a count of 0 means not parsed into the database, not necessarily absent: check the study's
     files (`get_study_files(action="manifest")`) before saying the data doesn't exist
   - a study can come back with an `error` entry (e.g. no release file); report it and carry on
     with the others

3. **Compare with multi-study calls.** `get_study_data` takes up to 20 comma-separated studies
   for every resource, and every row carries `studyAccession`. Make one call per resource for all
   studies, and run independent calls in parallel:
   - `resource="summary"` (one entry per study): title, PI, description, design, enrollment
   - `resource="arm"`, `"planned_visits"`, `"conditions"`, `"experiments"`
   - `resource="demographic"` (one row per subject) for sex, age, race and ethnicity breakdowns.
     It's large; for more than a few hundred subjects per study, summarise rather than list.
   Never loop one call per study when a multi-study call does it.

4. **Release history when it matters.** `get_release_notes(study_accession="SDY180")` lists each
   release (`DR6` … `DR58`) with date, status (Initial or Updated) and notes;
   `version="latest"` gives only the study's most recent one. `get_release_notes(version="DR68")`
   describes a whole data release.

5. **Large or detailed data → Tab.zip.** If you need more than two resources for one study, or a
   table is large (e.g. `assessment_component` > 10,000, `fcs_analyzed_result`), get the study's
   Tab.zip instead of many API calls: `get_study_files(action="manifest",
   study_accession=..., file_type="release_file")`, find `_Tab.zip`, then
   `get_study_files(action="download", file_uuid=...)`. Give the user the download link. Never
   try to fetch a signed download URL yourself: it fails from a sandbox. Then use the
   immport-tab-analysis skill.

## Presenting results

- Put comparisons in one table: rows = studies, columns = what was asked (title, condition,
  subjects, arms, start date, key assays with counts, latest release).
- Say which numbers come from counts of parsed records and which from the study description
  (e.g. planned vs. actual enrollment).
- Name each study by its accession and short title, and link it as
  `https://www.immport.org/shared/study/SDY180`.
- If the user's premise doesn't match the data (e.g. a study isn't about the condition they
  named), say so plainly.

## Access

Searching, controlled vocabularies and the data model need no login. Study data, assay results,
files and release notes need ImmPort access: the connector's sign-in, or `IMMPORT_API_KEY` for the
command-line server (keys from https://www.immport.org/auth/api/keys, valid 30 days). If a tool
says authentication is missing or expired, tell the user how to fix it instead of retrying.
