import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import requests

try:
    import winsound
except ImportError:
    winsound = None

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
# ⚙️ CONFIGURACIÓN PRINCIPAL Y ALARMA DE DISCORD (LOCAL + NUBE 24/7)
# ==============================================================================
JWT_TOKEN = os.environ.get("JWT_TOKEN") or _cfg.get("JWT_TOKEN", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") or _cfg.get("DISCORD_WEBHOOK_URL", "")
DISCORD_USER_ID_MENCION = os.environ.get("DISCORD_USER_ID_MENCION") or _cfg.get("DISCORD_USER_ID_MENCION", "924392800534011935")
ES_MODO_NUBE = os.environ.get("CLOUD_MODE") == "1" or sys.platform != "win32"

LAT_ORIGEN = -12.058662
LNG_ORIGEN = -77.036896

# Opciones locales de apoyo (se desactivan solas cuando corre en la nube Linux)
ACTIVAR_ALARMA_SONORA_PC = not ES_MODO_NUBE
AUTO_COPIAR_PORTAPAPELES = not ES_MODO_NUBE

# Configuración del Vigilante Automático 24/7
MODO_VIGILANTE_CONTINUO = True     # True = revisa cada INTERVALO_SEGUNDOS automáticamente
INTERVALO_SEGUNDOS = 480           # Cada cuántos segundos busca nuevos Shundos (480s = 8 minutos)
MIN_SEGUNDOS_VIDA = 90             # Ignorar Shundos a los que les queden menos de 90s de vida (evita saltar en vano)
TTL_LIMPIEZA_CACHE_SEGUNDOS = 43200 # Limpiar automáticamente registros de más de 12 horas (mantenimiento 24/7)
MAX_REVEALS_POR_EJECUCION = 50

API_BASE = "https://coordinates-api.pokemongopro.com"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Tabla oficial de Cooldown de Pokémon GO (distancia en km -> minutos de espera)
TABLA_COOLDOWN_POGO = [
    (1, "0m 30s (Sin espera)"),
    (5, "2 min"),
    (10, "6 min"),
    (25, "11 min"),
    (30, "14 min"),
    (65, "22 min"),
    (81, "25 min"),
    (100, "28 min"),
    (250, "43 min"),
    (500, "62 min (1h 02m)"),
    (750, "78 min (1h 18m)"),
    (1000, "90 min (1h 30m)"),
    (1500, "120 min (2h máx)"),
]

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

# Particiones de /search exclusivas para SHUNDOS (100% IV + Shiny) para superar el cap=10
PARTICIONES_SEARCH = [
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


def calcular_distancia_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def calcular_cooldown_pogo(distancia_km):
    if distancia_km is None:
        return "Desconocido"
    for km_max, texto in TABLA_COOLDOWN_POGO:
        if distancia_km <= km_max:
            return texto
    return "120 min (2h máx)"


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
    # Limpiar cache_coordenadas (>12h)
    claves_borrar_cache = [
        k for k, v in cache_coords.items()
        if isinstance(v, dict) and (ahora - int(v.get("ts", ahora))) > TTL_LIMPIEZA_CACHE_SEGUNDOS
    ]
    for k in claves_borrar_cache:
        del cache_coords[k]

    # Limpiar shundos_notificados (>12h), conservando metadatos especiales (_meta_*)
    claves_borrar_notif = [
        k for k, v in notificados.items()
        if not k.startswith("_meta_") and isinstance(v, dict) and (ahora - int(v.get("ts", ahora))) > TTL_LIMPIEZA_CACHE_SEGUNDOS
    ]
    for k in claves_borrar_notif:
        del notificados[k]


def copiar_al_portapapeles(texto):
    if not AUTO_COPIAR_PORTAPAPELES or not texto or "," not in texto:
        return False
    try:
        subprocess.run(["clip"], input=texto.strip().encode("utf-8"), check=True)
        return True
    except Exception:
        return False


def sonar_alarma_shundo():
    if not ACTIVAR_ALARMA_SONORA_PC or not winsound:
        return
    try:
        for freq, dur in [(880, 160), (1175, 160), (1397, 160), (1760, 350), (1397, 150), (1760, 450)]:
            winsound.Beep(freq, dur)
    except Exception:
        pass


def enviar_alerta_token_vencido():
    if not DISCORD_WEBHOOK_URL.strip():
        return
    notificados = cargar_json(NOTIFICADOS_FILE)
    ahora = int(time.time())
    ultimo_aviso = int(notificados.get("_meta_alerta_401_ts", 0))
    # Avisar máximo 1 vez cada 6 horas para no hacer spam
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


def obtener_etiquetas_rareza(mon):
    etiquetas = ["✨ **SHUNDO 100% IV**"]
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


def enviar_alerta_discord(nuevos_shundos, ultimo_shundo_previo=None):
    if not DISCORD_WEBHOOK_URL.strip():
        return False

    embeds = []
    origen_txt = "☁️ Nube 24/7" if ES_MODO_NUBE else "💻 PC Local"
    ref_lat = ultimo_shundo_previo.get("lat") if isinstance(ultimo_shundo_previo, dict) else None
    ref_lng = ultimo_shundo_previo.get("lng") if isinstance(ultimo_shundo_previo, dict) else None
    ref_nombre = ultimo_shundo_previo.get("pokemon") if isinstance(ultimo_shundo_previo, dict) else None

    for mon in nuevos_shundos[:10]:
        poke_id = mon.get("pokemon_id") or 1
        nombre = mon.get("nombre_completo") or mon.get("pokemon_name") or f"#{poke_id}"
        coords = mon.get("coords_final") or "N/A"
        maps_url = f"https://www.google.com/maps?q={coords}" if "," in str(coords) else "https://maps.google.com"
        ubicacion = mon.get("location") or mon.get("region_mapa") or "Global"
        cp = mon.get("cp") or "?"
        nivel = mon.get("level") or "?"
        size = mon.get("size") or "-"
        gender = mon.get("gender") or "-"
        ttl = mon.get("ttl_texto") or "?"
        seg_rest = int(mon.get("ttl_segundos") or 0)
        despawn_unix = mon.get("despawn_unix")
        icon_url = f"https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Images/Pokemon/Addressable%20Assets/pm{poke_id}.s.icon.png"

        # Semáforo de urgencia según el tiempo de vida restante
        if seg_rest >= 900:
            estado_tiempo = f"🟢 **Tiempo Seguro** (`{ttl}`)"
            color_embed = 0xFFD700  # Dorado
        elif seg_rest >= 300:
            estado_tiempo = f"🟡 **Tiempo Medio** (`{ttl}`)"
            color_embed = 0xF97316  # Naranja
        else:
            estado_tiempo = f"🔴 **¡SALTAR YA!** (`{ttl}`)"
            color_embed = 0xEF4444  # Rojo urgencia

        if despawn_unix:
            estado_tiempo += f"\n🕒 Desaparece: <t:{despawn_unix}:R>"

        # Ataques
        fast_m = mon.get("fast_move")
        charge_m = mon.get("charge_move")
        ataques_txt = f"`{fast_m}` / `{charge_m}`" if (fast_m or charge_m) else "Estándar"

        # Calculadora de Cooldown desde el Shundo anterior (y desde origen)
        lat_m = mon.get("lat_final")
        lng_m = mon.get("lng_final")
        dist_origen = mon.get("distancia_km")
        cd_origen = calcular_cooldown_pogo(dist_origen)

        if ref_lat is not None and ref_lng is not None and lat_m is not None and lng_m is not None:
            dist_prev = calcular_distancia_km(ref_lat, ref_lng, lat_m, lng_m)
            cd_prev = calcular_cooldown_pogo(dist_prev)
            cooldown_txt = (
                f"🔄 **Desde {ref_nombre}:** `{cd_prev}` ({dist_prev:.1f} km)\n"
                f"🏠 **Desde tu Origen:** `{cd_origen}` ({dist_origen:.0f} km)"
            )
        else:
            cooldown_txt = f"🏠 **Desde tu Origen:** `{cd_origen}` ({dist_origen:.0f} km)" if dist_origen is not None else "N/A"

        # Actualizar referencia para el siguiente en la lista
        if lat_m is not None and lng_m is not None:
            ref_lat, ref_lng, ref_nombre = lat_m, lng_m, nombre

        rareza_txt = obtener_etiquetas_rareza(mon)

        embeds.append({
            "title": f"🌟 ¡SHUNDO 100% IV: {nombre}! (CP {cp} • Nivel {nivel})",
            "description": rareza_txt,
            "url": maps_url,
            "color": color_embed,
            "thumbnail": {"url": icon_url},
            "fields": [
                {"name": "📊 Estadísticas", "value": f"**IV:** `100% (15/15/15)`\n**CP:** `{cp}` | **Nivel:** `{nivel}`\n**Talla:** `{size}` ({gender})", "inline": True},
                {"name": "⏳ Estado Despawn", "value": estado_tiempo, "inline": True},
                {"name": "⚔️ Movimientos", "value": ataques_txt, "inline": False},
                {"name": "⏱️ Calculadora de Cooldown", "value": cooldown_txt, "inline": False},
                {"name": "📍 Ubicación", "value": f"{ubicacion} • [🗺️ Ver en Google Maps]({maps_url})", "inline": False},
                {"name": "🎯 Coordenadas Exactas", "value": f"```\n{coords}\n```", "inline": False},
            ],
            "footer": {"text": f"Radar Shundo Pro ({origen_txt}) • 100% Shiny Garantizado para XxTheScrasherxX"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    mencion = f"<@{DISCORD_USER_ID_MENCION}> " if DISCORD_USER_ID_MENCION else ""
    payload = {
        "username": "Radar Shundo Pro ✨",
        "content": f"🚨 {mencion}¡Apareció **{len(nuevos_shundos)} nuevo(s) SHUNDO(S) 100% IV (15/15/15)** en el mundo!",
        "embeds": embeds
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL.strip(), json=payload, timeout=10)
        if r.status_code in (200, 204):
            # Enviar mensaje separado SOLO con la coordenada limpia para copiar en 1 toque en Discord Móvil
            for mon in nuevos_shundos[:5]:
                coords = mon.get("coords_final") or ""
                if "," in str(coords):
                    requests.post(
                        DISCORD_WEBHOOK_URL.strip(),
                        json={"username": f"📋 Copiar: {mon.get('nombre_completo')} (CP {mon.get('cp')} L{mon.get('level')})", "content": f"{coords}"},
                        timeout=8
                    )
            print("   ✅ [Discord] ¡Tarjeta(s) + Coordenada(s) de 1-toque enviadas a tu Discord!")
            return True
        else:
            print(f"   ⚠️ [Discord] Error HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"   ⚠️ [Discord] Error al enviar webhook: {e}")
    return False


def disparar_alertas_nuevos_shundos(nuevos_shundos, ultimo_shundo_previo=None):
    if not nuevos_shundos:
        return

    mejor = nuevos_shundos[0]
    coords_mejor = mejor.get("coords_final") or ""
    nombre_mejor = mejor.get("nombre_completo") or mejor.get("pokemon_name")

    print("\n" + "🚨" * 35)
    print(f"🔔 ¡ALARMA DISCORD ACTIVADA! {len(nuevos_shundos)} NUEVO(S) SHUNDO(S) 100% IV DETECTADO(S) 🔔")
    print("🚨" * 35)

    if AUTO_COPIAR_PORTAPAPELES and copiar_al_portapapeles(coords_mejor):
        print(f"   📋 [Portapapeles] Coordenada copiada automáticamente (Ctrl+V): {coords_mejor} ({nombre_mejor})")

    sonar_alarma_shundo()
    enviar_alerta_discord(nuevos_shundos, ultimo_shundo_previo=ultimo_shundo_previo)
    print("🚨" * 35 + "\n")


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
        "iv_percent_min": 100,
        "iv_percent_max": 100,
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


def ejecutar_ciclo_radar(mostrar_cabecera=True):
    inicio = time.time()
    perfil, status_perfil = obtener_perfil_entrenador()

    if status_perfil == 401:
        print("❌ Error HTTP 401: El JWT_TOKEN ha expirado. Enviando aviso a Discord...")
        enviar_alerta_token_vencido()
        return

    if mostrar_cabecera:
        print("=" * 78)
        print("🌍 RADAR PRO GLOBAL DE SHUNDOS + ALARMA INTELIGENTE EN DISCORD")
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
            print("✨ Nota: Todos los Pokémon listados son 100% IV (15/15/15) y SHINY GARANTIZADO para esta cuenta.")
        else:
            print("⚠️ No se pudo verificar /users/me temporalmente. Continuando escaneo...")
        print("-" * 78)

    spawns_por_id = {}

    with ThreadPoolExecutor(max_workers=12) as executor:
        futuros_search = [executor.submit(ejecutar_particion_search, p) for p in PARTICIONES_SEARCH]
        futuros_mapa = [executor.submit(ejecutar_region_mapa, r) for r in REGIONES_GLOBALES]

        for fut in as_completed(futuros_search):
            for mon in fut.result():
                if float(mon.get("iv_percent") or 0.0) == 100.0 and mon.get("shiny"):
                    eid = str(mon.get("encounter_id"))
                    spawns_por_id[eid] = normalizar_spawn(spawns_por_id.get(eid), mon)

        for fut in as_completed(futuros_mapa):
            _, items = fut.result()
            shundos_reg = [m for m in items if float(m.get("iv_percent") or 0.0) == 100.0 and m.get("shiny")]
            for mon in shundos_reg:
                eid = str(mon.get("encounter_id"))
                spawns_por_id[eid] = normalizar_spawn(spawns_por_id.get(eid), mon)

    spawns_activos = []
    ignorados_por_ttl = 0
    for eid, mon in spawns_por_id.items():
        if float(mon.get("iv_percent") or 0.0) != 100.0:
            continue
        txt_ttl, seg_restantes, despawn_unix = calcular_tiempo_restante(mon.get("despawn_at"), mon.get("despawn_at_ms"))
        if seg_restantes < 0:
            continue
        if seg_restantes < MIN_SEGUNDOS_VIDA:
            ignorados_por_ttl += 1
            continue
        mon["ttl_texto"] = txt_ttl
        mon["ttl_segundos"] = seg_restantes
        mon["despawn_unix"] = despawn_unix

        nombre = mon.get("pokemon_name") or f"#{mon.get('pokemon_id')}"
        form = mon.get("form")
        costume = mon.get("costume")
        extras_nombre = " ".join(f"({x})" for x in [form, costume] if x and x != "Normal")
        mon["nombre_completo"] = f"{nombre} {extras_nombre}" if extras_nombre else nombre
        spawns_activos.append(mon)

    spawns_activos.sort(
        key=lambda x: (
            float(x.get("level") or 0.0),
            int(x.get("cp") or 0),
            int(x.get("ttl_segundos") or 0)
        ),
        reverse=True
    )

    cache_coords = cargar_json(CACHE_FILE)
    notificados = cargar_json(NOTIFICADOS_FILE)
    limpiar_archivos_antiguos(cache_coords, notificados)

    revelados_nuevos = 0
    cuota_agotada = False

    for mon in spawns_activos:
        eid = str(mon.get("encounter_id"))
        if eid in cache_coords:
            c_data = cache_coords[eid]
            mon["coords_final"] = c_data["coords"]
            mon["lat_final"] = c_data["lat"]
            mon["lng_final"] = c_data["lng"]
            mon["precision_coords"] = "Exacta (Caché)"
            continue

        reveal_code = mon.get("reveal_code")
        if reveal_code and not cuota_agotada and revelados_nuevos < MAX_REVEALS_POR_EJECUCION:
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
                        revelados_nuevos += 1
                        continue
                elif rev_res.status_code in (403, 429):
                    cuota_agotada = True
            except Exception:
                pass

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

    guardar_json(CACHE_FILE, cache_coords)

    for mon in spawns_activos:
        lat = mon.get("lat_final")
        lng = mon.get("lng_final")
        if lat is not None and lng is not None:
            mon["distancia_km"] = calcular_distancia_km(LAT_ORIGEN, LNG_ORIGEN, lat, lng)
        else:
            mon["distancia_km"] = None

    ultimo_shundo_previo = notificados.get("_meta_ultimo_shundo")
    nuevos_shundos = []
    ahora_ts = int(time.time())
    for mon in spawns_activos:
        eid = str(mon.get("encounter_id"))
        if eid not in notificados:
            nuevos_shundos.append(mon)
            notificados[eid] = {
                "pokemon": mon.get("nombre_completo"),
                "coords": mon.get("coords_final"),
                "ts": ahora_ts,
                "notificado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    if nuevos_shundos:
        ultimo = nuevos_shundos[-1]
        if ultimo.get("lat_final") is not None and ultimo.get("lng_final") is not None:
            notificados["_meta_ultimo_shundo"] = {
                "pokemon": ultimo.get("nombre_completo"),
                "lat": ultimo.get("lat_final"),
                "lng": ultimo.get("lng_final"),
                "coords": ultimo.get("coords_final"),
                "ts": ahora_ts
            }
    guardar_json(NOTIFICADOS_FILE, notificados)

    duracion = time.time() - inicio
    hora_actual = datetime.now().strftime("%H:%M:%S")
    extra_ign = f" | ⏭️ Ignorados (<{MIN_SEGUNDOS_VIDA}s): {ignorados_por_ttl}" if ignorados_por_ttl else ""
    print(f"\n[{hora_actual}] 📊 ESCANEO COMPLETADO ({duracion:.1f}s) | 🌟 Shundos: {len(spawns_activos)} | 🆕 Nuevos: {len(nuevos_shundos)}{extra_ign}")
    print("=" * 78)

    if not spawns_activos:
        print("No hay spawns 100% IV Shiny activos (>90s de vida) en este preciso instante en todo el mundo.")
        return

    lineas_export = [
        f"REPORTE MUNDIAL DE SHUNDOS (100% IV SHINY) - Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Shundos Activos: {len(spawns_activos)}\n"
    ]

    for idx, mon in enumerate(spawns_activos, start=1):
        nombre = mon.get("nombre_completo")
        raw_iv = mon.get("raw_iv") or "15/15/15"
        cp = mon.get("cp") or "?"
        nivel = mon.get("level") or "?"
        size = mon.get("size") or "-"
        gender = mon.get("gender") or "-"
        ubicacion = mon.get("location") or mon.get("region_mapa") or "Global"
        coords = mon.get("coords_final")
        precision = mon.get("precision_coords")
        ttl = mon.get("ttl_texto")
        dist = mon.get("distancia_km")
        cd_txt = calcular_cooldown_pogo(dist)
        dist_str = f"{dist:.2f} km • Cooldown: {cd_txt}" if dist is not None else "N/A"
        maps_url = f"https://www.google.com/maps?q={coords}" if coords and "," in coords else "N/A"
        es_nuevo_tag = " 🆕 ¡ENVIADO A DISCORD!" if mon in nuevos_shundos else ""

        bloque = (
            f"[{idx:02d}] 🌟 SHUNDO 100% IV ({raw_iv}) — {nombre}{es_nuevo_tag} | CP {cp} | Nivel {nivel} | Talla {size} ({gender})\n"
            f"     📍 Ubicación  : {ubicacion} ({dist_str})\n"
            f"     🎯 Coordenadas: {coords} [{precision}]\n"
            f"     🗺️ Google Maps: {maps_url}\n"
            f"     ⏳ Expira en  : {ttl}\n"
        )
        lineas_export.append(bloque)
        print(bloque)

    try:
        with open(EXPORT_TXT, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas_export))
        with open(EXPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(spawns_activos, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    if nuevos_shundos:
        disparar_alertas_nuevos_shundos(nuevos_shundos, ultimo_shundo_previo=ultimo_shundo_previo)


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
                    print(f"✅ Ciclo en la nube de {duracion_minutos} minutos completado. Guardando estado y encadenando siguiente ciclo...")
                    break
            print(f"⏳ Vigilante activo: próximo escaneo automático en {INTERVALO_SEGUNDOS // 60} minutos ({INTERVALO_SEGUNDOS}s)...")
            time.sleep(INTERVALO_SEGUNDOS)
            ciclo += 1
    except KeyboardInterrupt:
        print("\n👋 Vigilante detenido por el usuario.")


if __name__ == "__main__":
    iniciar_radar()
