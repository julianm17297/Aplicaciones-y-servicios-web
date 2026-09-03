import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
RUTA_CSV = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_JSON = BASE_DIR / "salida" / "estudiantes_resumen.json"

def leer_estudiantes(ruta: Path) -> list[dict]:
    """Lee el archivo CSV y devuelve una lista de diccionarios."""
    with open(ruta, encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        return list(lector)

def transformar_estudiante(fila: dict) -> dict:
    """Convierte una fila del CSV al formato del panel académico."""
    return {
        "id": fila["codigo"],
        "nombre_completo": f"{fila['nombre']} {fila['apellido']}",
        "programa": fila["programa"],
        "semestre": int(fila["semestre"]),
        "promedio": float(fila["promedio"]),
        "estado": "Activo" if fila["activo"] == "true" else "Inactivo",
    }

def serializar_estudiantes(ruta: Path, estudiantes: list[dict]) -> None:
    """Serializa una lista de diccionarios Python a un archivo JSON UTF-8."""
    ruta.parent.mkdir(exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(estudiantes, archivo, indent=2, ensure_ascii=False)

def deserializar_estudiantes(ruta: Path) -> list[dict]:
    """Deserializa un archivo JSON a una lista de diccionarios Python."""
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)

estudiantes = leer_estudiantes(RUTA_CSV)
print(f"Registros leidos: {len(estudiantes)}")

estudiantes_transformados = [transformar_estudiante(fila) for fila in estudiantes]
print(f"Registros transformados: {len(estudiantes_transformados)}")

serializar_estudiantes(RUTA_JSON, estudiantes_transformados)
print(f"Archivo JSON generado: {RUTA_JSON}")

estudiantes_recuperados = deserializar_estudiantes(RUTA_JSON)
print("\nDatos recuperados desde el JSON:")
print(estudiantes_recuperados[0])
print(f"Total recuperado: {len(estudiantes_recuperados)}")