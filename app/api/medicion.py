from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.medicion import Medicion
from app.models.sensor_magnitud import SensorMagnitud
from app.crud.sensor import get_sensor

router = APIRouter(tags=["Mediciones"])

# Esquema de salida para convertir UTC a hora Colombia en los GET
class MedicionOut(BaseModel):
    id: int
    sensor_magnitud_id: int
    valor: float
    timestamp_local: str  # Convertido a hora Colombia legible
    fecha_recepcion_local: str

    class Config:
        from_attributes = True

def convertir_a_colombia(dt_utc: datetime) -> str:
    if not dt_utc:
        return ""
    
    # Hora Colombia es UTC-5 fija
    colombia_tz = timezone(timedelta(hours=-5))
    
    # Si la fecha viene sin zona horaria, asumimos UTC
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    
    # Convertir a hora Colombia (UTC-5)
    dt_col = dt_utc.astimezone(colombia_tz)
    return dt_col.strftime("%Y-%m-%d %H:%M:%S")

@router.get("/mediciones/{id}", response_model=MedicionOut)
def obtener_medicion(id: int, db: Session = Depends(get_db)):
    med = db.query(Medicion).filter(Medicion.id == id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    
    return {
        "id": med.id,
        "sensor_magnitud_id": med.sensor_magnitud_id,
        "valor": float(med.valor),
        "timestamp_local": convertir_a_colombia(med.timestamp_utc),
        "fecha_recepcion_local": convertir_a_colombia(med.fecha_recepcion)
    }

@router.get("/sensores/{id}/mediciones", response_model=List[MedicionOut])
def listar_mediciones_sensor(
    id: int,
    magnitud: Optional[str] = None,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    limit: Optional[int] = Query(None, gt=0),
    db: Session = Depends(get_db)
):
    # Validar existencia del sensor
    sensor = get_sensor(db, id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    # Validar lógica de fechas (desde > hasta arroja código HTTP 400)
    if desde and hasta and desde > hasta:
        raise HTTPException(status_code=400, detail="La fecha 'desde' no puede ser mayor que 'hasta'")

    # Consulta base uniendo explícitamente Medicion y SensorMagnitud
    query = db.query(Medicion).join(
        SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id
    ).filter(SensorMagnitud.sensor_id == id)

    # Filtrar por magnitud si se envía el parámetro
    if magnitud:
        query = query.filter(SensorMagnitud.magnitud == magnitud)

    # Filtrar por rango de fechas
    if desde:
        query = query.filter(Medicion.timestamp_utc >= desde)
    if hasta:
        query = query.filter(Medicion.timestamp_utc <= hasta)

    # Ordenar por fecha descendente y aplicar límite
    query = query.order_by(Medicion.timestamp_utc.desc())
    if limit:
        query = query.limit(limit)

    mediciones = query.all()

    # Formatear la salida a hora local de Colombia
    resultado = []
    for med in mediciones:
        resultado.append({
            "id": med.id,
            "sensor_magnitud_id": med.sensor_magnitud_id,
            "valor": float(med.valor),
            "timestamp_local": convertir_a_colombia(med.timestamp_utc),
            "fecha_recepcion_local": convertir_a_colombia(med.fecha_recepcion)
        })
    return resultado

@router.get("/sensores/{id}/ultima-medicion")
def obtener_ultima_medicion(id: int, db: Session = Depends(get_db)):
    sensor = get_sensor(db, id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    med = db.query(Medicion).join(
        SensorMagnitud, Medicion.sensor_magnitud_id == SensorMagnitud.id
    ).filter(
        SensorMagnitud.sensor_id == id
    ).order_by(Medicion.timestamp_utc.desc()).first()

    if not med:
        raise HTTPException(status_code=404, detail="No hay mediciones registradas para este sensor")

    return {
        "id": med.id,
        "sensor_magnitud_id": med.sensor_magnitud_id,
        "valor": float(med.valor),
        "timestamp_local": convertir_a_colombia(med.timestamp_utc),
        "fecha_recepcion_local": convertir_a_colombia(med.fecha_recepcion)
    }