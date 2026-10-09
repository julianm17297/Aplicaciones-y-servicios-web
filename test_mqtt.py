import paho.mqtt.client as mqtt

BROKER = "emqx.coriotlab.co"
PORT = 1883
TOPIC = "iot/sensors/GAS-003/data"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado exitosamente al Broker MQTT. Suscribiéndose al tópico: {TOPIC}")
        client.subscribe(TOPIC)
    else:
        print(f"Falla en la conexión, código de error: {rc}")

def on_message(client, userdata, msg):
    print(f"\n[MENSAJE RECIBIDO] Tópico: {msg.topic}")
    print(f"Payload: {msg.payload.decode('utf-8')}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()

print("Escuchando mensajes MQTT... Presiona Ctrl+C para salir.")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("\nFinalizando cliente MQTT de prueba.")
    client.loop_stop()
    client.disconnect()