# IB Reader & Template Populator — Design

**Date:** 2026-02-03
**Status:** Draft

## Purpose

Add the ability to read an Investigator's Brochure (IB) PDF, extract its sections, and populate a filled-in version of the regulatory template by resolving source references like "IB 2.3" to actual IB content. This makes the tool drug-agnostic — swap the IB PDF and the template gets populated from the new drug's IB automatically.

## Data Flow

```
IB PDF
  → ib_extractor (reuses pdf_extractor logic)
  → list of IB sections indexed by section_num
  → ib_resolver: matches template required_sources ("IB 2.3") to IB sections
  → template_populator: walks parsed template, for each section:
      - IB ref found & matched    → insert verbatim IB text
      - IB ref found & not matched → "[CONTENT NOT FOUND: IB 2.3]"
      - Non-IB ref (PBRER, etc.)  → "[MANUAL INPUT REQUIRED: PBRER Section 5]"
      - No required sources        → leave template body as-is
  → write filled_template.md
  → convert to filled_template.docx (via python-docx)
```

## New Files

### `src/ib_extractor.py`

Thin wrapper around `pdf_extractor` for IB PDFs. Reuses `HEADING_RE` regex and `_detect_sections` logic. Returns a dict mapping section numbers to content for fast lookup.

### `src/ib_resolver.py`

Resolves `required_sources` strings from template sections:

- **IB reference regex:** `r"^IB\s*(?:Section\s*)?(\d+(?:\.\d+)*)$"` (case-insensitive)
- Parses strings like `"IB 2.3"`, `"IB Section 4.3.3"`, `"IB 6.1"` → extracts dotted-decimal number
- Looks up number in IB section index → returns verbatim content
- Classifies non-IB references → returns placeholder string
- Bare `"IB"` with no section number → placeholder `[MANUAL INPUT REQUIRED: IB — no specific section referenced]`

Source classification function for future extensibility:

```python
def classify_source(source: str) -> tuple[str, str | None]:
    """Returns (source_type, section_num_or_none).

    source_type is one of: "ib", "pbrer", "external", "unknown"
    """
```

When new source types are added later (PBRER, UpToDate, safety database), new resolver functions plug into this same module without architectural changes.

### `src/template_populator.py`

Walks the template section list and assembles a single markdown document:

- Template section headings become markdown headings
- For each section, calls `ib_resolver` with the section's `required_sources`
- When multiple IB refs exist for one section, inserts each under a labeled subheading:

```markdown
## 2.1.1 Drug Pharmacology

### From IB 2.3 — Pharmacology and Mechanism of Action
[verbatim content from IB section 2.3]

### From IB 1.2 — Formulation and Dosing (Summary)
[verbatim content from IB section 1.2]

### From IB 3.2 — Formulation and Dosing (Detailed)
[verbatim content from IB section 3.2]
```

After assembling markdown, converts to .docx using `python-docx`.

## CLI Changes

### New argument on both subcommands (`from-pdf`, `from-sections`):

- `--ib` (required): Path to the IB PDF file

### New output files:

- `data/output/filled_template.md`
- `data/output/filled_template.docx`

## Dependencies

- `python-docx` — added to `requirements.txt` for .docx generation (pure Python, no system dependency)

## Design Decisions

1. **Verbatim only** — no LLM summarization during population. Content is copied exactly from the IB to preserve regulatory defensibility.
2. **Single output document** — one filled-in template file rather than per-section files, matching how the template is structured as one document.
3. **Placeholder pattern** — `[MANUAL INPUT REQUIRED: <source>]` for non-IB sources. Easy to grep for, and designed so future resolvers can replace them programmatically.
4. **Extensible resolver** — `classify_source()` categorizes references by type. Adding PBRER or literature resolvers later requires only new functions, no pipeline changes.
5. **Reuse pdf_extractor** — IB PDFs have the same dotted-decimal heading structure as DSR PDFs. No need for a separate extraction approach.

## Out of Scope (Future Work)

- Resolvers for PBRER, UpToDate, Medline/Embase, company safety database
- LLM-assisted summarization of IB content
- Validation that populated content matches template expectations
