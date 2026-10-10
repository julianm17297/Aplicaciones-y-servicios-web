from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.mqtt.client import start_mqtt_client
from app.api import sensor, sensor_magnitud, medicion

# Variable para guardar la instancia del cliente y poder detenerla luego
mqtt_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- EVENTO DE INICIO (Startup) ---
    global mqtt_client
    print("Iniciando aplicación. Conectando al broker MQTT...")
    mqtt_client = start_mqtt_client()
    
    yield # Aquí FastAPI se queda corriendo y atendiendo peticiones HTTP
    
    # --- EVENTO DE APAGADO (Shutdown) ---
    print("Apagando aplicación. Desconectando cliente MQTT...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

app = FastAPI(title="API IoT - Taller 2", lifespan=lifespan)

app.include_router(sensor.router)
app.include_router(sensor_magnitud.router)
app.include_router(medicion.router)

@app.get("/")
def root():
    return {"mensaje": "La aplicación está en línea y escuchando MQTT."}