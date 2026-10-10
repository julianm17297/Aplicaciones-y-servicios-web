import json
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from pydantic import ValidationError
from app.database.connection import SessionLocal
from app.schemas.medicion import PayloadMQTT
from app.crud.medicion import procesar_y_guardar_payload

load_dotenv()

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = os.getenv("MQTT_TOPIC")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Conectado al Broker MQTT. Suscrito a: {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Error de conexión al broker MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode('utf-8')
    
    # Abrimos una sesión de base de datos específica para este mensaje
    db = SessionLocal()
    try:
        # 1. Decodificar el texto a un diccionario JSON
        data = json.loads(payload_str)
        
        # 2. Validar estructura, tipos y que el timestamp exista (Pydantic)
        payload_validado = PayloadMQTT(**data)
        
        # 3. Validar reglas de negocio (Catálogo, unidades, rangos) y Guardar (ORM)
        procesar_y_guardar_payload(db=db, payload=payload_validado)
        
        print(f"✅ [ÉXITO] Medición almacenada. Sensor: {payload_validado.sensor_id} | UTC: {payload_validado.timestamp}")
        
    except json.JSONDecodeError:
        print(f"❌ [RECHAZADO] El mensaje no es un JSON válido: {payload_str}")
    except ValidationError as e:
        # Aquí capturamos si falta un campo obligatorio o el timestamp está mal formateado
        print(f"❌ [RECHAZADO - Pydantic] Estructura inválida:\n{e.json()}")
    except ValueError as e:
        # Aquí capturamos los errores del CRUD (sensor inactivo, fuera de rango, unidad mala)
        print(f"❌ [RECHAZADO - Negocio] {e}")
    except RuntimeError as e:
        print(f"❌ [ERROR BD] Fallo al intentar guardar en PostgreSQL: {e}")
    except Exception as e:
        print(f"❌ [ERROR INESPERADO] {e}")
    finally:
        # Siempre debemos cerrar la sesión de la base de datos para no saturar PostgreSQL
        db.close()

def start_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    
    # loop_start() ejecuta la escucha en segundo plano sin bloquear el resto de la app
    client.loop_start() 
    return client