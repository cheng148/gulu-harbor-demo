from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvaluationStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    DEFERRED = "DEFERRED"


class CaseObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str = Field(min_length=1)
    status: EvaluationStatus
    expectedHardConstraints: int = Field(default=0, ge=0)
    coveredHardConstraints: int = Field(default=0, ge=0)
    hardConstraintViolations: int = Field(default=0, ge=0)
    totalQuestions: int = Field(default=0, ge=0)
    repeatedConfirmedQuestions: int = Field(default=0, ge=0)
    annotatedConflicts: int = Field(default=0, ge=0)
    detectedConflicts: int = Field(default=0, ge=0)
    decidableNextQuestions: int = Field(default=0, ge=0)
    consistentNextQuestions: int = Field(default=0, ge=0)
    recommendedCandidates: int = Field(default=0, ge=0)
    candidatesWithCompleteCatalogReferences: int = Field(default=0, ge=0)
    recommendations: int = Field(default=0, ge=0)
    recommendationsWithCompleteBasis: int = Field(default=0, ge=0)
    publicScoreLeaks: int = Field(default=0, ge=0)
    structuredModelCalls: int = Field(default=0, ge=0)
    structuredModelSuccesses: int = Field(default=0, ge=0)
    mockNetworkCalls: int = Field(default=0, ge=0)
    prototypeButtons: int = Field(default=0, ge=0)
    prototypeButtonsWithFeedback: int = Field(default=0, ge=0)
    failures: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_success_counters(self) -> CaseObservation:
        pairs = (
            (self.coveredHardConstraints, self.expectedHardConstraints),
            (self.repeatedConfirmedQuestions, self.totalQuestions),
            (self.detectedConflicts, self.annotatedConflicts),
            (self.consistentNextQuestions, self.decidableNextQuestions),
            (
                self.candidatesWithCompleteCatalogReferences,
                self.recommendedCandidates,
            ),
            (self.recommendationsWithCompleteBasis, self.recommendations),
            (self.structuredModelSuccesses, self.structuredModelCalls),
            (self.prototypeButtonsWithFeedback, self.prototypeButtons),
        )
        if any(successes > total for successes, total in pairs):
            raise ValueError("a successful unit count cannot exceed its total")
        if self.status is EvaluationStatus.DEFERRED and any(
            total
            for pair in pairs
            for total in pair
        ):
            raise ValueError("a deferred case cannot contribute measured units")
        return self


class MetricResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metricId: str
    label: str
    numerator: int
    denominator: int | None = None
    value: float | None
    displayValue: str
    target: str
    applicable: bool
    passed: bool | None


class EvaluationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sampleSize: int
    evaluatedCaseCount: int
    deferredCaseCount: int
    passedCaseCount: int
    failedCaseIds: tuple[str, ...]
    metrics: tuple[MetricResult, ...]
    observations: tuple[CaseObservation, ...]


def _rate_metric(
    metric_id: str,
    label: str,
    numerator: int,
    denominator: int,
    *,
    minimum: float | None = None,
    maximum_exclusive: float | None = None,
    target: str,
) -> MetricResult:
    if denominator == 0:
        return MetricResult(
            metricId=metric_id,
            label=label,
            numerator=numerator,
            denominator=denominator,
            value=None,
            displayValue="不适用",
            target=target,
            applicable=False,
            passed=None,
        )
    value = numerator / denominator
    passed = value >= minimum if minimum is not None else True
    if maximum_exclusive is not None:
        passed = passed and value < maximum_exclusive
    return MetricResult(
        metricId=metric_id,
        label=label,
        numerator=numerator,
        denominator=denominator,
        value=value,
        displayValue=f"{value:.1%}",
        target=target,
        applicable=True,
        passed=passed,
    )


def _count_metric(
    metric_id: str,
    label: str,
    value: int,
    *,
    maximum: int,
    target: str,
) -> MetricResult:
    return MetricResult(
        metricId=metric_id,
        label=label,
        numerator=value,
        value=float(value),
        displayValue=str(value),
        target=target,
        applicable=True,
        passed=value <= maximum,
    )


def calculate_metrics(
    observations: tuple[CaseObservation, ...],
) -> EvaluationSummary:
    active = tuple(
        item for item in observations if item.status is not EvaluationStatus.DEFERRED
    )

    def total(field: str) -> int:
        return sum(int(getattr(item, field)) for item in active)

    metrics = (
        _rate_metric(
            "hard_constraint_coverage_rate",
            "关键硬约束覆盖率",
            total("coveredHardConstraints"),
            total("expectedHardConstraints"),
            minimum=1.0,
            target="100%",
        ),
        _count_metric(
            "hard_constraint_violation_count",
            "硬约束违规推荐数",
            total("hardConstraintViolations"),
            maximum=0,
            target="0",
        ),
        _rate_metric(
            "confirmed_repeat_question_rate",
            "已确认信息重复询问率",
            total("repeatedConfirmedQuestions"),
            total("totalQuestions"),
            maximum_exclusive=0.05,
            target="<5%",
        ),
        _rate_metric(
            "conflict_recall_rate",
            "冲突识别召回率",
            total("detectedConflicts"),
            total("annotatedConflicts"),
            minimum=1.0,
            target="100%（固定集）",
        ),
        _rate_metric(
            "next_question_consistency_rate",
            "下一问题规则一致率",
            total("consistentNextQuestions"),
            total("decidableNextQuestions"),
            minimum=1.0,
            target="100%",
        ),
        _rate_metric(
            "catalog_reference_completeness_rate",
            "档案引用完整率",
            total("candidatesWithCompleteCatalogReferences"),
            total("recommendedCandidates"),
            minimum=1.0,
            target="100%",
        ),
        _rate_metric(
            "recommendation_basis_completeness_rate",
            "推荐依据完整率",
            total("recommendationsWithCompleteBasis"),
            total("recommendations"),
            minimum=1.0,
            target="100%",
        ),
        _count_metric(
            "public_score_leak_count",
            "公共精确分泄漏数",
            total("publicScoreLeaks"),
            maximum=0,
            target="0",
        ),
        _rate_metric(
            "structured_output_success_rate",
            "结构化输出成功率（真人）",
            total("structuredModelSuccesses"),
            total("structuredModelCalls"),
            minimum=0.95,
            target=">=95%（真人演示记录）",
        ),
        _count_metric(
            "mock_network_call_count",
            "Mock网络调用数",
            total("mockNetworkCalls"),
            maximum=0,
            target="0",
        ),
        _rate_metric(
            "prototype_button_feedback_rate",
            "原型按钮反馈覆盖率",
            total("prototypeButtonsWithFeedback"),
            total("prototypeButtons"),
            minimum=1.0,
            target="100%",
        ),
    )
    return EvaluationSummary(
        sampleSize=len(observations),
        evaluatedCaseCount=len(active),
        deferredCaseCount=len(observations) - len(active),
        passedCaseCount=sum(
            item.status is EvaluationStatus.PASSED for item in active
        ),
        failedCaseIds=tuple(
            item.caseId for item in active if item.status is EvaluationStatus.FAILED
        ),
        metrics=metrics,
        observations=observations,
    )
