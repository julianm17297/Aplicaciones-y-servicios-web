from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal

class MedicionBase(BaseModel):
    estudiante_id: int
    variable: str
    valor: Decimal
    unidad: str
    fecha_hora: datetime

class MedicionCreate(MedicionBase):
    pass

class MedicionUpdate(BaseModel):
    estudiante_id: int | None = None
    variable: str | None = None
    valor: Decimal | None = None
    unidad: str | None = None
    fecha_hora: datetime | None = None

class MedicionResponse(MedicionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int