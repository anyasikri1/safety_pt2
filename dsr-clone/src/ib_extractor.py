"""IB (Investigator's Brochure) PDF to section index.

Extracts sections from an IB PDF using the same regex-based detection
logic as ``pdf_extractor`` and returns a flat ``{section_num: content}``
dict.  No API calls — pure local extraction.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz  # PyMuPDF

from .models import DSRSection
from .pdf_extractor import HEADING_RE, _detect_sections, _is_valid_section_num
from .utils import logger


def _sections_to_index(sections: list[DSRSection]) -> dict[str, str]:
    """Convert a list of DSRSection objects to a ``{section_num: content}`` dict.

    If duplicate ``section_num`` values exist the *last* entry wins.
    """
    index: dict[str, str] = {}
    for section in sections:
        index[section.section_num] = section.content
    return index


def build_ib_index(ib_pdf_path: Path) -> dict[str, str]:
    """Extract an IB PDF and return a section-number-to-content index.

    Steps
    -----
    1. Open the PDF with PyMuPDF and extract text page-by-page.
    2. Optionally read the document TOC for validation.
    3. Detect section boundaries via ``_detect_sections`` (reused from
       ``pdf_extractor``).
    4. Convert the resulting list of ``DSRSection`` objects to a flat
       ``{section_num: content}`` dict via ``_sections_to_index``.

    No API calls are made — this is pure regex extraction.
    """
    logger.info("Building IB index from: %s", ib_pdf_path.name)

    # --- Step 1: Extract full text page by page ---
    doc = fitz.open(str(ib_pdf_path))
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    logger.info("Extracted %d pages from IB", len(pages))

    # --- Step 2: Optional TOC extraction for validation ---
    doc2 = fitz.open(str(ib_pdf_path))
    toc = doc2.get_toc()
    doc2.close()

    toc_sections: set[str] = set()
    if toc:
        for _level, title, _page_num in toc:
            m = re.match(r"^(\d+(?:\.\d+)*)\s+", title)
            if m:
                toc_sections.add(m.group(1))
        logger.info("IB TOC found with %d entries for validation", len(toc_sections))

    # --- Step 3: Detect section boundaries ---
    sections = _detect_sections(pages, toc_sections)
    logger.info("Detected %d sections in IB", len(sections))

    # --- Step 4: Convert to index dict ---
    index = _sections_to_index(sections)
    logger.info("IB index built with %d entries", len(index))

    return index
