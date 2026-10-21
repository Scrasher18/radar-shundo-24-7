"""
Motor principal de escaneo multi-canal (Shundos 100%, Great League y Ultra League)
y orquestador de ciclos 24/7.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
import sys
import time
from typing import Any, Dict

from src.api_client import (
    ejecutar_particion_search,
    ejecutar_region_mapa,
    obtener_perfil_entrenador,
    preparar_lista_spawns,
)
from src.config import (
    AUTO_COPIAR_PORTAPAPELES,
    BOT_NOMBRES_POR_CANAL,
    CACHE_FILE,
    DISCORD_WEBHOOK_GL,
    DISCORD_WEBHOOK_UL,
    DISCORD_WEBHOOK_URL,
    ES_MODO_NUBE,
    INTERVALO_SEGUNDOS,
    MODO_VIGILANTE_CONTINUO,
    NOTIFICADOS_FILE,
    PARTICIONES_PVP_GL,
    PARTICIONES_PVP_UL,
    PARTICIONES_SHUNDOS,
    PVP_MIN_CP_GL,
    PVP_MIN_CP_UL,
    PVP_TOP_RANK_MAX,
    REGIONES_GLOBALES,
)
from src.discord_service import (
    eliminar_mensajes_expirados_discord,
    enviar_alerta_token_vencido,
    enviar_lote_webhook,
    iniciar_hilos_reloj_tiempo_real,
)
from src.models import copiar_al_portapapeles, normalizar_spawn
from src.state_manager import (
    _LOCK_ESTADO,
    cargar_json,
    guardar_json,
    limpiar_archivos_antiguos,
    sincronizar_estado_remoto_pull,
    sincronizar_estado_remoto_push,
    ya_fue_notificado,
)


def ejecutar_ciclo_radar(mostrar_cabecera: bool = True) -> None:
    """Ejecuta un ciclo completo de escaneo global en las 3 ligas/canales."""
    inicio = time.time()
    iniciar_hilos_reloj_tiempo_real()
    sincronizar_estado_remoto_pull()

    perfil, status_perfil = obtener_perfil_entrenador()

    if status_perfil == 401:
        print("❌ Error HTTP 401: El JWT_TOKEN ha expirado. Enviando aviso a Discord...")
        enviar_alerta_token_vencido()
        return

    if mostrar_cabecera:
        print("=" * 78)
        print("🌍 RADAR PRO MULTI-CANAL v2.0: SHUNDOS 100% + PVP GREAT LEAGUE + ULTRA LEAGUE")
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

    shundos_por_id: Dict[str, Dict[str, Any]] = {}
    gl_por_id: Dict[str, Dict[str, Any]] = {}
    ul_por_id: Dict[str, Dict[str, Any]] = {}

    # Oleada 1: Shundos 100% IV
    with ThreadPoolExecutor(max_workers=2) as executor:
        fut_shundos = [executor.submit(ejecutar_particion_search, p) for p in PARTICIONES_SHUNDOS]
        fut_mapa_shundos = [executor.submit(ejecutar_region_mapa, r, "shundo") for r in REGIONES_GLOBALES]
        for fut in as_completed(fut_shundos):
            for mon in fut.result():
                if float(mon.get("iv_percent") or 0.0) == 100.0 and mon.get("shiny"):
                    eid = str(mon.get("encounter_id"))
                    shundos_por_id[eid] = normalizar_spawn(shundos_por_id.get(eid), mon)
        for fut in as_completed(fut_mapa_shundos):
            _, items = fut.result()
            for mon in items:
                if float(mon.get("iv_percent") or 0.0) == 100.0 and mon.get("shiny"):
                    eid = str(mon.get("encounter_id"))
                    shundos_por_id[eid] = normalizar_spawn(shundos_por_id.get(eid), mon)

    time.sleep(1.0)

    # Oleada 2: PvP Great League (Rank #1 al #5 Shiny, CP mínimo competitivo >= 1400)
    with ThreadPoolExecutor(max_workers=2) as executor:
        fut_gl = [executor.submit(ejecutar_particion_search, p) for p in PARTICIONES_PVP_GL]
        fut_mapa_gl = [executor.submit(ejecutar_region_mapa, r, "great") for r in REGIONES_GLOBALES]
        for fut in as_completed(fut_gl):
            for mon in fut.result():
                pvp = mon.get("pvp") or {}
                if (
                    mon.get("shiny")
                    and pvp.get("league") == "great"
                    and int(pvp.get("rank", 99)) <= PVP_TOP_RANK_MAX
                    and int(pvp.get("cp") or 0) >= PVP_MIN_CP_GL
                ):
                    eid = str(mon.get("encounter_id"))
                    gl_por_id[eid] = normalizar_spawn(gl_por_id.get(eid), mon)
        for fut in as_completed(fut_mapa_gl):
            _, items = fut.result()
            for mon in items:
                pvp = mon.get("pvp") or {}
                if (
                    mon.get("shiny")
                    and pvp.get("league") == "great"
                    and int(pvp.get("rank", 99)) <= PVP_TOP_RANK_MAX
                    and int(pvp.get("cp") or 0) >= PVP_MIN_CP_GL
                ):
                    eid = str(mon.get("encounter_id"))
                    gl_por_id[eid] = normalizar_spawn(gl_por_id.get(eid), mon)

    time.sleep(1.0)

    # Oleada 3: PvP Ultra League (Rank #1 al #5 Shiny, CP mínimo competitivo >= 2350)
    with ThreadPoolExecutor(max_workers=2) as executor:
        fut_ul = [executor.submit(ejecutar_particion_search, p) for p in PARTICIONES_PVP_UL]
        fut_mapa_ul = [executor.submit(ejecutar_region_mapa, r, "ultra") for r in REGIONES_GLOBALES]
        for fut in as_completed(fut_ul):
            for mon in fut.result():
                pvp = mon.get("pvp") or {}
                if (
                    mon.get("shiny")
                    and pvp.get("league") == "ultra"
                    and int(pvp.get("rank", 99)) <= PVP_TOP_RANK_MAX
                    and int(pvp.get("cp") or 0) >= PVP_MIN_CP_UL
                ):
                    eid = str(mon.get("encounter_id"))
                    ul_por_id[eid] = normalizar_spawn(ul_por_id.get(eid), mon)
        for fut in as_completed(fut_mapa_ul):
            _, items = fut.result()
            for mon in items:
                pvp = mon.get("pvp") or {}
                if (
                    mon.get("shiny")
                    and pvp.get("league") == "ultra"
                    and int(pvp.get("rank", 99)) <= PVP_TOP_RANK_MAX
                    and int(pvp.get("cp") or 0) >= PVP_MIN_CP_UL
                ):
                    eid = str(mon.get("encounter_id"))
                    ul_por_id[eid] = normalizar_spawn(ul_por_id.get(eid), mon)

    with _LOCK_ESTADO:
        cache_coords = cargar_json(CACHE_FILE)
        notificados = cargar_json(NOTIFICADOS_FILE)
        limpiar_archivos_antiguos(cache_coords, notificados)

    estado_cuota = {"revelados": 0, "agotada": False}

    shundos_activos = preparar_lista_spawns(shundos_por_id, cache_coords, estado_cuota)
    gl_activos = preparar_lista_spawns(gl_por_id, cache_coords, estado_cuota)
    ul_activos = preparar_lista_spawns(ul_por_id, cache_coords, estado_cuota)

    guardar_json(CACHE_FILE, cache_coords)

    shundos_activos.sort(
        key=lambda x: (float(x.get("level") or 0.0), int(x.get("cp") or 0), int(x.get("ttl_segundos") or 0)),
        reverse=True,
    )
    gl_activos.sort(
        key=lambda x: (
            int((x.get("pvp") or {}).get("rank", 99)),
            -float((x.get("pvp") or {}).get("percent", 0.0)),
            -int(x.get("ttl_segundos") or 0),
        )
    )
    ul_activos.sort(
        key=lambda x: (
            int((x.get("pvp") or {}).get("rank", 99)),
            -float((x.get("pvp") or {}).get("percent", 0.0)),
            -int(x.get("ttl_segundos") or 0),
        )
    )

    with _LOCK_ESTADO:
        notificados = cargar_json(NOTIFICADOS_FILE)
        nuevos_shundos = [m for m in shundos_activos if not ya_fue_notificado(m, "shundo", notificados)]
        nuevos_gl = [m for m in gl_activos if not ya_fue_notificado(m, "great", notificados)]
        nuevos_ul = [m for m in ul_activos if not ya_fue_notificado(m, "ultra", notificados)]

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
        print(
            f"  [SHUNDO #{idx:02d}] 🌟 {mon['nombre_completo']} 100% IV | CP {mon.get('cp')} | L{mon.get('level')} | 📍 {mon.get('location') or mon.get('region_mapa')} | 🎯 {mon.get('coords_final')} | ⏳ {mon.get('ttl_texto')}"
        )

    for idx, mon in enumerate(gl_activos, start=1):
        pvp = mon.get("pvp") or {}
        print(
            f"  [GL #{idx:02d}] 🔵 Rank #{pvp.get('rank')} ({pvp.get('percent')}%) {mon['nombre_completo']} ➔ {pvp.get('pokemon_name')} (CP {pvp.get('cp')}) | IV {mon.get('raw_iv')} | 🎯 {mon.get('coords_final')} | ⏳ {mon.get('ttl_texto')}"
        )

    for idx, mon in enumerate(ul_activos, start=1):
        pvp = mon.get("pvp") or {}
        print(
            f"  [UL #{idx:02d}] 🟣 Rank #{pvp.get('rank')} ({pvp.get('percent')}%) {mon['nombre_completo']} ➔ {pvp.get('pokemon_name')} (CP {pvp.get('cp')}) | IV {mon.get('raw_iv')} | 🎯 {mon.get('coords_final')} | ⏳ {mon.get('ttl_texto')}"
        )

    ahora_ts = int(time.time())
    lotes_enviados = [
        ("shundo", DISCORD_WEBHOOK_URL, nuevos_shundos),
        ("great", DISCORD_WEBHOOK_GL, nuevos_gl),
        ("ultra", DISCORD_WEBHOOK_UL, nuevos_ul),
    ]

    if nuevos_shundos and AUTO_COPIAR_PORTAPAPELES:
        copiar_al_portapapeles(nuevos_shundos[0].get("coords_final") or "")

    hubo_nuevos = False
    for canal_tipo, webhook_url, lista_nuevos in lotes_enviados:
        if not lista_nuevos:
            continue
        ids_enviados = enviar_lote_webhook(
            webhook_url,
            lista_nuevos,
            canal_tipo,
            BOT_NOMBRES_POR_CANAL[canal_tipo],
        )
        with _LOCK_ESTADO:
            notificados_actual = cargar_json(NOTIFICADOS_FILE)
            for mon in lista_nuevos:
                eid = str(mon.get("encounter_id"))
                mid = ids_enviados.get(eid)
                notificados_actual[f"{canal_tipo}:{eid}"] = {
                    "canal": canal_tipo,
                    "pokemon": mon.get("nombre_completo"),
                    "coords": mon.get("coords_final"),
                    "ts": ahora_ts,
                    "despawn_unix": mon.get("despawn_unix"),
                    "discord_msg_id": mid,
                    "discord_msg_ids": [mid] if mid else [],
                    "eliminado_de_discord": False,
                    "notificado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            guardar_json(NOTIFICADOS_FILE, notificados_actual)
            hubo_nuevos = True

    if hubo_nuevos:
        sincronizar_estado_remoto_push(asincrono=True)


def esperar_con_limpieza_despawn(segundos_totales: float) -> None:
    """
    Mantiene vivo el proceso principal entre escaneos de 8 minutos mientras
    los 3 hilos dedicados actualizan los segundos en tiempo real cada 1s.
    """
    iniciar_hilos_reloj_tiempo_real()
    fin = time.time() + segundos_totales
    while time.time() < fin:
        restante = fin - time.time()
        if restante <= 0:
            break
        time.sleep(min(1.0, restante))


def iniciar_radar() -> None:
    """Punto de entrada principal de la aplicación."""
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

    iniciar_hilos_reloj_tiempo_real()
    inicio_bucle = time.time()
    ciclo = 1
    try:
        while True:
            ejecutar_ciclo_radar(mostrar_cabecera=(ciclo == 1))
            if duracion_minutos is not None:
                transcurrido_min = (time.time() - inicio_bucle) / 60.0
                if transcurrido_min + (INTERVALO_SEGUNDOS / 60.0) >= duracion_minutos:
                    eliminar_mensajes_expirados_discord(actualizar_tiempo_real=True)
                    sincronizar_estado_remoto_push(asincrono=False)
                    print(
                        f"✅ Ciclo en la nube de {duracion_minutos} minutos completado. Guardando estado y encadenando siguiente ciclo..."
                    )
                    break
            print(
                f"⏳ Vigilante activo: próximo escaneo en {INTERVALO_SEGUNDOS // 60} min (reloj 1s en vivo y auto-delete activos en 3 hilos)..."
            )
            esperar_con_limpieza_despawn(INTERVALO_SEGUNDOS)
            ciclo += 1
    except KeyboardInterrupt:
        print("\n👋 Vigilante detenido por el usuario.")
