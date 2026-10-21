"""
Utilidades de dominio, cálculos geográficos, tiempos de despawn y normalización de spawns.
"""

import math
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from src.config import AUTO_COPIAR_PORTAPAPELES


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
