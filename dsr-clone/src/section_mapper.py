"""3-pass section mapping: exact → fuzzy → API-assisted.

Maps DSR sections to template sections using progressively more
expensive matching strategies. Only unmatched sections after pass 2
are sent to the API.
"""

from __future__ import annotations

import json
import re

from .models import DSRSection, SectionMapping, TemplateSection
from .openai_client import LLMClient
from .utils import logger


def _normalize(s: str) -> str:
    """Lowercase, strip punctuation/whitespace for comparison."""
    return re.sub(r"[^a-z0-9\s]", "", s.lower()).strip()


def _keyword_overlap(a: str, b: str) -> float:
    """Fraction of words in common between two normalized strings."""
    words_a = set(_normalize(a).split())
    words_b = set(_normalize(b).split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


# --------------------------------------------------------------------------
# Pass 1: Exact title match
# --------------------------------------------------------------------------

def _pass_exact(
    dsr_sections: list[DSRSection],
    template_sections: list[TemplateSection],
    mappings: dict[str, SectionMapping],
) -> None:
    """Case-insensitive exact title match."""
    tmpl_by_title: dict[str, TemplateSection] = {}
    for t in template_sections:
        tmpl_by_title[_normalize(t.title)] = t

    for d in dsr_sections:
        if d.section_num in mappings:
            continue
        norm_title = _normalize(d.title)
        if norm_title in tmpl_by_title:
            t = tmpl_by_title[norm_title]
            mappings[d.section_num] = SectionMapping(
                dsr_section=d.section_num,
                dsr_title=d.title,
                dsr_file=d.file,
                template_section=t.section_id,
                template_title=t.title,
                match_method="exact_title",
                notes="Exact title match",
            )
            logger.debug("Pass 1 exact match: DSR %s → Template %s", d.section_num, t.section_id)


# --------------------------------------------------------------------------
# Pass 2: Fuzzy/keyword title match
# --------------------------------------------------------------------------

FUZZY_THRESHOLD = 0.5


def _pass_fuzzy(
    dsr_sections: list[DSRSection],
    template_sections: list[TemplateSection],
    mappings: dict[str, SectionMapping],
) -> None:
    """Keyword overlap matching for unmatched sections."""
    for d in dsr_sections:
        if d.section_num in mappings:
            continue
        best_score = 0.0
        best_tmpl: TemplateSection | None = None
        for t in template_sections:
            score = _keyword_overlap(d.title, t.title)
            if score > best_score:
                best_score = score
                best_tmpl = t
        if best_tmpl and best_score >= FUZZY_THRESHOLD:
            mappings[d.section_num] = SectionMapping(
                dsr_section=d.section_num,
                dsr_title=d.title,
                dsr_file=d.file,
                template_section=best_tmpl.section_id,
                template_title=best_tmpl.title,
                match_method="title_match",
                notes=f"Fuzzy keyword match (score={best_score:.2f})",
            )
            logger.debug(
                "Pass 2 fuzzy match: DSR %s → Template %s (%.2f)",
                d.section_num, best_tmpl.section_id, best_score,
            )


# --------------------------------------------------------------------------
# Pass 3: API-assisted match
# --------------------------------------------------------------------------

API_MATCH_SYSTEM = """\
You are a regulatory document mapping specialist. Given a list of \
unmatched DSR sections and a list of template sections, determine the \
best mapping for each DSR section.

Return a JSON object with key "matches" containing a list of objects:
  - "dsr_section": the DSR section number
  - "template_section": the best-matching template section_id, or null \
if no reasonable match exists
  - "template_title": the template section title, or null
  - "match_method": one of "conceptual_match", "content_match", or "no_match"
  - "notes": brief explanation of why this mapping was chosen

Rules:
1. Only map sections that have a genuine conceptual relationship.
2. If no good match exists, set template_section to null and \
match_method to "no_match".
3. Multiple DSR sections may map to the same template section.
4. Do not force mappings. Be honest about mismatches.\
"""


def _pass_api(
    dsr_sections: list[DSRSection],
    template_sections: list[TemplateSection],
    mappings: dict[str, SectionMapping],
    llm: LLMClient,
) -> None:
    """API-assisted matching for remaining unmatched sections."""
    unmatched = [d for d in dsr_sections if d.section_num not in mappings]
    if not unmatched:
        logger.info("Pass 3: No unmatched sections — skipping API call")
        return

    logger.info("Pass 3: %d unmatched sections → API-assisted matching", len(unmatched))

    user_data = {
        "unmatched_dsr_sections": [
            {"section_num": d.section_num, "title": d.title}
            for d in unmatched
        ],
        "template_sections": [
            {"section_id": t.section_id, "title": t.title}
            for t in template_sections
        ],
    }

    result = llm.call_json(
        system_prompt=API_MATCH_SYSTEM,
        user_prompt=json.dumps(user_data, indent=2),
        label="section_mapping",
    )

    for m in result.get("matches", []):
        dsn = m.get("dsr_section", "")
        if not dsn or dsn in mappings:
            continue
        # Find the original DSR section for file info
        dsr_obj = next((d for d in unmatched if d.section_num == dsn), None)
        mappings[dsn] = SectionMapping(
            dsr_section=dsn,
            dsr_title=dsr_obj.title if dsr_obj else "",
            dsr_file=dsr_obj.file if dsr_obj else "",
            template_section=m.get("template_section"),
            template_title=m.get("template_title"),
            match_method=m.get("match_method", "no_match"),
            notes=m.get("notes", ""),
        )


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def map_sections(
    dsr_sections: list[DSRSection],
    template_sections: list[TemplateSection],
    llm: LLMClient,
) -> list[SectionMapping]:
    """Run 3-pass mapping and return ordered list of SectionMapping objects."""
    mappings: dict[str, SectionMapping] = {}

    _pass_exact(dsr_sections, template_sections, mappings)
    logger.info("After pass 1 (exact): %d mapped", len(mappings))

    _pass_fuzzy(dsr_sections, template_sections, mappings)
    logger.info("After pass 2 (fuzzy): %d mapped", len(mappings))

    _pass_api(dsr_sections, template_sections, mappings, llm)
    logger.info("After pass 3 (API): %d mapped", len(mappings))

    # Ensure every DSR section has an entry
    for d in dsr_sections:
        if d.section_num not in mappings:
            mappings[d.section_num] = SectionMapping(
                dsr_section=d.section_num,
                dsr_title=d.title,
                dsr_file=d.file,
                template_section=None,
                template_title=None,
                match_method="no_match",
                notes="No template analog identified",
            )

    # Return in DSR section order
    section_order = [d.section_num for d in dsr_sections]
    return [mappings[sn] for sn in section_order if sn in mappings]
