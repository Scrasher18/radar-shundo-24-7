"""
Módulo del Panel Maestro de Control centralizado para todos los canales del Radar:
- Panel único e interactivo en el canal #🎛️-panel-control.
- Modificación en caliente del tiempo de búsqueda (5m, 7m, 10m, 15m).
- Interruptores independientes ON/OFF por canal (Shundo, Great League, Ultra League, Evento).
- Pausa global del radar (pausar / reanudar).
- Selector dinámico de rango PvP (Rank #1-3 / Rank #1-5).
- Disparo de escaneo inmediato forzado (scan / buscar).
- Monitor de cuota y salud del pool de 3 cuentas en vivo.
- Eliminación automática de comandos del usuario para mantener el canal 100% limpio.
"""

from datetime import datetime, timezone
import json
import os
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import requests

from src.api_client import (
    actualizar_jwt_token_en_vivo,
    obtener_jwt_actual,
    obtener_resumen_cuentas_pool,
)
from src.config import (
    CONTROL_CONFIG_FILE,
    DISCORD_BOT_TOKEN,
    DISCORD_CONTROL_CHANNEL_ID,
    DISCORD_USER_ID_MENCION,
    DISCORD_WEBHOOK_CONTROL,
    EVENTO_CONFIG_FILE,
    INTERVALO_SEGUNDOS,
)
from src.state_manager import sincronizar_estado_remoto_push

_LOCK_CONTROL = threading.RLock()
_SESION_BOT = requests.Session()
_SESION_WH = requests.Session()
_HILO_CONTROL_INICIADO = False
_CALLBACK_ESCANEO_INMEDIATO: Optional[Callable[[], None]] = None


def cargar_config_control() -> Dict[str, Any]:
    """Carga la configuración maestra desde control_config.json."""
    with _LOCK_CONTROL:
        if os.path.exists(CONTROL_CONFIG_FILE):
            try:
                with open(CONTROL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {
            "pausa_global": False,
            "intervalo_minutos": 7,
            "canales": {
                "shundo": True,
                "great": True,
                "ultra": True,
                "evento": True,
            },
            "pvp_top_rank": 5,
            "pvp_reveal_rank": 2,
            "panel_msg_id": None,
        }


def guardar_config_control(cfg: Dict[str, Any]) -> None:
    """Guarda la configuración maestra en control_config.json."""
    with _LOCK_CONTROL:
        try:
            with open(CONTROL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _enviar_aviso_temporal(texto: str, segundos_visible: float = 6.0) -> None:
    """Envía una confirmación rápida en #🎛️-panel-control y la auto-elimina para mantener el chat limpio."""
    if not DISCORD_WEBHOOK_CONTROL.strip():
        return
    base_wh = DISCORD_WEBHOOK_CONTROL.strip().split("?")[0].rstrip("/")

    def _tarea() -> None:
        try:
            r = _SESION_WH.post(
                f"{base_wh}?wait=true",
                json={"username": "ScrasherBOT 🎛️", "content": texto},
                timeout=6,
            )
            if r.status_code in (200, 204):
                mid = r.json().get("id")
                if mid:
                    time.sleep(segundos_visible)
                    _SESION_WH.delete(f"{base_wh}/messages/{mid}", timeout=5)
        except Exception:
            pass

    threading.Thread(target=_tarea, daemon=True).start()


def construir_embed_panel_maestro(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Genera el Embed rico e interactivo del Panel Maestro de Control."""
    pausado = bool(cfg.get("pausa_global", False))
    intervalo_min = int(cfg.get("intervalo_minutos", 7))
    canales = cfg.get("canales", {})
    shundo_on = bool(canales.get("shundo", True))
    gl_on = bool(canales.get("great", True))
    ul_on = bool(canales.get("ultra", True))
    evento_on = bool(canales.get("evento", True))
    pvp_top_rank = int(cfg.get("pvp_top_rank", 5))
    pvp_rev_rank = int(cfg.get("pvp_reveal_rank", 2))

    color_embed = 0xEF4444 if pausado else 0x2563EB

    estado_radar = "🔴 **PAUSADO GLOBALMENTE**" if pausado else "🟢 **ACTIVO Y ESCANEANDO EN LA NUBE 24/7**"
    tag_shundo = "🟢 ACTIVO" if shundo_on else "🔴 PAUSADO"
    tag_gl = "🟢 ACTIVO" if gl_on else "🔴 PAUSADO"
    tag_ul = "🟢 ACTIVO" if ul_on else "🔴 PAUSADO"
    tag_evento = "🟢 ACTIVO" if evento_on else "🔴 PAUSADO"

    resumen_pool = obtener_resumen_cuentas_pool()

    return {
        "title": "🎛️ PANEL MAESTRO DE CONTROL — RADAR POKÉMON GO PRO",
        "description": (
            f"**Estado del Radar:** {estado_radar}\n\n"
            "Controla todos los canales, frecuencias y ligas directamente desde este chat.\n"
            "Escribe un comando abajo y ScrasherBOT lo ejecutará al instante borrando tu mensaje."
        ),
        "color": color_embed,
        "fields": [
            {
                "name": "📡 Estado de los Canales",
                "value": (
                    f"• 🌟 **Shundos 100% IV:** `{tag_shundo}`\n"
                    f"• 🔵 **Great League (1500 CP):** `{tag_gl}`\n"
                    f"• 🟣 **Ultra League (2500 CP):** `{tag_ul}`\n"
                    f"• 🎉 **Eventos / CD:** `{tag_evento}`"
                ),
                "inline": True,
            },
            {
                "name": "⚙️ Parámetros de Búsqueda",
                "value": (
                    f"• ⏱️ **Intervalo:** `{intervalo_min} minutos`\n"
                    f"• 🏆 **Filtro PvP:** `Rank #1 al #{pvp_top_rank}`\n"
                    f"• 🎯 **Coords Exactas:** `Shundos + Top #{pvp_rev_rank} PvP`\n"
                    f"• 📍 **Origen:** `Global (5 Continentes)`"
                ),
                "inline": True,
            },
            {
                "name": "🔑 Pool Multi-Cuenta (3 Cuentas)",
                "value": f"```\n{resumen_pool}\n```",
                "inline": False,
            },
            {
                "name": "🎮 Comandos Rápidos Disponibles (Escríbelos aquí)",
                "value": (
                    "• ⏱️ **Cambiar Intervalo:** `3m` • `5m` • `7m` • `10m` • `15m` *(o `tiempo 5`)*\n"
                    "• 🔴/🟢 **Activar/Pausar Canales:** `shundo on/off` • `gl on/off` • `ul on/off` • `evento on/off`\n"
                    "• ⏸️ **Pausa Global:** `pausar` • `reanudar`\n"
                    "• 🏆 **Filtro PvP:** `rank 1-3` • `rank 1-5`\n"
                    "• ⚡ **Escaneo Forzado:** `scan` o `buscar` *(busca en este segundo)*\n"
                    "• 🧹 **Limpieza:** `limpiar`\n"
                    "• 🔑 **Renovar Token:** Pega `token eyJ...`"
                ),
                "inline": False,
            },
        ],
        "footer": {
            "text": "ScrasherBOT • Panel de Control 24/7 • Escribe tu comando y el bot limpiará tu texto"
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publicar_o_actualizar_panel_maestro() -> Optional[str]:
    """Actualiza el mensaje existente del Panel Maestro mediante PATCH o lo crea si no existe."""
    if not DISCORD_WEBHOOK_CONTROL.strip():
        return None

    with _LOCK_CONTROL:
        cfg = cargar_config_control()
        base_wh = DISCORD_WEBHOOK_CONTROL.strip().split("?")[0].rstrip("/")
        embed_panel = construir_embed_panel_maestro(cfg)
        panel_mid = cfg.get("panel_msg_id")

        if panel_mid:
            try:
                r_patch = _SESION_WH.patch(
                    f"{base_wh}/messages/{panel_mid}",
                    json={"content": "", "embeds": [embed_panel]},
                    timeout=8,
                )
                if r_patch.status_code == 200:
                    return str(panel_mid)
            except Exception:
                pass

        try:
            r_post = _SESION_WH.post(
                f"{base_wh}?wait=true",
                json={
                    "username": "Radar Pro 🎛️",
                    "content": "",
                    "embeds": [embed_panel],
                },
                timeout=10,
            )
            if r_post.status_code in (200, 204):
                nuevo_id = str(r_post.json().get("id"))
                cfg["panel_msg_id"] = nuevo_id
                guardar_config_control(cfg)
                return nuevo_id
        except Exception:
            pass
        return None


def procesar_comando_control(contenido: str) -> bool:
    """Interpreta el comando enviado por el usuario, actualiza la configuración y el panel."""
    low = contenido.strip().lower()
    cfg = cargar_config_control()
    cambio = False
    aviso = ""

    # 1. Comandos de Renovación de JWT_TOKEN
    cand_jwt = None
    if low.startswith("token eyj"):
        cand_jwt = contenido.strip()[5:].strip()
    elif contenido.strip().startswith("eyJ") and len(contenido.strip()) > 80:
        cand_jwt = contenido.strip()

    if cand_jwt:
        valido, info, code = actualizar_jwt_token_en_vivo(cand_jwt)
        if valido:
            _enviar_aviso_temporal(f"✅ **JWT_TOKEN renovado con éxito** para `{info.get('display_name')}`.")
            publicar_o_actualizar_panel_maestro()
            sincronizar_estado_remoto_push(asincrono=True)
            return True
        else:
            _enviar_aviso_temporal(f"❌ Error al validar token (HTTP {code}).")
            return False

    # 2. Comandos de tiempo (3m, 5m, 7m, 10m, 15m, tiempo 5, etc.)
    m_tiempo = re.match(r"^(?:tiempo\s+)?(\d+)(?:m|min|minutos)?$", low)
    if m_tiempo:
        num = int(m_tiempo.group(1))
        if 1 <= num <= 60:
            cfg["intervalo_minutos"] = num
            guardar_config_control(cfg)
            _enviar_aviso_temporal(f"⏱️ **Intervalo de escaneo actualizado a:** `{num} minutos`.")
            publicar_o_actualizar_panel_maestro()
            sincronizar_estado_remoto_push(asincrono=True)
            return True

    # 3. Comandos de Pausa Global (pausar / reanudar)
    if low in ("pausar", "pause", "parar", "stop", "detener"):
        cfg["pausa_global"] = True
        guardar_config_control(cfg)
        _enviar_aviso_temporal("⏸️ **Radar pausado globalmente.** No se enviarán nuevas alertas hasta reanudar.")
        publicar_o_actualizar_panel_maestro()
        sincronizar_estado_remoto_push(asincrono=True)
        return True

    if low in ("reanudar", "resume", "iniciar", "start", "play", "activar"):
        cfg["pausa_global"] = False
        guardar_config_control(cfg)
        _enviar_aviso_temporal("▶️ **Radar reanudado.** El escaneo 24/7 vuelve a estar en marcha.")
        publicar_o_actualizar_panel_maestro()
        sincronizar_estado_remoto_push(asincrono=True)
        return True

    # 4. Comandos de activación / desactivación por canal
    canales = cfg.setdefault("canales", {"shundo": True, "great": True, "ultra": True, "evento": True})

    if low in ("shundo off", "shundo apagar", "shundo pausar", "shundos off"):
        canales["shundo"] = False
        aviso = "🔴 Canal **Shundos 100% IV** pausado."
        cambio = True
    elif low in ("shundo on", "shundo activar", "shundos on"):
        canales["shundo"] = True
        aviso = "🟢 Canal **Shundos 100% IV** activado."
        cambio = True

    elif low in ("gl off", "great off", "great league off"):
        canales["great"] = False
        aviso = "🔴 Canal **Great League** pausado."
        cambio = True
    elif low in ("gl on", "great on", "great league on"):
        canales["great"] = True
        aviso = "🟢 Canal **Great League** activado."
        cambio = True

    elif low in ("ul off", "ultra off", "ultra league off"):
        canales["ultra"] = False
        aviso = "🔴 Canal **Ultra League** pausado."
        cambio = True
    elif low in ("ul on", "ultra on", "ultra league on"):
        canales["ultra"] = True
        aviso = "🟢 Canal **Ultra League** activado."
        cambio = True

    elif low in ("evento off", "cd off"):
        canales["evento"] = False
        aviso = "🔴 Canal **Eventos & CD** pausado."
        cambio = True
    elif low in ("evento on", "cd on"):
        canales["evento"] = True
        aviso = "🟢 Canal **Eventos & CD** activado."
        cambio = True

    # 5. Filtro PvP Top Rank (rank 1-3, rank 1-5, pvp 3, top 3, etc.)
    m_rank = re.match(r"^(?:rank|pvp|top)\s*(?:1-)?(\d+)$", low)
    if m_rank:
        rk = int(m_rank.group(1))
        if 1 <= rk <= 10:
            cfg["pvp_top_rank"] = rk
            aviso = f"🏆 **Filtro PvP actualizado a:** `Rank #1 al #{rk}`."
            cambio = True

    # 6. Disparo de escaneo inmediato (scan / buscar)
    if low in ("scan", "buscar", "buscar ya", "escanear", "forzar"):
        _enviar_aviso_temporal("⚡ **Disparando escaneo global inmediato en todos los canales activos...**")
        if _CALLBACK_ESCANEO_INMEDIATO:
            threading.Thread(target=_CALLBACK_ESCANEO_INMEDIATO, daemon=True).start()
        return True

    # 7. Limpiar chat
    if low in ("limpiar", "clean", "cls"):
        _enviar_aviso_temporal("🧹 **Limpiando mensajes huérfanos del canal...**")
        limpiar_mensajes_canal_control(cfg.get("panel_msg_id"))
        publicar_o_actualizar_panel_maestro()
        return True

    # 8. Estado de cuentas
    if low in ("pool", "cuota", "cuotas", "tokens"):
        _enviar_aviso_temporal(f"📊 **Estado del Pool:**\n```{obtener_resumen_cuentas_pool()}```", segundos_visible=10.0)
        publicar_o_actualizar_panel_maestro()
        return True

    if cambio:
        guardar_config_control(cfg)
        if aviso:
            _enviar_aviso_temporal(aviso)
        publicar_o_actualizar_panel_maestro()
        sincronizar_estado_remoto_push(asincrono=True)
        return True

    return False


def limpiar_mensajes_canal_control(panel_mid: Optional[str]) -> None:
    """Elimina los mensajes que no sean el panel principal del canal de control."""
    if not DISCORD_BOT_TOKEN.strip() or not DISCORD_CONTROL_CHANNEL_ID.strip():
        return
    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN.strip()}"}
    try:
        r = _SESION_BOT.get(
            f"https://discord.com/api/v10/channels/{DISCORD_CONTROL_CHANNEL_ID}/messages?limit=20",
            headers=headers,
            timeout=6,
        )
        if r.status_code == 200:
            for m in r.json():
                mid = str(m.get("id"))
                if panel_mid and mid == str(panel_mid):
                    continue
                _SESION_BOT.delete(
                    f"https://discord.com/api/v10/channels/{DISCORD_CONTROL_CHANNEL_ID}/messages/{mid}",
                    headers=headers,
                    timeout=5,
                )
    except Exception:
        pass


def _worker_escucha_control() -> None:
    """Hilo demonio que lee los mensajes escritos en #🎛️-panel-control y elimina los comandos tras ejecutarlos."""
    if not DISCORD_BOT_TOKEN.strip() or not DISCORD_CONTROL_CHANNEL_ID.strip():
        return

    headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN.strip()}"}
    ultimos_vistos: Optional[int] = None

    # Publicar el panel de inmediato al iniciar
    publicar_o_actualizar_panel_maestro()

    # Inicializar último visto
    try:
        r_init = _SESION_BOT.get(
            f"https://discord.com/api/v10/channels/{DISCORD_CONTROL_CHANNEL_ID}/messages?limit=5",
            headers=headers,
            timeout=6,
        )
        if r_init.status_code == 200:
            ms = r_init.json()
            if ms:
                ultimos_vistos = int(ms[0]["id"])
    except Exception:
        pass

    while True:
        try:
            r = _SESION_BOT.get(
                f"https://discord.com/api/v10/channels/{DISCORD_CONTROL_CHANNEL_ID}/messages?limit=5",
                headers=headers,
                timeout=6,
            )
            if r.status_code == 200:
                mensajes = r.json()
                if isinstance(mensajes, list) and mensajes:
                    if ultimos_vistos is None:
                        ultimos_vistos = int(mensajes[0]["id"])
                    else:
                        nuevos = [
                            m for m in reversed(mensajes)
                            if int(m["id"]) > ultimos_vistos and not m.get("author", {}).get("bot", False)
                        ]
                        ultimos_vistos = int(mensajes[0]["id"])

                        for m in nuevos:
                            mid = m.get("id")
                            contenido = str(m.get("content") or "").strip()

                            # Borrar de inmediato el mensaje del usuario para no ensuciar el canal
                            try:
                                _SESION_BOT.delete(
                                    f"https://discord.com/api/v10/channels/{DISCORD_CONTROL_CHANNEL_ID}/messages/{mid}",
                                    headers=headers,
                                    timeout=5,
                                )
                            except Exception:
                                pass

                            if contenido:
                                ejecutado = procesar_comando_control(contenido)
                                if not ejecutado:
                                    try:
                                        from src.event_manager import procesar_comando_texto_evento
                                        disparar_scan = procesar_comando_texto_evento(contenido)
                                        if disparar_scan and _CALLBACK_ESCANEO_INMEDIATO:
                                            threading.Thread(target=_CALLBACK_ESCANEO_INMEDIATO, daemon=True).start()
                                    except Exception:
                                        pass

        except Exception:
            pass

        time.sleep(2.0)


def iniciar_hilo_panel_control(callback_escaneo_inmediato: Optional[Callable[[], None]] = None) -> None:
    """Inicia el hilo permanente de escucha para el Panel Maestro de Control."""
    global _HILO_CONTROL_INICIADO, _CALLBACK_ESCANEO_INMEDIATO
    with _LOCK_CONTROL:
        if callback_escaneo_inmediato:
            _CALLBACK_ESCANEO_INMEDIATO = callback_escaneo_inmediato
        if _HILO_CONTROL_INICIADO:
            return
        t = threading.Thread(target=_worker_escucha_control, name="EscuchaControlRadar", daemon=True)
        t.start()
        _HILO_CONTROL_INICIADO = True
