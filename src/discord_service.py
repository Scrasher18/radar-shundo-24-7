"""
Servicio multihilo de Discord con Panel Consolidado Multi-Embed por Canal:
- Agrupa los Pokémon activos de cada canal (Shundos, Great League, Ultra League)
  en un único mensaje activo por canal (hasta 8 embeds simultáneos).
- Gracias a esto, cada canal requiere SOLO 1 petición PATCH por segundo para
  actualizar TODOS sus Pokémon al mismo tiempo (1s exacto en Shundos, GL y UL).
- Cuando un Pokémon individual dentro del mensaje llega a 00 seg, su tarjeta desaparece
  instantáneamente del mensaje; cuando expira el último, se elimina el mensaje completo.
"""

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import requests

from src.config import (
    BOT_NOMBRES_POR_CANAL,
    DISCORD_BOT_TOKEN,
    DISCORD_EVENTO_CHANNEL_ID,
    DISCORD_USER_ID_MENCION,
    DISCORD_WEBHOOK_URL,
    NOTIFICADOS_FILE,
    WEBHOOKS_POR_CANAL,
)
from src.discord_embeds import (
    actualizar_embed_con_segundos_reales,
    construir_embed_pvp,
    construir_embed_shundo,
)
from src.state_manager import (
    _LOCK_ESTADO,
    cargar_json,
    guardar_json,
    sincronizar_estado_remoto_push,
)

MAX_EMBEDS_POR_MENSAJE = 6

_MEM_EMBEDS_POR_CLAVE: Dict[str, Dict[str, Any]] = {}
_ULTIMO_TICK_CANAL: Dict[str, int] = {}
_HILOS_RELOJ_INICIADOS = False
_LOCK_HILOS = threading.Lock()

# Sesiones HTTP persistentes (Keep-Alive) independientes por canal
_SESIONES_CANAL: Dict[str, requests.Session] = {
    "shundo": requests.Session(),
    "great": requests.Session(),
    "ultra": requests.Session(),
    "evento": requests.Session(),
}


def enviar_alerta_token_vencido() -> None:
    """Envía una alerta al canal principal si el JWT_TOKEN devuelve HTTP 401 (máximo 1 vez cada 6h)."""
    if not DISCORD_WEBHOOK_URL.strip():
        return
    with _LOCK_ESTADO:
        notificados = cargar_json(NOTIFICADOS_FILE)
        ahora = int(time.time())
        ultimo_aviso = int(notificados.get("_meta_alerta_401_ts", 0))
        if ahora - ultimo_aviso < 21600:
            return

    mencion = f"<@{DISCORD_USER_ID_MENCION}> " if DISCORD_USER_ID_MENCION else ""
    payload = {
        "username": "Radar Shundo Pro ⚠️",
        "content": f"⚠️ {mencion}**¡Atención!** Tu `JWT_TOKEN` de Pokémon GO Pro ha expirado (`Error HTTP 401`).",
        "embeds": [
            {
                "title": "🔑 Sesión Expirada — Actualiza tu JWT_TOKEN",
                "color": 0xEF4444,
                "description": (
                    "El servidor devolvió **HTTP 401 (Unauthorized)**.\n\n"
                    "**Cómo renovarlo en 10 segundos desde Discord:**\n"
                    "1. Abre `coordinates.pokemongopro.com` e inicia sesión.\n"
                    "2. Copia el nuevo `jwt` desde *Local Storage*.\n"
                    "3. Pega **`token eyJ...`** en tu canal **`#🎉-evento-cd`** *(el bot borrará tu mensaje por privacidad y lo activará en vivo al instante)*."
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ],
    }
    try:
        r = _SESIONES_CANAL["shundo"].post(DISCORD_WEBHOOK_URL.strip(), json=payload, timeout=10)
        if r.status_code in (200, 204):
            with _LOCK_ESTADO:
                notificados = cargar_json(NOTIFICADOS_FILE)
                notificados["_meta_alerta_401_ts"] = int(time.time())
                guardar_json(NOTIFICADOS_FILE, notificados)
    except Exception:
        pass


def construir_embed_seguro(mon: Dict[str, Any], canal_tipo: str) -> Dict[str, Any]:
    if canal_tipo == "shundo":
        return construir_embed_shundo(mon)
    if canal_tipo == "evento":
        pvp = mon.get("pvp") or {}
        if pvp.get("league") in ("great", "ultra"):
            return construir_embed_pvp(mon, str(pvp.get("league")))
        return construir_embed_shundo(mon)
    return construir_embed_pvp(mon, canal_tipo)


def construir_encabezado_lote(spawns_nuevos: List[Dict[str, Any]], total_activos: int, canal_tipo: str) -> str:
    mencion = f"<@{DISCORD_USER_ID_MENCION}> " if DISCORD_USER_ID_MENCION else ""
    primero = spawns_nuevos[0]
    nombre = primero.get("nombre_completo") or primero.get("pokemon_name")
    if canal_tipo == "shundo":
        return f"🚨 {mencion}¡Nuevo **SHUNDO 100% IV ({nombre})** detectado!"
    elif canal_tipo == "evento":
        return f"🎉 {mencion}¡Nuevo **SHINY DE EVENTO / CD ({nombre})** detectado!"
    else:
        pvp = primero.get("pvp") or {}
        rank = pvp.get("rank", "?")
        pvp_name = pvp.get("pokemon_name") or nombre
        liga_tag = "GREAT LEAGUE" if canal_tipo == "great" else "ULTRA LEAGUE"
        return f"⚔️ {mencion}¡Nuevo **SHINY {liga_tag} RANK #{rank} ({nombre} ➔ {pvp_name})** detectado!"


def limpiar_mensajes_huerfanos_canal(canal_tipo: str, mid_activo_valido: Optional[str] = None) -> None:
    """
    Usa DISCORD_BOT_TOKEN para asegurar que NINGÚN mensaje viejo o huérfano quede en el chat.
    Conserva únicamente el mid_activo_valido (si existe) y el panel de control en #🎉-evento-cd.
    """
    if not DISCORD_BOT_TOKEN.strip():
        return
    channel_id_map = {
        "shundo": "1562146985996193873",
        "great": "1562157246425858139",
        "ultra": "1562157292168810576",
        "evento": DISCORD_EVENTO_CHANNEL_ID,
    }
    cid = channel_id_map.get(canal_tipo)
    if not cid:
        return
    headers_bot = {"Authorization": f"Bot {DISCORD_BOT_TOKEN.strip()}"}
    try:
        r = requests.get(f"https://discord.com/api/v10/channels/{cid}/messages?limit=15", headers=headers_bot, timeout=6)
        if r.status_code == 200:
            msgs = r.json()
            for m in msgs:
                mid = str(m.get("id"))
                if mid_activo_valido and mid == str(mid_activo_valido):
                    continue
                if canal_tipo == "evento" and m.get("embeds") and "PANEL DE CONTROL" in str(m["embeds"][0].get("title", "")):
                    continue
                if m.get("webhook_id"):
                    requests.delete(f"https://discord.com/api/v10/channels/{cid}/messages/{mid}", headers=headers_bot, timeout=5)
    except Exception:
        pass


def _eliminar_mensaje_webhook_seguro(sesion: requests.Session, base_webhook: str, mid: str) -> bool:
    """Elimina un mensaje de webhook manejando automáticamente HTTP 429 (Rate Limit)."""
    url_del = f"{base_webhook}/messages/{mid}"
    for intento in range(3):
        try:
            r = sesion.delete(url_del, timeout=6)
            if r.status_code in (200, 204, 404):
                return True
            if r.status_code == 429:
                try:
                    espera = float(r.json().get("retry_after", 1.2))
                except Exception:
                    espera = 1.2
                time.sleep(min(espera + 0.15, 4.0))
        except Exception:
            time.sleep(0.4)
    return False


def publicar_panel_consolidado_canal(
    canal_tipo: str,
    spawns_nuevos: List[Dict[str, Any]],
    spawns_activos_totales: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Reemplaza el mensaje anterior del canal por un único mensaje consolidado con todos los
    Pokémon activos del canal (máx 6 embeds), para que 1 solo PATCH por segundo actualice TODOS a 1s.
    """
    webhook_url = WEBHOOKS_POR_CANAL.get(canal_tipo) or ""
    if not webhook_url.strip() or not spawns_nuevos:
        return None

    sesion = _SESIONES_CANAL.get(canal_tipo) or requests.Session()
    base_webhook = webhook_url.strip().split("?")[0].rstrip("/")
    url_wait = f"{base_webhook}?wait=true"

    # 1. Eliminar cualquier mensaje previo activo de este canal para que solo exista 1 mensaje vivo
    with _LOCK_ESTADO:
        notificados = cargar_json(NOTIFICADOS_FILE)
        mids_previos = set()
        for k, info in notificados.items():
            if k.startswith("_meta_") or not isinstance(info, dict):
                continue
            if info.get("canal", "shundo") == canal_tipo and not info.get("eliminado_de_discord", False):
                for m in (info.get("discord_msg_ids") or []) + [info.get("discord_msg_id")]:
                    if m:
                        mids_previos.add(str(m))

    for old_mid in mids_previos:
        _eliminar_mensaje_webhook_seguro(sesion, base_webhook, old_mid)

    # 2. Construir la lista de embeds de los spawns activos (hasta MAX_EMBEDS_POR_MENSAJE)
    seleccionados = spawns_activos_totales[:MAX_EMBEDS_POR_MENSAJE]
    embeds_lote: List[Dict[str, Any]] = []
    for mon in seleccionados:
        eid = str(mon.get("encounter_id"))
        clave = f"{canal_tipo}:{eid}"
        emb = construir_embed_seguro(mon, canal_tipo)
        _MEM_EMBEDS_POR_CLAVE[clave] = emb
        mon["embed_base"] = emb
        embeds_lote.append(emb)

    contenido = construir_encabezado_lote(spawns_nuevos, len(seleccionados), canal_tipo)
    payload = {
        "username": BOT_NOMBRES_POR_CANAL.get(canal_tipo, "Radar Pro ✨"),
        "content": contenido,
        "embeds": embeds_lote,
    }

    try:
        r = sesion.post(url_wait, json=payload, timeout=10)
        if r.status_code in (200, 204):
            msg_data = r.json()
            if msg_data and "id" in msg_data:
                nuevo_mid = str(msg_data["id"])
                print(
                    f"   ✅ [Discord-{canal_tipo.upper()}] Panel enviado ({len(seleccionados)} Pokémon activos en 1 mensaje • reloj dinámico)."
                )
                limpiar_mensajes_huerfanos_canal(canal_tipo, mid_activo_valido=nuevo_mid)
                return nuevo_mid
        else:
            print(f"   ⚠️ [Discord-{canal_tipo.upper()}] Error HTTP {r.status_code}: {r.text[:150]}")
    except Exception as e:
        print(f"   ⚠️ [Discord-{canal_tipo.upper()}] Error al enviar panel webhook: {e}")

    return None


def procesar_canal_discord(canal_tipo: str, actualizar_tiempo_real: bool = True) -> int:
    """
    Procesa un canal ('shundo', 'great', 'ultra', 'evento') cada 1 segundo:
    - Si existen mensajes antiguos rezagados, los elimina de Discord con DELETE.
    - Actualiza todos los embeds activos del mensaje del canal en UNA SOLA petición PATCH (1s exacto).
    - Si algún Pokémon dentro del mensaje ya expiró, retira su tarjeta inmediatamente con PATCH.
    - Si todos los Pokémon del mensaje expiraron, elimina el mensaje completo con DELETE.
    """
    webhook_url = WEBHOOKS_POR_CANAL.get(canal_tipo) or ""
    if not webhook_url.strip():
        return 0

    sesion = _SESIONES_CANAL.get(canal_tipo) or requests.Session()
    base_webhook = webhook_url.strip().split("?")[0].rstrip("/")

    with _LOCK_ESTADO:
        notificados = cargar_json(NOTIFICADOS_FILE)

    eliminados = 0
    claves_recien_expiradas: List[str] = []

    # Agrupar entradas activas por discord_msg_id
    entradas_por_mid: Dict[str, List[tuple]] = {}
    for clave, info in list(notificados.items()):
        if clave.startswith("_meta_") or not isinstance(info, dict):
            continue
        if info.get("canal", "shundo") != canal_tipo:
            continue
        if info.get("eliminado_de_discord", False):
            continue

        mid = info.get("discord_msg_id")
        despawn_unix = info.get("despawn_unix")
        if not mid or not despawn_unix:
            continue
        entradas_por_mid.setdefault(str(mid), []).append((clave, info, int(despawn_unix)))

    if not entradas_por_mid:
        return 0

    hubo_cambios_estado = False

    # Si hay más de 1 mensaje registrado como activo en el mismo canal, conservar SOLO el más reciente
    # y eliminar de inmediato los mensajes anteriores en Discord (sin crear mensajes nuevos en bucle).
    if len(entradas_por_mid) > 1:
        mids_ordenados = sorted(entradas_por_mid.keys(), key=lambda x: int(x) if x.isdigit() else 0)
        mid_mas_reciente = mids_ordenados[-1]
        for mid_viejo in mids_ordenados[:-1]:
            if _eliminar_mensaje_webhook_seguro(sesion, base_webhook, mid_viejo):
                for clave_v, _, _ in entradas_por_mid[mid_viejo]:
                    claves_recien_expiradas.append(clave_v)
                    _MEM_EMBEDS_POR_CLAVE.pop(clave_v, None)
                    eliminados += 1
                hubo_cambios_estado = True
            entradas_por_mid.pop(mid_viejo, None)

    # Procesar el mensaje activo del canal
    for mid, lista_entradas in list(entradas_por_mid.items()):
        ahora_loop = int(time.time())
        vivos_en_mid = []
        expirados_en_mid = []
        for clave, info, despawn_unix in lista_entradas:
            if ahora_loop >= despawn_unix:
                expirados_en_mid.append((clave, info))
            else:
                vivos_en_mid.append((clave, info, despawn_unix))

        # Caso A: Todos los Pokémon de este mensaje ya expiraron -> DELETE del mensaje completo
        if not vivos_en_mid:
            mids_a_borrar = {str(mid)}
            for _, info_e in expirados_en_mid:
                for m_extra in info_e.get("discord_msg_ids") or []:
                    if m_extra:
                        mids_a_borrar.add(str(m_extra))

            borrado_ok = False
            for m_del in mids_a_borrar:
                if _eliminar_mensaje_webhook_seguro(sesion, base_webhook, m_del):
                    borrado_ok = True

            if borrado_ok:
                for clave, info in expirados_en_mid:
                    claves_recien_expiradas.append(clave)
                    _MEM_EMBEDS_POR_CLAVE.pop(clave, None)
                    eliminados += 1
                    print(
                        f"   🗑️ [Discord-{canal_tipo.upper()}] Mensaje de {info.get('pokemon', clave)} eliminado del chat (ya hizo despawn)."
                    )
                hubo_cambios_estado = True
            continue

        # Caso B y C: Siguen quedando Pokémon vivos en el mensaje -> Actualizar con PATCH
        # (y si alguno expiró en este segundo, el PATCH quita su tarjeta del mensaje inmediatamente)
        if actualizar_tiempo_real or expirados_en_mid:
            ahora_sec = int(time.time())
            if not expirados_en_mid and (ahora_sec - _ULTIMO_TICK_CANAL.get(mid, 0) < 6):
                continue

            embeds_actualizados: List[Dict[str, Any]] = []
            embeds_remotos_cache: Optional[List[Dict[str, Any]]] = None

            for idx_e, (clave, info, despawn_unix) in enumerate(vivos_en_mid[:MAX_EMBEDS_POR_MENSAJE]):
                emb_base = _MEM_EMBEDS_POR_CLAVE.get(clave) or info.get("embed_base")
                if not emb_base:
                    if embeds_remotos_cache is None:
                        try:
                            r_get = sesion.get(f"{base_webhook}/messages/{mid}", timeout=5)
                            if r_get.status_code == 200:
                                embeds_remotos_cache = r_get.json().get("embeds") or []
                            elif r_get.status_code == 404:
                                for c_v, _, _ in vivos_en_mid:
                                    claves_recien_expiradas.append(c_v)
                                for c_e, _ in expirados_en_mid:
                                    claves_recien_expiradas.append(c_e)
                                hubo_cambios_estado = True
                                break
                            else:
                                embeds_remotos_cache = []
                        except Exception:
                            embeds_remotos_cache = []
                    if embeds_remotos_cache and idx_e < len(embeds_remotos_cache):
                        emb_base = embeds_remotos_cache[idx_e]
                        _MEM_EMBEDS_POR_CLAVE[clave] = emb_base

                if emb_base:
                    _MEM_EMBEDS_POR_CLAVE[clave] = emb_base
                    embeds_actualizados.append(
                        actualizar_embed_con_segundos_reales(emb_base, despawn_unix, canal_tipo)
                    )

            if embeds_actualizados:
                mencion = f"<@{DISCORD_USER_ID_MENCION}> " if DISCORD_USER_ID_MENCION else ""
                nombre_dest = vivos_en_mid[0][1].get("pokemon", "Pokémon")
                if canal_tipo == "shundo":
                    contenido_patch = f"🚨 {mencion}¡Nuevo **SHUNDO 100% IV ({nombre_dest})** detectado!"
                    footer_limpio = "Radar Shundo Pro (☁️ Nube 24/7) • Se eliminará automáticamente al desaparecer"
                elif canal_tipo == "great":
                    contenido_patch = f"⚔️ {mencion}¡Nuevo **SHINY GREAT LEAGUE ({nombre_dest})** detectado!"
                    footer_limpio = "Radar PvP Shiny Pro (☁️ Nube 24/7) • Se eliminará automáticamente al desaparecer"
                elif canal_tipo == "evento":
                    contenido_patch = f"🎉 {mencion}¡Nuevo **SHINY DE EVENTO / CD ({nombre_dest})** detectado!"
                    footer_limpio = "Radar Eventos & CD Pro (☁️ Nube 24/7) • Se eliminará automáticamente al desaparecer"
                else:
                    contenido_patch = f"⚔️ {mencion}¡Nuevo **SHINY ULTRA LEAGUE ({nombre_dest})** detectado!"
                    footer_limpio = "Radar PvP Shiny Pro (☁️ Nube 24/7) • Se eliminará automáticamente al desaparecer"

                for emb_item in embeds_actualizados:
                    emb_item["footer"] = {"text": footer_limpio}

                try:
                    r_patch = sesion.patch(
                        f"{base_webhook}/messages/{mid}",
                        json={"content": contenido_patch, "embeds": embeds_actualizados},
                        timeout=5,
                    )
                    if r_patch.status_code == 200:
                        _ULTIMO_TICK_CANAL[mid] = int(time.time())
                        if expirados_en_mid:
                            for clave_e, info_e in expirados_en_mid:
                                claves_recien_expiradas.append(clave_e)
                                _MEM_EMBEDS_POR_CLAVE.pop(clave_e, None)
                                eliminados += 1
                                print(
                                    f"   🗑️ [Discord-{canal_tipo.upper()}] Tarjeta de {info_e.get('pokemon', clave_e)} retirada del panel (ya hizo despawn)."
                                )
                            hubo_cambios_estado = True
                        rem = r_patch.headers.get("X-RateLimit-Remaining")
                        reset_after = r_patch.headers.get("X-RateLimit-Reset-After")
                        if rem == "0" and reset_after:
                            try:
                                time.sleep(min(float(reset_after), 1.5))
                            except Exception:
                                pass
                    elif r_patch.status_code == 404:
                        for c_v, _, _ in vivos_en_mid:
                            claves_recien_expiradas.append(c_v)
                        for c_e, _ in expirados_en_mid:
                            claves_recien_expiradas.append(c_e)
                        hubo_cambios_estado = True
                    elif r_patch.status_code == 429:
                        try:
                            retry_after = float(r_patch.json().get("retry_after", 1.0))
                        except Exception:
                            retry_after = 1.0
                        time.sleep(min(retry_after, 2.0))
                        r_retry = sesion.patch(
                            f"{base_webhook}/messages/{mid}",
                            json={"content": contenido_patch, "embeds": embeds_actualizados},
                            timeout=5,
                        )
                        if r_retry.status_code in (200, 204):
                            _ULTIMO_TICK_CANAL[mid] = int(time.time())
                            if expirados_en_mid:
                                for clave_e, info_e in expirados_en_mid:
                                    claves_recien_expiradas.append(clave_e)
                                    _MEM_EMBEDS_POR_CLAVE.pop(clave_e, None)
                                    eliminados += 1
                                    print(
                                        f"   🗑️ [Discord-{canal_tipo.upper()}] Tarjeta de {info_e.get('pokemon', clave_e)} retirada del panel (tras reintento)."
                                    )
                                hubo_cambios_estado = True
                except Exception:
                    pass

    if hubo_cambios_estado and claves_recien_expiradas:
        with _LOCK_ESTADO:
            notif_actual = cargar_json(NOTIFICADOS_FILE)
            for k in claves_recien_expiradas:
                if k in notif_actual and isinstance(notif_actual[k], dict):
                    notif_actual[k]["eliminado_de_discord"] = True
            guardar_json(NOTIFICADOS_FILE, notif_actual)
        sincronizar_estado_remoto_push(asincrono=True)

    return eliminados


def _worker_reloj_canal(canal_tipo: str) -> None:
    """Bucle dedicado que corre en su propio hilo para vigilar despawns y actualizar el reloj."""
    while True:
        inicio_tick = time.time()
        try:
            procesar_canal_discord(canal_tipo, actualizar_tiempo_real=True)
        except Exception:
            pass
        transcurrido = time.time() - inicio_tick
        pausa = max(0.5, 2.0 - transcurrido)
        time.sleep(pausa)


def iniciar_hilos_reloj_tiempo_real() -> None:
    """Inicia los 4 hilos daemon independientes (Shundo, GL, UL, Evento) para actualizar los relojes cada 1 segundo."""
    global _HILOS_RELOJ_INICIADOS
    with _LOCK_HILOS:
        if _HILOS_RELOJ_INICIADOS:
            return
        for canal in ("shundo", "great", "ultra", "evento"):
            t = threading.Thread(
                target=_worker_reloj_canal,
                args=(canal,),
                name=f"RelojDiscord-{canal.upper()}",
                daemon=True,
            )
            t.start()
        _HILOS_RELOJ_INICIADOS = True


def eliminar_mensajes_expirados_discord(actualizar_tiempo_real: bool = True) -> int:
    """Procesa de inmediato los 4 canales (Shundos, GL, UL, Evento)."""
    total = 0
    for canal in ("shundo", "great", "ultra", "evento"):
        total += procesar_canal_discord(canal, actualizar_tiempo_real=actualizar_tiempo_real)
    return total
