from sqlalchemy.orm import Session
from app.models.sensor import Sensor
from app.models.sensor_magnitud import SensorMagnitud
from app.models.medicion import Medicion
from app.schemas.medicion import PayloadMQTT

def procesar_y_guardar_payload(db: Session, payload: PayloadMQTT):
    # 1. Validar existencia y estado del sensor por su 'codigo'
    sensor = db.query(Sensor).filter(Sensor.codigo == payload.sensor_id).first()
    if not sensor:
        raise ValueError(f"Sensor {payload.sensor_id} no existe en el catálogo.")
    if not sensor.activo:
        raise ValueError(f"Sensor {payload.sensor_id} está inactivo.")

    nuevas_mediciones = []

    # 2. Iterar sobre las magnitudes del payload
    for mag_nombre, mag_data in payload.measurements.items():
        
        # Consultar la configuración específica de ESA magnitud para ESTE sensor
        config_magnitud = db.query(SensorMagnitud).filter(
            SensorMagnitud.sensor_id == sensor.id,
            SensorMagnitud.magnitud == mag_nombre
        ).first()
        
        if not config_magnitud:
            raise ValueError(f"El sensor {sensor.codigo} no tiene configurada la magnitud '{mag_nombre}'.")
        
        # 3. Validar unidad correspondiente
        if config_magnitud.unidad != mag_data.unit:
            raise ValueError(f"Unidad incorrecta para {mag_nombre}. Esperada: {config_magnitud.unidad}, Recibida: {mag_data.unit}.")
            
        # 4. Validar rangos (valor_minimo y valor_maximo)
        if not (config_magnitud.valor_minimo <= mag_data.value <= config_magnitud.valor_maximo):
            raise ValueError(f"Valor {mag_data.value} fuera de rango para {mag_nombre} (Min: {config_magnitud.valor_minimo}, Max: {config_magnitud.valor_maximo}).")

        # 5. Preparar registro de medición conservando timestamp_utc
        nueva_medicion = Medicion(
            sensor_magnitud_id=config_magnitud.id,
            valor=mag_data.value,
            timestamp_utc=payload.timestamp # Pydantic ya lo convirtió a objeto datetime validado
        )
        nuevas_mediciones.append(nueva_medicion)

    # 6. Regla "Todo o Nada": Guardar solo si todas las magnitudes fueron válidas
    try:
        db.add_all(nuevas_mediciones)
        db.commit()
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Error en base de datos al guardar mediciones: {str(e)}")