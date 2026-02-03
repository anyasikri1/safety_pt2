# IB Reader & Template Populator — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Read an IB PDF, extract its sections, and populate a filled-in regulatory template document by resolving source references like "IB 2.3" to verbatim IB content.

**Architecture:** Three new modules (`ib_extractor`, `ib_resolver`, `template_populator`) added to the existing `dsr-clone/src/` package. The IB extractor reuses the existing `pdf_extractor` logic. The resolver classifies source references and looks up IB sections. The populator walks template sections and assembles a single filled document. CLI gets a new `--ib` flag.

**Tech Stack:** Python 3.11+, PyMuPDF (existing), python-docx (new), pydantic (existing)

**Design doc:** `docs/plans/2026-02-03-ib-populator-design.md`

---

### Task 1: Add python-docx dependency

**Files:**
- Modify: `dsr-clone/requirements.txt`

**Step 1: Add python-docx to requirements.txt**

Add `python-docx>=0.8.11` as a new line at the end of `dsr-clone/requirements.txt`.

**Step 2: Install dependencies**

Run: `pip install -r dsr-clone/requirements.txt`
Expected: All packages install successfully, including python-docx.

**Step 3: Commit**

```bash
git add dsr-clone/requirements.txt
git commit -m "deps: add python-docx for filled template .docx generation"
```

---

### Task 2: Create ib_resolver.py — source classification and IB lookup

This is the core logic module. No PDF dependency — it operates on a `dict[str, str]` of IB sections.

**Files:**
- Create: `dsr-clone/src/ib_resolver.py`
- Create: `dsr-clone/tests/__init__.py`
- Create: `dsr-clone/tests/test_ib_resolver.py`

**Step 1: Create tests directory and write failing tests**

Create `dsr-clone/tests/__init__.py` (empty).

Create `dsr-clone/tests/test_ib_resolver.py`:

```python
"""Tests for ib_resolver: source classification and IB content lookup."""

from src.ib_resolver import classify_source, resolve_sources


class TestClassifySource:
    def test_ib_with_section_number(self):
        assert classify_source("IB 2.3") == ("ib", "2.3")

    def test_ib_section_keyword(self):
        assert classify_source("IB Section 4.3.3") == ("ib", "4.3.3")

    def test_ib_bare(self):
        assert classify_source("IB") == ("ib", None)

    def test_ib_case_insensitive(self):
        assert classify_source("ib 6.1") == ("ib", "6.1")

    def test_ib_with_extra_spaces(self):
        assert classify_source("  IB  2.3  ") == ("ib", "2.3")

    def test_pbrer_reference(self):
        source_type, _ = classify_source("PBRER Section 5")
        assert source_type == "pbrer"

    def test_external_uptodate(self):
        source_type, _ = classify_source("UpToDate")
        assert source_type == "external"

    def test_external_medline(self):
        source_type, _ = classify_source("Medline")
        assert source_type == "external"

    def test_company_safety_database(self):
        source_type, _ = classify_source("Company safety database")
        assert source_type == "external"

    def test_unknown_source(self):
        source_type, _ = classify_source("Some random text")
        assert source_type == "unknown"

    def test_signal_assessment(self):
        source_type, _ = classify_source("Signal assessment")
        assert source_type == "external"


class TestResolveSources:
    """Test resolve_sources which takes a list of required_sources and an IB index."""

    def setup_method(self):
        self.ib_index = {
            "2.3": "Pralsetinib is a kinase inhibitor targeting RET...",
            "1.2": "Available as 100mg capsules...",
            "3.2": "Detailed formulation data: excipients include...",
            "6.1": "Approved indications: RET-positive NSCLC...",
            "4.3.3": "In a 28-day toxicology study in rats...",
        }

    def test_single_ib_ref_found(self):
        results = resolve_sources(["IB 2.3"], self.ib_index)
        assert len(results) == 1
        assert results[0].source_type == "ib"
        assert results[0].content == self.ib_index["2.3"]
        assert results[0].found is True

    def test_single_ib_ref_not_found(self):
        results = resolve_sources(["IB 99.9"], self.ib_index)
        assert len(results) == 1
        assert results[0].found is False
        assert "CONTENT NOT FOUND" in results[0].content

    def test_multiple_ib_refs(self):
        results = resolve_sources(["IB 2.3", "IB 1.2", "IB 3.2"], self.ib_index)
        assert len(results) == 3
        assert all(r.found for r in results)

    def test_non_ib_ref_placeholder(self):
        results = resolve_sources(["PBRER Section 5"], self.ib_index)
        assert len(results) == 1
        assert results[0].found is False
        assert "MANUAL INPUT REQUIRED" in results[0].content

    def test_bare_ib_placeholder(self):
        results = resolve_sources(["IB"], self.ib_index)
        assert len(results) == 1
        assert results[0].found is False
        assert "MANUAL INPUT REQUIRED" in results[0].content

    def test_empty_sources(self):
        results = resolve_sources([], self.ib_index)
        assert results == []

    def test_mixed_ib_and_non_ib(self):
        results = resolve_sources(["IB 6.1", "UpToDate"], self.ib_index)
        assert len(results) == 2
        assert results[0].found is True
        assert results[1].found is False
        assert "MANUAL INPUT REQUIRED" in results[1].content
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m pytest tests/test_ib_resolver.py -v`
Expected: ImportError — `src.ib_resolver` does not exist yet.

**Step 3: Write the implementation**

Create `dsr-clone/src/ib_resolver.py`:

```python
"""Resolve template source references against an IB section index.

Classifies each required_source string (e.g. "IB 2.3", "PBRER Section 5")
and looks up IB content when applicable. Non-IB sources get placeholder text
for future resolver expansion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Regex: "IB" optionally followed by "Section" and a dotted-decimal number
_IB_RE = re.compile(
    r"^\s*IB\s*(?:Section\s*)?(\d+(?:\.\d+)*)\s*$",
    re.IGNORECASE,
)
_IB_BARE_RE = re.compile(r"^\s*IB\s*$", re.IGNORECASE)

_PBRER_RE = re.compile(r"PBRER", re.IGNORECASE)

_EXTERNAL_KEYWORDS = [
    "UpToDate", "Medline", "Embase", "Company safety database",
    "Signal assessment",
]


def classify_source(source: str) -> tuple[str, str | None]:
    """Classify a required_source string and extract section number if applicable.

    Returns (source_type, section_num_or_none).
    source_type is one of: "ib", "pbrer", "external", "unknown".
    """
    m = _IB_RE.match(source)
    if m:
        return ("ib", m.group(1))

    if _IB_BARE_RE.match(source):
        return ("ib", None)

    if _PBRER_RE.search(source):
        return ("pbrer", None)

    for kw in _EXTERNAL_KEYWORDS:
        if kw.lower() in source.lower():
            return ("external", None)

    return ("unknown", None)


@dataclass
class ResolvedSource:
    """Result of resolving one source reference."""

    original_ref: str
    source_type: str
    section_num: str | None
    content: str
    found: bool


def resolve_sources(
    required_sources: list[str],
    ib_index: dict[str, str],
) -> list[ResolvedSource]:
    """Resolve a list of required_source strings against an IB section index.

    For IB references with a section number: look up verbatim content.
    For bare IB, non-IB, or unknown references: return placeholder text.
    """
    results: list[ResolvedSource] = []

    for src in required_sources:
        source_type, section_num = classify_source(src)

        if source_type == "ib" and section_num is not None:
            content = ib_index.get(section_num)
            if content is not None:
                results.append(ResolvedSource(
                    original_ref=src,
                    source_type=source_type,
                    section_num=section_num,
                    content=content,
                    found=True,
                ))
            else:
                results.append(ResolvedSource(
                    original_ref=src,
                    source_type=source_type,
                    section_num=section_num,
                    content=f"[CONTENT NOT FOUND: {src}]",
                    found=False,
                ))
        elif source_type == "ib" and section_num is None:
            results.append(ResolvedSource(
                original_ref=src,
                source_type=source_type,
                section_num=None,
                content="[MANUAL INPUT REQUIRED: IB — no specific section referenced]",
                found=False,
            ))
        else:
            results.append(ResolvedSource(
                original_ref=src,
                source_type=source_type,
                section_num=None,
                content=f"[MANUAL INPUT REQUIRED: {src}]",
                found=False,
            ))

    return results
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m pytest tests/test_ib_resolver.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add dsr-clone/src/ib_resolver.py dsr-clone/tests/__init__.py dsr-clone/tests/test_ib_resolver.py
git commit -m "feat: add ib_resolver with source classification and IB lookup"
```

---

### Task 3: Create ib_extractor.py — extract IB PDF into section index

**Files:**
- Create: `dsr-clone/src/ib_extractor.py`
- Create: `dsr-clone/tests/test_ib_extractor.py`

**Step 1: Write failing tests**

Create `dsr-clone/tests/test_ib_extractor.py`:

```python
"""Tests for ib_extractor: IB PDF section extraction to dict index."""

from unittest.mock import patch, MagicMock
from src.ib_extractor import build_ib_index, _sections_to_index


class TestSectionsToIndex:
    """Test the conversion from DSRSection list to dict index."""

    def test_basic_indexing(self):
        from src.models import DSRSection
        sections = [
            DSRSection(section_num="2.3", title="Pharmacology", content="Drug MOA text"),
            DSRSection(section_num="1.2", title="Formulation", content="Capsule info"),
        ]
        index = _sections_to_index(sections)
        assert index["2.3"] == "Drug MOA text"
        assert index["1.2"] == "Capsule info"

    def test_empty_sections(self):
        index = _sections_to_index([])
        assert index == {}

    def test_duplicate_section_num_keeps_last(self):
        from src.models import DSRSection
        sections = [
            DSRSection(section_num="2.3", title="First", content="First content"),
            DSRSection(section_num="2.3", title="Second", content="Second content"),
        ]
        index = _sections_to_index(sections)
        assert index["2.3"] == "Second content"
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m pytest tests/test_ib_extractor.py -v`
Expected: ImportError — `src.ib_extractor` does not exist yet.

**Step 3: Write the implementation**

Create `dsr-clone/src/ib_extractor.py`:

```python
"""Extract sections from an Investigator's Brochure PDF.

Reuses the pdf_extractor logic (HEADING_RE, _detect_sections) to split the
IB into sections, then returns a dict mapping section_num -> content for
fast lookup by ib_resolver.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from .models import DSRSection
from .pdf_extractor import HEADING_RE, _detect_sections, _is_valid_section_num
from .utils import logger


def _sections_to_index(sections: list[DSRSection]) -> dict[str, str]:
    """Convert a list of DSRSection objects to a {section_num: content} dict."""
    return {s.section_num: s.content for s in sections}


def build_ib_index(ib_pdf_path: Path) -> dict[str, str]:
    """Extract an IB PDF and return a section_num -> content index.

    Uses the same heading regex and section detection as the DSR pdf_extractor.
    No API calls — pure regex-based extraction.
    """
    logger.info("Extracting IB PDF: %s", ib_pdf_path.name)
    doc = fitz.open(str(ib_pdf_path))

    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    logger.info("Extracted %d pages from IB", len(pages))

    # Reuse TOC extraction for validation
    doc2 = fitz.open(str(ib_pdf_path))
    toc = doc2.get_toc()
    doc2.close()
    toc_sections: set[str] = set()
    if toc:
        import re
        for level, title, page_num in toc:
            m = re.match(r"^(\d+(?:\.\d+)*)\s+", title)
            if m:
                toc_sections.add(m.group(1))
        logger.info("IB TOC found with %d entries", len(toc_sections))

    sections = _detect_sections(pages, toc_sections)
    logger.info("Detected %d IB sections", len(sections))

    index = _sections_to_index(sections)
    return index
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m pytest tests/test_ib_extractor.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add dsr-clone/src/ib_extractor.py dsr-clone/tests/test_ib_extractor.py
git commit -m "feat: add ib_extractor to build section index from IB PDF"
```

---

### Task 4: Create template_populator.py — assemble filled template

**Files:**
- Create: `dsr-clone/src/template_populator.py`
- Create: `dsr-clone/tests/test_template_populator.py`

**Step 1: Write failing tests**

Create `dsr-clone/tests/test_template_populator.py`:

```python
"""Tests for template_populator: assemble filled template from resolved sources."""

from pathlib import Path
from src.models import TemplateSection
from src.template_populator import assemble_markdown


class TestAssembleMarkdown:
    def setup_method(self):
        self.ib_index = {
            "2.3": "Pralsetinib is a kinase inhibitor targeting RET.",
            "1.2": "Available as 100mg capsules.",
            "3.2": "Detailed formulation: excipients include...",
            "6.1": "Approved for RET-positive NSCLC.",
        }

    def test_single_ib_ref_populated(self):
        sections = [
            TemplateSection(
                section_id="2.1.2",
                title="Therapeutic Indications",
                body="",
                required_sources=["IB 6.1"],
            ),
        ]
        md = assemble_markdown(sections, self.ib_index)
        assert "## 2.1.2 Therapeutic Indications" in md
        assert "Approved for RET-positive NSCLC." in md
        assert "IB 6.1" in md

    def test_multiple_ib_refs_get_subheadings(self):
        sections = [
            TemplateSection(
                section_id="2.1.1",
                title="Drug Pharmacology",
                body="",
                required_sources=["IB 2.3", "IB 1.2", "IB 3.2"],
            ),
        ]
        md = assemble_markdown(sections, self.ib_index)
        assert "### From IB 2.3" in md
        assert "### From IB 1.2" in md
        assert "### From IB 3.2" in md
        assert "Pralsetinib is a kinase inhibitor" in md
        assert "100mg capsules" in md

    def test_non_ib_ref_gets_placeholder(self):
        sections = [
            TemplateSection(
                section_id="2.1.3",
                title="Patient exposure",
                body="",
                required_sources=["PBRER Section 5"],
            ),
        ]
        md = assemble_markdown(sections, self.ib_index)
        assert "[MANUAL INPUT REQUIRED: PBRER Section 5]" in md

    def test_no_sources_keeps_body(self):
        sections = [
            TemplateSection(
                section_id="4",
                title="Discussion",
                body="Discuss findings here.",
                required_sources=[],
            ),
        ]
        md = assemble_markdown(sections, self.ib_index)
        assert "## 4 Discussion" in md
        assert "Discuss findings here." in md

    def test_ib_ref_not_found(self):
        sections = [
            TemplateSection(
                section_id="3.1",
                title="Review of toxicology data",
                body="",
                required_sources=["IB Section 4.3.3"],
            ),
        ]
        md = assemble_markdown(sections, self.ib_index)
        assert "[CONTENT NOT FOUND: IB Section 4.3.3]" in md

    def test_bare_ib_gets_placeholder(self):
        sections = [
            TemplateSection(
                section_id="2.1",
                title="Product Background",
                body="",
                required_sources=["IB"],
            ),
        ]
        md = assemble_markdown(sections, self.ib_index)
        assert "[MANUAL INPUT REQUIRED: IB" in md

    def test_full_document_structure(self):
        sections = [
            TemplateSection(section_id="1", title="Introduction", body="Intro text.", required_sources=[]),
            TemplateSection(section_id="2", title="Background", body="", required_sources=[]),
            TemplateSection(section_id="2.1.1", title="Drug Pharmacology", body="", required_sources=["IB 2.3"]),
        ]
        md = assemble_markdown(sections, self.ib_index)
        # Verify document ordering
        intro_pos = md.index("Introduction")
        bg_pos = md.index("Background")
        pharm_pos = md.index("Drug Pharmacology")
        assert intro_pos < bg_pos < pharm_pos
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m pytest tests/test_template_populator.py -v`
Expected: ImportError — `src.template_populator` does not exist yet.

**Step 3: Write the implementation**

Create `dsr-clone/src/template_populator.py`:

```python
"""Assemble a filled regulatory template from parsed sections and IB content.

Walks the template section list, resolves source references via ib_resolver,
and produces a single markdown document. Optionally converts to .docx.
"""

from __future__ import annotations

from pathlib import Path

from .ib_resolver import resolve_sources
from .models import TemplateSection
from .utils import ensure_dir, logger


def _heading_level(section_id: str) -> int:
    """Determine markdown heading level from section_id depth.

    "1" -> ##, "2.1" -> ###, "2.1.1" -> ####, etc.
    Non-numeric ids (e.g. "Executive Summary") -> ##.
    """
    parts = section_id.split(".")
    try:
        [int(p) for p in parts]
        # Numeric: depth 1 = ##, depth 2 = ###, etc.
        return min(len(parts) + 1, 6)
    except ValueError:
        return 2


def assemble_markdown(
    template_sections: list[TemplateSection],
    ib_index: dict[str, str],
) -> str:
    """Build a single markdown document from template sections and IB content.

    For each template section:
    - If it has IB source refs: resolve them and insert content
    - If it has non-IB refs: insert placeholder
    - If no sources: keep the template body as-is
    """
    lines: list[str] = []
    lines.append("# Filled Signal Assessment Report")
    lines.append("")

    for section in template_sections:
        level = _heading_level(section.section_id)
        heading = "#" * level + f" {section.section_id} {section.title}"
        lines.append(heading)
        lines.append("")

        if not section.required_sources:
            # No sources — keep template body
            if section.body.strip():
                lines.append(section.body.strip())
                lines.append("")
            continue

        resolved = resolve_sources(section.required_sources, ib_index)

        if len(resolved) == 1:
            r = resolved[0]
            lines.append(f"*Source: {r.original_ref}*")
            lines.append("")
            lines.append(r.content)
            lines.append("")
        else:
            for r in resolved:
                sub_heading = "#" * min(level + 1, 6) + f" From {r.original_ref}"
                lines.append(sub_heading)
                lines.append("")
                lines.append(r.content)
                lines.append("")

    return "\n".join(lines)


def write_filled_template(
    template_sections: list[TemplateSection],
    ib_index: dict[str, str],
    output_dir: Path,
) -> dict[str, Path]:
    """Generate filled_template.md and filled_template.docx.

    Returns dict with keys "md" and "docx" pointing to output paths.
    """
    md_content = assemble_markdown(template_sections, ib_index)

    out = ensure_dir(output_dir)
    md_path = out / "filled_template.md"
    md_path.write_text(md_content, encoding="utf-8")
    logger.info("Written: %s", md_path)

    # Convert to .docx
    docx_path = out / "filled_template.docx"
    _markdown_to_docx(md_content, docx_path)
    logger.info("Written: %s", docx_path)

    return {"md": md_path, "docx": docx_path}


def _markdown_to_docx(md_content: str, output_path: Path) -> None:
    """Convert markdown string to a .docx file using python-docx."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()

    for line in md_content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Heading detection
        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            text = stripped.lstrip("#").strip()
            level = min(hashes, 9)  # python-docx supports heading levels 0-9
            doc.add_heading(text, level=level)
        elif stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            # Italic source label
            p = doc.add_paragraph()
            run = p.add_run(stripped.strip("*"))
            run.italic = True
            run.font.size = Pt(10)
        elif stripped.startswith("[MANUAL INPUT REQUIRED:") or stripped.startswith("[CONTENT NOT FOUND:"):
            # Placeholder — style distinctly
            p = doc.add_paragraph()
            run = p.add_run(stripped)
            run.bold = True
            run.font.size = Pt(10)
        else:
            doc.add_paragraph(stripped)

    doc.save(str(output_path))
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m pytest tests/test_template_populator.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add dsr-clone/src/template_populator.py dsr-clone/tests/test_template_populator.py
git commit -m "feat: add template_populator to assemble filled template .md and .docx"
```

---

### Task 5: Wire into CLI — add --ib flag and population step

**Files:**
- Modify: `dsr-clone/src/cli.py`
- Modify: `dsr-clone/src/config.py`

**Step 1: Add ib_path to Config**

In `dsr-clone/src/config.py`, add a new field after `pdf_path`:

```python
ib_path: Path = field(default_factory=lambda: Path("data/input/ib.pdf"))
```

**Step 2: Add --ib argument to both subcommands in cli.py**

In `build_parser()`, add to both `sp_sections` and `sp_pdf` (after `--template`):

```python
sp_sections.add_argument(
    "--ib", required=True,
    help="Path to Investigator's Brochure PDF",
)
```

```python
sp_pdf.add_argument(
    "--ib", required=True,
    help="Path to Investigator's Brochure PDF",
)
```

**Step 3: Update cmd_from_sections to use IB**

In `cmd_from_sections`, after the `Config.from_env(...)` call, add `ib_path=Path(args.ib)` to the overrides.

After Step 4 (generate deliverables), add Step 4b:

```python
# Step 4b: Populate filled template from IB
logger.info("Step 4b: Populating filled template from IB")
from .ib_extractor import build_ib_index
from .template_populator import write_filled_template

ib_index = build_ib_index(Path(args.ib))
filled_paths = write_filled_template(
    template_sections, ib_index, config.traced_output_dir,
)
logger.info("Filled template: %s, %s", filled_paths["md"], filled_paths["docx"])
```

**Step 4: Update cmd_from_pdf with same IB logic**

Same as Step 3, add `ib_path=Path(args.ib)` to config and add the Step 4b block after deliverable generation.

**Step 5: Run full test suite**

Run: `cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m pytest tests/ -v`
Expected: All tests PASS.

**Step 6: Commit**

```bash
git add dsr-clone/src/cli.py dsr-clone/src/config.py
git commit -m "feat: wire IB extraction and template population into CLI"
```

---

### Task 6: Integration test — run with real IB PDF

**Files:**
- No new files — manual verification

**Step 1: Run the tool with the Gavreto IB**

Run from the project root:

```bash
cd /Users/anyasikri/Downloads/rigel/safety_DSR_project/dsr-clone && python -m src.cli from-sections \
    --sections-dir ../dsr_sections/dsr_sections \
    --index-csv ../dsr_sections_index.csv \
    --template ../signal_assessment_template.txt \
    --ib "../Published Report - Investigator Brochure  RO7499790 (pralsetinib) 11.pdf" \
    --scope "1.1-1.2.2.4" \
    --output-dir ../data/mappings \
    --dry-run
```

Expected: Tool runs, extracts IB sections, produces `filled_template.md` and `filled_template.docx` in `data/output/`.

**Step 2: Inspect filled_template.md**

Verify:
- Section 2.1.1 has content from IB 2.3, IB 1.2, IB 3.2
- Section 2.1.2 has content from IB 6.1
- Section 3.1 has content from IB Section 4.3.3
- Section 2.1.3 has `[MANUAL INPUT REQUIRED: PBRER Section 5]`
- Section 2.2 has `[MANUAL INPUT REQUIRED: UpToDate]`

**Step 3: Inspect filled_template.docx**

Open in Word/Pages and verify headings, content, and placeholders render correctly.

**Step 4: Commit any fixes if needed**

```bash
git add -A
git commit -m "fix: integration adjustments from real IB test"
```
