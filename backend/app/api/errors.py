from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException


class PublicErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    retryable: bool
    details: dict[str, Any]


class ResponseMeta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requestId: str = Field(min_length=1)


class PublicErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error: PublicErrorBody
    meta: ResponseMeta


class PublicAPIError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        retryable: bool,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = dict(details or {})


def get_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(request_id, str) and request_id:
        return request_id
    return uuid4().hex


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
    details: Mapping[str, Any] | None = None,
) -> JSONResponse:
    body = PublicErrorResponse(
        error=PublicErrorBody(
            code=code,
            message=message,
            retryable=retryable,
            details=dict(details or {}),
        ),
        meta=ResponseMeta(requestId=get_request_id(request)),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(PublicAPIError)
    async def public_api_error_handler(
        request: Request, error: PublicAPIError
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=error.message,
            retryable=error.retryable,
            details=error.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="请检查填写内容后再试。",
            retryable=False,
            details={"issues": jsonable_encoder(error.errors())},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, error: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=error.status_code,
            code="INVALID_REQUEST",
            message="请求的内容不存在或暂不可用。",
            retryable=False,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(
        request: Request, error: Exception
    ) -> JSONResponse:
        del error
        return _error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="服务暂时遇到问题，请稍后再试。",
            retryable=True,
        )
