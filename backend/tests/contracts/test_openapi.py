import json
from pathlib import Path
from typing import Any

from app.core.config import AppSettings, ModelProvider
from app.main import create_app

OPENAPI_SNAPSHOT = Path(__file__).parents[2] / "openapi.json"
FORBIDDEN_PUBLIC_FIELDS = {
    "internalScore",
    "matchScore",
    "rawScore",
    "sourceMessageIds",
    "questionHistory",
    "retrievedSourceIds",
    "systemPrompt",
}


def _schema() -> dict[str, Any]:
    app = create_app(settings=AppSettings(modelProvider=ModelProvider.MOCK))
    return app.openapi()


def test_openapi_matches_the_committed_snapshot() -> None:
    assert OPENAPI_SNAPSHOT.exists(), "请先运行 scripts/export-openapi.ps1"
    expected = json.loads(OPENAPI_SNAPSHOT.read_text(encoding="utf-8"))

    assert _schema() == expected


def test_openapi_exposes_reset_as_an_idempotent_no_content_operation() -> None:
    operation = _schema()["paths"]["/api/v1/conversations/{conversation_id}"]["delete"]

    assert set(operation["responses"]) >= {"204", "404", "410"}
    assert "content" not in operation["responses"]["204"]


def test_openapi_does_not_publish_internal_scores_or_agent_state() -> None:
    serialized = json.dumps(_schema(), ensure_ascii=False)

    assert FORBIDDEN_PUBLIC_FIELDS.isdisjoint(serialized.split('"'))
