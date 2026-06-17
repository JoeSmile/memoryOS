from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    """业务异常：在路由/Service 中主动抛出。"""

    def __init__(
        self,
        code: int,
        message: str,
        status_code: int = 400,
        data: object = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "data": exc.data,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail if isinstance(exc.detail, str) else "error",
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "message": "validation_error",
                "data": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "internal_server_error",
                "data": None,
            },
        )
