"""
Tests for shared/models.py after Phase 0 bug fixes.

Bugs covered:
  BUG-05 — RequirementType was not a str Enum; caused NameError on instantiation.
  BUG-06 — RequirementIn had fret_statement / fret_fields fields that don't belong
            to the input model (FRET fields live on a separate refinement model).

Also verifies:
  D-03 — RequirementIn.req_type defaults to RequirementType.FUN.
  D-04 — RequirementArea and module-level make_req_id removed from models.py.
  D-05 — RequirementIn has no fret fields.
"""

from __future__ import annotations

from requirements_agent_tools.models import (
    REQUIREMENT_TYPE_METADATA,
    ProjectMeta,
    RequirementIn,
    RequirementType,
    RequirementTypeMeta,
)


# ═══════════════════════════════════════════════════════════════════════════════
# RequirementType Enum (BUG-05)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequirementTypeEnum:
    def test_requirement_type_is_str_enum(self):
        """BUG-05: RequirementType must be a str Enum."""
        from enum import Enum

        assert issubclass(RequirementType, str)
        assert issubclass(RequirementType, Enum)

    def test_fun_value(self):
        """FUN member value must equal its code string."""
        assert RequirementType.FUN == "FUN"
        assert RequirementType.FUN.value == "FUN"

    def test_construct_from_string(self):
        """Must be constructable from its string value (required for DB round-trips)."""
        rt = RequirementType("FUN")
        assert rt == RequirementType.FUN

    def test_all_34_codes_present(self):
        """All 34 three-letter requirement type codes must be present."""
        expected = {
            "BUS",
            "USR",
            "FUN",
            "DAT",
            "MOD",
            "MLP",
            "MET",
            "NFR",
            "PER",
            "SCL",
            "SEC",
            "PRV",
            "COM",
            "ETH",
            "EXP",
            "ROB",
            "OPS",
            "DEP",
            "INT",
            "UIX",
            "TST",
            "MON",
            "AUD",
            "GOV",
            "LGL",
            "RES",
            "ENV",
            "MAI",
            "REL",
            "CON",
            "ASM",
            "RSK",
            "DOC",
            "TRN",
        }
        actual = {rt.value for rt in RequirementType}
        assert actual == expected

    def test_str_comparison_works(self):
        """str Enum allows comparison with plain strings (used in search filters)."""
        assert RequirementType.SEC == "SEC"
        assert "PRV" == RequirementType.PRV

    def test_enum_usable_as_dict_key(self):
        """str Enum members work as dict keys and match their string equivalent."""
        d = {RequirementType.FUN: "functional"}
        assert d[RequirementType.FUN] == "functional"


# ═══════════════════════════════════════════════════════════════════════════════
# RequirementTypeMeta NamedTuple
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequirementTypeMeta:
    def test_requirement_type_meta_is_namedtuple(self):
        """RequirementTypeMeta must be a NamedTuple (subclass of tuple)."""
        assert issubclass(RequirementTypeMeta, tuple)

    def test_metadata_list_has_34_items(self):
        """REQUIREMENT_TYPE_METADATA must have exactly 34 entries."""
        assert len(REQUIREMENT_TYPE_METADATA) == 34

    def test_metadata_item_has_code_name_description(self):
        """Each metadata entry must expose code, name, and description attributes."""
        item = REQUIREMENT_TYPE_METADATA[0]
        assert hasattr(item, "code")
        assert hasattr(item, "name")
        assert hasattr(item, "description")

    def test_metadata_codes_match_enum(self):
        """Codes in REQUIREMENT_TYPE_METADATA must exactly match RequirementType values."""
        meta_codes = {m.code for m in REQUIREMENT_TYPE_METADATA}
        enum_codes = {rt.value for rt in RequirementType}
        assert meta_codes == enum_codes

    def test_metadata_descriptions_are_nonempty(self):
        """Every metadata entry must have a non-empty description."""
        for m in REQUIREMENT_TYPE_METADATA:
            assert m.description, f"Empty description for code {m.code}"


# ═══════════════════════════════════════════════════════════════════════════════
# RequirementIn instantiation (BUG-05, BUG-06, D-03, D-04, D-05)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequirementInInstantiation:
    def test_requirement_in_instantiation(self):
        """BUG-05: RequirementIn must instantiate without NameError."""
        req = RequirementIn(title="x", description="y", req_type="FUN")
        assert req.title == "x"
        assert req.req_type == RequirementType.FUN

    def test_requirement_in_minimal(self):
        """RequirementIn with only title must instantiate (all other fields have defaults)."""
        req = RequirementIn(title="minimal")
        assert req.title == "minimal"

    def test_no_fret_statement_field(self):
        """BUG-06 / D-05: fret_statement must not exist on RequirementIn."""
        req = RequirementIn(title="x")
        assert not hasattr(req, "fret_statement")

    def test_no_fret_fields_field(self):
        """BUG-06 / D-05: fret_fields must not exist on RequirementIn."""
        req = RequirementIn(title="x")
        assert not hasattr(req, "fret_fields")

    def test_default_req_type_is_fun(self):
        """D-03: default req_type is RequirementType.FUN."""
        req = RequirementIn(title="x")
        assert req.req_type == RequirementType.FUN

    def test_req_type_coercion_from_string(self):
        """RequirementIn accepts req_type as a plain string and coerces it to the Enum."""
        req = RequirementIn(title="x", req_type="SEC")
        assert req.req_type == RequirementType.SEC

    def test_no_requirement_area_in_module(self):
        """D-04: RequirementArea must not be importable from models."""
        from requirements_agent_tools import models

        assert not hasattr(models, "RequirementArea")

    def test_no_make_req_id_in_module(self):
        """D-04: module-level make_req_id must be removed from models."""
        from requirements_agent_tools import models

        assert not hasattr(models, "make_req_id")

    def test_required_fields_have_correct_types(self):
        """RequirementIn fields must be typed correctly after instantiation."""
        from requirements_agent_tools.models import (
            RequirementPriority,
            RequirementStatus,
        )

        req = RequirementIn(title="type check")
        assert isinstance(req.status, RequirementStatus)
        assert isinstance(req.priority, RequirementPriority)
        assert isinstance(req.stakeholders, list)
        assert isinstance(req.tags, list)


# ═══════════════════════════════════════════════════════════════════════════════
# ProjectMeta model
# ═══════════════════════════════════════════════════════════════════════════════


class TestProjectMeta:
    def test_project_meta_instantiation(self):
        """ProjectMeta must instantiate with only name provided."""
        meta = ProjectMeta(name="Test")
        assert meta.name == "Test"
        assert meta.slug == ""

    def test_project_meta_slug_default_empty(self):
        """slug defaults to empty string; auto-derivation is done by upsert_project."""
        meta = ProjectMeta(name="My Project")
        assert meta.slug == ""

    def test_project_meta_slug_explicit(self):
        """Explicit slug is preserved unchanged."""
        meta = ProjectMeta(name="My Project", slug="custom")
        assert meta.slug == "custom"
