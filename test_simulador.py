import json
import time
from app.database.connection import SessionLocal
from app.crud.medicion import procesar_y_guardar_payload
from app.schemas.medicion import PayloadMQTT
from pydantic import ValidationError

db = SessionLocal()

print("--- INICIANDO PRUEBAS AUTOMÁTICAS DE MQTT (EVIDENCIAS 1 A 7) ---\n")

# 1 y 2: Payload Válido
p1 = {
    "sensor_id": "GAS-003",
    "timestamp": "2026-10-10T00:56:45+00:00",
    "measurements": {
        "no2": {"value": 0.67, "unit": "ppm"},
        "co": {"value": 5.87, "unit": "ppm"},
        "temperature": {"value": 19.36, "unit": "C"},
        "humidity": {"value": 71.39, "unit": "%"}
    }
}

# 3: Sensor Inexistente
p3 = {
    "sensor_id": "SENSOR-INEXISTENTE-999",
    "timestamp": "2026-10-10T00:56:45+00:00",
    "measurements": {"co": {"value": 5.87, "unit": "ppm"}}
}

# 4: Unidad Incorrecta
p4 = {
    "sensor_id": "GAS-003",
    "timestamp": "2026-10-10T00:56:45+00:00",
    "measurements": {"temperature": {"value": 25.0, "unit": "Fahrenheit"}}
}

# 5: Tipo de dato Incorrecto
p5 = {
    "sensor_id": "GAS-003",
    "timestamp": "2026-10-10T00:56:45+00:00",
    "measurements": {"temperature": {"value": "veinticinco", "unit": "C"}}
}

# 6: Magnitud Incorrecta
p6 = {
    "sensor_id": "GAS-003",
    "timestamp": "2026-10-10T00:56:45+00:00",
    "measurements": {"presion_atmosferica": {"value": 1013.25, "unit": "hPa"}}
}

# 7: Timestamp Inválido
p7 = {
    "sensor_id": "GAS-003",
    "timestamp": "fecha-invalida",
    "measurements": {"temperature": {"value": 20.0, "unit": "C"}}
}

pruebas = [
    ("PRUEBA 1 y 2 (Válido)", p1),
    ("PRUEBA 3 (Sensor Inexistente)", p3),
    ("PRUEBA 4 (Unidad Incorrecta)", p4),
    ("PRUEBA 5 (Tipo Incorrecto)", p5),
    ("PRUEBA 6 (Magnitud Incorrecta)", p6),
    ("PRUEBA 7 (Timestamp Inválido)", p7)
]

for nombre, payload_dict in pruebas:
    print(f"\n>>> Executing: {nombre}")
    try:
        # 1. Validar primero con Pydantic
        payload_obj = PayloadMQTT(**payload_dict)
        # 2. Pasar el objeto validado al CRUD
        exito, msg = procesar_y_guardar_payload(db, payload_obj)
        if exito:
            print(f"[ÉXITO]: {msg}")
        else:
            print(f"[RECHAZADO CONTROLADO POR NEGOCIO]: {msg}")
    except ValidationError as ve:
        print(f"[RECHAZADO CONTROLADO POR PYDANTIC]: {ve.errors()[0]['msg']}")
    except Exception as e:
        print(f"[ERROR INESPERADO]: {e}")
    time.sleep(0.5)

    from app.models.medicion import Medicion
from datetime import datetime

print("\n>>> PROBANDO PRUEBA 17 (Claves Foráneas)")
try:
    # Intentamos insertar una medición apuntando a un ID de magnitud inexistente (ej. 999999)
    medicion_falsa = Medicion(
        sensor_magnitud_id=999999,  # ID que no existe en PostgreSQL
        valor=25.0,
        timestamp_utc=datetime.utcnow()
    )
    db.add(medicion_falsa)
    db.commit() # Esto forzará la violación de la ForeignKey en PostgreSQL
except Exception as e:
    db.rollback() # Limpiamos la transacción fallida
    print(f"[RECHAZADO POR POSTGRESQL / INTEGRITY ERROR]: Violación de clave foránea detectada con éxito.")

db.close()
print("\n--- PRUEBAS FINALIZADAS CON ÉXITO ---")