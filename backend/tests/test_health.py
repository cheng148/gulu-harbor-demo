from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_service_is_ready() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {
        "status": "ok",
        "service": "gulu-port-agent",
        "dependencies": {"configuration": "ok"},
    }
    assert body["meta"]["requestId"] == response.headers["X-Request-ID"]
