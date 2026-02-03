"""Tests for ib_resolver: source classification and IB lookup."""

from __future__ import annotations

import pytest

from src.ib_resolver import ResolvedSource, classify_source, resolve_sources


# ---------------------------------------------------------------------------
# classify_source tests
# ---------------------------------------------------------------------------


class TestClassifySource:
    """Tests for classify_source()."""

    def test_ib_with_section_number(self):
        assert classify_source("IB 2.3") == ("ib", "2.3")

    def test_ib_with_deep_section_number(self):
        assert classify_source("IB 4.3.3") == ("ib", "4.3.3")

    def test_ib_section_keyword(self):
        assert classify_source("IB Section 4.3.3") == ("ib", "4.3.3")

    def test_ib_single_digit_section(self):
        assert classify_source("IB 6") == ("ib", "6")

    def test_bare_ib(self):
        assert classify_source("IB") == ("ib", None)

    def test_case_insensitive_lower(self):
        assert classify_source("ib 2.3") == ("ib", "2.3")

    def test_case_insensitive_mixed(self):
        assert classify_source("Ib Section 1.2") == ("ib", "1.2")

    def test_extra_spaces(self):
        assert classify_source("  IB   2.3  ") == ("ib", "2.3")

    def test_extra_spaces_section_keyword(self):
        assert classify_source("  IB   Section   6.1  ") == ("ib", "6.1")

    def test_bare_ib_with_spaces(self):
        assert classify_source("  IB  ") == ("ib", None)

    def test_pbrer(self):
        assert classify_source("PBRER Section 5") == ("pbrer", None)

    def test_pbrer_lowercase(self):
        assert classify_source("pbrer") == ("pbrer", None)

    def test_uptodate(self):
        assert classify_source("UpToDate") == ("external", None)

    def test_medline(self):
        assert classify_source("Medline") == ("external", None)

    def test_embase(self):
        assert classify_source("Embase") == ("external", None)

    def test_company_safety_database(self):
        assert classify_source("Company safety database") == ("external", None)

    def test_signal_assessment(self):
        assert classify_source("Signal assessment") == ("external", None)

    def test_external_case_insensitive(self):
        assert classify_source("uptodate") == ("external", None)
        assert classify_source("MEDLINE") == ("external", None)
        assert classify_source("company safety database") == ("external", None)

    def test_unknown_source(self):
        assert classify_source("Some random text") == ("unknown", None)

    def test_unknown_empty(self):
        assert classify_source("") == ("unknown", None)


# ---------------------------------------------------------------------------
# resolve_sources tests
# ---------------------------------------------------------------------------


class TestResolveSources:
    """Tests for resolve_sources()."""

    @pytest.fixture()
    def ib_index(self) -> dict[str, str]:
        return {
            "2.3": "This is the content of IB section 2.3.",
            "4.3.3": "Safety data from section 4.3.3.",
            "6.1": "Adverse events summary.",
        }

    def test_single_ib_found(self, ib_index: dict[str, str]):
        result = resolve_sources(["IB 2.3"], ib_index)
        assert len(result) == 1
        r = result[0]
        assert r.original_ref == "IB 2.3"
        assert r.source_type == "ib"
        assert r.section_num == "2.3"
        assert r.content == "This is the content of IB section 2.3."
        assert r.found is True

    def test_single_ib_not_found(self, ib_index: dict[str, str]):
        result = resolve_sources(["IB 9.9"], ib_index)
        assert len(result) == 1
        r = result[0]
        assert r.original_ref == "IB 9.9"
        assert r.source_type == "ib"
        assert r.section_num == "9.9"
        assert r.content == "[CONTENT NOT FOUND: IB 9.9]"
        assert r.found is False

    def test_multiple_ib_refs(self, ib_index: dict[str, str]):
        result = resolve_sources(["IB 2.3", "IB 9.9", "IB 6.1"], ib_index)
        assert len(result) == 3
        assert result[0].found is True
        assert result[0].content == "This is the content of IB section 2.3."
        assert result[1].found is False
        assert result[1].content == "[CONTENT NOT FOUND: IB 9.9]"
        assert result[2].found is True
        assert result[2].content == "Adverse events summary."

    def test_non_ib_placeholder(self, ib_index: dict[str, str]):
        result = resolve_sources(["PBRER Section 5"], ib_index)
        assert len(result) == 1
        r = result[0]
        assert r.original_ref == "PBRER Section 5"
        assert r.source_type == "pbrer"
        assert r.section_num is None
        assert r.content == "[MANUAL INPUT REQUIRED: PBRER Section 5]"
        assert r.found is False

    def test_bare_ib_placeholder(self, ib_index: dict[str, str]):
        result = resolve_sources(["IB"], ib_index)
        assert len(result) == 1
        r = result[0]
        assert r.original_ref == "IB"
        assert r.source_type == "ib"
        assert r.section_num is None
        assert r.content == "[MANUAL INPUT REQUIRED: IB — no specific section referenced]"
        assert r.found is False

    def test_empty_sources(self, ib_index: dict[str, str]):
        result = resolve_sources([], ib_index)
        assert result == []

    def test_mixed_ib_and_non_ib(self, ib_index: dict[str, str]):
        result = resolve_sources(["IB 2.3", "PBRER Section 5", "UpToDate"], ib_index)
        assert len(result) == 3
        # IB found
        assert result[0].found is True
        assert result[0].source_type == "ib"
        assert result[0].content == "This is the content of IB section 2.3."
        # PBRER placeholder
        assert result[1].found is False
        assert result[1].source_type == "pbrer"
        assert result[1].content == "[MANUAL INPUT REQUIRED: PBRER Section 5]"
        # External placeholder
        assert result[2].found is False
        assert result[2].source_type == "external"
        assert result[2].content == "[MANUAL INPUT REQUIRED: UpToDate]"
