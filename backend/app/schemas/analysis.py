from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.catalog import InclusiveMonthRange


class CreateAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(min_length=1)
    window: InclusiveMonthRange
