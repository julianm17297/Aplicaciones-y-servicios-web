import json
import csv
import time
import requests
from datetime import datetime
from pathlib import Path


URL_BASE = "https://appsweb.quantaiot.co"
EQUIPO = "EQUIPO-05-APPSWEB"  #julian-daniel-mauricio
RUTA_MEDICIONES = "/api/v1/mediciones"

MAX_INTENTOS = 3
ESPERA_BASE_SEGUNDOS = 2
TIEMPO_ESPERA_TIMEOUT = 10

DIRECTORIO_BASE = Path(__file__).resolve().parent
DIRECTORIO_SALIDA = DIRECTORIO_BASE / "salida"
ARCHIVO_NORMALIZADAS = DIRECTORIO_SALIDA / "normalizadas.json"
ARCHIVO_REPORTE = DIRECTORIO_SALIDA / "reporte.json"
ARCHIVO_CONSULTA = DIRECTORIO_SALIDA / "consulta_final.json"

class DataProcessor:
    def __init__(self, ruta_json, ruta_csv):
        self.ruta_json = ruta_json
        self.ruta_csv = ruta_csv

    def procesar_todo(self):
        datos_crudos = []
        normalizadas = []
        bitacora = []

        print("Leyendo Proveedor A (JSON)...")
        datos_crudos.extend(self.procesar_json())
        
        print("Leyendo Proveedor B (CSV)...")
        datos_crudos.extend(self.procesar_csv())

        print("Normalizando y validando reglas de negocio...")
        for indice, crudo in enumerate(datos_crudos):
            base_trazabilidad = {
                "id_trazabilidad": crudo.get("id_trazabilidad", f"REG-{indice}"),
                "fuente": crudo.get("origen", "desconocida")
            }

            errores = self.validar_reglas(crudo)
            
            estado_val = "rechazado_localmente" if errores else "valido"
            normalizadas.append({
                **base_trazabilidad,
                "estado_validacion": estado_val,
                "errores_validacion": errores,
                "medicion": crudo
            })

            if errores:
                bitacora.append({
                    **base_trazabilidad,
                    "estado": "rechazado_localmente",
                    "motivo": "; ".join(errores),
                    "codigo_http": None, "intentos": 0, "respuesta_api": None
                })
            else:
                bitacora.append({
                    **base_trazabilidad,
                    "estado": "pendiente_envio",
                    "medicion": crudo
                })

        self.guardar_json(ARCHIVO_NORMALIZADAS, normalizadas)
        print(f"[INFO] Archivo guardado: {ARCHIVO_NORMALIZADAS}")
        return bitacora

    def validar_reglas(self, registro):
        errores = []
        lat = registro.get('latitud')
        if lat is None or not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            errores.append("Latitud fuera de rango o ausente")
            
        lon = registro.get('longitud')
        if lon is None or not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            errores.append("Longitud fuera de rango o ausente")
            
        hum = registro.get('humedad')
        if hum is None or not isinstance(hum, (int, float)) or not (0 <= hum <= 100):
            errores.append("Humedad fuera de rango o ausente")
            
        viento = registro.get('viento_kmh')
        if viento is None or not isinstance(viento, (int, float)) or viento < 0:
            errores.append("Viento negativo o ausente")
            
        if not registro.get('ciudad') or not registro.get('pais'):
            errores.append("Ciudad o país vacíos")
            
        if not registro.get('fecha_hora'):
            errores.append("Fecha ausente")
            
        return errores

    def procesar_json(self):
        datos = []
        with open(self.ruta_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for record in data.get('records', []):
                station = record.get('station', {})
                location = record.get('location', {})
                measurements = record.get('measurements', {})

                temp_f = measurements.get('temperature_f')
                temp_c = round((temp_f - 32) * 5.0 / 9.0, 2) if isinstance(temp_f, (int, float)) else None

                vel_ms = measurements.get('wind_speed_ms')
                viento_kmh = round(vel_ms * 3.6, 2) if isinstance(vel_ms, (int, float)) else None

                dato = {
                    "id_trazabilidad": record.get('provider_record_id', 'A-DESCONOCIDO'),
                    "ciudad": station.get('city_name'),
                    "pais": station.get('country_code'),
                    "latitud": location.get('lat'),
                    "longitud": location.get('lon'),
                    "temperatura_c": temp_c,
                    "humedad": measurements.get('relative_humidity'),
                    "viento_kmh": viento_kmh,
                    "fecha_hora": record.get('observed_at'),
                    "origen": "proveedor_a"
                }
                datos.append(dato)
        return datos

    def procesar_csv(self):
        datos = []
        with open(self.ruta_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                fecha_cruda = row.get('measurement_time', '')
                try:
                    fecha_obj = datetime.strptime(fecha_cruda, '%d/%m/%Y %H:%M')
                    # Añadimos la zona horaria por defecto de Colombia (-05:00) exigida por la API
                    fecha_iso = fecha_obj.strftime('%Y-%m-%dT%H:%M:%S') + "-05:00"
                except ValueError:
                    fecha_iso = None 

                def to_float(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return None

                dato = {
                    "id_trazabilidad": row.get('record_code', 'B-DESCONOCIDO'),
                    "ciudad": row.get('municipality'),
                    "pais": row.get('country'),
                    "latitud": to_float(row.get('latitude_deg')),
                    "longitud": to_float(row.get('longitude_deg')),
                    "temperatura_c": to_float(row.get('temp_celsius')),
                    "humedad": to_float(row.get('humidity_pct')),
                    "viento_kmh": to_float(row.get('wind_kmh')),
                    "fecha_hora": fecha_iso,
                    "origen": "proveedor_b"
                }
                datos.append(dato)
        return datos
    
    def guardar_json(self, ruta: Path, contenido):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(contenido, archivo, ensure_ascii=False, indent=2)

class ApiClient:
    def __init__(self, url_base, equipo_id):
        self.url = url_base.rstrip("/") + RUTA_MEDICIONES
        self.equipo_id = equipo_id

    def cabeceras(self):
        return {"Content-Type": "application/json", "X-Equipo": self.equipo_id}

    def enviar_registros(self, bitacora):
        sesion = requests.Session()
        print("\nIniciando envío HTTP a la API real...")

        for item in bitacora:
            if item["estado"] == "rechazado_localmente":
                continue

            medicion_completa = item.pop("medicion")
            
            # 💡 AQUÍ ESTÁ LA CLAVE: Creamos una copia exacta del diccionario 
            # pero eliminando 'id_trazabilidad' para que la API no devuelva error 422
            payload_api = {k: v for k, v in medicion_completa.items() if k != "id_trazabilidad"}
            
            resultado_envio = self._post_con_reintentos(sesion, payload_api)
            
            item["estado"] = resultado_envio["estado"]
            item["codigo_http"] = resultado_envio["codigo_http"]
            item["intentos"] = resultado_envio["intentos"]
            item["respuesta_api"] = resultado_envio["respuesta"]
            print(f" -> Registro {item['id_trazabilidad']} ({item['fuente']}): {item['estado']} (HTTP {item['codigo_http']})")

        consulta = self.consultar_resultado(sesion)
        return bitacora, consulta

    def _post_con_reintentos(self, sesion, medicion):
        ultimo_resultado = {
            "estado": "error_comunicacion", "codigo_http": None,
            "intentos": 0, "respuesta": None
        }

        for intento in range(1, MAX_INTENTOS + 1):
            try:
                resp = sesion.post(self.url, json=medicion, headers=self.cabeceras(), timeout=TIEMPO_ESPERA_TIMEOUT)
            except Exception as e:
                ultimo_resultado["intentos"] = intento
                ultimo_resultado["respuesta"] = {"error": str(e)}
                if intento < MAX_INTENTOS:
                    time.sleep(ESPERA_BASE_SEGUNDOS * intento)
                    continue
                return ultimo_resultado

            codigo = resp.status_code
            try:
                cuerpo = resp.json()
            except Exception:
                cuerpo = {"texto": resp.text[:200]}

            if codigo == 201:
                return {"estado": "aceptado_api", "codigo_http": codigo, "intentos": intento, "respuesta": cuerpo}
            
            if 400 <= codigo < 500:
                return {"estado": "rechazado_api", "codigo_http": codigo, "intentos": intento, "respuesta": cuerpo}
            
            if codigo >= 500:
                ultimo_resultado = {"estado": "error_comunicacion", "codigo_http": codigo, "intentos": intento, "respuesta": cuerpo}
                if intento < MAX_INTENTOS:
                    time.sleep(ESPERA_BASE_SEGUNDOS * intento)
                    continue
                return ultimo_resultado

            return {"estado": "respuesta_inesperada", "codigo_http": codigo, "intentos": intento, "respuesta": cuerpo}

        return ultimo_resultado

    def consultar_resultado(self, sesion):
        print("\nConsultando estado final en la API real (GET)...")
        try:
            resp = sesion.get(self.url, params={"equipo": self.equipo_id}, headers={"X-Equipo": self.equipo_id}, timeout=TIEMPO_ESPERA_TIMEOUT)
            cuerpo = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"texto": resp.text[:200]}
            
            resultado = {"codigo_http": resp.status_code, "respuesta": cuerpo}
            print(f" -> Consulta final exitosa. Código HTTP: {resp.status_code}")
            
            with open(ARCHIVO_CONSULTA, "w", encoding="utf-8") as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
                
            return resultado
        except Exception as e:
            print(f" -> Error al consultar la API: {e}")
            return {"codigo_http": None, "error": str(e)}

def generar_reporte_final(bitacora, consulta, total_procesados):
    validos = sum(1 for r in bitacora if r.get("estado") != "rechazado_localmente")
    rechazados_loc = sum(1 for r in bitacora if r.get("estado") == "rechazado_localmente")
    aceptados = sum(1 for r in bitacora if r.get("estado") == "aceptado_api")
    rechazados_api = sum(1 for r in bitacora if r.get("estado") == "rechazado_api")
    comunicacion = sum(1 for r in bitacora if r.get("estado") == "error_comunicacion")

    reporte = {
        "equipo": EQUIPO,
        "url_base": URL_BASE,
        "resumen": {
            "procesados": total_procesados,
            "normalizados": validos,
            "rechazados_localmente": rechazados_loc,
            "aceptados_api": aceptados,
            "rechazados_api": rechazados_api,
            "errores_comunicacion": comunicacion
        },
        "consulta_final": consulta,
        "detalle": bitacora
    }
    
    with open(ARCHIVO_REPORTE, "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Reporte final guardado en: {ARCHIVO_REPORTE}")

if __name__ == "__main__":
    ruta_json = "datos/proveedor_a.json"
    ruta_csv = "datos/proveedor_b.csv"

    with open(ruta_json, "r", encoding="utf-8") as f:
        total_a = len(json.load(f).get("records", []))
    with open(ruta_csv, "r", encoding="utf-8") as f:
        total_b = sum(1 for _ in f) - 1

    total_procesados = total_a + total_b

    procesador = DataProcessor(ruta_json, ruta_csv)
    cliente = ApiClient(URL_BASE, EQUIPO)

    bitacora_inicial = procesador.procesar_todo()
    bitacora_final, consulta_final = cliente.enviar_registros(bitacora_inicial)
    generar_reporte_final(bitacora_final, consulta_final, total_procesados)