from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime

class MeasurementValue(BaseModel):
    value: float
    unit: str

class PayloadMQTT(BaseModel):
    sensor_id: str = Field(..., description="Código del sensor, ej. GAS-003")
    timestamp: datetime = Field(..., description="Timestamp en formato UTC")
    measurements: Dict[str, MeasurementValue] = Field(..., description="Diccionario de magnitudes")