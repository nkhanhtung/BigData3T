from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class PredictionRequest(BaseModel):
    symbol: Optional[str] = None
    closes: List[float] = Field(..., min_items=60, max_items=60)

    # Validator để đảm bảo chính xác 60 phần tử
    @field_validator('closes')
    def check_length(cls, v):
        if len(v) != 60:
            raise ValueError('closes must have exactly 60 items')
        return v

class PredictionResponse(BaseModel):
    predictions: List[float]
    symbol: Optional[str]
    device: str