from pydantic import BaseModel, Field


class DemoAnalysisTemplateRead(BaseModel):
    id: str
    label: str
    description: str


class DemoTurnRequest(BaseModel):
    match_id: str = Field(min_length=1, max_length=24)
    template_id: str = Field(min_length=1, max_length=64)


class DemoTurnResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str
