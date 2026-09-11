from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.metrics import (
    CaseObservation,
    EvaluationStatus,
    calculate_metrics,
)
from evaluation.run import (
    CASE_PLANS,
    _write_outputs,
    build_case_observation,
    load_case_ids,
    render_markdown_report,
    validate_plan_coverage,
)


def test_known_sample_calculates_gate_five_metrics() -> None:
    observations = (
        CaseObservation(
            caseId="pass",
            status=EvaluationStatus.PASSED,
            expectedHardConstraints=2,
            coveredHardConstraints=2,
            totalQuestions=20,
            repeatedConfirmedQuestions=0,
            annotatedConflicts=1,
            detectedConflicts=1,
            decidableNextQuestions=4,
            consistentNextQuestions=4,
            recommendedCandidates=3,
            candidatesWithCompleteCatalogReferences=3,
            recommendations=3,
            recommendationsWithCompleteBasis=3,
            prototypeButtons=2,
            prototypeButtonsWithFeedback=2,
        ),
        CaseObservation(
            caseId="bad-score-leak",
            status=EvaluationStatus.FAILED,
            publicScoreLeaks=1,
            mockNetworkCalls=1,
            failures=("公共响应出现rawScore",),
        ),
        CaseObservation(
            caseId="browser-later",
            status=EvaluationStatus.DEFERRED,
            failures=("由T42真实浏览器审查执行",),
        ),
    )

    summary = calculate_metrics(observations)
    metrics = {item.metricId: item for item in summary.metrics}

    assert summary.sampleSize == 3
    assert summary.evaluatedCaseCount == 2
    assert summary.deferredCaseCount == 1
    assert summary.failedCaseIds == ("bad-score-leak",)
    assert metrics["hard_constraint_coverage_rate"].value == 1.0
    assert metrics["confirmed_repeat_question_rate"].value == 0.0
    assert metrics["conflict_recall_rate"].value == 1.0
    assert metrics["next_question_consistency_rate"].value == 1.0
    assert metrics["catalog_reference_completeness_rate"].value == 1.0
    assert metrics["recommendation_basis_completeness_rate"].value == 1.0
    assert metrics["public_score_leak_count"].value == 1.0
    assert metrics["public_score_leak_count"].passed is False
    assert metrics["mock_network_call_count"].passed is False
    assert metrics["structured_output_success_rate"].applicable is False


def test_invalid_metric_counters_are_rejected() -> None:
    with pytest.raises(ValueError):
        CaseObservation(
            caseId="invalid",
            status=EvaluationStatus.PASSED,
            expectedHardConstraints=1,
            coveredHardConstraints=2,
        )


def test_runner_has_a_truthful_plan_for_every_fixed_case() -> None:
    case_ids = load_case_ids(PROJECT_ROOT / "evaluation" / "cases.jsonl")

    validate_plan_coverage(case_ids, CASE_PLANS)

    assert set(CASE_PLANS) == set(case_ids)
    assert {
        case_id for case_id, plan in CASE_PLANS.items() if plan.deferredReason
    } == {"EVAL-034", "EVAL-035"}
    assert all(
        plan.testNodes or plan.deferredReason for plan in CASE_PLANS.values()
    )


def test_failed_regression_test_becomes_a_bad_case_and_reduces_its_metric() -> None:
    plan = CASE_PLANS["EVAL-011"]

    observation = build_case_observation(
        plan,
        passed=False,
        failures=("species allergy regression failed",),
    )

    assert observation.status is EvaluationStatus.FAILED
    assert observation.expectedHardConstraints == 1
    assert observation.coveredHardConstraints == 0
    assert observation.hardConstraintViolations == 1
    assert observation.failures == ("species allergy regression failed",)


def test_report_preserves_mock_results_and_completed_t42_browser_evidence() -> None:
    observations = tuple(
        build_case_observation(plan, passed=True)
        for plan in CASE_PLANS.values()
    )
    summary = calculate_metrics(observations)

    report = render_markdown_report(
        summary,
        dataset_version="1.0.0",
        rule_version="SDD_SPEC 0.3.7",
        generated_at="2026-09-06T12:00:00+08:00",
    )

    assert "确定性Mock" in report
    assert "不读取DeepSeek Key" in report
    assert "EVAL-034" in report and "EVAL-035" in report
    assert "T42补充审查结果" in report
    assert "样本总数 | 36" in report
    assert "Mock已执行 | 34" in report
    assert "当时延期到浏览器审查 | 2" in report
    assert "EVAL-034 | Manifest、192／512标准图标和完整核心流程已通过浏览器检查" in report
    assert "EVAL-035 | 无需安装即可从普通链接进入首页、选宠并完成核心流程" in report
    assert "36条固定案例目前是：34条Mock自动执行通过" in report
    assert "待T42执行" not in report
    assert "真人模型指标不得用本报告冒充" in report
    assert "浏览器审查：`docs/qa/browser-check.md`" in report


def test_output_writer_uses_the_current_t43_rule_version(tmp_path: Path) -> None:
    observations = tuple(
        build_case_observation(plan, passed=True)
        for plan in CASE_PLANS.values()
    )
    summary = calculate_metrics(observations)
    result_path = tmp_path / "mock-latest.json"
    report_path = tmp_path / "report.md"

    _write_outputs(
        summary,
        result_path=result_path,
        report_path=report_path,
        dataset_version="1.0.0",
    )

    report = report_path.read_text(encoding="utf-8")
    assert "规则版本：SDD_SPEC 0.3.10" in report
    assert "待T42执行" not in report


def test_latest_result_json_can_round_trip_without_losing_bad_cases() -> None:
    summary = calculate_metrics(
        (
            CaseObservation(caseId="ok", status=EvaluationStatus.PASSED),
            CaseObservation(
                caseId="bad",
                status=EvaluationStatus.FAILED,
                failures=("regression",),
            ),
        )
    )

    restored = json.loads(summary.model_dump_json())

    assert restored["failedCaseIds"] == ["bad"]
    assert restored["observations"][1]["failures"] == ["regression"]
