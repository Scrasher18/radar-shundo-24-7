"""
Cliente HTTP optimizado con Connection Pooling (requests.Session) para consultar
los endpoints /users/me, /search, /map/lookup y /reveal/{code}.
Incluye un TokenPool multi-cuenta inteligente que rota automáticamente entre tus cuentas
cuando una alcanza el límite horario de reveals (HTTP 429), asegurando coordenadas exactas
garantizadas para Shundos 100% IV y Top PvP Meta.
"""

import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import requests

from src.config import (
    API_BASE,
    CONFIG_LOCAL_FILE,
    HEADERS_API,
    JWT_TOKEN,
    JWT_TOKENS,
    LAT_ORIGEN,
    LNG_ORIGEN,
    MAX_REVEALS_POR_EJECUCION,
    MIN_SEGUNDOS_VIDA,
    PVP_MIN_CP_GL,
    PVP_MIN_CP_UL,
    PVP_REVEAL_MAX_RANK,
    PVP_TOP_RANK_MAX,
)
from src.models import calcular_distancia_km, calcular_tiempo_restante


class AccountSlot:
    """Representa una cuenta de Coordinates PoGo Pro con su propia sesión HTTP y control de cuota."""

    def __init__(self, token: str, indice: int):
        self.token = token.strip()
        self.indice = indice
        self.rate_limited_until: float = 0.0
        self.nombre_usuario: str = f"Cuenta #{indice}"
        self.nombre_entrenador: str = ""
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        })
        self._verificada = False

    def verificar_perfil(self) -> bool:
        """Verifica /users/me y cachea el nombre de usuario y entrenador."""
        if self._verificada:
            return True
        try:
            r = self.session.get(f"{API_BASE}/users/me", timeout=8)
            if r.status_code == 200:
                data = r.json()
                self.nombre_usuario = data.get("display_name") or f"Cuenta #{self.indice}"
                trainer = data.get("trainer") or {}
                self.nombre_entrenador = trainer.get("trainer_name") or ""
                self._verificada = True
                return True
        except Exception:
            pass
        return False


class TokenRevealPool:
    """
    Pool multi-cuenta sincronizado (Thread-Safe) para rotación inteligente de JWT_TOKENS.
    Maneja el rate limit horario de 10 reveals por cuenta cambiando en caliente sin fallos.
    """

    def __init__(self, tokens: List[str]):
        self._lock = threading.RLock()
        self.slots: List[AccountSlot] = []
        tokens_unicos = []
        for t in tokens:
            t_clean = t.strip()
            if t_clean and t_clean.startswith("eyJ") and t_clean not in tokens_unicos:
                tokens_unicos.append(t_clean)
        for idx, t in enumerate(tokens_unicos, start=1):
            self.slots.append(AccountSlot(t, idx))

    def agregar_o_actualizar_token(self, nuevo_token: str) -> None:
        with self._lock:
            limpio = nuevo_token.strip().replace("Bearer ", "").strip()
            if not limpio.startswith("eyJ"):
                return
            for s in self.slots:
                if s.token == limpio:
                    s.rate_limited_until = 0.0
                    s._verificada = False
                    return
            # Si es nuevo, reemplazar el slot 1 o agregar
            nuevo_slot = AccountSlot(limpio, len(self.slots) + 1)
            self.slots.insert(0, nuevo_slot)

    def obtener_resumen_pool(self) -> str:
        with self._lock:
            ahora = time.time()
            partes = []
            for s in self.slots:
                s.verificar_perfil()
                if ahora < s.rate_limited_until:
                    min_rest = int((s.rate_limited_until - ahora) / 60)
                    partes.append(f"[{s.nombre_usuario}: ⏳ Bloqueado por {min_rest}m]")
                else:
                    partes.append(f"[{s.nombre_usuario}: ✅ Disponible]")
            return " • ".join(partes)

    def revelar_coordenada(
        self, reveal_code: str
    ) -> Tuple[bool, Optional[str], Optional[float], Optional[float]]:
        """
        Intenta revelar la coordenada exacta llamando a /reveal/{code}.
        Si la cuenta actual devuelve HTTP 429, guarda el tiempo de espera y pasa
        automáticamente a la siguiente cuenta disponible del pool.
        """
        if not reveal_code:
            return False, None, None, None

        with self._lock:
            ahora = time.time()
            # Ordenar primero las cuentas que no estén en rate limit
            slots_candidatos = sorted(
                self.slots, key=lambda s: 0 if ahora >= s.rate_limited_until else s.rate_limited_until
            )

            for s in slots_candidatos:
                if ahora < s.rate_limited_until:
                    continue

                s.verificar_perfil()
                try:
                    r = s.session.get(f"{API_BASE}/reveal/{reveal_code}", timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        coords = data.get("coords")
                        lat = data.get("lat")
                        lng = data.get("lng")
                        if coords and lat is not None and lng is not None:
                            print(
                                f"      🎯 [Pool-{s.nombre_usuario}] Coordenada exacta revelada: {coords}"
                            )
                            return True, coords, lat, lng

                    elif r.status_code == 429:
                        try:
                            err_data = r.json()
                            retry_after = int(err_data.get("detail", {}).get("retry_after") or 3600)
                        except Exception:
                            retry_after = 3600
                        s.rate_limited_until = time.time() + retry_after
                        min_rest = max(1, retry_after // 60)
                        print(
                            f"      🔄 [Pool-{s.nombre_usuario}] Límite horario alcanzado (429). Enfriamiento de {min_rest} min. Rotando a siguiente cuenta..."
                        )
                        continue

                    elif r.status_code == 403:
                        s.rate_limited_until = time.time() + 1800
                        continue

                except Exception as e:
                    print(f"      ⚠️ [Pool-{s.nombre_usuario}] Error de conexión en reveal: {e}")
                    continue

            return False, None, None, None


_TOKEN_POOL = TokenRevealPool(JWT_TOKENS)
_JWT_ACTIVO_MEMORIA: str = JWT_TOKEN
_api_session = requests.Session()
_api_session.headers.update(HEADERS_API)


def obtener_jwt_actual() -> str:
    """Devuelve el JWT_TOKEN actualmente activo en memoria."""
    return _JWT_ACTIVO_MEMORIA


def obtener_resumen_cuentas_pool() -> str:
    """Devuelve el estado de disponibilidad de cada cuenta en el pool multi-cuenta."""
    return _TOKEN_POOL.obtener_resumen_pool()


def actualizar_jwt_token_en_vivo(nuevo_token: str) -> Tuple[bool, Optional[Dict[str, Any]], int]:
    """
    Valida un nuevo JWT_TOKEN contra /users/me y, si es válido (HTTP 200),
    lo activa inmediatamente en la sesión HTTP en memoria y en el pool.
    """
    global _JWT_ACTIVO_MEMORIA
    limpio = nuevo_token.strip().replace("Bearer ", "").strip()
    if not limpio.startswith("eyJ"):
        return False, None, 400

    headers_prueba = dict(HEADERS_API)
    headers_prueba["Authorization"] = f"Bearer {limpio}"
    try:
        r = requests.get(f"{API_BASE}/users/me", headers=headers_prueba, timeout=10)
        if r.status_code == 200:
            _JWT_ACTIVO_MEMORIA = limpio
            HEADERS_API["Authorization"] = f"Bearer {limpio}"
            _api_session.headers["Authorization"] = f"Bearer {limpio}"
            _TOKEN_POOL.agregar_o_actualizar_token(limpio)
            return True, r.json(), 200
        return False, None, r.status_code
    except Exception:
        return False, None, 0


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
    estado_cuota: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Enriquece cada spawn con tiempo restante, nombre completo y coordenadas exactas verificadas.
    Prioriza reveals en:
    1. Shundos 100% IV (prioridad máxima global).
    2. Spawns del canal de Evento/CD configurados por el usuario.
    3. PvP Top Rank #1 y #2 (los más competitivos y buscados).
    Guarda cada coordenada revelada en caché persistente para no gastar créditos repetidos.
    """
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

        # 1. Comprobar si ya existe en la caché persistente
        if eid in cache_coords:
            c_data = cache_coords[eid]
            mon["coords_final"] = c_data["coords"]
            mon["lat_final"] = c_data["lat"]
            mon["lng_final"] = c_data["lng"]
            mon["precision_coords"] = "Exacta (Caché)"
        else:
            reveal_code = mon.get("reveal_code")
            iv_pct = float(mon.get("iv_percent") or 0.0)
            pvp_rank = int((mon.get("pvp") or {}).get("rank", 99))
            es_shundo_100 = (iv_pct == 100.0)
            es_top_pvp = (pvp_rank <= PVP_REVEAL_MAX_RANK)
            es_evento = bool(mon.get("origen_evento"))

            debe_revelar = (es_shundo_100 or es_evento or es_top_pvp)

            if debe_revelar and reveal_code and estado_cuota.get("revelados", 0) < MAX_REVEALS_POR_EJECUCION:
                ok, coords, lat, lng = _TOKEN_POOL.revelar_coordenada(reveal_code)
                if ok and coords and lat is not None and lng is not None:
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
                    estado_cuota["revelados"] = estado_cuota.get("revelados", 0) + 1

            if not mon.get("coords_final"):
                apx_lat = mon.get("apx_lat")
                apx_long = mon.get("apx_long")
                if apx_lat is not None and apx_long is not None:
                    mon["coords_final"] = f"{apx_lat:.6f},{apx_long:.6f}"
                    mon["lat_final"] = apx_lat
                    mon["lng_final"] = apx_long
                    mon["precision_coords"] = "Aproximada (Radio ~300m)"
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
