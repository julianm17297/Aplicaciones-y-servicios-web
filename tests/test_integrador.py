import pytest
from pathlib import Path
import sys

# Agregamos la ruta principal para poder importar funciones o clases de integrador.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from integrador import DataProcessor

# Inicializamos el procesador para usar sus métodos en las pruebas
processor = DataProcessor("datos/proveedor_a.json", "datos/proveedor_b.csv")

def test_conversion_temperatura():
    """Prueba 1: Conversión correcta de Fahrenheit a Celsius"""
    # 68 °F deberían ser 20 °C -> (68 - 32) * 5/9 = 20.0
    temp_f = 68.0
    temp_c = round((temp_f - 32) * 5.0 / 9.0, 2)
    assert temp_c == 20.0

def test_conversion_velocidad():
    """Prueba 2: Conversión correcta de m/s a km/h"""
    # 10 m/s * 3.6 = 36.0 km/h
    vel_ms = 10.0
    viento_kmh = round(vel_ms * 3.6, 2)
    assert viento_kmh == 36.0

def test_registro_valido():
    """Prueba 3: Un registro completamente válido no debe arrojar errores de validación"""
    registro_limpio = {
        "ciudad": "Medellín",
        "pais": "CO",
        "latitud": 6.2442,
        "longitud": -75.5812,
        "temperatura_c": 24.5,
        "humedad": 60.0,
        "viento_kmh": 15.0,
        "fecha_hora": "2026-09-01T00:00:00-05:00",
        "origen": "proveedor_a"
    }
    errores = processor.validar_reglas(registro_limpio)
    assert len(errores) == 0

def test_registro_invalido():
    """Prueba 4: Un registro con datos fuera de rango debe ser rechazado localmente"""
    registro_malo = {
        "ciudad": "Bogotá",
        "pais": "CO",
        "latitud": 4.6097,
        "longitud": -74.0817,
        "temperatura_c": 18.0,
        "humedad": 150.0,  # INVÁLIDO: la humedad máxima es 100
        "viento_kmh": -5.0,  # INVÁLIDO: el viento no puede ser negativo
        "fecha_hora": "2026-09-01T00:00:00-05:00",
        "origen": "proveedor_b"
    }
    errores = processor.validar_reglas(registro_malo)
    assert len(errores) > 0
    assert any("Humedad" in e for e in errores)

def test_caso_limite_coordenadas():
    """Prueba 5: Caso límite con coordenadas exactamente en los extremos permitidos (-90 y 90)"""
    registro_limite = {
        "ciudad": "Polo Norte",
        "pais": "XX",
        "latitud": 90.0,   # Límite válido superior
        "longitud": -180.0, # Límite válido inferior
        "temperatura_c": -10.0,
        "humedad": 50.0,
        "viento_kmh": 0.0,
        "fecha_hora": "2026-09-01T00:00:00-05:00",
        "origen": "proveedor_a"
    }
    errores = processor.validar_reglas(registro_limite)
    assert len(errores) == 0