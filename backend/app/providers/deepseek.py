from __future__ import annotations

import json
from typing import TypeVar

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from app.providers.base import (
    ProfileExtractionRequest,
    ProfileExtractionResponse,
    ProviderFailure,
    ProviderFailureCode,
    ProviderRequest,
    QuestionWordingRequest,
    QuestionWordingResponse,
    RecommendationExplanationRequest,
    RecommendationExplanationResponse,
    SafetyReviewRequest,
    SafetyReviewResponse,
    validate_profile_extraction_response,
    validate_question_wording_response,
)

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class _DeepSeekMessage(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    content: str | None


class _DeepSeekChoice(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    finish_reason: str
    message: _DeepSeekMessage


class _DeepSeekCompletion(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    choices: tuple[_DeepSeekChoice, ...] = Field(min_length=1)


_OPERATION_INSTRUCTIONS: dict[type[ProviderRequest], str] = {
    ProfileExtractionRequest: (
        "Extract a structured profile delta only from the supplied user message and "
        "current context. Preserve uncertainty and never turn an ordinary preference "
        "into a hard constraint."
    ),
    QuestionWordingRequest: (
        "Rewrite the supplied prompt in warm, natural Simplified Chinese. Preserve "
        "questionId and quickReplies exactly; only improve the question wording."
    ),
    RecommendationExplanationRequest: (
        "Explain only the supplied deterministic recommendation facts in warm, clear "
        "Simplified Chinese. Do not change candidates, match levels, or factual claims."
    ),
    SafetyReviewRequest: (
        "Review the supplied draft text for unsupported guarantees, medical diagnosis, "
        "or unsafe claims. Return the structured review and safe replacements when needed."
    ),
}


class DeepSeekProvider:
    """DeepSeek JSON adapter; product decisions stay outside this boundary."""

    def __init__(
        self,
        *,
        api_key: SecretStr,
        base_url: str,
        model: str,
        timeout_seconds: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._http_client = http_client or httpx.Client()

    def _complete(
        self, request: ProviderRequest, response_model: type[ResponseT]
    ) -> ResponseT:
        schema = json.dumps(
            response_model.model_json_schema(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        instruction = _OPERATION_INSTRUCTIONS[type(request)]
        system_prompt = (
            f"{instruction} Return JSON only. The JSON object must match this JSON "
            f"Schema: {schema}"
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.model_dump_json()},
            ],
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "stream": False,
            "max_tokens": 2048,
        }

        for attempt in range(2):
            try:
                return self._complete_once(payload, response_model)
            except ProviderFailure as error:
                if error.code is not ProviderFailureCode.INVALID_OUTPUT or attempt == 1:
                    raise
        raise AssertionError("retry loop must either return or raise")

    def _complete_once(
        self, payload: dict[str, object], response_model: type[ResponseT]
    ) -> ResponseT:

        try:
            response = self._http_client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise ProviderFailure(
                ProviderFailureCode.TIMEOUT, "model request timed out"
            ) from error
        except httpx.HTTPError as error:
            raise ProviderFailure(
                ProviderFailureCode.UNAVAILABLE, "model provider is unavailable"
            ) from error

        try:
            completion = _DeepSeekCompletion.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            raise ProviderFailure(
                ProviderFailureCode.INVALID_OUTPUT,
                "model provider returned an invalid response envelope",
            ) from error

        choice = completion.choices[0]
        content = choice.message.content
        if choice.finish_reason != "stop" or content is None or not content.strip():
            raise ProviderFailure(
                ProviderFailureCode.INVALID_OUTPUT,
                "model provider returned empty or incomplete content",
            )

        try:
            return response_model.model_validate_json(content)
        except (ValueError, ValidationError) as error:
            raise ProviderFailure(
                ProviderFailureCode.INVALID_OUTPUT,
                "model content did not match the provider contract",
            ) from error

    def extract_profile(
        self, request: ProfileExtractionRequest
    ) -> ProfileExtractionResponse:
        response = self._complete(request, ProfileExtractionResponse)
        return validate_profile_extraction_response(request, response)

    def phrase_question(
        self, request: QuestionWordingRequest
    ) -> QuestionWordingResponse:
        response = self._complete(request, QuestionWordingResponse)
        return validate_question_wording_response(request, response)

    def explain_recommendation(
        self, request: RecommendationExplanationRequest
    ) -> RecommendationExplanationResponse:
        return self._complete(request, RecommendationExplanationResponse)

    def review_safety(self, request: SafetyReviewRequest) -> SafetyReviewResponse:
        return self._complete(request, SafetyReviewResponse)
