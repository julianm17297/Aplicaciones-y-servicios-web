# Reporte de Evidencias

---

## 1. Recepción MQTT y Medición Válida

* **Prueba número:** 1 y 2
* **Datos de entrada:** Payload JSON emitido por el sensor asignado en el tópico `iot/sensors/GAS-003/data`:

```json
{
  "sensor_id": "GAS-003",
  "timestamp": "2026-10-10T00:56:45+00:00",
  "measurements": {
    "no2": {"value": 0.67, "unit": "ppm"},
    "co": {"value": 5.87, "unit": "ppm"},
    "temperature": {"value": 19.36, "unit": "C"},
    "humidity": {"value": 71.39, "unit": "%"}
  }
}
```

* **Resultado obtenido:** Mensaje recibido con éxito, validado correctamente y almacenado en la base de datos de PostgreSQL.
* **Registro de consola (Log):**

```text
[ÉXITO] Medición almacenada. Sensor: GAS-003 | UTC: 2026-10-10 00:56:45+00:00
```

* **Archivos y funciones relacionados:**
  * `app/mqtt/client.py`: función `on_message()`
  * `app/crud/medicion.py`: función `procesar_y_guardar_payload()`

* **Breve explicación:**  
  El cliente MQTT consumió el mensaje del tópico del grupo `GAS-003`, Pydantic validó la estructura del JSON y el ORM confirmó que el sensor estaba activo, que las magnitudes correspondían al catálogo, que las unidades eran exactas y que los valores se encontraban dentro de los rangos permitidos. Se almacenó cada magnitud como un registro independiente conservando la referencia UTC.

---

## 2. Timestamp / Estructura Inválida (Mensaje Rechazado)

* **Prueba número:** 7 (Timestamp inválido / Estructura incorrecta)
* **Datos de entrada:** Payload JSON malformado con un formato de fecha erróneo emitido de forma intencional por el sistema de pruebas:

```json
{
  "sensor_id": "GAS-003",
  "timestamp": "not-a-timestamp",
  "measurements": { ... }
}
```

* **Resultado obtenido:** El mensaje fue interceptado, analizado y rechazado de forma interna por la capa de validación sin afectar la ejecución del servidor ni contaminar la base de datos.
* **Registro de consola (Log):**

```text
[RECHAZADO - Pydantic] Estructura inválida:
[{"type": "datetime_from_date_parsing", "loc": ["timestamp"], "msg": "Input should be a valid datetime or date..."}]
```

* **Archivos y funciones relacionados:**
  * `app/mqtt/client.py`: bloque de excepción `except ValidationError as e` dentro de `on_message()`
  * `app/schemas/medicion.py`: modelo `PayloadMQTT`

* **Breve explicación:**  
  Pydantic actuó como filtro estricto al detectar que el campo `timestamp` no cumplía con el formato estándar ISO 8601 exigido. El error fue capturado y controlado de manera interna en el cliente MQTT, imprimiendo el aviso en consola y evitando que datos corruptos llegaran a PostgreSQL.