from pydantic import BaseModel, Field


class HealthData(BaseModel):
    status: str = Field("ok", examples=["ok"])
    app: str
    env: str


class HealthResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: HealthData
