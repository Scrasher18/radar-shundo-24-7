"""
Utilidades de dominio, cálculos geográficos, tiempos de despawn y normalización de spawns.
"""

import math
import re
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.config import AUTO_COPIAR_PORTAPAPELES


HOTSPOTS_POKEMON_GO: Dict[str, Tuple[float, float, str]] = {
    "zaragoza": (41.6616, -0.8928, "Zaragoza, España"),
    "pier 39": (37.8087, -122.4098, "Pier 39, San Francisco"),
    "pier": (37.8087, -122.4098, "Pier 39, San Francisco"),
    "san francisco": (37.8087, -122.4098, "San Francisco, USA"),
    "central park": (40.7829, -73.9654, "Central Park, Nueva York"),
    "nyc": (40.7829, -73.9654, "Nueva York, USA"),
    "new york": (40.7829, -73.9654, "Nueva York, USA"),
    "tokyo": (35.6909, 139.7003, "Tokio, Japón"),
    "tokio": (35.6909, 139.7003, "Tokio, Japón"),
    "shinjuku": (35.6909, 139.7003, "Shinjuku, Tokio"),
    "sydney": (-33.8617, 151.2108, "Sídney, Australia"),
    "sidney": (-33.8617, 151.2108, "Sídney, Australia"),
    "sao paulo": (-23.5874, -46.6576, "Parque Ibirapuera, Brasil"),
    "ibirapuera": (-23.5874, -46.6576, "Parque Ibirapuera, Brasil"),
    "lima": (-12.1218, -77.0298, "Parque Kennedy, Lima"),
    "parque kennedy": (-12.1218, -77.0298, "Parque Kennedy, Lima"),
    "taipei": (25.0330, 121.5654, "Taipéi, Taiwán"),
    "londres": (51.5074, -0.1278, "Londres, Reino Unido"),
    "london": (51.5074, -0.1278, "Londres, Reino Unido"),
    "honolulu": (21.3069, -157.8583, "Honolulu, Hawái"),
    "hawaii": (21.3069, -157.8583, "Hawái, USA"),
    "dubai": (25.2048, 55.2708, "Dubái, EAU"),
    "larissa": (39.6390, 22.4191, "Larissa, Grecia"),
    "busan": (35.1587, 129.1604, "Busan, Corea del Sur"),
    "auckland": (-36.8485, 174.7633, "Auckland, Nueva Zelanda"),
}


def calcular_cooldown_minutos(distancia_km: float) -> int:
    """Calcula el tiempo de enfriamiento (cooldown) oficial de Pokémon GO según la distancia."""
    if distancia_km < 1.0:
        return 0
    elif distancia_km <= 3.0:
        return 2
    elif distancia_km <= 5.0:
        return 4
    elif distancia_km <= 10.0:
        return 7
    elif distancia_km <= 15.0:
        return 10
    elif distancia_km <= 20.0:
        return 15
    elif distancia_km <= 25.0:
        return 19
    elif distancia_km <= 30.0:
        return 22
    elif distancia_km <= 40.0:
        return 25
    elif distancia_km <= 50.0:
        return 30
    elif distancia_km <= 75.0:
        return 40
    elif distancia_km <= 100.0:
        return 45
    elif distancia_km <= 250.0:
        return 60
    elif distancia_km <= 500.0:
        return 75
    elif distancia_km <= 1000.0:
        return 90
    else:
        return 120


def formatear_distancia_y_cooldown(distancia_km: float) -> Tuple[str, str]:
    """Devuelve (texto_distancia, texto_cooldown con semáforo)."""
    if distancia_km < 1.0:
        dist_txt = f"{int(distancia_km * 1000)} m"
    else:
        dist_txt = f"{distancia_km:.1f} km"

    mins = calcular_cooldown_minutos(distancia_km)
    if mins == 0:
        cd_txt = "🟢 **¡Sin cooldown! (0 min - Inmediato)**"
    elif mins <= 15:
        cd_txt = f"🟢 **~{mins} min** *(Cooldown mínimo)*"
    elif mins <= 35:
        cd_txt = f"🟡 **~{mins} min** *(Cooldown moderado)*"
    elif mins <= 60:
        cd_txt = f"🟠 **~{mins} min** *(1 hora aprox.)*"
    else:
        cd_txt = f"🔴 **~{mins} min** *(Cooldown alto / 2h máx.)*"

    return dist_txt, cd_txt


def resolver_coordenadas_y_radio(texto: str) -> Optional[Tuple[float, float, Optional[int], str]]:
    """
    Interpreta coordenadas en formato 'lat, lng' o nombres de hotspots populares,
    extrayendo opcionalmente el radio (ej: '40.7128, -74.0060 radio 25' o 'zaragoza 30km').
    Retorna (lat, lng, radio_km, nombre_lugar) o None si no se reconoce.
    """
    limpio = texto.strip()
    if not limpio:
        return None

    # Detectar radio opcional (ej: "radio 25", "r 25", "25km", "radio: 30")
    radio_km: Optional[int] = None
    m_radio = re.search(r"(?:radio|r|\b)\s*[:=]?\s*(\d+)\s*(?:km|k)?\b", limpio, flags=re.IGNORECASE)
    # Extraer el radio si viene explícito
    m_radio_exp = re.search(r"\b(?:radio|r)\s*[:=]?\s*(\d+)\b", limpio, flags=re.IGNORECASE)
    if not m_radio_exp:
        m_radio_exp = re.search(r"\b(\d+)\s*km\b", limpio, flags=re.IGNORECASE)

    if m_radio_exp:
        try:
            val_r = int(m_radio_exp.group(1))
            if 1 <= val_r <= 20000:
                radio_km = val_r
                # Remover la parte del radio para aislar la coordenada o nombre
                limpio = limpio[:m_radio_exp.start()] + " " + limpio[m_radio_exp.end():]
                limpio = limpio.strip()
        except Exception:
            pass

    # 1. Verificar si coincide con coordenadas numéricas lat, lng
    m_coords = re.search(r"(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)", limpio)
    if m_coords:
        try:
            lat = float(m_coords.group(1))
            lng = float(m_coords.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0:
                nombre = f"{lat:.4f}, {lng:.4f}"
                return lat, lng, radio_km, nombre
        except Exception:
            pass

    # 2. Verificar si coincide con algún Hotspot popular
    low = limpio.lower().strip(",.- ")
    # Quitar palabras clave prefijo como "coords", "coordenadas", "ubicacion", "base"
    low = re.sub(r"^(?:coords|coordenadas|ubicacion|base|spot)\s+", "", low).strip()

    if low in HOTSPOTS_POKEMON_GO:
        lat, lng, nombre = HOTSPOTS_POKEMON_GO[low]
        return lat, lng, radio_km, nombre

    # Búsqueda parcial de hotspot
    for k, (lat, lng, nombre) in HOTSPOTS_POKEMON_GO.items():
        if k in low or low in k:
            return lat, lng, radio_km, nombre

    return None



def calcular_distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia ortodrómica (Haversine) en kilómetros entre dos coordenadas."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def calcular_tiempo_restante(
    despawn_iso: Optional[str] = None,
    despawn_ms: Optional[float] = None
) -> Tuple[str, int, Optional[int]]:
    """Convierte el tiempo de expiración (ISO o ms) en texto legible, segundos restantes y timestamp Unix."""
    ahora_ms = time.time() * 1000.0
    target_ms = None
    if despawn_ms:
        target_ms = float(despawn_ms)
    elif despawn_iso:
        try:
            dt = datetime.fromisoformat(despawn_iso.replace("Z", "+00:00"))
            target_ms = dt.timestamp() * 1000.0
        except Exception:
            pass
    if not target_ms:
        return "Desconocido", 0, None
    diff_sec = int((target_ms - ahora_ms) / 1000.0)
    despawn_unix = int(target_ms / 1000.0)
    if diff_sec <= 0:
        return "Expirado", -1, despawn_unix
    mins, secs = divmod(diff_sec, 60)
    return f"{mins}m {secs:02d}s", diff_sec, despawn_unix


def normalizar_spawn(existente: Optional[Dict[str, Any]], nuevo: Dict[str, Any]) -> Dict[str, Any]:
    """Combina campos de /search y /map/lookup para conservar el máximo detalle de cada Pokémon."""
    if not existente:
        existente = {}
    combinado = dict(existente)
    for k, v in nuevo.items():
        if v is not None and (k not in combinado or combinado[k] is None):
            combinado[k] = v
    return combinado


def copiar_al_portapapeles(texto: str) -> bool:
    """Copia coordenadas al portapapeles cuando se ejecuta en modo escritorio local."""
    if not AUTO_COPIAR_PORTAPAPELES or not texto or "," not in texto:
        return False
    try:
        subprocess.run(["clip"], input=texto.strip().encode("utf-8"), check=True)
        return True
    except Exception:
        return False
