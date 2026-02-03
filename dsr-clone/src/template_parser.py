"""Parse a regulatory template .txt into TemplateSection objects.

Uses two API calls:
  1. Section identification (structure extraction)
  2. Verbatim source extraction per section

Post-extraction validation ensures every extracted source appears as an
exact substring in the template text. Results are cached to
data/intermediate/ to avoid redundant API calls on re-runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .config import Config
from .models import TemplateSection
from .openai_client import LLMClient
from .utils import ensure_dir, logger


def _template_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _load_cache(cache_path: Path) -> list[TemplateSection] | None:
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        return [TemplateSection(**s) for s in data["sections"]]
    except Exception:
        return None


def _save_cache(cache_path: Path, sections: list[TemplateSection], text_hash: str) -> None:
    data = {
        "text_hash": text_hash,
        "sections": [s.model_dump() for s in sections],
    }
    cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------
# API prompts
# --------------------------------------------------------------------------

SECTION_ID_SYSTEM = """\
You are a regulatory document parser. Given the full text of a regulatory \
template, identify every discrete section. Return a JSON object with key \
"sections" containing a list of objects, each with:
  - "section_id": the section number or identifier (e.g. "2.1.1", \
"Executive Summary", "Appendices")
  - "title": the section heading
  - "body": the full text belonging to that section (everything until \
the next section heading)

Include ALL sections, even those with minimal body text. Preserve the \
exact wording of headings and body text. Do not infer, merge, or skip \
sections. If a section has sub-sections, list each sub-section as its \
own entry AND include the parent section.\
"""

SOURCE_EXTRACT_SYSTEM = """\
You are a regulatory compliance specialist. For each template section \
provided, extract ONLY the sources that are EXPLICITLY named in the \
template text.

RULES — follow these exactly:
1. Copy each source reference VERBATIM from the template text.
2. Do NOT expand abbreviations (e.g. keep "IB 2.3" not \
"Investigator's Brochure section 2.3").
3. Do NOT infer sources from industry conventions or your own knowledge.
4. Do NOT add sources that are not literally written in the section text.
5. If no source is explicitly named, return an empty list.
6. Include a "notes" field with a brief factual statement about what \
the template says (start with "Template states:").

Return a JSON object with key "sections" containing a list of objects:
  - "section_id": matching the input section_id
  - "required_sources": list of verbatim source strings
  - "notes": factual note about what the template states\
"""


def parse_template(
    template_path: Path,
    config: Config,
    llm: LLMClient,
) -> list[TemplateSection]:
    """Parse a template .txt file into TemplateSection objects.

    Checks cache first; only calls the API if the template has changed.
    """
    text = template_path.read_text(encoding="utf-8")
    text_hash = _template_hash(text)
    cache_dir = ensure_dir(config.intermediate_dir)
    cache_path = cache_dir / f"parsed_template_{text_hash}.json"

    cached = _load_cache(cache_path)
    if cached is not None:
        logger.info("Using cached template parse (%d sections)", len(cached))
        return cached

    logger.info("Parsing template: %s", template_path.name)

    # --- Call 1: identify sections ---
    section_data = llm.call_json(
        system_prompt=SECTION_ID_SYSTEM,
        user_prompt=text,
        label="template_sections",
    )
    raw_sections = section_data.get("sections", [])
    logger.info("Identified %d template sections", len(raw_sections))

    # Build user prompt for source extraction with section bodies
    sections_for_source = json.dumps(
        [
            {
                "section_id": s.get("section_id", ""),
                "title": s.get("title", ""),
                "body": s.get("body", ""),
            }
            for s in raw_sections
        ],
        indent=2,
    )

    # --- Call 2: extract sources ---
    source_data = llm.call_json(
        system_prompt=SOURCE_EXTRACT_SYSTEM,
        user_prompt=sections_for_source,
        label="template_sources",
    )
    source_map: dict[str, dict] = {}
    for s in source_data.get("sections", []):
        source_map[s.get("section_id", "")] = s

    # --- Merge and validate ---
    sections: list[TemplateSection] = []
    for raw in raw_sections:
        sid = raw.get("section_id", "")
        src_info = source_map.get(sid, {})
        raw_sources = src_info.get("required_sources", [])

        # Post-extraction validation: every source must appear verbatim
        validated_sources: list[str] = []
        for src in raw_sources:
            if src in text:
                validated_sources.append(src)
            else:
                logger.warning(
                    "Dropped non-verbatim source '%s' from section %s", src, sid
                )

        section = TemplateSection(
            section_id=sid,
            title=raw.get("title", ""),
            body=raw.get("body", ""),
            required_sources=validated_sources,
            notes=src_info.get("notes", ""),
        )
        sections.append(section)

    logger.info("Template parsing complete: %d sections, sources validated", len(sections))
    _save_cache(cache_path, sections, text_hash)
    return sections
