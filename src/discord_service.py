"""
Servicio multihilo de Discord:
- Envío de alertas por canal (Shundos 100%, Great League, Ultra League)
- 3 Hilos dedicados (uno por canal) con Connection Pooling (requests.Session)
  que actualizan el reloj segundo a segundo en tiempo real (PATCH) sin bloquearse
- Eliminación instantánea (DELETE) en cuanto el contador llega a 00 seg
"""

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
import requests

from src.config import (
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

_MEM_EMBEDS: Dict[str, Dict[str, Any]] = {}
_ULTIMO_SEGUNDO_RENDERIZADO: Dict[str, int] = {}
_HILOS_RELOJ_INICIADOS = False
_LOCK_HILOS = threading.Lock()

# Sesiones HTTP persistentes (Keep-Alive) independientes por canal para latencia mínima (~70ms por PATCH)
_SESIONES_CANAL: Dict[str, requests.Session] = {
    "shundo": requests.Session(),
    "great": requests.Session(),
    "ultra": requests.Session(),
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
                    "**Cómo renovarlo:**\n"
                    "1. Abre `coordinates.pokemongopro.com` en tu navegador.\n"
                    "2. Copia el nuevo `jwt` desde *Local Storage*.\n"
                    "3. Actualízalo en `config_local.json` / Secret `JWT_TOKEN` en GitHub."
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


def enviar_lote_webhook(
    webhook_url: str,
    spawns_nuevos: List[Dict[str, Any]],
    canal_tipo: str,
    bot_username: str,
) -> Dict[str, str]:
    """Envía nuevos spawns al webhook del canal indicado y registra su embed en memoria para el reloj de 1s."""
    if not webhook_url or not webhook_url.strip() or not spawns_nuevos:
        return {}

    sesion = _SESIONES_CANAL.get(canal_tipo) or requests.Session()
    base_webhook = webhook_url.strip().split("?")[0].rstrip("/")
    url_wait = f"{base_webhook}?wait=true"
    mencion = f"<@{DISCORD_USER_ID_MENCION}> " if DISCORD_USER_ID_MENCION else ""
    ids_mensajes: Dict[str, str] = {}

    for idx, mon in enumerate(spawns_nuevos[:10]):
        eid = str(mon.get("encounter_id"))
        nombre = mon.get("nombre_completo") or mon.get("pokemon_name")
        if canal_tipo == "shundo":
            embed = construir_embed_shundo(mon)
            contenido = (
                f"🚨 {mencion}¡Nuevo **SHUNDO 100% IV ({nombre})** detectado!"
                if idx == 0
                else f"🌟 ¡Nuevo **SHUNDO 100% IV ({nombre})**!"
            )
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
            "embeds": [embed],
        }
        try:
            r = sesion.post(url_wait, json=payload, timeout=10)
            if r.status_code in (200, 204):
                try:
                    msg_data = r.json()
                    if msg_data and "id" in msg_data:
                        mid = str(msg_data["id"])
                        ids_mensajes[eid] = mid
                        _MEM_EMBEDS[mid] = embed
                        _ULTIMO_SEGUNDO_RENDERIZADO[mid] = int(mon.get("ttl_segundos") or 0)
                except Exception:
                    pass
                print(f"   ✅ [Discord-{canal_tipo.upper()}] Alerta enviada para {nombre} (reloj 1s en vivo activo).")
            else:
                print(f"   ⚠️ [Discord-{canal_tipo.upper()}] Error HTTP {r.status_code}: {r.text[:150]}")
        except Exception as e:
            print(f"   ⚠️ [Discord-{canal_tipo.upper()}] Error al enviar webhook: {e}")

    return ids_mensajes


def procesar_canal_discord(canal_tipo: str, actualizar_tiempo_real: bool = True) -> int:
    """
    Procesa un canal específico ('shundo', 'great', 'ultra'):
    1. Elimina al instante cualquier mensaje cuyo despawn_unix ya se cumplió.
    2. Actualiza en tiempo real los segundos restantes (PATCH) de los mensajes activos.
    """
    webhook_url = WEBHOOKS_POR_CANAL.get(canal_tipo) or ""
    if not webhook_url.strip():
        return 0

    sesion = _SESIONES_CANAL.get(canal_tipo) or requests.Session()
    base_webhook = webhook_url.strip().split("?")[0].rstrip("/")

    with _LOCK_ESTADO:
        notificados = cargar_json(NOTIFICADOS_FILE)

    ahora = int(time.time())
    eliminados = 0
    claves_eliminadas: List[str] = []
    activos_canal: List[tuple] = []

    for clave, info in list(notificados.items()):
        if clave.startswith("_meta_") or not isinstance(info, dict):
            continue
        if info.get("canal", "shundo") != canal_tipo:
            continue
        if info.get("eliminado_de_discord", False):
            continue

        mids = list(info.get("discord_msg_ids") or [])
        if info.get("discord_msg_id") and info.get("discord_msg_id") not in mids:
            mids.append(info.get("discord_msg_id"))
        despawn_unix = info.get("despawn_unix")
        if not mids or not despawn_unix:
            continue

        if ahora >= int(despawn_unix):
            borrado_alguno = False
            for mid in mids:
                try:
                    r = sesion.delete(f"{base_webhook}/messages/{mid}", timeout=6)
                    if r.status_code in (200, 204, 404):
                        borrado_alguno = True
                    _MEM_EMBEDS.pop(mid, None)
                    _ULTIMO_SEGUNDO_RENDERIZADO.pop(mid, None)
                except Exception:
                    pass
            if borrado_alguno:
                claves_eliminadas.append(clave)
                eliminados += 1
                print(
                    f"   🗑️ [Discord-{canal_tipo.upper()}] Mensaje de {info.get('pokemon', clave)} eliminado del chat (ya hizo despawn)."
                )
        elif actualizar_tiempo_real:
            activos_canal.append((clave, info, str(mids[-1]), int(despawn_unix)))

    if claves_eliminadas:
        with _LOCK_ESTADO:
            notif_actual = cargar_json(NOTIFICADOS_FILE)
            for k in claves_eliminadas:
                if k in notif_actual and isinstance(notif_actual[k], dict):
                    notif_actual[k]["eliminado_de_discord"] = True
            guardar_json(NOTIFICADOS_FILE, notif_actual)
        sincronizar_estado_remoto_push(asincrono=True)

    if not actualizar_tiempo_real or not activos_canal:
        return eliminados

    # Ordenar por menor tiempo restante para priorizar los que están más próximos a desaparecer
    activos_canal.sort(key=lambda x: x[3])

    for clave, info, mid, despawn_unix in activos_canal:
        ahora_sec = int(time.time())
        if ahora_sec >= despawn_unix:
            continue

        seg_rest = despawn_unix - ahora_sec
        if _ULTIMO_SEGUNDO_RENDERIZADO.get(mid) == seg_rest:
            continue

        embed_base = _MEM_EMBEDS.get(mid)
        if not embed_base:
            try:
                r_get = sesion.get(f"{base_webhook}/messages/{mid}", timeout=5)
                if r_get.status_code == 200:
                    embeds_remotos = r_get.json().get("embeds") or []
                    if embeds_remotos:
                        embed_base = embeds_remotos[0]
                        _MEM_EMBEDS[mid] = embed_base
                elif r_get.status_code == 404:
                    with _LOCK_ESTADO:
                        notif_actual = cargar_json(NOTIFICADOS_FILE)
                        if clave in notif_actual and isinstance(notif_actual[clave], dict):
                            notif_actual[clave]["eliminado_de_discord"] = True
                            guardar_json(NOTIFICADOS_FILE, notif_actual)
                    continue
            except Exception:
                continue

        if not embed_base:
            continue

        # Recalcular justo antes de enviar el PATCH para que el segundo mostrado sea exacto
        seg_rest_exacto = max(0, despawn_unix - int(time.time()))
        nuevo_embed = actualizar_embed_con_segundos_reales(embed_base, despawn_unix, canal_tipo)
        try:
            r_patch = sesion.patch(
                f"{base_webhook}/messages/{mid}",
                json={"embeds": [nuevo_embed]},
                timeout=5,
            )
            if r_patch.status_code == 200:
                _ULTIMO_SEGUNDO_RENDERIZADO[mid] = seg_rest_exacto
                rem = r_patch.headers.get("X-RateLimit-Remaining")
                reset_after = r_patch.headers.get("X-RateLimit-Reset-After")
                if rem == "0" and reset_after:
                    try:
                        time.sleep(min(float(reset_after), 2.0))
                    except Exception:
                        pass
            elif r_patch.status_code == 404:
                with _LOCK_ESTADO:
                    notif_actual = cargar_json(NOTIFICADOS_FILE)
                    if clave in notif_actual and isinstance(notif_actual[clave], dict):
                        notif_actual[clave]["eliminado_de_discord"] = True
                        guardar_json(NOTIFICADOS_FILE, notif_actual)
            elif r_patch.status_code == 429:
                try:
                    retry_after = float(r_patch.json().get("retry_after", 1.0))
                except Exception:
                    retry_after = 1.0
                time.sleep(min(retry_after, 2.5))
                break
        except Exception:
            pass

    return eliminados


def _worker_reloj_canal(canal_tipo: str) -> None:
    """Bucle dedicado que corre cada 1.0 segundo en su propio hilo para un canal de Discord."""
    while True:
        inicio_tick = time.time()
        try:
            procesar_canal_discord(canal_tipo, actualizar_tiempo_real=True)
        except Exception:
            pass
        transcurrido = time.time() - inicio_tick
        pausa = max(0.15, 1.0 - transcurrido)
        time.sleep(pausa)


def iniciar_hilos_reloj_tiempo_real() -> None:
    """Inicia los 3 hilos daemon independientes (Shundo, GL, UL) para actualizar los relojes cada segundo."""
    global _HILOS_RELOJ_INICIADOS
    with _LOCK_HILOS:
        if _HILOS_RELOJ_INICIADOS:
            return
        for canal in ("shundo", "great", "ultra"):
            t = threading.Thread(
                target=_worker_reloj_canal,
                args=(canal,),
                name=f"RelojDiscord-{canal.upper()}",
                daemon=True,
            )
            t.start()
        _HILOS_RELOJ_INICIADOS = True


def eliminar_mensajes_expirados_discord(actualizar_tiempo_real: bool = True) -> int:
    """Función compatible que procesa los 3 canales de inmediato."""
    total = 0
    for canal in ("shundo", "great", "ultra"):
        total += procesar_canal_discord(canal, actualizar_tiempo_real=actualizar_tiempo_real)
    return total
