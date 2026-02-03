# STANDARD OPERATING PROCEDURE

## Generation of Compliance Deliverables from Regulatory Templates

---

| Field                | Value                                                                 |
|----------------------|-----------------------------------------------------------------------|
| **Document ID**      | SOP-SAF-001                                                           |
| **Version**          | 1.0                                                                   |
| **Effective Date**   | [DD MMM YYYY]                                                         |
| **Document Owner**   | [Name / Role]                                                         |
| **Prepared By**      | [Name / Role]                                                         |
| **Approved By**      | [Name / Role / Date]                                                  |
| **Confidentiality**  | Confidential                                                          |

---

## Revision History

| Version | Date         | Author         | Description of Change         |
|---------|--------------|----------------|-------------------------------|
| 1.0     | [DD MMM YYYY]| [Name]         | Initial release               |
|         |              |                |                               |

---

## Approval Signatures

| Role             | Name | Signature | Date         |
|------------------|------|-----------|--------------|
| Document Owner   |      |           |              |
| Quality Reviewer |      |           |              |
| Department Head  |      |           |              |

---

## Distribution List

| Role                          | Distribution Method |
|-------------------------------|---------------------|
| Safety Assessment Team        | Controlled copy     |
| Quality Assurance             | Controlled copy     |
| Regulatory Affairs            | Controlled copy     |
| Audit & Compliance            | On request          |

---

## Table of Contents

1. Purpose
2. Scope
3. Definitions and Abbreviations
4. Responsibilities
5. Procedure
   - 5.1 Prepare Template Text
   - 5.2 Identify Template Sections
   - 5.3 Extract Required Sources
   - 5.4 Create Template Source Rules File
   - 5.5 Map Template to Target Framework
   - 5.6 Insert SOURCE TRACE Blocks
   - 5.7 Generate Compliance Snapshot
   - 5.8 Validate Against Hard Rules
6. Global Hard Rules
7. Deliverable Specifications
8. References
9. Appendices

---

## 1. Purpose

This Standard Operating Procedure establishes a standardized, repeatable process for generating four compliance deliverables from any regulatory template (e.g., Signal Assessment Report Template, Investigative Brochure). It ensures traceability, audit defensibility, and zero inference in source attribution.

The process is template-agnostic and shall preserve the integrity of all source references and downstream content without modification, interpretation, or supplementation.

---

## 2. Scope

### 2.1 In Scope

- Any regulatory template used as the basis for safety assessment reports, including but not limited to: Drug Safety Reports (DSRs), Periodic Benefit-Risk Evaluation Reports (PBRERs), and Signal Assessment Reports.
- Generation of the following four deliverables:
  1. Template Source Rules File
  2. Template-to-Framework Mapping File
  3. SOURCE TRACE Provenance Blocks
  4. Compliance Snapshot
- Framework sections designated as in-scope for a given project.

### 2.2 Out of Scope

- Verification of sources against actual reference documents (covered by a separate verification SOP).
- Rewriting, summarizing, or modifying any downstream report content.
- Generation of deliverables beyond the four specified above, unless explicitly approved by the Document Owner.

### 2.3 Future-Scope Sections

Framework sections designated as future-scope shall be documented in the mapping file but shall not receive SOURCE TRACE blocks or compliance snapshot entries in the current iteration.

---

## 3. Definitions and Abbreviations

| Term              | Definition                                                                                         |
|-------------------|-----------------------------------------------------------------------------------------------------|
| Template          | The regulatory document defining section structure and required sources (the single source of truth) |
| Framework         | The target document structure being assessed (e.g., DSR sections 1.1-1.2.2.4)                      |
| Source            | A document or database explicitly named in the template as required input for a given section       |
| SOURCE TRACE      | A machine-readable provenance block inserted into framework section files                           |
| NOT VERIFIED      | Default status indicating source compliance has not been confirmed against actual reference documents|
| NOT MAPPED        | Status indicating no template analog exists for a given framework section                           |
| Verbatim          | Copied exactly as written in the template, with no corrections, expansions, or normalization        |
| DSR               | Drug Safety Report                                                                                  |
| PBRER             | Periodic Benefit-Risk Evaluation Report                                                             |
| IB                | Investigator's Brochure                                                                             |
| RMP               | Risk Management Plan                                                                                |
| MedDRA            | Medical Dictionary for Regulatory Activities                                                        |
| YAML              | YAML Ain't Markup Language (structured data format)                                                 |
| CSV               | Comma-Separated Values                                                                              |

---

## 4. Responsibilities

| Role              | Responsibility                                                                                     |
|-------------------|-----------------------------------------------------------------------------------------------------|
| Safety Analyst    | Executes Steps 5.1 through 5.7 of this SOP. Prepares all four deliverables.                        |
| Quality Reviewer  | Executes Step 5.8 (validation against hard rules). Reviews deliverables before finalization.        |
| Document Owner    | Maintains this SOP. Approves scope changes, framework extensions, and any deviation requests.      |
| Auditor           | Uses the compliance snapshot and SOURCE TRACE blocks to verify process adherence during audits.    |

**Separation of Duties:** The Safety Analyst and Quality Reviewer shall be different individuals to ensure independent verification.

---

## 5. Procedure

### 5.1 Prepare Template Text

**Performed by:** Safety Analyst

1. The Safety Analyst shall obtain the current version of the regulatory template.
2. The template shall be converted to plain text format (from PDF, Word, or other source format).
3. The following elements shall be preserved exactly as they appear in the original:
   - Section numbering
   - Section titles
   - All references, citations, and source attributions
4. The Safety Analyst shall **not** normalize formatting, correct wording, or standardize references during conversion.
5. **Stop-gate:** A second person shall confirm that the plain text representation faithfully matches the original template before proceeding.

**Outcome:** A faithful textual representation of the template, suitable for source extraction.

---

### 5.2 Identify Template Sections

**Performed by:** Safety Analyst

1. The Safety Analyst shall scan the template from start to finish.
2. Each discrete section shall be identified using:
   - Section numbers (e.g., 2.1.1, 3.3.2)
   - Section headings (e.g., "Drug pharmacology", "Review of toxicology data")
3. Appendices and footnotes shall be treated as sections if they contain source references.
4. For each section, the following shall be recorded:
   - Template section identifier (number)
   - Template section title
   - Full section body (unchanged)

**Outcome:** A complete, ordered list of all template sections.

---

### 5.3 Extract Required Sources

**Performed by:** Safety Analyst

1. For each template section identified in Step 5.2, the Safety Analyst shall read the section text carefully.
2. Only explicitly named sources shall be extracted. Examples include:
   - Document identifiers (e.g., "IB 6.1", "PBRER Section 5")
   - External named references (e.g., "UpToDate", "Medline", "Embase")
   - Database references (e.g., "company safety database")
3. Each source shall be copied **exactly as written** in the template (verbatim).
4. The Safety Analyst shall **not**:
   - Expand abbreviations
   - Correct typographical errors
   - Add implied or inferred references
   - Supplement sources from external knowledge or industry conventions
5. If a section contains no explicitly named sources, an empty list shall be recorded.

**Outcome:** Each template section has a definitive, auditable list of required sources.

---

### 5.4 Create Template Source Rules File

**Performed by:** Safety Analyst

1. A YAML file shall be created containing one entry per template section.
2. Each entry shall include:
   - `section_id`: Template section identifier
   - `title`: Template section title
   - `required_sources`: List of verbatim-extracted sources (may be empty)
   - `notes`: Factual context from the template text (e.g., "Template states: 'IB includes the necessary information'"). Notes shall not contain interpretation or commentary.
3. The file shall not merge, split, or reorder sources relative to their appearance in the template.
4. All template sections shall be included, including those with empty source lists.

**File format:** YAML
**Naming convention:** `template_source_rules.yaml`
**Storage location:** `data/mappings/`

**Outcome:** A complete rules file defining what sources are required by the template itself.

---

### 5.5 Map Template to Target Framework

**Performed by:** Safety Analyst

1. For each target framework section (as defined in the project scope):
   - The Safety Analyst shall determine whether a corresponding template section exists.
2. If a match is found:
   - A one-to-one mapping shall be recorded.
   - The match method shall be documented (e.g., "exact_title", "conceptual_match", "content_match").
3. If no match is found:
   - The mapping shall be explicitly marked with `template_section: null` and status `NOT MAPPED`.
   - The notes field shall state "No template analog identified."
4. Framework sections designated as future-scope:
   - Shall be recorded in a separate `future_mappings` section of the same file.
   - Shall not receive SOURCE TRACE blocks or compliance snapshot entries.
5. The Safety Analyst shall **not** force a mapping to "make it fit." If the alignment is uncertain, the section shall be marked as NOT MAPPED with an explanatory note.

**File format:** YAML
**Naming convention:** `template_to_dsr_map.yaml`
**Storage location:** `data/mappings/`

**Outcome:** A transparent, honest mapping that distinguishes in-scope, out-of-scope, and future sections.

---

### 5.6 Insert SOURCE TRACE Blocks

**Performed by:** Safety Analyst

1. For each in-scope framework section, a SOURCE TRACE block shall be inserted at the **top** of the section's markdown file, above the existing heading.
2. The block shall use HTML comment format:

```
<!-- SOURCE TRACE
Template section: [template section ID] - [template section title]
Required sources: [verbatim source list, comma-separated]
Verification status: NOT VERIFIED
Missing inputs: Source verification
-->
```

3. For framework sections marked NOT MAPPED:

```
<!-- SOURCE TRACE
Template section: NOT MAPPED
Required sources: N/A
Verification status: NOT MAPPED
Missing inputs: No template analog identified
-->
```

4. The Safety Analyst shall **not**:
   - Modify any existing content below the SOURCE TRACE block
   - Remove or reformat original text
   - Add, delete, or change any part of the section body

**Outcome:** Each in-scope section gains machine-readable provenance without altering substance.

---

### 5.7 Generate Compliance Snapshot

**Performed by:** Safety Analyst

1. A CSV file shall be created with one row per in-scope framework section.
2. The following columns shall be included:

| Column             | Description                                                     |
|--------------------|-----------------------------------------------------------------|
| `dsr_section`      | Framework section identifier                                    |
| `dsr_title`        | Framework section title                                         |
| `template_section` | Mapped template section identifier (blank if NOT MAPPED)        |
| `template_title`   | Mapped template section title (blank if NOT MAPPED)             |
| `required_sources` | Verbatim source list from template (N/A if NOT MAPPED)          |
| `status`           | NOT VERIFIED or NOT MAPPED                                      |
| `notes`            | Factual notes only (e.g., "Parent section", "Subsection of 2.2")|

3. Notes shall contain only factual, descriptive information. No interpretation, assessment, or recommendation shall appear in the notes column.

**File format:** CSV
**Naming convention:** `compliance_snapshot.csv`
**Storage location:** `data/mappings/`

**Outcome:** A single-view compliance dashboard suitable for audit or review.

---

### 5.8 Validate Against Hard Rules

**Performed by:** Quality Reviewer

The Quality Reviewer shall independently verify all four deliverables against the following checklist before finalization:

| # | Validation Check                                                          | Pass/Fail |
|---|---------------------------------------------------------------------------|-----------|
| 1 | Every source listed in the source rules file appears verbatim in the template text | |
| 2 | No source has been inferred, expanded, corrected, or supplemented         |           |
| 3 | No downstream framework content has been rewritten, summarized, or altered|           |
| 4 | All unmapped sections are explicitly marked as NOT MAPPED in all deliverables |       |
| 5 | Verification status has not been prematurely set to any value other than NOT VERIFIED or NOT MAPPED | |
| 6 | All in-scope framework sections have a SOURCE TRACE block                 |           |
| 7 | All in-scope framework sections appear in the compliance snapshot         |           |
| 8 | The mapping file distinguishes in-scope from future-scope sections        |           |
| 9 | File formats match specifications (YAML for rules/mapping, CSV for snapshot) |        |
| 10| Files are stored in the designated location (`data/mappings/`)            |           |

**If any check fails:** The Quality Reviewer shall return the deliverables to the Safety Analyst with specific findings. The Safety Analyst shall correct the issues and resubmit for validation.

**If all checks pass:** The Quality Reviewer shall sign off on the deliverables.

**Outcome:** Defensible, reproducible, audit-ready deliverables.

---

## 6. Global Hard Rules

The following rules apply at every step of this procedure and shall not be overridden without written approval from the Document Owner:

1. **Verbatim sources only.** Only sources explicitly written in the template may be used. Source names shall be captured exactly as written.
2. **No inference.** No inferred, standardized, corrected, or "cleaned up" citations are permitted.
3. **No content modification.** No rewriting, summarizing, or altering of downstream framework content is permitted.
4. **Explicit unmapped marking.** Sections that do not map to the template shall be explicitly marked as NOT MAPPED in all deliverables.
5. **Default verification status.** Verification status shall default to NOT VERIFIED. It may only be changed through a separate, documented verification process.
6. **Four deliverables only.** No additional deliverables shall be produced unless explicitly approved by the Document Owner.

---

## 7. Deliverable Specifications

| Deliverable               | Format | File Name                    | Location         | Description                                       |
|---------------------------|--------|------------------------------|------------------|----------------------------------------------------|
| Template Source Rules      | YAML   | `template_source_rules.yaml` | `data/mappings/` | All template sections with verbatim required sources|
| Template-to-Framework Map  | YAML   | `template_to_dsr_map.yaml`   | `data/mappings/` | Section-level mapping with match method and notes  |
| SOURCE TRACE Blocks        | HTML   | (embedded in `.md` files)    | Section files    | Provenance blocks at top of each in-scope file     |
| Compliance Snapshot        | CSV    | `compliance_snapshot.csv`    | `data/mappings/` | One row per in-scope section with status and sources|

---

## 8. References

- ICH E2C(R2): Periodic Benefit-Risk Evaluation Report
- ICH E2E: Pharmacovigilance Planning
- Signal Assessment Report Template (internal, version as applicable)
- Applicable regulatory template (project-specific)

---

## 9. Appendices

### Appendix A: Example SOURCE TRACE Block (Mapped Section)

```html
<!-- SOURCE TRACE
Template section: 2.1.2 - Therapeutic Indications
Required sources: IB 6.1
Verification status: NOT VERIFIED
Missing inputs: Source verification
-->
```

### Appendix B: Example SOURCE TRACE Block (Unmapped Section)

```html
<!-- SOURCE TRACE
Template section: NOT MAPPED
Required sources: N/A
Verification status: NOT MAPPED
Missing inputs: No template analog identified
-->
```

### Appendix C: Example Compliance Snapshot Row

```
dsr_section,dsr_title,template_section,template_title,required_sources,status,notes
1.2.1.1,Therapeutic Indications,2.1.2,Therapeutic Indications,IB 6.1,NOT VERIFIED,
```

### Appendix D: Validation Checklist (Printable)

| # | Check                                                                     | Pass | Fail | N/A | Reviewer Initials | Date |
|---|---------------------------------------------------------------------------|------|------|-----|-------------------|------|
| 1 | All sources appear verbatim in template                                   |      |      |     |                   |      |
| 2 | No inferred or supplemented sources                                       |      |      |     |                   |      |
| 3 | No downstream content modified                                            |      |      |     |                   |      |
| 4 | Unmapped sections explicitly marked                                       |      |      |     |                   |      |
| 5 | Verification status not prematurely updated                               |      |      |     |                   |      |
| 6 | All in-scope sections have SOURCE TRACE blocks                            |      |      |     |                   |      |
| 7 | All in-scope sections in compliance snapshot                              |      |      |     |                   |      |
| 8 | In-scope vs. future-scope properly distinguished                          |      |      |     |                   |      |
| 9 | File formats match specifications                                         |      |      |     |                   |      |
| 10| Files in designated location                                              |      |      |     |                   |      |

**Reviewer Name:** ___________________________
**Reviewer Signature:** ___________________________
**Date:** ___________________________

---

*End of Document*
