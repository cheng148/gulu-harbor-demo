import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from app.api.conversations import router as conversations_router
from app.api.errors import ResponseMeta, get_request_id, install_error_handlers
from app.core.clock import Clock, SystemClock
from app.core.config import AppSettings, load_settings
from app.core.config import ModelProvider as ModelProviderKind
from app.providers.base import ModelProvider
from app.providers.deepseek import DeepSeekProvider
from app.repositories.base import ConversationRepository
from app.repositories.sqlite import SQLiteConversationRepository
from app.services.session_service import SessionService
from app.services.turn_service import TurnService


def create_app(
    settings: AppSettings | None = None,
    *,
    conversation_repository: ConversationRepository | None = None,
    clock: Clock | None = None,
    model_provider: ModelProvider | None = None,
) -> FastAPI:
    resolved_settings = settings or load_settings()
    resolved_settings.validate_for_startup()

    application = FastAPI(title="咕噜港 AI 选宠顾问")
    application.state.settings = resolved_settings
    repository = conversation_repository or SQLiteConversationRepository(
        Path(os.getenv("DATABASE_PATH", "./var/gulu-port.db"))
    )
    repository.initialize()
    resolved_clock = clock or SystemClock()
    session_service = SessionService(repository, resolved_clock)
    if (
        model_provider is None
        and resolved_settings.modelProvider is ModelProviderKind.DEEPSEEK
    ):
        api_key = resolved_settings.deepseekApiKey
        assert api_key is not None
        model_provider = DeepSeekProvider(
            api_key=api_key,
            base_url=resolved_settings.deepseekBaseUrl,
            model=resolved_settings.deepseekModel,
            timeout_seconds=resolved_settings.deepseekTimeoutSeconds,
        )
    application.state.session_service = session_service
    application.state.turn_service = TurnService(repository, session_service)
    application.state.clock = resolved_clock
    application.state.model_provider = model_provider
    install_error_handlers(application)
    application.include_router(conversations_router)

    @application.middleware("http")
    async def attach_request_id(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.request_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = get_request_id(request)
        return response

    @application.get("/health")
    def health(request: Request) -> dict[str, object]:
        return {
            "data": {
                "status": "ok",
                "service": "gulu-port-agent",
                "dependencies": {"configuration": "ok"},
            },
            "meta": ResponseMeta(requestId=get_request_id(request)).model_dump(
                mode="json"
            ),
        }

    return application


app = create_app()
