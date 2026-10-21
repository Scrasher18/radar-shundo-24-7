"""
Módulo escalable para Eventos Especiales y Community Days (CD).
Permite filtrar Pokémon específicos (por ID o nombre) tanto en 100% Shundo
como en PvP Great League y Ultra League (Rank #1-#5 Shiny), además de poder
sincronizarse con un canal de configuración en Discord.
"""

import json
import os
from typing import Any, Dict, List

from src.config import BASE_DIR

EVENTO_CONFIG_FILE = os.path.join(BASE_DIR, "evento_config.json")


def cargar_config_evento() -> Dict[str, Any]:
    """Carga la configuración actual del Evento / Community Day sin afectar los canales principales."""
    if os.path.exists(EVENTO_CONFIG_FILE):
        try:
            with open(EVENTO_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "activo": False,
        "nombre_evento": "Community Day / Evento Especial",
        "webhook_evento": "",
        "pokemon_ids": [],
        "pokemon_nombres": [],
        "incluir_shundos_100": True,
        "incluir_pvp_gl": True,
        "incluir_pvp_ul": True,
        "pvp_top_rank": 5,
    }


def guardar_config_evento(cfg: Dict[str, Any]) -> None:
    """Guarda los cambios de configuración del Evento / Community Day."""
    try:
        with open(EVENTO_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def coincide_con_evento(mon: Dict[str, Any], cfg_evento: Dict[str, Any]) -> bool:
    """Verifica si un Pokémon pertenece a la lista configurada del Evento o Community Day."""
    if not cfg_evento.get("activo"):
        return False

    ids_objetivo: List[int] = [int(x) for x in (cfg_evento.get("pokemon_ids") or []) if str(x).isdigit()]
    nombres_objetivo: List[str] = [str(n).strip().lower() for n in (cfg_evento.get("pokemon_nombres") or []) if n]

    poke_id = int(mon.get("pokemon_id") or 0)
    nombre_salvaje = str(mon.get("pokemon_name") or "").strip().lower()
    pvp = mon.get("pvp") or {}
    pvp_id = int(pvp.get("pokemon_id") or 0)
    pvp_nombre = str(pvp.get("pokemon_name") or "").strip().lower()

    if ids_objetivo and (poke_id in ids_objetivo or pvp_id in ids_objetivo):
        return True

    for buscado in nombres_objetivo:
        if buscado and (buscado in nombre_salvaje or buscado in pvp_nombre):
            return True

    return False
