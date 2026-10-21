"""
Cliente HTTP optimizado con Connection Pooling (requests.Session) para consultar
los endpoints /users/me, /search, /map/lookup y /reveal/{code}.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import requests

from src.config import (
    API_BASE,
    HEADERS_API,
    LAT_ORIGEN,
    LNG_ORIGEN,
    MAX_REVEALS_POR_EJECUCION,
    MIN_SEGUNDOS_VIDA,
    PVP_MIN_CP_GL,
    PVP_MIN_CP_UL,
    PVP_TOP_RANK_MAX,
)
from src.models import calcular_distancia_km, calcular_tiempo_restante

_api_session = requests.Session()
_api_session.headers.update(HEADERS_API)


def obtener_perfil_entrenador() -> Tuple[Optional[Dict[str, Any]], int]:
    """Obtiene el perfil del entrenador autenticado y verifica la validez del JWT_TOKEN."""
    try:
        r = _api_session.get(f"{API_BASE}/users/me", timeout=10)
        if r.status_code == 200:
            return r.json(), 200
        return None, r.status_code
    except Exception:
        return None, 0


def construir_payload_search(overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Construye el cuerpo estándar para el endpoint /search aplicando los filtros indicados."""
    p: Dict[str, Any] = {
        "shiny_only": True,
        "shiny_account": None,
        "background_only": False,
        "pvp_mode": False,
        "pvp_league": "great",
        "pvp_top_rank": None,
        "pvp_include_pre_evolutions": True,
        "pvp_min_cp": None,
        "pokemon_ids": [],
        "species_forms": [],
        "location": None,
        "cp_min": None,
        "cp_max": None,
        "level_min": None,
        "level_max": None,
        "iv_mode": "percent",
        "iv_percent_min": None,
        "iv_percent_max": None,
        "raw_iv_atk": None,
        "raw_iv_def": None,
        "raw_iv_sta": None,
        "sizes": [],
        "forms": [],
        "gender": None,
        "boosted": None,
        "weather_id": None,
        "min_ttl": None,
        "sort": "DSP",
        "center_lat": None,
        "center_lng": None,
        "radius_km": None,
        "blacklist_pokemon_ids": [],
        "blacklist_species_forms": [],
        "blacklist_forms": [],
    }
    for k, v in overrides.items():
        if k != "label":
            p[k] = v
    return p


def ejecutar_particion_search(particion: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Ejecuta una consulta en /search con reintento automático ante HTTP 429."""
    payload = construir_payload_search(particion)
    for intento in range(2):
        try:
            r = _api_session.post(f"{API_BASE}/search", json=payload, timeout=12)
            if r.status_code == 200:
                return r.json().get("results", [])
            elif r.status_code == 429 and intento == 0:
                time.sleep(1.5)
        except Exception:
            pass
    return []


def ejecutar_region_mapa(
    region_tuple: Tuple[str, float, float, float, float],
    modo: str = "shundo",
    pokemon_ids: Optional[List[int]] = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Consulta una región geográfica en /map/lookup para Shundos 100%, Great League o Ultra League."""
    nombre_region, n_lat, w_lng, s_lat, e_lng = region_tuple
    es_pvp = modo in ("great", "ultra")
    payload = {
        "mode": "pokemon",
        "n_lat": n_lat,
        "s_lat": s_lat,
        "w_lng": w_lng,
        "e_lng": e_lng,
        "num_results": 100,
        "filters": {
            "pokemon_ids": pokemon_ids or [],
            "species_forms": [],
            "blacklist_pokemon_ids": [],
            "blacklist_species_forms": [],
            "iv_min": None if es_pvp else 100,
            "iv_max": None if es_pvp else 100,
            "cp_min": None,
            "cp_max": None,
            "level_min": None,
            "level_max": None,
            "gender": None,
            "sizes": [],
            "boosted": None,
            "sort": "DSP",
            "pvp_mode": es_pvp,
            "pvp_league": modo if es_pvp else "great",
            "pvp_top_rank": PVP_TOP_RANK_MAX if es_pvp else None,
            "pvp_include_pre_evolutions": True,
            "pvp_min_cp": None,
            "shiny_only": True,
            "shiny_account": None,
            "background_only": False,
            "always_show": [],
        },
    }
    for intento in range(2):
        try:
            r = _api_session.post(f"{API_BASE}/map/lookup", json=payload, timeout=12)
            if r.status_code == 200:
                items = r.json().get("results", [])
                for item in items:
                    item["region_mapa"] = nombre_region
                return nombre_region, items
            elif r.status_code == 429 and intento == 0:
                time.sleep(1.5)
        except Exception:
            pass
    return nombre_region, []


def preparar_lista_spawns(
    diccionario_spawns: Dict[str, Dict[str, Any]],
    cache_coords: Dict[str, Dict[str, Any]],
    estado_cuota: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Enriquece cada spawn con tiempo restante, nombre completo y coordenadas exactas."""
    activos: List[Dict[str, Any]] = []
    for eid, mon in diccionario_spawns.items():
        txt_ttl, seg_restantes, despawn_unix = calcular_tiempo_restante(
            mon.get("despawn_at"), mon.get("despawn_at_ms")
        )
        if seg_restantes < MIN_SEGUNDOS_VIDA:
            continue
        mon["ttl_texto"] = txt_ttl
        mon["ttl_segundos"] = seg_restantes
        mon["despawn_unix"] = despawn_unix

        nombre = mon.get("pokemon_name") or f"#{mon.get('pokemon_id')}"
        form = mon.get("form")
        costume = mon.get("costume")
        extras_nombre = " ".join(f"({x})" for x in [form, costume] if x and x != "Normal")
        mon["nombre_completo"] = f"{nombre} {extras_nombre}" if extras_nombre else nombre

        if eid in cache_coords:
            c_data = cache_coords[eid]
            mon["coords_final"] = c_data["coords"]
            mon["lat_final"] = c_data["lat"]
            mon["lng_final"] = c_data["lng"]
            mon["precision_coords"] = "Exacta (Caché)"
        else:
            reveal_code = mon.get("reveal_code")
            if reveal_code and not estado_cuota["agotada"] and estado_cuota["revelados"] < MAX_REVEALS_POR_EJECUCION:
                try:
                    rev_res = _api_session.get(f"{API_BASE}/reveal/{reveal_code}", timeout=8)
                    if rev_res.status_code == 200:
                        res_data = rev_res.json()
                        coords = res_data.get("coords")
                        lat = res_data.get("lat")
                        lng = res_data.get("lng")
                        if coords and lat is not None and lng is not None:
                            mon["coords_final"] = coords
                            mon["lat_final"] = lat
                            mon["lng_final"] = lng
                            mon["precision_coords"] = "Exacta (Revelada)"
                            cache_coords[eid] = {
                                "coords": coords,
                                "lat": lat,
                                "lng": lng,
                                "ts": int(time.time()),
                            }
                            estado_cuota["revelados"] += 1
                    elif rev_res.status_code in (403, 429):
                        estado_cuota["agotada"] = True
                except Exception:
                    pass

            if not mon.get("coords_final"):
                apx_lat = mon.get("apx_lat")
                apx_long = mon.get("apx_long")
                if apx_lat is not None and apx_long is not None:
                    mon["coords_final"] = f"{apx_lat:.6f},{apx_long:.6f}"
                    mon["lat_final"] = apx_lat
                    mon["lng_final"] = apx_long
                    mon["precision_coords"] = "Mapa"
                else:
                    mon["coords_final"] = None
                    mon["lat_final"] = None
                    mon["lng_final"] = None

        lat = mon.get("lat_final")
        lng = mon.get("lng_final")
        if lat is None or lng is None:
            continue
        mon["distancia_km"] = calcular_distancia_km(LAT_ORIGEN, LNG_ORIGEN, lat, lng)
        activos.append(mon)

    return activos
