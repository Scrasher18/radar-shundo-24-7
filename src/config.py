"""
Configuración centralizada del proyecto, constantes globales, ligas PvP y credenciales.
Separa completamente la configuración de la lógica de negocio.
"""

from base64 import urlsafe_b64decode, urlsafe_b64encode
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_LOCAL_FILE = os.path.join(BASE_DIR, "config_local.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache_coordenadas.json")
NOTIFICADOS_FILE = os.path.join(BASE_DIR, "shundos_notificados.json")
EVENTO_CONFIG_FILE = os.path.join(BASE_DIR, "evento_config.json")


def cargar_config_local() -> Dict[str, Any]:
    """Carga variables locales desde config_local.json si existe (entorno de desarrollo)."""
    if os.path.exists(CONFIG_LOCAL_FILE):
        try:
            with open(CONFIG_LOCAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def extraer_exp_jwt(token_str: str) -> int:
    """Extrae el timestamp Unix de expiración ('exp') de un JWT sin verificar firma."""
    try:
        partes = token_str.strip().split(".")
        if len(partes) < 2:
            return 0
        payload_b64 = partes[1] + "=" * (-len(partes[1]) % 4)
        data = json.loads(urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8"))
        return int(data.get("exp") or 0)
    except Exception:
        return 0


def cifrar_jwt_con_secreto(jwt_str: str, secreto: str) -> str:
    """Cifra simétricamente el JWT usando DISCORD_BOT_TOKEN para guardarlo seguro en evento_config.json."""
    if not jwt_str or not secreto:
        return ""
    raw = jwt_str.encode("utf-8")
    out = bytearray(len(raw))
    key_bytes = secreto.encode("utf-8")
    bloque_idx = 0
    pos = 0
    while pos < len(raw):
        digest = hashlib.sha256(key_bytes + f":{bloque_idx}".encode("utf-8")).digest()
        for b in digest:
            if pos >= len(raw):
                break
            out[pos] = raw[pos] ^ b
            pos += 1
        bloque_idx += 1
    return urlsafe_b64encode(bytes(out)).decode("utf-8")


def descifrar_jwt_con_secreto(cifrado_b64: str, secreto: str) -> str:
    """Descifra el JWT guardado en evento_config.json usando DISCORD_BOT_TOKEN."""
    if not cifrado_b64 or not secreto:
        return ""
    try:
        enc = urlsafe_b64decode(cifrado_b64.encode("utf-8"))
        out = bytearray(len(enc))
        key_bytes = secreto.encode("utf-8")
        bloque_idx = 0
        pos = 0
        while pos < len(enc):
            digest = hashlib.sha256(key_bytes + f":{bloque_idx}".encode("utf-8")).digest()
            for b in digest:
                if pos >= len(enc):
                    break
                out[pos] = enc[pos] ^ b
                pos += 1
            bloque_idx += 1
        texto = bytes(out).decode("utf-8")
        return texto if texto.startswith("eyJ") else ""
    except Exception:
        return ""


_cfg = cargar_config_local()

# Credenciales y Webhooks por canal
DISCORD_WEBHOOK_URL: str = os.environ.get("DISCORD_WEBHOOK_URL") or _cfg.get("DISCORD_WEBHOOK_URL", "")
DISCORD_WEBHOOK_GL: str = os.environ.get("DISCORD_WEBHOOK_GL") or _cfg.get("DISCORD_WEBHOOK_GL", "")
DISCORD_WEBHOOK_UL: str = os.environ.get("DISCORD_WEBHOOK_UL") or _cfg.get("DISCORD_WEBHOOK_UL", "")
DISCORD_WEBHOOK_EVENTO: str = os.environ.get("DISCORD_WEBHOOK_EVENTO") or _cfg.get("DISCORD_WEBHOOK_EVENTO", "")
DISCORD_EVENTO_CHANNEL_ID: str = os.environ.get("DISCORD_EVENTO_CHANNEL_ID") or _cfg.get("DISCORD_EVENTO_CHANNEL_ID", "1562344305606262846")
DISCORD_BOT_TOKEN: str = os.environ.get("DISCORD_BOT_TOKEN") or _cfg.get("DISCORD_BOT_TOKEN", "")
DISCORD_USER_ID_MENCION: str = os.environ.get("DISCORD_USER_ID_MENCION") or _cfg.get("DISCORD_USER_ID_MENCION", "924392800534011935")


def resolver_jwt_mas_reciente() -> str:
    """Selecciona automáticamente el JWT más reciente entre variables de entorno, config_local y el renovado por Discord."""
    candidato_base = os.environ.get("JWT_TOKEN") or _cfg.get("JWT_TOKEN", "")
    exp_base = extraer_exp_jwt(candidato_base)
    if os.path.exists(EVENTO_CONFIG_FILE) and DISCORD_BOT_TOKEN:
        try:
            with open(EVENTO_CONFIG_FILE, "r", encoding="utf-8") as f:
                ev_data = json.load(f)
            jwt_cif = ev_data.get("jwt_cifrado", "")
            if jwt_cif:
                jwt_desc = descifrar_jwt_con_secreto(jwt_cif, DISCORD_BOT_TOKEN)
                if extraer_exp_jwt(jwt_desc) > exp_base:
                    return jwt_desc
        except Exception:
            pass
    return candidato_base


JWT_TOKEN: str = resolver_jwt_mas_reciente()
JWT_TOKEN_2: str = os.environ.get("JWT_TOKEN_2") or _cfg.get("JWT_TOKEN_2", "")
JWT_TOKEN_3: str = os.environ.get("JWT_TOKEN_3") or _cfg.get("JWT_TOKEN_3", "")
JWT_TOKENS: List[str] = [t.strip() for t in [JWT_TOKEN, JWT_TOKEN_2, JWT_TOKEN_3] if t and t.strip().startswith("eyJ")]

ES_MODO_NUBE: bool = os.environ.get("CLOUD_MODE") == "1" or sys.platform != "win32"
AUTO_COPIAR_PORTAPAPELES: bool = not ES_MODO_NUBE

WEBHOOKS_POR_CANAL: Dict[str, str] = {
    "shundo": DISCORD_WEBHOOK_URL,
    "great": DISCORD_WEBHOOK_GL,
    "ultra": DISCORD_WEBHOOK_UL,
    "evento": DISCORD_WEBHOOK_EVENTO,
}

BOT_NOMBRES_POR_CANAL: Dict[str, str] = {
    "shundo": "Radar Shundo Pro ✨",
    "great": "Radar PvP Great League 🔵✨",
    "ultra": "Radar PvP Ultra League 🟣✨",
    "evento": "Radar Eventos & CD 🎉✨",
}

# Coordenadas base de referencia
LAT_ORIGEN: float = -12.058662
LNG_ORIGEN: float = -77.036896

# Parámetros operativos del motor 24/7
MODO_VIGILANTE_CONTINUO: bool = True
INTERVALO_SEGUNDOS: int = 300              # Escaneo de nuevos spawns cada 5 minutos (300s)
MIN_SEGUNDOS_VIDA: int = 90                # Ignorar spawns con menos de 90s restantes
PVP_TOP_RANK_MAX: int = 5                  # Filtrar Rank #1 al #5 en Great League y Ultra League
PVP_REVEAL_MAX_RANK: int = 2              # Coordenadas exactas garantizadas en PvP Rank #1 y #2
PVP_MIN_CP_GL: int = 1200                  # CP mínimo competitivo en Great League (en filtro local Python)
PVP_MIN_CP_UL: int = 2100                  # CP mínimo competitivo en Ultra League (en filtro local Python)
TTL_LIMPIEZA_CACHE_SEGUNDOS: int = 7200    # Limpiar registros ya expirados después de 2 horas
MAX_REVEALS_POR_EJECUCION: int = 12        # Presupuesto dinámico multi-cuenta para revelar coordenadas exactas

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
