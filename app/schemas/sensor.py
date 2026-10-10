from pydantic import BaseModel
from datetime import datetime

class SensorOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    categoria: str
    ubicacion: str
    activo: bool
    fecha_registro: datetime

    class Config:
        from_attributes = True