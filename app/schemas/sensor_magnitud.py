from pydantic import BaseModel
from decimal import Decimal

class SensorMagnitudOut(BaseModel):
    id: int
    sensor_id: int
    magnitud: str
    unidad: str
    valor_minimo: Decimal
    valor_maximo: Decimal

    class Config:
        from_attributes = True