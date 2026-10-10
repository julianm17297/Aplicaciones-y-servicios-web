from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.crud.sensor import get_sensores, get_sensor, get_sensor_por_codigo
from app.schemas.sensor import SensorOut

router = APIRouter(prefix="/sensores", tags=["Sensores"])

@router.get("/", response_model=List[SensorOut])
def listar_sensores(db: Session = Depends(get_db)):
    return get_sensores(db)

@router.get("/por-codigo/{codigo}", response_model=SensorOut)
def obtener_sensor_por_codigo(codigo: str, db: Session = Depends(get_db)):
    sensor = get_sensor_por_codigo(db, codigo)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado por código")
    return sensor

@router.get("/{id}", response_model=SensorOut)
def obtener_sensor_por_id(id: int, db: Session = Depends(get_db)):
    sensor = get_sensor(db, id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor