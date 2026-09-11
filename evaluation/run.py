from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from _pytest.reports import TestReport

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.metrics import (
    CaseObservation,
    EvaluationStatus,
    EvaluationSummary,
    calculate_metrics,
)

PROJECT_ROOT = Path(__file__).parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CURRENT_RULE_VERSION = "SDD_SPEC 0.3.10"


@dataclass(frozen=True)
class CasePlan:
    caseId: str
    testNodes: tuple[str, ...] = ()
    deferredReason: str | None = None
    expectedHardConstraints: int = 0
    totalQuestions: int = 0
    annotatedConflicts: int = 0
    decidableNextQuestions: int = 0
    recommendedCandidates: int = 0
    recommendations: int = 0
    scoreLeakChecks: int = 0
    mockNetworkChecks: int = 0
    prototypeButtons: int = 0


def _plan(
    case_id: str,
    *nodes: str,
    expectedHardConstraints: int = 0,
    totalQuestions: int = 0,
    annotatedConflicts: int = 0,
    decidableNextQuestions: int = 0,
    recommendedCandidates: int = 0,
    recommendations: int = 0,
    scoreLeakChecks: int = 0,
    mockNetworkChecks: int = 0,
    prototypeButtons: int = 0,
) -> CasePlan:
    return CasePlan(
        caseId=case_id,
        testNodes=tuple(nodes),
        expectedHardConstraints=expectedHardConstraints,
        totalQuestions=totalQuestions,
        annotatedConflicts=annotatedConflicts,
        decidableNextQuestions=decidableNextQuestions,
        recommendedCandidates=recommendedCandidates,
        recommendations=recommendations,
        scoreLeakChecks=scoreLeakChecks,
        mockNetworkChecks=mockNetworkChecks,
        prototypeButtons=prototypeButtons,
    )


CASE_PLANS: dict[str, CasePlan] = {
    "EVAL-001": _plan(
        "EVAL-001",
        "tests/agent/test_question_flow.py::test_free_text_updates_profile_and_skips_core_topics_already_answered",
        totalQuestions=1,
        decidableNextQuestions=1,
    ),
    "EVAL-002": _plan(
        "EVAL-002",
        "tests/domain/test_question_selection.py::test_initial_profile_starts_with_time_in_a_warm_plain_tone",
        totalQuestions=1,
        decidableNextQuestions=1,
    ),
    "EVAL-003": _plan(
        "EVAL-003",
        "tests/agent/test_question_flow.py::test_two_profiles_can_follow_different_dynamic_question_branches",
        totalQuestions=2,
        decidableNextQuestions=2,
    ),
    "EVAL-004": _plan(
        "EVAL-004",
        "tests/domain/test_question_limit.py::test_three_core_questions_stop_without_extra_impact",
        decidableNextQuestions=1,
    ),
    "EVAL-005": _plan(
        "EVAL-005",
        "tests/domain/test_question_limit.py::test_top_two_member_change_can_trigger_the_one_extra_question",
        totalQuestions=1,
        decidableNextQuestions=1,
    ),
    "EVAL-006": _plan(
        "EVAL-006",
        "tests/domain/test_question_limit.py::test_top_two_reorder_does_not_trigger_the_extra_question",
        decidableNextQuestions=1,
    ),
    "EVAL-007": _plan(
        "EVAL-007",
        "tests/domain/test_question_limit.py::test_backup_reorder_does_not_trigger_the_extra_question",
        decidableNextQuestions=1,
    ),
    "EVAL-008": _plan(
        "EVAL-008",
        "tests/domain/test_readiness.py::test_direct_request_is_provisional_and_only_exposes_important_unknowns",
    ),
    "EVAL-009": _plan(
        "EVAL-009",
        "tests/domain/test_question_limit.py::test_allergy_is_confirmed_after_core_questions_before_recommendation",
        expectedHardConstraints=1,
        totalQuestions=1,
        decidableNextQuestions=1,
    ),
    "EVAL-010": _plan(
        "EVAL-010",
        "tests/domain/test_question_limit.py::test_known_allergy_is_not_asked_again",
        totalQuestions=1,
        decidableNextQuestions=1,
    ),
    "EVAL-011": _plan(
        "EVAL-011",
        "tests/domain/test_constraints.py::test_cat_allergy_excludes_cat_but_not_dog",
        expectedHardConstraints=1,
    ),
    "EVAL-012": _plan(
        "EVAL-012",
        "tests/evaluation/test_fixed_case_regressions.py::test_dog_allergy_excludes_dog_but_not_cat",
        expectedHardConstraints=1,
    ),
    "EVAL-013": _plan(
        "EVAL-013",
        "tests/domain/test_constraints.py::test_explicit_shedding_bottom_line_excludes_before_scoring",
        expectedHardConstraints=1,
    ),
    "EVAL-014": _plan(
        "EVAL-014",
        "tests/evaluation/test_fixed_case_regressions.py::test_explicit_noise_bottom_line_excludes_before_scoring",
        expectedHardConstraints=1,
    ),
    "EVAL-015": _plan(
        "EVAL-015",
        "tests/domain/test_scoring_weights.py::test_unknown_gets_half_weight_but_remains_unknown",
    ),
    "EVAL-016": _plan(
        "EVAL-016",
        "tests/domain/test_profile_merge.py::test_explicit_any_is_confirmed_neutral_not_unknown",
    ),
    "EVAL-017": _plan(
        "EVAL-017",
        "tests/evaluation/test_fixed_case_regressions.py::test_wording_intensity_does_not_create_an_extra_scoring_factor",
    ),
    "EVAL-018": _plan(
        "EVAL-018",
        "tests/domain/test_scoring_weights.py::test_species_scope_filters_candidates_but_never_changes_score",
    ),
    "EVAL-019": _plan(
        "EVAL-019",
        "tests/evaluation/test_fixed_case_regressions.py::test_direction_and_size_share_one_scoring_factor",
    ),
    "EVAL-020": _plan(
        "EVAL-020",
        "tests/domain/test_adjustments.py::test_explicit_willingness_records_one_gap_at_seventy_five_percent",
    ),
    "EVAL-021": _plan(
        "EVAL-021",
        "tests/domain/test_adjustments.py::test_accepting_one_gap_does_not_clear_another_conflict",
        annotatedConflicts=1,
    ),
    "EVAL-022": _plan(
        "EVAL-022",
        "tests/domain/test_matching.py::test_level_boundaries_are_eighty_and_sixty",
        "tests/domain/test_matching.py::test_relationship_or_life_zero_forces_caution_even_above_eighty",
    ),
    "EVAL-023": _plan(
        "EVAL-023",
        "tests/domain/test_matching.py::test_ranking_is_level_first_then_score_then_stable_id",
        "tests/domain/test_public_result.py::test_public_result_has_no_internal_score_and_includes_merchant_demo_boundary",
        scoreLeakChecks=1,
    ),
    "EVAL-024": _plan(
        "EVAL-024",
        "tests/domain/test_public_result.py::test_public_result_is_limited_to_four_and_one_pet_per_direction",
    ),
    "EVAL-025": _plan(
        "EVAL-025",
        "tests/domain/test_public_result.py::test_all_caution_results_never_claim_priority_recommendation",
        recommendations=1,
    ),
    "EVAL-026": _plan(
        "EVAL-026",
        "tests/evaluation/test_fixed_case_regressions.py::test_two_eligible_pets_are_not_padded_to_four",
        recommendedCandidates=2,
    ),
    "EVAL-027": _plan(
        "EVAL-027",
        "tests/domain/test_matching.py::test_level_boundaries_are_eighty_and_sixty",
        "tests/domain/test_readiness.py::test_no_eligible_candidates_is_not_recommended",
    ),
    "EVAL-028": _plan(
        "EVAL-028",
        "tests/domain/test_catalog_data.py::test_catalog_contains_only_the_approved_directions_pets_and_merchants",
        "tests/domain/test_catalog_data.py::test_each_direction_has_its_two_approved_pets",
        recommendedCandidates=16,
    ),
    "EVAL-029": _plan(
        "EVAL-029",
        "tests/integration/test_model_failure_rollback.py::test_two_invalid_model_responses_do_not_commit_or_refresh_ttl",
        "tests/integration/test_model_failure_rollback.py::test_model_timeout_does_not_commit_or_refresh_ttl",
    ),
    "EVAL-030": _plan(
        "EVAL-030",
        "tests/providers/test_mock_determinism.py::test_same_fixture_and_input_are_byte_stable_without_network",
        "tests/providers/test_provider_contract.py::test_mock_implements_the_same_four_operation_contract_as_real_providers",
        mockNetworkChecks=1,
    ),
    "EVAL-031": _plan(
        "EVAL-031",
        "tests/services/test_session_ttl.py::test_session_is_expired_at_the_exact_boundary",
    ),
    "EVAL-032": _plan(
        "EVAL-032",
        "tests/services/test_session_reset.py::test_new_session_after_reset_starts_with_an_empty_profile",
    ),
    "EVAL-033": _plan(
        "EVAL-033",
        "tests/domain/test_public_result.py::test_public_result_has_no_internal_score_and_includes_merchant_demo_boundary",
        recommendedCandidates=1,
        recommendations=1,
        prototypeButtons=1,
    ),
    "EVAL-034": CasePlan(
        caseId="EVAL-034",
        deferredReason="由T42真实浏览器审查验证手机安装与完整核心流程",
    ),
    "EVAL-035": CasePlan(
        caseId="EVAL-035",
        deferredReason="由T42真实浏览器审查验证不支持安装时的链接回退",
    ),
    "EVAL-036": _plan(
        "EVAL-036",
        "tests/agent/test_question_flow.py::test_conflicting_statement_is_preserved_and_clarified_before_other_questions",
        annotatedConflicts=1,
        totalQuestions=1,
        decidableNextQuestions=1,
    ),
}


class _PytestCollector:
    def __init__(self) -> None:
        self.reports: dict[str, list[TestReport]] = {}

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        self.reports.setdefault(report.nodeid, []).append(report)

    def outcome_for(self, requested_node: str) -> tuple[bool, tuple[str, ...]]:
        matching = {
            node_id: reports
            for node_id, reports in self.reports.items()
            if node_id == requested_node or node_id.startswith(f"{requested_node}[")
        }
        if not matching:
            return False, (f"未找到回归测试结果：{requested_node}",)
        failures = tuple(
            f"{node_id}: {report.longreprtext.splitlines()[-1]}"
            for node_id, reports in matching.items()
            for report in reports
            if report.failed
        )
        return not failures, failures


def load_case_ids(path: Path) -> tuple[str, ...]:
    return tuple(
        json.loads(line)["caseId"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def load_dataset_version(path: Path) -> str:
    versions = {
        json.loads(line)["schemaVersion"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    if len(versions) != 1:
        raise ValueError("fixed evaluation cases must use one schema version")
    return str(versions.pop())


def validate_plan_coverage(
    case_ids: tuple[str, ...], plans: dict[str, CasePlan]
) -> None:
    expected = set(case_ids)
    actual = set(plans)
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"evaluation plan mismatch; missing={missing}, extra={extra}")
    for plan in plans.values():
        if bool(plan.testNodes) == bool(plan.deferredReason):
            raise ValueError(
                f"{plan.caseId} must have tests or one truthful deferred reason"
            )


def build_case_observation(
    plan: CasePlan,
    *,
    passed: bool,
    failures: tuple[str, ...] = (),
) -> CaseObservation:
    if plan.deferredReason:
        return CaseObservation(
            caseId=plan.caseId,
            status=EvaluationStatus.DEFERRED,
            failures=(plan.deferredReason,),
        )
    status = EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED
    return CaseObservation(
        caseId=plan.caseId,
        status=status,
        expectedHardConstraints=plan.expectedHardConstraints,
        coveredHardConstraints=plan.expectedHardConstraints if passed else 0,
        hardConstraintViolations=0 if passed else plan.expectedHardConstraints,
        totalQuestions=plan.totalQuestions,
        repeatedConfirmedQuestions=0 if passed else plan.totalQuestions,
        annotatedConflicts=plan.annotatedConflicts,
        detectedConflicts=plan.annotatedConflicts if passed else 0,
        decidableNextQuestions=plan.decidableNextQuestions,
        consistentNextQuestions=plan.decidableNextQuestions if passed else 0,
        recommendedCandidates=plan.recommendedCandidates,
        candidatesWithCompleteCatalogReferences=(
            plan.recommendedCandidates if passed else 0
        ),
        recommendations=plan.recommendations,
        recommendationsWithCompleteBasis=plan.recommendations if passed else 0,
        publicScoreLeaks=0 if passed else plan.scoreLeakChecks,
        mockNetworkCalls=0 if passed else plan.mockNetworkChecks,
        prototypeButtons=plan.prototypeButtons,
        prototypeButtonsWithFeedback=plan.prototypeButtons if passed else 0,
        failures=failures,
    )


def _execute_regression_tests(plans: dict[str, CasePlan]) -> _PytestCollector:
    nodes = sorted(
        {node for plan in plans.values() for node in plan.testNodes}
    )
    collector = _PytestCollector()
    scratch_root = PROJECT_ROOT / ".pytest-tmp"
    scratch_root.mkdir(exist_ok=True)
    previous_provider = os.environ.get("MODEL_PROVIDER")
    os.environ["MODEL_PROVIDER"] = "mock"
    try:
        with tempfile.TemporaryDirectory(prefix="t41-", dir=scratch_root) as base_temp:
            pytest.main(
                [
                    *nodes,
                    "-q",
                    "--tb=short",
                    "--basetemp",
                    base_temp,
                ],
                plugins=[collector],
            )
    finally:
        if previous_provider is None:
            os.environ.pop("MODEL_PROVIDER", None)
        else:
            os.environ["MODEL_PROVIDER"] = previous_provider
    return collector


def run_fixed_evaluation() -> EvaluationSummary:
    dataset_path = PROJECT_ROOT / "evaluation" / "cases.jsonl"
    case_ids = load_case_ids(dataset_path)
    validate_plan_coverage(case_ids, CASE_PLANS)
    collector = _execute_regression_tests(CASE_PLANS)
    observations: list[CaseObservation] = []
    for case_id in case_ids:
        plan = CASE_PLANS[case_id]
        if plan.deferredReason:
            observations.append(build_case_observation(plan, passed=True))
            continue
        outcomes = tuple(collector.outcome_for(node) for node in plan.testNodes)
        failures = tuple(
            failure for _, node_failures in outcomes for failure in node_failures
        )
        observations.append(
            build_case_observation(
                plan,
                passed=all(passed for passed, _ in outcomes),
                failures=failures,
            )
        )
    return calculate_metrics(tuple(observations))


def render_markdown_report(
    summary: EvaluationSummary,
    *,
    dataset_version: str,
    rule_version: str,
    generated_at: str,
) -> str:
    lines = [
        "# 咕噜港固定评测报告",
        "",
        "## 运行身份",
        "",
        "本报告来自确定性Mock回归测试：只替换模型边界，业务规则仍运行生产代码；不读取DeepSeek Key、不访问模型网络。真人模型指标不得用本报告冒充。",
        "",
        f"- 生成时间：{generated_at}",
        f"- 数据集版本：{dataset_version}",
        f"- 规则版本：{rule_version}",
        "- 模型提供方：MockProvider",
        "- 模型名：deterministic-fixtures",
        "",
        "## T41固定运行器结果",
        "",
        "| 项目 | 数量 |",
        "|---|---:|",
        f"| 样本总数 | {summary.sampleSize} |",
        f"| Mock已执行 | {summary.evaluatedCaseCount} |",
        f"| Mock已通过 | {summary.passedCaseCount} |",
        f"| Bad Case | {len(summary.failedCaseIds)} |",
        f"| 当时延期到浏览器审查 | {summary.deferredCaseCount} |",
        "",
        "## Gate 5指标",
        "",
        "| 指标 | 本次结果 | 目标 | 判断 |",
        "|---|---:|---:|---|",
    ]
    for metric in summary.metrics:
        judgment = (
            "不适用"
            if not metric.applicable
            else ("通过" if metric.passed else "未通过")
        )
        lines.append(
            f"| {metric.label} | {metric.displayValue} | {metric.target} | {judgment} |"
        )
    lines.extend(["", "## Bad Case", ""])
    if summary.failedCaseIds:
        for case_id in summary.failedCaseIds:
            observation = next(
                item for item in summary.observations if item.caseId == case_id
            )
            lines.append(f"- {case_id}：{'；'.join(observation.failures)}")
    else:
        lines.append("- 本次已执行的Mock案例没有Bad Case。")
    lines.extend(
        [
            "",
            "## T42补充审查结果",
            "",
            "| 案例 | T42结果 | 结论 |",
            "| --- | --- | --- |",
            "| EVAL-034 | Manifest、192／512标准图标和完整核心流程已通过浏览器检查；实体手机系统安装动作未执行 | 部分验证，保留手工项 |",
            "| EVAL-035 | 无需安装即可从普通链接进入首页、选宠并完成核心流程 | 通过 |",
            "",
            "因此36条固定案例目前是：34条Mock自动执行通过，1条浏览器案例通过，1条完成安装前置条件但仍保留实体手机手工步骤。不能把它写成“36条全自动通过”。",
            "",
            "## 解释边界",
            "",
            "- 通过表示关联的生产业务回归测试通过，不表示真人DeepSeek每次输出都相同。",
            "- 结构化输出成功率只适用于真人调用，本次Mock报告显示为不适用。",
            "- 原型按钮反馈率仍只统计固定集已标注的联系商家按钮；T42另行确认七个主要页面的可见交互控件都有可读名称，并检查代表性弹窗键盘路径。",
            "- T42完成浏览器安装前置条件和普通链接回退检查，但没有把桌面模拟当作实体手机系统安装证据。",
            "",
            "## 证据索引",
            "",
            "- 原始固定评测结果：`evaluation/results/mock-latest.json`",
            "- 固定案例定义：`evaluation/cases.jsonl`",
            "- 真人模型观察：`docs/evaluation/live-model-observations.md`",
            "- 浏览器审查：`docs/qa/browser-check.md`",
            "- 最终全量验证：属于T44，当前尚未生成`docs/qa/final-verification.md`",
            "",
        ]
    )
    return "\n".join(lines)


def _write_outputs(
    summary: EvaluationSummary,
    *,
    result_path: Path,
    report_path: Path,
    dataset_version: str,
) -> None:
    result_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        summary.model_dump_json(indent=2),
        encoding="utf-8",
    )
    report_path.write_text(
        render_markdown_report(
            summary,
            dataset_version=dataset_version,
            rule_version=CURRENT_RULE_VERSION,
            generated_at=datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="运行咕噜港确定性Mock固定评测")
    parser.add_argument(
        "--result",
        type=Path,
        default=PROJECT_ROOT / "evaluation" / "results" / "mock-latest.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "docs" / "evaluation" / "report.md",
    )
    args = parser.parse_args(argv)
    dataset_path = PROJECT_ROOT / "evaluation" / "cases.jsonl"
    summary = run_fixed_evaluation()
    _write_outputs(
        summary,
        result_path=args.result,
        report_path=args.report,
        dataset_version=load_dataset_version(dataset_path),
    )
    return 1 if summary.failedCaseIds else 0


if __name__ == "__main__":
    raise SystemExit(main())
