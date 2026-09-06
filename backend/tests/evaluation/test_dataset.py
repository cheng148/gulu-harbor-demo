from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

PROJECT_ROOT = Path(__file__).parents[3]
DATASET_PATH = PROJECT_ROOT / "evaluation" / "cases.jsonl"
SCHEMA_PATH = PROJECT_ROOT / "evaluation" / "schema.json"
REQUIRED_SDD_COVERAGE = {f"SDD-22-{index:02d}" for index in range(1, 36)}


class EvaluationCategory(StrEnum):
    NORMAL = "NORMAL"
    VAGUE_BEGINNER = "VAGUE_BEGINNER"
    CONFLICT = "CONFLICT"
    HARD_RISK = "HARD_RISK"
    NOT_SUITABLE = "NOT_SUITABLE"
    NO_PET_CANDIDATE = "NO_PET_CANDIDATE"
    MODIFY_CONDITIONS = "MODIFY_CONDITIONS"
    SYSTEM_BOUNDARY = "SYSTEM_BOUNDARY"


class EvaluationSurface(StrEnum):
    AGENT = "AGENT"
    API = "API"
    WEB_APP = "WEB_APP"


class EvaluationAction(StrEnum):
    SUBMIT_MESSAGE = "SUBMIT_MESSAGE"
    REQUEST_EARLY_RECOMMENDATION = "REQUEST_EARLY_RECOMMENDATION"
    RUN_MATCH = "RUN_MATCH"
    INJECT_MODEL_FAILURE = "INJECT_MODEL_FAILURE"
    REPEAT_RUN = "REPEAT_RUN"
    ADVANCE_TIME = "ADVANCE_TIME"
    RESET_SESSION = "RESET_SESSION"
    OPEN_WEB_APP = "OPEN_WEB_APP"
    INSTALL_WEB_APP = "INSTALL_WEB_APP"
    CLICK_PROTOTYPE_ACTION = "CLICK_PROTOTYPE_ACTION"


class ExpectationOperator(StrEnum):
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    EMPTY = "EMPTY"
    NOT_EMPTY = "NOT_EMPTY"
    COUNT_EQUALS = "COUNT_EQUALS"
    MAX_EQUALS = "MAX_EQUALS"
    SET_EQUALS = "SET_EQUALS"
    NO_NETWORK = "NO_NETWORK"


class EvaluationStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: EvaluationAction
    payload: dict[str, Any] = Field(default_factory=dict)


class EvaluationExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    operator: ExpectationOperator
    value: Any | None = None


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: str
    caseId: str
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: EvaluationCategory
    surface: EvaluationSurface
    tags: list[str] = Field(min_length=1)
    sddCoverage: list[str] = Field(min_length=1)
    steps: list[EvaluationStep] = Field(min_length=1)
    expectations: list[EvaluationExpectation] = Field(min_length=1)


def _load_cases() -> list[EvaluationCase]:
    payloads = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return TypeAdapter(list[EvaluationCase]).validate_python(payloads)


def test_dataset_and_schema_files_exist_and_are_valid_json() -> None:
    assert DATASET_PATH.is_file()
    assert SCHEMA_PATH.is_file()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "咕噜港固定评测案例"
    assert set(EvaluationCase.model_fields) <= set(schema["required"])
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]["category"]["enum"]) == {
        item.value for item in EvaluationCategory
    }
    assert set(schema["properties"]["surface"]["enum"]) == {
        item.value for item in EvaluationSurface
    }
    assert set(
        schema["properties"]["steps"]["items"]["properties"]["action"]["enum"]
    ) == {item.value for item in EvaluationAction}
    assert set(
        schema["properties"]["expectations"]["items"]["properties"][
            "operator"
        ]["enum"]
    ) == {item.value for item in ExpectationOperator}


def test_dataset_has_at_least_30_well_formed_unique_cases() -> None:
    cases = _load_cases()

    assert len(cases) >= 30
    assert len({case.caseId for case in cases}) == len(cases)
    assert all(re.fullmatch(r"EVAL-\d{3}", case.caseId) for case in cases)
    assert {case.schemaVersion for case in cases} == {"1.0.0"}


def test_dataset_covers_all_required_scenarios_and_task_categories() -> None:
    cases = _load_cases()
    actual_sdd_coverage = {
        coverage for case in cases for coverage in case.sddCoverage
    }

    assert actual_sdd_coverage == REQUIRED_SDD_COVERAGE
    assert {case.category for case in cases} == set(EvaluationCategory)


def test_every_case_is_machine_checkable_and_traceable() -> None:
    cases = _load_cases()

    for case in cases:
        assert len(case.tags) == len(set(case.tags))
        assert len(case.sddCoverage) == len(set(case.sddCoverage))
        assert all(tag.strip() == tag and tag for tag in case.tags)
        assert all(
            coverage in REQUIRED_SDD_COVERAGE for coverage in case.sddCoverage
        )
        assert all(step.payload is not None for step in case.steps)
        assert all(expectation.path for expectation in case.expectations)
