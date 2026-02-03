"""Source classification and IB section lookup.

Classifies template source references (IB, PBRER, external databases)
and resolves IB references against a pre-built section index.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

# Regex for IB references with an optional "Section" keyword and a dotted number.
_IB_SECTION_RE = re.compile(
    r"^\s*IB\s*(?:Section\s*)?(\d+(?:\.\d+)*)\s*$",
    re.IGNORECASE,
)

# Regex for bare "IB" (no section number).
_IB_BARE_RE = re.compile(r"^\s*IB\s*$", re.IGNORECASE)

# Known external source keywords (substring-matched, case-insensitive).
_EXTERNAL_KEYWORDS = [
    "uptodate",
    "medline",
    "embase",
    "company safety database",
    "signal assessment",
]


def classify_source(source: str) -> Tuple[str, Optional[str]]:
    """Classify a required_source string into a type and optional section number.

    Returns:
        A ``(source_type, section_number)`` tuple where *source_type* is one of
        ``"ib"``, ``"pbrer"``, ``"external"``, or ``"unknown"``; and
        *section_number* is a dotted-decimal string for IB refs or ``None``.
    """
    # Try IB with section number first.
    m = _IB_SECTION_RE.match(source)
    if m:
        return ("ib", m.group(1))

    # Bare IB.
    if _IB_BARE_RE.match(source):
        return ("ib", None)

    # PBRER (case-insensitive, may include trailing text like "Section 5").
    stripped = source.strip()
    if stripped.lower().startswith("pbrer"):
        return ("pbrer", None)

    # Known external sources (substring match for flexibility).
    lower = stripped.lower()
    for kw in _EXTERNAL_KEYWORDS:
        if kw in lower:
            return ("external", None)

    return ("unknown", None)


@dataclass
class ResolvedSource:
    """Result of resolving a single source reference."""

    original_ref: str
    source_type: str
    section_num: Optional[str]
    content: str
    found: bool


def resolve_sources(
    required_sources: list[str],
    ib_index: dict[str, str],
) -> list[ResolvedSource]:
    """Resolve a list of source references against an IB section index.

    For IB references whose section number exists in *ib_index*, the
    corresponding text is returned with ``found=True``.  All other
    references produce placeholder strings with ``found=False``.
    """
    if not required_sources:
        return []

    results: list[ResolvedSource] = []
    for ref in required_sources:
        source_type, section_num = classify_source(ref)

        if source_type == "ib":
            if section_num is not None:
                # IB with a specific section number.
                text = ib_index.get(section_num)
                if text is not None:
                    results.append(
                        ResolvedSource(
                            original_ref=ref,
                            source_type=source_type,
                            section_num=section_num,
                            content=text,
                            found=True,
                        )
                    )
                else:
                    results.append(
                        ResolvedSource(
                            original_ref=ref,
                            source_type=source_type,
                            section_num=section_num,
                            content=f"[CONTENT NOT FOUND: {ref.strip()}]",
                            found=False,
                        )
                    )
            else:
                # Bare "IB" -- no section number.
                results.append(
                    ResolvedSource(
                        original_ref=ref,
                        source_type=source_type,
                        section_num=None,
                        content="[MANUAL INPUT REQUIRED: IB \u2014 no specific section referenced]",
                        found=False,
                    )
                )
        else:
            # Non-IB source (PBRER, external, unknown).
            results.append(
                ResolvedSource(
                    original_ref=ref,
                    source_type=source_type,
                    section_num=None,
                    content=f"[MANUAL INPUT REQUIRED: {ref.strip()}]",
                    found=False,
                )
            )

    return results
