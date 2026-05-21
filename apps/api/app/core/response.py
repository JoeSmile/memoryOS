from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应：与前端约定 code / message / data。"""

    code: int = Field(0, description="0 表示成功，非 0 表示业务或系统错误")
    message: str = Field("ok", description="提示信息")
    data: T | None = Field(None, description="业务数据")


def success(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return ApiResponse(code=0, message=message, data=data).model_dump()


def fail(code: int, message: str, data: Any = None) -> dict[str, Any]:
    return ApiResponse(code=code, message=message, data=data).model_dump()
