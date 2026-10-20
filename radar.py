import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_LOCAL_FILE = os.path.join(BASE_DIR, "config_local.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache_coordenadas.json")
NOTIFICADOS_FILE = os.path.join(BASE_DIR, "shundos_notificados.json")
EXPORT_TXT = os.path.join(BASE_DIR, "shinies_mundiales.txt")
EXPORT_JSON = os.path.join(BASE_DIR, "shinies_mundiales.json")


def cargar_config_local():
    if os.path.exists(CONFIG_LOCAL_FILE):
        try:
            with open(CONFIG_LOCAL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


_cfg = cargar_config_local()

# ==============================================================================
# ⚙️ CONFIGURACIÓN PRINCIPAL Y CANALES DE DISCORD (SHUNDOS / GL / UL)
# ==============================================================================
JWT_TOKEN = os.environ.get("JWT_TOKEN") or _cfg.get("JWT_TOKEN", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") or _cfg.get("DISCORD_WEBHOOK_URL", "")
DISCORD_WEBHOOK_GL = os.environ.get("DISCORD_WEBHOOK_GL") or _cfg.get("DISCORD_WEBHOOK_GL", "")
DISCORD_WEBHOOK_UL = os.environ.get("DISCORD_WEBHOOK_UL") or _cfg.get("DISCORD_WEBHOOK_UL", "")
DISCORD_USER_ID_MENCION = os.environ.get("DISCORD_USER_ID_MENCION") or _cfg.get("DISCORD_USER_ID_MENCION", "924392800534011935")
ES_MODO_NUBE = os.environ.get("CLOUD_MODE") == "1" or sys.platform != "win32"

WEBHOOKS_POR_CANAL = {
    "shundo": DISCORD_WEBHOOK_URL,
    "great": DISCORD_WEBHOOK_GL,
    "ultra": DISCORD_WEBHOOK_UL,
}

LAT_ORIGEN = -12.058662
LNG_ORIGEN = -77.036896

AUTO_COPIAR_PORTAPAPELES = not ES_MODO_NUBE

# Configuración del Vigilante Automático 24/7
MODO_VIGILANTE_CONTINUO = True     # True = revisa cada INTERVALO_SEGUNDOS automáticamente
INTERVALO_SEGUNDOS = 480           # Cada cuántos segundos busca nuevos spawns (480s = 8 minutos)
MIN_SEGUNDOS_VIDA = 90             # Ignorar spawns a los que les queden menos de 90s de vida
PVP_TOP_RANK_MAX = 5               # Mostrar del Rank #1 al #5 en Great League y Ultra League
TTL_LIMPIEZA_CACHE_SEGUNDOS = 43200 # Limpiar automáticamente registros de más de 12 horas (mantenimiento 24/7)
MAX_REVEALS_POR_EJECUCION = 65

API_BASE = "https://coordinates-api.pokemongopro.com"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# 8 regiones globales que cubren todo el mundo (hasta 100 Shundos por región en /map/lookup)
REGIONES_GLOBALES = [
    ("Norteamérica (Este)", 55.0, -98.0, 24.0, -60.0),
    ("Norteamérica (Oeste y Centro)", 55.0, -135.0, 14.0, -98.0),
    ("Sudamérica", 13.0, -85.0, -55.0, -34.0),
    ("Europa Occidental", 65.0, -12.0, 35.0, 16.0),
    ("Europa Oriental y Medio Oriente", 65.0, 16.0, 25.0, 60.0),
    ("Asia Oriental (Japón, Corea, Taiwán)", 48.0, 112.0, 20.0, 150.0),
    ("Sudeste Asiático e India", 24.0, 68.0, -11.0, 125.0),
    ("Oceanía (Australia y Nueva Zelanda)", -10.0, 112.0, -48.0, 180.0),
]

# Particiones de /search exclusivas para SHUNDOS (100% IV + Shiny)
PARTICIONES_SHUNDOS = [
    {"label": "100% Shundos (DSP)", "iv_percent_min": 100, "iv_percent_max": 100, "sort": "DSP"},
    {"label": "100% Shundos (CP)", "iv_percent_min": 100, "iv_percent_max": 100, "sort": "CP"},
    {"label": "100% Shundos (LEVEL)", "iv_percent_min": 100, "iv_percent_max": 100, "sort": "LEVEL"},
    {"label": "100% Shundos (Male)", "iv_percent_min": 100, "iv_percent_max": 100, "gender": "Male", "sort": "DSP"},
    {"label": "100% Shundos (Female)", "iv_percent_min": 100, "iv_percent_max": 100, "gender": "Female", "sort": "DSP"},
    {"label": "100% Shundos (Genderless)", "iv_percent_min": 100, "iv_percent_max": 100, "gender": "Genderless", "sort": "DSP"},
    {"label": "100% Shundos (Nivel 1-14)", "iv_percent_min": 100, "iv_percent_max": 100, "level_min": 1, "level_max": 14, "sort": "DSP"},
    {"label": "100% Shundos (Nivel 15-25)", "iv_percent_min": 100, "iv_percent_max": 100, "level_min": 15, "level_max": 25, "sort": "DSP"},
    {"label": "100% Shundos (Nivel 26-35)", "iv_percent_min": 100, "iv_percent_max": 100, "level_min": 26, "level_max": 35, "sort": "DSP"},
]

# Particiones de /search para PvP Great League (GL) y Ultra League (UL) Top 1-5 Shiny Garantizado
PARTICIONES_PVP_GL = [
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": 1, "pvp_include_pre_evolutions": True, "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "CP"},
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "LEVEL"},
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "gender": "Male", "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "great", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "gender": "Female", "sort": "DSP"},
]

PARTICIONES_PVP_UL = [
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": 1, "pvp_include_pre_evolutions": True, "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "CP"},
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "sort": "LEVEL"},
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "gender": "Male", "sort": "DSP"},
    {"pvp_mode": True, "pvp_league": "ultra", "pvp_top_rank": PVP_TOP_RANK_MAX, "pvp_include_pre_evolutions": True, "gender": "Female", "sort": "DSP"},
]


def calcular_distancia_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def cargar_json(ruta):
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def guardar_json(ruta, datos):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def limpiar_archivos_antiguos(cache_coords, notificados):
    ahora = int(time.time())
    claves_borrar_cache = [
        k for k, v in cache_coords.items()
        if isinstance(v, dict) and (ahora - int(v.get("ts", ahora))) > TTL_LIMPIEZA_CACHE_SEGUNDOS
    ]
    for k in claves_borrar_cache:
        del cache_coords[k]

    claves_borrar_notif = [
        k for k, v in notificados.items()
        if not k.startswith("_meta_") and isinstance(v, dict) and (ahora - int(v.get("ts", ahora))) > TTL_LIMPIEZA_CACHE_SEGUNDOS
    ]
    for k in claves_borrar_notif:
        del notificados[k]


def eliminar_mensajes_expirados_discord():
    """Revisa los Shundos y PvP GL/UL enviados a Discord y elimina del canal correspondiente los que ya hicieron despawn."""
    notificados = cargar_json(NOTIFICADOS_FILE)
    ahora = int(time.time())
    eliminados = 0
    hubo_cambios = False

    for clave, info in list(notificados.items()):
        if clave.startswith("_meta_") or not isinstance(info, dict):
            continue
        msg_id = info.get("discord_msg_id")
        despawn_unix = info.get("despawn_unix")
        ya_borrado = info.get("eliminado_de_discord", False)
        canal_tipo = info.get("canal", "shundo")
        webhook_url = WEBHOOKS_POR_CANAL.get(canal_tipo) or DISCORD_WEBHOOK_URL

        if msg_id and despawn_unix and not ya_borrado and webhook_url and ahora >= int(despawn_unix):
            base_webhook = webhook_url.strip().split("?")[0].rstrip("/")
            try:
                del_url = f"{base_webhook}/messages/{msg_id}"
                r = requests.delete(del_url, timeout=8)
                if r.status_code in (200, 204, 404):
                    info["eliminado_de_discord"] = True
                    hubo_cambios = True
                    eliminados += 1
                    print(f"   🗑️ [Discord-{canal_tipo.upper()}] Mensaje de {info.get('pokemon', clave)} eliminado del chat (ya hizo despawn).")
            except Exception:
                pass

    if hubo_cambios:
        guardar_json(NOTIFICADOS_FILE, notificados)
    return eliminados


def copiar_al_portapapeles(texto):
    if not AUTO_COPIAR_PORTAPAPELES or not texto or "," not in texto:
        return False
    try:
        subprocess.run(["clip"], input=texto.strip().encode("utf-8"), check=True)
        return True
    except Exception:
        return False


def enviar_alerta_token_vencido():
    if not DISCORD_WEBHOOK_URL.strip():
        return
    notificados = cargar_json(NOTIFICADOS_FILE)
    ahora = int(time.time())
    ultimo_aviso = int(notificados.get("_meta_alerta_401_ts", 0))
    if ahora - ultimo_aviso < 21600:
        return

    mencion = f"<@{DISCORD_USER_ID_MENCION}> " if DISCORD_USER_ID_MENCION else ""
    payload = {
        "username": "Radar Shundo Pro ⚠️",
        "content": f"⚠️ {mencion}**¡Atención!** Tu `JWT_TOKEN` de Pokémon GO Pro ha expirado (`Error HTTP 401`).",
        "embeds": [{
            "title": "🔑 Sesión Expirada — Actualiza tu JWT_TOKEN",
            "color": 0xEF4444,
            "description": (
                "El servidor devolvió **HTTP 401 (Unauthorized)**.\n\n"
                "**Cómo renovarlo:**\n"
                "1. Abre `coordinates.pokemongopro.com` en tu navegador.\n"
                "2. Copia el nuevo `jwt` desde *Local Storage*.\n"
                "3. Actualízalo en `config_local.json` / Secret `JWT_TOKEN` en GitHub."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL.strip(), json=payload, timeout=10)
        if r.status_code in (200, 204):
            notificados["_meta_alerta_401_ts"] = ahora
            guardar_json(NOTIFICADOS_FILE, notificados)
    except Exception:
        pass


def obtener_etiquetas_rareza(mon, etiqueta_base="✨ **SHUNDO 100% IV**"):
    etiquetas = [etiqueta_base]
    if mon.get("background"):
        etiquetas.append("🏞️ **FONDO ESPECIAL (BACKGROUND)**")
    if mon.get("costume"):
        etiquetas.append(f"🎭 **DISFRAZ ({mon.get('costume')})**")
    size = str(mon.get("size") or "").upper()
    if size in ("XXL", "XXS"):
        etiquetas.append(f"📏 **TALLA RARA ({size})**")
    if mon.get("weather_boosted"):
        etiquetas.append("☁️ **CLIMA BOOSTEADO**")
    return " • ".join(etiquetas)


def construir_estado_despawn(mon):
    seg_rest = max(0, int(mon.get("ttl_segundos") or 0))
    mins, secs = divmod(seg_rest, 60)
    ttl_con_segundos = f"{mins} min {secs:02d} seg"
    despawn_unix = mon.get("despawn_unix")

    if seg_rest >= 900:
        semaforo = "🟢 **Tiempo Seguro**"
        color_urgencia = 0xFFD700
    elif seg_rest >= 300:
        semaforo = "🟡 **Tiempo Medio**"
        color_urgencia = 0xF97316
    else:
        semaforo = "🔴 **¡SALTAR YA!**"
        color_urgencia = 0xEF4444

    estado_tiempo = f"{semaforo}\n⏱️ **Desaparece en:** `{ttl_con_segundos}`"
    if despawn_unix:
        estado_tiempo += f"\n🕒 **Hora exacta:** <t:{despawn_unix}:T>"
    return estado_tiempo, color_urgencia


def construir_embed_shundo(mon):
    origen_txt = "☁️ Nube 24/7" if ES_MODO_NUBE else "💻 PC Local"
    poke_id = mon.get("pokemon_id") or 1
    nombre = mon.get("nombre_completo") or mon.get("pokemon_name") or f"#{poke_id}"
    coords = mon.get("coords_final") or "N/A"
    maps_url = f"https://www.google.com/maps?q={coords}" if "," in str(coords) else "https://maps.google.com"
    ubicacion = mon.get("location") or mon.get("region_mapa") or "Global"
    cp = mon.get("cp") or "?"
    nivel = mon.get("level") or "?"
    size = mon.get("size") or "-"
    gender = mon.get("gender") or "-"
    icon_url = f"https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Images/Pokemon/Addressable%20Assets/pm{poke_id}.s.icon.png"

    estado_tiempo, color_embed = construir_estado_despawn(mon)
    rareza_txt = obtener_etiquetas_rareza(mon, "✨ **SHUNDO 100% IV**")

    return {
        "title": f"🌟 ¡SHUNDO 100% IV: {nombre}! (CP {cp} • Nivel {nivel})",
        "description": rareza_txt,
        "url": maps_url,
        "color": color_embed,
        "thumbnail": {"url": icon_url},
        "fields": [
            {"name": "📊 Estadísticas", "value": f"**IV:** `100% (15/15/15)`\n**CP:** `{cp}` | **Nivel:** `{nivel}`\n**Talla:** `{size}` ({gender})", "inline": True},
            {"name": "⏳ Estado Despawn", "value": estado_tiempo, "inline": True},
            {"name": "📍 Ubicación", "value": f"{ubicacion} • [🗺️ Ver en Google Maps]({maps_url})", "inline": False},
            {"name": "🎯 Coordenadas Exactas", "value": f"```\n{coords}\n```", "inline": False},
        ],
        "footer": {"text": f"Radar Shundo Pro ({origen_txt}) • Se eliminará automáticamente al desaparecer"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def construir_embed_pvp(mon, league):
    origen_txt = "☁️ Nube 24/7" if ES_MODO_NUBE else "💻 PC Local"
    poke_id = mon.get("pokemon_id") or 1
    nombre_salvaje = mon.get("nombre_completo") or mon.get("pokemon_name") or f"#{poke_id}"
    coords = mon.get("coords_final") or "N/A"
    maps_url = f"https://www.google.com/maps?q={coords}" if "," in str(coords) else "https://maps.google.com"
    ubicacion = mon.get("location") or mon.get("region_mapa") or "Global"
    cp_salvaje = mon.get("cp") or "?"
    nivel_salvaje = mon.get("level") or "?"
    raw_iv = mon.get("raw_iv") or "?/?/?"
    size = mon.get("size") or "-"
    gender = mon.get("gender") or "-"

    pvp = mon.get("pvp") or {}
    rank = pvp.get("rank", "?")
    pvp_poke_id = pvp.get("pokemon_id") or poke_id
    pvp_poke_name = pvp.get("pokemon_name") or nombre_salvaje
    pvp_cp = pvp.get("cp", "?")
    pvp_lvl = pvp.get("level", "?")
    pvp_pct = pvp.get("percent", 100.0)

    es_gl = league == "great"
    liga_nombre = "🔵 GREAT LEAGUE (1500 CP)" if es_gl else "🟣 ULTRA LEAGUE (2500 CP)"
    color_liga = 0x3B82F6 if es_gl else 0xA855F7
    medalla_rank = "🥇 **RANK #1 (100% STAT PRODUCT)**" if rank == 1 else f"🏆 **RANK #{rank}** (`{pvp_pct:.2f}%` PvP)"

    evolucion_txt = (
        f"🔄 **Para Liga:** Evolucionar a **{pvp_poke_name}** (`CP {pvp_cp}` a Nivel `{pvp_lvl}`)"
        if int(pvp_poke_id) != int(poke_id)
        else f"⚔️ **En Liga:** **{pvp_poke_name}** alcanza `CP {pvp_cp}` en Nivel `{pvp_lvl}`"
    )

    icon_url = f"https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Images/Pokemon/Addressable%20Assets/pm{pvp_poke_id}.s.icon.png"
    estado_tiempo, _ = construir_estado_despawn(mon)
    rareza_txt = obtener_etiquetas_rareza(mon, f"✨ **SHINY GARANTIZADO** • {medalla_rank}")

    titulo_especie = f"{nombre_salvaje} ➔ {pvp_poke_name}" if int(pvp_poke_id) != int(poke_id) else nombre_salvaje

    return {
        "title": f"⚔️ ¡{liga_nombre} — RANK #{rank}: {titulo_especie}!",
        "description": f"{rareza_txt}\n{evolucion_txt}",
        "url": maps_url,
        "color": color_liga,
        "thumbnail": {"url": icon_url},
        "fields": [
            {
                "name": "📊 Datos de Captura y PvP",
                "value": (
                    f"**Rank PvP:** `#{rank}` (`{pvp_pct:.2f}%`)\n"
                    f"**IVs PvP:** `{raw_iv}`\n"
                    f"**Salvaje:** `CP {cp_salvaje}` | `Nivel {nivel_salvaje}` ({size}, {gender})\n"
                    f"**Final en Liga:** `CP {pvp_cp}` | `Nivel {pvp_lvl}`"
                ),
                "inline": True
            },
            {"name": "⏳ Estado Despawn", "value": estado_tiempo, "inline": True},
            {"name": "📍 Ubicación", "value": f"{ubicacion} • [🗺️ Ver en Google Maps]({maps_url})", "inline": False},
            {"name": "🎯 Coordenadas Exactas", "value": f"```\n{coords}\n```", "inline": False},
        ],
        "footer": {"text": f"Radar PvP Shiny Pro ({origen_txt}) • Se eliminará automáticamente al desaparecer"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def enviar_lote_webhook(webhook_url, spawns_nuevos, canal_tipo, bot_username):
    if not webhook_url or not webhook_url.strip() or not spawns_nuevos:
        return {}

    base_webhook = webhook_url.strip().split("?")[0].rstrip("/")
    url_wait = f"{base_webhook}?wait=true"
    mencion = f"<@{DISCORD_USER_ID_MENCION}> " if DISCORD_USER_ID_MENCION else ""
    ids_mensajes = {}

    for idx, mon in enumerate(spawns_nuevos[:10]):
        eid = str(mon.get("encounter_id"))
        nombre = mon.get("nombre_completo") or mon.get("pokemon_name")
        if canal_tipo == "shundo":
            embed = construir_embed_shundo(mon)
            contenido = f"🚨 {mencion}¡Nuevo **SHUNDO 100% IV ({nombre})** detectado!" if idx == 0 else f"🌟 ¡Nuevo **SHUNDO 100% IV ({nombre})**!"
        else:
            pvp = mon.get("pvp") or {}
            rank = pvp.get("rank", "?")
            pvp_name = pvp.get("pokemon_name") or nombre
            liga_tag = "Great League" if canal_tipo == "great" else "Ultra League"
            embed = construir_embed_pvp(mon, canal_tipo)
            contenido = (
                f"⚔️ {mencion}¡Nuevo **SHINY {liga_tag.upper()} RANK #{rank} ({nombre} ➔ {pvp_name})** detectado!"
                if idx == 0
                else f"⚔️ ¡Nuevo **SHINY {liga_tag} Rank #{rank} ({nombre})**!"
            )

        payload = {
            "username": bot_username,
            "content": contenido,
            "embeds": [embed]
        }
        try:
            r = requests.post(url_wait, json=payload, timeout=10)
            if r.status_code in (200, 204):
                try:
                    msg_data = r.json()
                    if msg_data and "id" in msg_data:
                        ids_mensajes[eid] = msg_data["id"]
                except Exception:
                    pass
                print(f"   ✅ [Discord-{canal_tipo.upper()}] Alerta enviada para {nombre} (se borrará al expirar).")
            else:
                print(f"   ⚠️ [Discord-{canal_tipo.upper()}] Error HTTP {r.status_code}: {r.text[:150]}")
        except Exception as e:
            print(f"   ⚠️ [Discord-{canal_tipo.upper()}] Error al enviar webhook: {e}")

    return ids_mensajes


def obtener_perfil_entrenador():
    try:
        r = requests.get(f"{API_BASE}/users/me", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json(), 200
        return None, r.status_code
    except Exception:
        return None, 0


def construir_payload_search(overrides):
    p = {
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
        "blacklist_forms": []
    }
    for k, v in overrides.items():
        if k != "label":
            p[k] = v
    return p


def ejecutar_particion_search(particion):
    payload = construir_payload_search(particion)
    try:
        r = requests.post(f"{API_BASE}/search", headers=headers, json=payload, timeout=12)
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception:
        pass
    return []


def ejecutar_region_mapa(region_tuple):
    nombre_region, n_lat, w_lng, s_lat, e_lng = region_tuple
    payload = {
        "mode": "pokemon",
        "n_lat": n_lat,
        "s_lat": s_lat,
        "w_lng": w_lng,
        "e_lng": e_lng,
        "num_results": 100,
        "filters": {
            "pokemon_ids": [],
            "species_forms": [],
            "blacklist_pokemon_ids": [],
            "blacklist_species_forms": [],
            "iv_min": 100,
            "iv_max": 100,
            "cp_min": None,
            "cp_max": None,
            "level_min": None,
            "level_max": None,
            "gender": None,
            "sizes": [],
            "boosted": None,
            "sort": "DSP",
            "pvp_mode": False,
            "pvp_league": "great",
            "pvp_top_rank": None,
            "pvp_include_pre_evolutions": True,
            "pvp_min_cp": None,
            "shiny_only": True,
            "shiny_account": None,
            "background_only": False,
            "always_show": []
        }
    }
    try:
        r = requests.post(f"{API_BASE}/map/lookup", headers=headers, json=payload, timeout=12)
        if r.status_code == 200:
            items = r.json().get("results", [])
            for item in items:
                item["region_mapa"] = nombre_region
            return nombre_region, items
    except Exception:
        pass
    return nombre_region, []


def calcular_tiempo_restante(despawn_iso=None, despawn_ms=None):
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


def normalizar_spawn(existente, nuevo):
    if not existente:
        existente = {}
    combinado = dict(existente)
    for k, v in nuevo.items():
        if v is not None and (k not in combinado or combinado[k] is None):
            combinado[k] = v
    return combinado


def preparar_lista_spawns(diccionario_spawns, cache_coords, estado_cuota):
    activos = []
    for eid, mon in diccionario_spawns.items():
        txt_ttl, seg_restantes, despawn_unix = calcular_tiempo_restante(mon.get("despawn_at"), mon.get("despawn_at_ms"))
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
                    rev_res = requests.get(f"{API_BASE}/reveal/{reveal_code}", headers=headers, timeout=8)
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
                            cache_coords[eid] = {"coords": coords, "lat": lat, "lng": lng, "ts": int(time.time())}
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
                    mon["precision_coords"] = "Mapa (~300m)"
                else:
                    mon["coords_final"] = "No disponible (cuota /reveal en espera)"
                    mon["lat_final"] = None
                    mon["lng_final"] = None
                    mon["precision_coords"] = "Pendiente"

        lat = mon.get("lat_final")
        lng = mon.get("lng_final")
        if lat is None or lng is None:
            continue
        mon["distancia_km"] = calcular_distancia_km(LAT_ORIGEN, LNG_ORIGEN, lat, lng)
        activos.append(mon)

    return activos


def ejecutar_ciclo_radar(mostrar_cabecera=True):
    inicio = time.time()
    eliminar_mensajes_expirados_discord()

    perfil, status_perfil = obtener_perfil_entrenador()

    if status_perfil == 401:
        print("❌ Error HTTP 401: El JWT_TOKEN ha expirado. Enviando aviso a Discord...")
        enviar_alerta_token_vencido()
        return

    if mostrar_cabecera:
        print("=" * 78)
        print("🌍 RADAR PRO MULTI-CANAL: SHUNDOS 100% + PVP GREAT LEAGUE + PVP ULTRA LEAGUE")
        print("=" * 78)

        if perfil:
            trainer = perfil.get("trainer") or {}
            t_name = trainer.get("trainer_name", "Desconocido")
            t_code = trainer.get("trainer_code", "N/A")
            t_team = trainer.get("team_name", "N/A")
            t_lvl = trainer.get("level", "?")
            entorno = "Nube GitHub Actions 24/7 ☁️" if ES_MODO_NUBE else "PC Local 💻"
            print(f"👤 Usuario Discord : {perfil.get('display_name')} | Modo: {entorno}")
            print(f"🎮 Entrenador PoGO : {t_name} (Código: {t_code} | Equipo: {t_team} | Nivel: {t_lvl})")
            print("📡 Canales Activos : [1] 🌟 Shundos 100%  |  [2] 🔵 PvP GL (Top 1-5)  |  [3] 🟣 PvP UL (Top 1-5)")
        else:
            print("⚠️ No se pudo verificar /users/me temporalmente. Continuando escaneo...")
        print("-" * 78)

    shundos_por_id = {}
    gl_por_id = {}
    ul_por_id = {}

    with ThreadPoolExecutor(max_workers=14) as executor:
        fut_shundos = [executor.submit(ejecutar_particion_search, p) for p in PARTICIONES_SHUNDOS]
        fut_mapa = [executor.submit(ejecutar_region_mapa, r) for r in REGIONES_GLOBALES]
        fut_gl = [executor.submit(ejecutar_particion_search, p) for p in PARTICIONES_PVP_GL]
        fut_ul = [executor.submit(ejecutar_particion_search, p) for p in PARTICIONES_PVP_UL]

        for fut in as_completed(fut_shundos):
            for mon in fut.result():
                if float(mon.get("iv_percent") or 0.0) == 100.0 and mon.get("shiny"):
                    eid = str(mon.get("encounter_id"))
                    shundos_por_id[eid] = normalizar_spawn(shundos_por_id.get(eid), mon)

        for fut in as_completed(fut_mapa):
            _, items = fut.result()
            for mon in items:
                if float(mon.get("iv_percent") or 0.0) == 100.0 and mon.get("shiny"):
                    eid = str(mon.get("encounter_id"))
                    shundos_por_id[eid] = normalizar_spawn(shundos_por_id.get(eid), mon)

        for fut in as_completed(fut_gl):
            for mon in fut.result():
                pvp = mon.get("pvp") or {}
                if mon.get("shiny") and pvp.get("league") == "great" and int(pvp.get("rank", 99)) <= PVP_TOP_RANK_MAX:
                    eid = str(mon.get("encounter_id"))
                    gl_por_id[eid] = normalizar_spawn(gl_por_id.get(eid), mon)

        for fut in as_completed(fut_ul):
            for mon in fut.result():
                pvp = mon.get("pvp") or {}
                if mon.get("shiny") and pvp.get("league") == "ultra" and int(pvp.get("rank", 99)) <= PVP_TOP_RANK_MAX:
                    eid = str(mon.get("encounter_id"))
                    ul_por_id[eid] = normalizar_spawn(ul_por_id.get(eid), mon)

    cache_coords = cargar_json(CACHE_FILE)
    notificados = cargar_json(NOTIFICADOS_FILE)
    limpiar_archivos_antiguos(cache_coords, notificados)

    estado_cuota = {"revelados": 0, "agotada": False}

    shundos_activos = preparar_lista_spawns(shundos_por_id, cache_coords, estado_cuota)
    gl_activos = preparar_lista_spawns(gl_por_id, cache_coords, estado_cuota)
    ul_activos = preparar_lista_spawns(ul_por_id, cache_coords, estado_cuota)

    guardar_json(CACHE_FILE, cache_coords)

    shundos_activos.sort(key=lambda x: (float(x.get("level") or 0.0), int(x.get("cp") or 0), int(x.get("ttl_segundos") or 0)), reverse=True)
    gl_activos.sort(key=lambda x: (int((x.get("pvp") or {}).get("rank", 99)), -float((x.get("pvp") or {}).get("percent", 0.0)), -int(x.get("ttl_segundos") or 0)))
    ul_activos.sort(key=lambda x: (int((x.get("pvp") or {}).get("rank", 99)), -float((x.get("pvp") or {}).get("percent", 0.0)), -int(x.get("ttl_segundos") or 0)))

    nuevos_shundos = [m for m in shundos_activos if f"shundo:{m.get('encounter_id')}" not in notificados and str(m.get("encounter_id")) not in notificados]
    nuevos_gl = [m for m in gl_activos if f"great:{m.get('encounter_id')}" not in notificados]
    nuevos_ul = [m for m in ul_activos if f"ultra:{m.get('encounter_id')}" not in notificados]

    duracion = time.time() - inicio
    hora_actual = datetime.now().strftime("%H:%M:%S")
    print(
        f"\n[{hora_actual}] 📊 ESCANEO COMPLETADO ({duracion:.1f}s) | "
        f"🌟 Shundos: {len(shundos_activos)} (🆕 {len(nuevos_shundos)}) | "
        f"🔵 GL Top 1-5: {len(gl_activos)} (🆕 {len(nuevos_gl)}) | "
        f"🟣 UL Top 1-5: {len(ul_activos)} (🆕 {len(nuevos_ul)})"
    )
    print("=" * 78)

    for idx, mon in enumerate(shundos_activos, start=1):
        print(f"  [SHUNDO #{idx:02d}] 🌟 {mon['nombre_completo']} 100% IV | CP {mon.get('cp')} | L{mon.get('level')} | 📍 {mon.get('location') or mon.get('region_mapa')} | 🎯 {mon.get('coords_final')} | ⏳ {mon.get('ttl_texto')}")

    for idx, mon in enumerate(gl_activos, start=1):
        pvp = mon.get("pvp") or {}
        print(f"  [GL #{idx:02d}] 🔵 Rank #{pvp.get('rank')} ({pvp.get('percent')}%) {mon['nombre_completo']} ➔ {pvp.get('pokemon_name')} (CP {pvp.get('cp')}) | IV {mon.get('raw_iv')} | 🎯 {mon.get('coords_final')} | ⏳ {mon.get('ttl_texto')}")

    for idx, mon in enumerate(ul_activos, start=1):
        pvp = mon.get("pvp") or {}
        print(f"  [UL #{idx:02d}] 🟣 Rank #{pvp.get('rank')} ({pvp.get('percent')}%) {mon['nombre_completo']} ➔ {pvp.get('pokemon_name')} (CP {pvp.get('cp')}) | IV {mon.get('raw_iv')} | 🎯 {mon.get('coords_final')} | ⏳ {mon.get('ttl_texto')}")

    ahora_ts = int(time.time())

    # 1. Enviar nuevos Shundos al canal de Shundos
    if nuevos_shundos:
        if AUTO_COPIAR_PORTAPAPELES:
            copiar_al_portapapeles(nuevos_shundos[0].get("coords_final") or "")
        ids_shundo = enviar_lote_webhook(DISCORD_WEBHOOK_URL, nuevos_shundos, "shundo", "Radar Shundo Pro ✨")
        for mon in nuevos_shundos:
            eid = str(mon.get("encounter_id"))
            notificados[f"shundo:{eid}"] = {
                "canal": "shundo",
                "pokemon": mon.get("nombre_completo"),
                "coords": mon.get("coords_final"),
                "ts": ahora_ts,
                "despawn_unix": mon.get("despawn_unix"),
                "discord_msg_id": ids_shundo.get(eid),
                "eliminado_de_discord": False,
                "notificado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    # 2. Enviar nuevos PvP Great League (Rank 1-5) al canal GL
    if nuevos_gl:
        ids_gl = enviar_lote_webhook(DISCORD_WEBHOOK_GL, nuevos_gl, "great", "Radar PvP Great League 🔵✨")
        for mon in nuevos_gl:
            eid = str(mon.get("encounter_id"))
            notificados[f"great:{eid}"] = {
                "canal": "great",
                "pokemon": mon.get("nombre_completo"),
                "coords": mon.get("coords_final"),
                "ts": ahora_ts,
                "despawn_unix": mon.get("despawn_unix"),
                "discord_msg_id": ids_gl.get(eid),
                "eliminado_de_discord": False,
                "notificado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    # 3. Enviar nuevos PvP Ultra League (Rank 1-5) al canal UL
    if nuevos_ul:
        ids_ul = enviar_lote_webhook(DISCORD_WEBHOOK_UL, nuevos_ul, "ultra", "Radar PvP Ultra League 🟣✨")
        for mon in nuevos_ul:
            eid = str(mon.get("encounter_id"))
            notificados[f"ultra:{eid}"] = {
                "canal": "ultra",
                "pokemon": mon.get("nombre_completo"),
                "coords": mon.get("coords_final"),
                "ts": ahora_ts,
                "despawn_unix": mon.get("despawn_unix"),
                "discord_msg_id": ids_ul.get(eid),
                "eliminado_de_discord": False,
                "notificado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    if nuevos_shundos or nuevos_gl or nuevos_ul:
        guardar_json(NOTIFICADOS_FILE, notificados)


def esperar_con_limpieza_despawn(segundos_totales):
    """Durante la espera entre escaneos, verifica cada 5s si algún Shundo o PvP GL/UL ya expiró para borrarlo de su canal de Discord."""
    fin = time.time() + segundos_totales
    while time.time() < fin:
        eliminar_mensajes_expirados_discord()
        restante = fin - time.time()
        if restante <= 0:
            break
        time.sleep(min(5.0, restante))


def iniciar_radar():
    if "--reset-notificados" in sys.argv and os.path.exists(NOTIFICADOS_FILE):
        try:
            os.remove(NOTIFICADOS_FILE)
        except Exception:
            pass

    duracion_minutos = None
    if "--duracion-minutos" in sys.argv:
        idx = sys.argv.index("--duracion-minutos")
        if idx + 1 < len(sys.argv):
            duracion_minutos = float(sys.argv[idx + 1])

    una_vez = "--una-vez" in sys.argv or (not MODO_VIGILANTE_CONTINUO and duracion_minutos is None)
    if una_vez:
        ejecutar_ciclo_radar(mostrar_cabecera=True)
        return

    inicio_bucle = time.time()
    ciclo = 1
    try:
        while True:
            ejecutar_ciclo_radar(mostrar_cabecera=(ciclo == 1))
            if duracion_minutos is not None:
                transcurrido_min = (time.time() - inicio_bucle) / 60.0
                if transcurrido_min + (INTERVALO_SEGUNDOS / 60.0) >= duracion_minutos:
                    eliminar_mensajes_expirados_discord()
                    print(f"✅ Ciclo en la nube de {duracion_minutos} minutos completado. Guardando estado y encadenando siguiente ciclo...")
                    break
            print(f"⏳ Vigilante activo: próximo escaneo en {INTERVALO_SEGUNDOS // 60} min (borrado automático de despawns activo en los 3 canales)...")
            esperar_con_limpieza_despawn(INTERVALO_SEGUNDOS)
            ciclo += 1
    except KeyboardInterrupt:
        print("\n👋 Vigilante detenido por el usuario.")


if __name__ == "__main__":
    iniciar_radar()
