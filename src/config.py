"""
Configuración centralizada del proyecto, constantes globales, ligas PvP y credenciales.
Separa completamente la configuración de la lógica de negocio.
"""

import json
import os
import sys
from typing import Any, Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_LOCAL_FILE = os.path.join(BASE_DIR, "config_local.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache_coordenadas.json")
NOTIFICADOS_FILE = os.path.join(BASE_DIR, "shundos_notificados.json")


def cargar_config_local() -> Dict[str, Any]:
    """Carga variables locales desde config_local.json si existe (entorno de desarrollo)."""
    if os.path.exists(CONFIG_LOCAL_FILE):
        try:
            with open(CONFIG_LOCAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


_cfg = cargar_config_local()

# Credenciales y Webhooks por canal
JWT_TOKEN: str = os.environ.get("JWT_TOKEN") or _cfg.get("JWT_TOKEN", "")
DISCORD_WEBHOOK_URL: str = os.environ.get("DISCORD_WEBHOOK_URL") or _cfg.get("DISCORD_WEBHOOK_URL", "")
DISCORD_WEBHOOK_GL: str = os.environ.get("DISCORD_WEBHOOK_GL") or _cfg.get("DISCORD_WEBHOOK_GL", "")
DISCORD_WEBHOOK_UL: str = os.environ.get("DISCORD_WEBHOOK_UL") or _cfg.get("DISCORD_WEBHOOK_UL", "")
DISCORD_USER_ID_MENCION: str = os.environ.get("DISCORD_USER_ID_MENCION") or _cfg.get("DISCORD_USER_ID_MENCION", "924392800534011935")

ES_MODO_NUBE: bool = os.environ.get("CLOUD_MODE") == "1" or sys.platform != "win32"
AUTO_COPIAR_PORTAPAPELES: bool = not ES_MODO_NUBE

WEBHOOKS_POR_CANAL: Dict[str, str] = {
    "shundo": DISCORD_WEBHOOK_URL,
    "great": DISCORD_WEBHOOK_GL,
    "ultra": DISCORD_WEBHOOK_UL,
}

BOT_NOMBRES_POR_CANAL: Dict[str, str] = {
    "shundo": "Radar Shundo Pro ✨",
    "great": "Radar PvP Great League 🔵✨",
    "ultra": "Radar PvP Ultra League 🟣✨",
}

# Coordenadas base de referencia
LAT_ORIGEN: float = -12.058662
LNG_ORIGEN: float = -77.036896

# Parámetros operativos del motor 24/7
MODO_VIGILANTE_CONTINUO: bool = True
INTERVALO_SEGUNDOS: int = 480              # Escaneo de nuevos spawns cada 8 minutos (480s)
MIN_SEGUNDOS_VIDA: int = 90                # Ignorar spawns con menos de 90s restantes
PVP_TOP_RANK_MAX: int = 5                  # Filtrar Rank #1 al #5 en Great League y Ultra League
TTL_LIMPIEZA_CACHE_SEGUNDOS: int = 7200    # Limpiar registros ya expirados después de 2 horas
MAX_REVEALS_POR_EJECUCION: int = 65

# Endpoints y cabeceras HTTP
API_BASE: str = "https://coordinates-api.pokemongopro.com"

HEADERS_API: Dict[str, str] = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

# Regiones globales que cubren los 5 continentes habitados en /map/lookup
REGIONES_GLOBALES: List[Tuple[str, float, float, float, float]] = [
    ("Norteamérica (Este)", 55.0, -98.0, 24.0, -60.0),
    ("Norteamérica (Oeste y Centro)", 55.0, -135.0, 14.0, -98.0),
    ("Sudamérica", 13.0, -85.0, -55.0, -34.0),
    ("Europa Occidental", 65.0, -12.0, 35.0, 16.0),
    ("Europa Oriental y Medio Oriente", 65.0, 16.0, 25.0, 60.0),
    ("Asia Oriental (Japón, Corea, Taiwán)", 48.0, 112.0, 20.0, 150.0),
    ("Sudeste Asiático e India", 24.0, 68.0, -11.0, 125.0),
    ("Oceanía (Australia y Nueva Zelanda)", -10.0, 112.0, -48.0, 180.0),
]

# Particiones de búsqueda directa (/search)
PARTICIONES_SHUNDOS: List[Dict[str, Any]] = [
    {"label": "100% Shundos (DSP)", "iv_percent_min": 100, "iv_percent_max": 100, "sort": "DSP"},
    {"label": "100% Shundos (CP)", "iv_percent_min": 100, "iv_percent_max": 100, "sort": "CP"},
]

PARTICIONES_PVP_GL: List[Dict[str, Any]] = [
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "CP"},
]

PARTICIONES_PVP_UL: List[Dict[str, Any]] = [
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "CP"},
]
