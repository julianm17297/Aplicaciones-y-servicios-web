# Análisis Técnico — Taller 1: Integración de Datos entre Aplicaciones

**Equipo:** EQUIPO-05-APPSWEB  
**Autor:** Julián-daniel-mauricio

---

## 1. Diferencias encontradas entre los contratos de los proveedores

Durante la fase de análisis exploratorio de los datasets suministrados, se identificaron divergencias estructurales significativas entre las fuentes de origen y el contrato institucional:

* **Proveedor A (JSON):** Presenta una estructura jerárquica anidada y distribuida en objetos lógicos (`station`, `location`, `measurements`). Utiliza nomenclaturas en inglés con unidades anglosajonas (temperatura en Fahrenheit y velocidad del viento en metros por segundo). Además, las marcas de tiempo se encuentran en formato ISO 8601 con sufijo universal UTC (`Z`).
* **Proveedor B (CSV):** Se presenta como un archivo plano tabular delimitado por punto y coma (`;`). Sus campos manejan nombres completamente diferentes (ej. `municipality` en lugar de `city_name`) y las fechas vienen en un formato plano de texto (`dd/mm/YYYY HH:MM`) sin información explícita de zona horaria.

## 2. Transformaciones necesarias aplicadas

Para homologar ambas fuentes al contrato institucional, el cliente integrador implementó las siguientes transformaciones de datos:
1. **Normalización de Unidades:** Conversión de grados Fahrenheit a Celsius mediante la fórmula $(F - 32) \times \frac{5}{9}$ y conversión de velocidad del viento multiplicando los metros por segundo por un factor de $3.6$ para obtener kilómetros por hora.
2. **Homologación Temporal:** Estandarización de las fechas del Proveedor B al formato ISO 8601 añadiendo el desfase de la zona horaria local de Colombia (`-05:00`), garantizando la compatibilidad con el esquema estricto de validación del servidor.
3. **Mapeo de Campos:** Reestructuración de diccionarios anidados (JSON) y filas tabulares (CSV) a un esquema plano unificado de 9 campos obligatorios (`ciudad`, `pais`, `latitud`, `longitud`, `temperatura_c`, `humedad`, `viento_kmh`, `fecha_hora`, `origen`).

## 3. Tipos de errores encontrados antes de enviar información

El sistema clasifica los incidentes detectados de forma previa al envío en dos grandes categorías operativas:
* **Errores de Normalización:** Registros con anomalías de sintaxis o tipos de datos imposibles de castear (ej. cadenas vacías en campos numéricos, archivos JSON corruptos o filas de CSV con columnas sobrantes). Estos registros se descartan de la salida institucional y se documentan en el reporte.
* **Errores de Validación Local:** Registros que superan el casteo técnico pero incumplen las reglas de negocio del contrato (ej. humedades superiores al 100%, valores de viento negativos o coordenadas geográficas fuera de los rangos globales válidos entre $-90$ y $90$ para latitud). Estos registros sí se conservan en `salida/normalizadas.json` pero se retienen localmente para evitar solicitudes innecesarias al servidor.

## 4. Diferencias entre validación local y validación del servidor

La **validación local** actúa como un filtro preventivo y económico que protege los recursos de red ejecutando comprobaciones de rangos físicos y lógicos (coordenadas, límites de sensores). Por su parte, la **validación del servidor** (ejecutada por la API del docente) representa la autoridad final de negocio; esta evalúa restricciones más profundas que escapan al alcance local, tales como la integridad relacional, el rechazo de payloads que incluyan atributos no autorizados (ej. campos de trazabilidad interna) o la detección de conflictos por duplicidad de registros (código HTTP 409).

## 5. Decisión de implementación más importante

La decisión arquitectónica más crítica fue **desacoplar el identificador interno de trazabilidad (`id_trazabilidad`) del cuerpo de la petición HTTP (`payload`) enviado a la API**. Aunque el motor genera un código único de seguimiento para cada registro y lo documenta rigurosamente en el reporte final y en `normalizadas.json`, este campo es excluido deliberadamente justo antes de realizar el método `POST` al servidor. Esto evitó de manera directa el rechazo masivo por errores de tipo `422 Unprocessable Entity` (exceso de parámetros no permitidos), cumpliendo estrictamente con el contrato institucional.

---

## Evidencia Resuelta de Ejecución Real

* **Cantidad total de registros procesados:** 400
* **Cantidad normalizada con éxito:** 385
* **Cantidad rechazada localmente:** 15
* **Cantidad enviada a la API:** 385
* **Cantidad aceptada por la API (HTTP 201):** 190
* **Cantidad rechazada por la API (HTTP 409 / 422):** 195 (Debido a registros duplicados por pruebas previas y validaciones de esquema del servidor).