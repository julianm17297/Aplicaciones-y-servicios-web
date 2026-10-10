from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.crud.sensor_magnitud import get_magnitudes_por_sensor, get_magnitud
from app.schemas.sensor_magnitud import SensorMagnitudOut
from app.crud.sensor import get_sensor

router = APIRouter(tags=["Magnitudes"])

@router.get("/sensores/{id}/magnitudes", response_model=List[SensorMagnitudOut])
def listar_magnitudes_de_sensor(id: int, db: Session = Depends(get_db)):
    sensor = get_sensor(db, id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return get_magnitudes_por_sensor(db, id)

@router.get("/sensor-magnitudes/{id}", response_model=SensorMagnitudOut)
def obtener_sensor_magnitud(id: int, db: Session = Depends(get_db)):
    mag = get_magnitud(db, id)
    if not mag:
        raise HTTPException(status_code=404, detail="Configuración de magnitud no encontrada")
    return mag