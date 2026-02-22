from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Any

class MeasurementBase(BaseModel):
    sensor_id: int = Field(..., gt=0, description="ID сенсора повинен бути більше 0")
    value: float = Field(..., description="Значення вимірювання")
    unit: str = Field("C", max_length=10)
    metadata_info: Optional[dict[str, Any]] = None

    @field_validator('value')
    def check_value_range(cls, v):
        if v < -273.15 or v > 5000:
            raise ValueError('Значення температури виходить за межі фізично можливих')
        return v

class MeasurementCreate(MeasurementBase):
    pass

class MeasurementResponse(MeasurementBase):
    id: int
    recorded_at: datetime
    prev_hash: str
    data_hash: str

    class Config:
        from_attributes = True

class MeasurementUpdate(BaseModel):
    value: Optional[float] = Field(None, description="Нове значення вимірювання")
    metadata_info: Optional[dict[str, Any]] = None

    @field_validator('value')
    def check_value_range(cls, v):
        if v is not None and (v < -273.15 or v > 5000):
            raise ValueError('Значення температури виходить за межі фізично можливих')
        return v