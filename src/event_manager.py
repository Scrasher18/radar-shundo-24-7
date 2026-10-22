"""
Módulo escalable para Eventos Especiales y Community Days (CD):
- Panel de Control interactivo único en el canal #🎉-evento-cd
- Lector en tiempo real de comandos escritos en Discord mediante ScrasherBOT
- Soporte de Presets de 1 palabra (preset master, preset mega, preset meta, preset iniciales)
- Renovación segura en caliente del JWT_TOKEN directamente desde Discord (token eyJ...)
"""

from datetime import datetime, timezone
import json
import os
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import requests

from src.api_client import actualizar_jwt_token_en_vivo, obtener_jwt_actual
from src.config import (
    CONFIG_LOCAL_FILE,
    DISCORD_BOT_TOKEN,
    DISCORD_EVENTO_CHANNEL_ID,
    DISCORD_WEBHOOK_EVENTO,
    EVENTO_CONFIG_FILE,
    NOTIFICADOS_FILE,
    cifrar_jwt_con_secreto,
    extraer_exp_jwt,
)
from src.presets_catalog import (
    FAMILIAS_POKEDEX,
    PRESETS_EVENTO,
    obtener_preset,
    resolver_nombres_e_ids,
)
from src.state_manager import (
    _LOCK_ESTADO,
    cargar_json,
    guardar_json,
    sincronizar_estado_remoto_push,
)

_LOCK_EVENTO = threading.RLock()
_SESION_BOT = requests.Session()
_SESION_WEBHOOK_EV = requests.Session()
_HILO_BOT_INICIADO = False
_CALLBACK_ESCANEO_INMEDIATO: Optional[Callable[[], None]] = None


def cargar_config_evento() -> Dict[str, Any]:
    """Carga la configuración actual del Evento / Community Day."""
    with _LOCK_EVENTO:
        if os.path.exists(EVENTO_CONFIG_FILE):
            try:
                with open(EVENTO_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {
            "activo": False,
            "nombre_evento": "Community Day / Evento Especial",
            "pokemon_ids": [],
            "pokemon_nombres": [],
            "incluir_shundos_100": True,
            "incluir_pvp_gl": True,
            "incluir_pvp_ul": True,
            "pvp_top_rank": 5,
            "panel_msg_id": None,
            "ultimo_cmd_msg_id": None,
        }


def guardar_config_evento(cfg: Dict[str, Any]) -> None:
    """Guarda los cambios de configuración del Evento / Community Day."""
    with _LOCK_EVENTO:
        try:
            with open(EVENTO_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def _enviar_aviso_temporal_evento(texto: str, segundos_visible: float = 8.0) -> None:
    """Envía una confirmación breve en #🎉-evento-cd y la auto-elimina para no ensuciar el canal."""
    if not DISCORD_WEBHOOK_EVENTO.strip():
        return
    base_wh = DISCORD_WEBHOOK_EVENTO.strip().split("?")[0].rstrip("/")

    def _tarea() -> None:
        try:
            r = _SESION_WEBHOOK_EV.post(
                f"{base_wh}?wait=true",
                json={"username": "ScrasherBOT 🎛️", "content": texto},
                timeout=6,
            )
            if r.status_code in (200, 204):
                mid_temp = r.json().get("id")
                if mid_temp:
                    time.sleep(segundos_visible)
                    _SESION_WEBHOOK_EV.delete(f"{base_wh}/messages/{mid_temp}", timeout=6)
        except Exception:
            pass

    threading.Thread(target=_tarea, daemon=True).start()


def construir_embed_panel_evento(cfg: Dict[str, Any], aviso_permisos: bool = False) -> Dict[str, Any]:
    """Construye el Embed del Panel de Control Fijo en #🎉-evento-cd."""
    activo = bool(cfg.get("activo"))
    nombres = cfg.get("pokemon_nombres") or []
    ids = cfg.get("pokemon_ids") or []
    titulo_evento = cfg.get("nombre_evento") or "Community Day / Evento Especial"

    estado_str = f"🟢 **ACTIVO** ({titulo_evento})" if activo and (nombres or ids) else "⏸️ **EN ESPERA (Sin Pokémon asignados)**"
    color = 0x10B981 if (activo and (nombres or ids)) else 0x6366F1

    if nombres:
        mostrados = ", ".join(f"**{n}**" for n in nombres[:24])
        if len(nombres) > 24:
            mostrados += f" *(+{len(nombres) - 24} más)*"
        lista_pokes_str = mostrados
        if ids:
            lista_pokes_str += f"\n*(Total familia evolutiva rastreada: `{len(ids)} especies de Pokédex`)*"
    elif ids:
        lista_pokes_str = ", ".join(f"`#{i}`" for i in ids[:25])
    else:
        lista_pokes_str = "*Ninguno configurado actualmente. Escribe un comando o un preset en este canal para empezar.*"

    modos = []
    if cfg.get("incluir_shundos_100", True):
        modos.append("🌟 `100% Shundo`")
    if cfg.get("incluir_pvp_gl", True):
        modos.append("🔵 `Great League`")
    if cfg.get("incluir_pvp_ul", True):
        modos.append("🟣 `Ultra League`")
    modos_str = " • ".join(modos) if modos else "Ninguno"

    # Estado de expiración del JWT_TOKEN en tiempo real
    exp_ts = extraer_exp_jwt(obtener_jwt_actual())
    ahora = int(time.time())
    if exp_ts > ahora:
        estado_jwt = f"🟢 **Válido** • Expira <t:{exp_ts}:R>"
    elif exp_ts > 0:
        estado_jwt = f"🔴 **Expirado** (<t:{exp_ts}:R>) • Escribe `token eyJ...`"
    else:
        estado_jwt = "🟢 **Activo**"

    guia_presets = (
        "• **`preset master`** ➔ 👑 Top Master League, Raids y Pseudo-Legendarios *(100% Shundo)*\n"
        "• **`preset mega`** ➔ 🧬 Todos los Pokémon con Mega Evolución *(100% Shundo)*\n"
        "• **`preset meta`** ➔ 🔥 Top Meta GBL competitivo *(Great & Ultra League)*\n"
        "• **`preset iniciales`** ➔ 🌱🔥💧 Todos los Iniciales Gen 1 a Gen 9"
    )

    guia_comandos = (
        "• **`Mankey, Beldum, Ralts`** ➔ Busca esos Pokémon y sus evoluciones\n"
        "• **`+Bagon`** o **`-Bagon`** ➔ Agrega o quita un Pokémon de la lista\n"
        "• **`modo todo`** | **`modo shundo`** | **`modo pvp`** | **`modo gl`** | **`modo ul`**\n"
        "• **`token eyJ...`** ➔ Renueva tu `JWT_TOKEN` directo desde Discord sin abrir GitHub\n"
        "• **`off`** o **`apagar`** ➔ Detiene el evento y limpia las alertas"
    )

    fields = [
        {"name": "📡 Estado del Evento / CD", "value": estado_str, "inline": True},
        {"name": "⚙️ Filtros Activos", "value": modos_str, "inline": True},
        {"name": "🔑 Sesión API (JWT)", "value": estado_jwt, "inline": True},
        {"name": "🎯 Pokémon Rastreados", "value": lista_pokes_str, "inline": False},
        {"name": "⚡ Presets Rápidos de 1 Palabra", "value": guia_presets, "inline": False},
        {"name": "⌨️ Comandos desde Celular o PC", "value": guia_comandos, "inline": False},
    ]

    if aviso_permisos:
        fields.append({
            "name": "🔑 Nota única para activar lectura en este canal privado",
            "value": (
                "Haz clic derecho en **`#🎉-evento-cd`** ➔ **Editar canal** ➔ **Permisos** ➔ "
                "**Añadir miembros o roles** ➔ agrega a **`ScrasherBOT`**."
            ),
            "inline": False,
        })

    return {
        "title": "🎛️ PANEL DE CONTROL — EVENTOS Y COMMUNITY DAY",
        "description": "Controla en tiempo real tus **Eventos, Community Days, Presets y Sesión JWT** desde Discord.",
        "color": color,
        "fields": fields,
        "footer": {"text": "ScrasherBOT • Radar Eventos & CD 24/7 (☁️ Nube • Escaneo cada 8m)"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publicar_o_actualizar_panel_control(aviso_permisos: bool = False, permitir_crear: bool = False) -> Optional[str]:
    """
    Actualiza el Panel de Control existente en #🎉-evento-cd mediante PATCH.
    Nunca crea mensajes nuevos en bucle: solo publica uno si no existe panel_msg_id
    o si el usuario escribe explícitamente 'panel' (permitir_crear=True) y el anterior fue borrado (404).
    """
    if not DISCORD_WEBHOOK_EVENTO.strip():
        return None

    with _LOCK_EVENTO:
        cfg = cargar_config_evento()
        base_webhook = DISCORD_WEBHOOK_EVENTO.strip().split("?")[0].rstrip("/")
        embed_panel = construir_embed_panel_evento(cfg, aviso_permisos=aviso_permisos)
        panel_mid = cfg.get("panel_msg_id")

        if panel_mid:
            try:
                r_patch = _SESION_WEBHOOK_EV.patch(
                    f"{base_webhook}/messages/{panel_mid}",
                    json={"content": "", "embeds": [embed_panel]},
                    timeout=8,
                )
                if r_patch.status_code == 200:
                    return str(panel_mid)
                if r_patch.status_code != 404 or not permitir_crear:
                    return str(panel_mid)
            except Exception:
                return str(panel_mid)

        if not permitir_crear and panel_mid:
            return str(panel_mid)

        try:
            r_post = _SESION_WEBHOOK_EV.post(
                f"{base_webhook}?wait=true",
                json={
                    "username": "Panel Eventos & CD 🎛️",
                    "content": "",
                    "embeds": [embed_panel],
                },
                timeout=10,
            )
            if r_post.status_code in (200, 204):
                nuevo_id = str(r_post.json().get("id"))
                cfg["panel_msg_id"] = nuevo_id
                guardar_config_evento(cfg)
                return nuevo_id
        except Exception:
            pass
        return None


def limpiar_alertas_evento_discord() -> None:
    """Elimina del canal #🎉-evento-cd los mensajes de spawns cuando se apaga o cambia el evento."""
    if not DISCORD_WEBHOOK_EVENTO.strip():
        return
    base_webhook = DISCORD_WEBHOOK_EVENTO.strip().split("?")[0].rstrip("/")
    with _LOCK_ESTADO:
        notificados = cargar_json(NOTIFICADOS_FILE)
        mids = set()
        for k, info in notificados.items():
            if k.startswith("_meta_") or not isinstance(info, dict):
                continue
            if info.get("canal") == "evento" and not info.get("eliminado_de_discord", False):
                if info.get("discord_msg_id"):
                    mids.add(str(info["discord_msg_id"]))
                info["eliminado_de_discord"] = True
        guardar_json(NOTIFICADOS_FILE, notificados)

    for mid in mids:
        try:
            _SESION_WEBHOOK_EV.delete(f"{base_webhook}/messages/{mid}", timeout=6)
        except Exception:
            pass


def _procesar_renovacion_token_discord(candidato_jwt: str) -> bool:
    """Valida, activa en caliente y persiste cifrado el nuevo JWT_TOKEN enviado por Discord."""
    ok, perfil, status = actualizar_jwt_token_en_vivo(candidato_jwt)
    if not ok:
        _enviar_aviso_temporal_evento(
            f"❌ **No se pudo actualizar el `JWT_TOKEN`** ( el servidor devolvió `HTTP {status}`). Verifica que hayas copiado el token completo.",
            segundos_visible=12.0,
        )
        return False

    jwt_limpio = obtener_jwt_actual()
    cfg = cargar_config_evento()
    if DISCORD_BOT_TOKEN:
        cfg["jwt_cifrado"] = cifrar_jwt_con_secreto(jwt_limpio, DISCORD_BOT_TOKEN)
    guardar_config_evento(cfg)

    # Si existe config_local.json en entorno local, actualizarlo también
    if os.path.exists(CONFIG_LOCAL_FILE):
        try:
            with open(CONFIG_LOCAL_FILE, "r", encoding="utf-8") as f:
                local_data = json.load(f)
            local_data["JWT_TOKEN"] = jwt_limpio
            with open(CONFIG_LOCAL_FILE, "w", encoding="utf-8") as f:
                json.dump(local_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    publicar_o_actualizar_panel_control()
    sincronizar_estado_remoto_push(asincrono=True)

    trainer = (perfil or {}).get("trainer") or {}
    t_name = trainer.get("trainer_name") or (perfil or {}).get("display_name") or "Entrenador"
    exp_ts = extraer_exp_jwt(jwt_limpio)
    exp_txt = f" (vence <t:{exp_ts}:R>)" if exp_ts > 0 else ""
    _enviar_aviso_temporal_evento(
        f"✅ **`JWT_TOKEN` renovado y activado en vivo** para **{t_name}**{exp_txt}. *(Este mensaje se auto-eliminará)*",
        segundos_visible=10.0,
    )
    return True


def procesar_comando_texto_evento(texto: str) -> bool:
    """
    Interpreta el mensaje escrito por el usuario en Discord y actualiza evento_config.json.
    Retorna True si debe disparar un escaneo inmediato del evento.
    """
    limpio = texto.strip()
    if not limpio:
        return False

    low = limpio.lower()
    if low.startswith("!evento"):
        limpio = limpio[7:].strip()
        low = limpio.lower()
    elif low.startswith("/evento"):
        limpio = limpio[7:].strip()
        low = limpio.lower()

    # 0. Renovación de JWT_TOKEN ("token eyJ..." o pegar directamente "eyJ...")
    if low.startswith(("token ", "jwt ")) or (limpio.startswith("eyJ") and limpio.count(".") >= 2 and len(limpio) > 60):
        cand = re.sub(r"^(token|jwt)\s+", "", limpio, flags=re.IGNORECASE).strip()
        _procesar_renovacion_token_discord(cand)
        return False

    cfg = cargar_config_evento()

    # 1. Comando de apagado
    if low in ("off", "apagar", "stop", "desactivar", "limpiar", "none", "ninguno"):
        cfg["activo"] = False
        cfg["nombre_evento"] = "Community Day / Evento Especial"
        cfg["pokemon_nombres"] = []
        cfg["pokemon_ids"] = []
        guardar_config_evento(cfg)
        limpiar_alertas_evento_discord()
        publicar_o_actualizar_panel_control()
        sincronizar_estado_remoto_push(asincrono=True)
        return False

    # 2. Comando de mostrar panel
    if low in ("panel", "ayuda", "help", "estado", "status"):
        publicar_o_actualizar_panel_control(permitir_crear=True)
        return False

    # 3. Comandos de Presets ("preset master", "preset mega", "preset meta", "preset iniciales" o directo "master", "mega", "meta")
    posible_preset = re.sub(r"^preset\s+", "", low).strip() if low.startswith("preset ") else low
    datos_preset = obtener_preset(posible_preset)
    if datos_preset:
        nombres_res, ids_res = resolver_nombres_e_ids(datos_preset["pokemones"])
        cfg["nombre_evento"] = datos_preset["titulo"]
        cfg["pokemon_nombres"] = nombres_res
        cfg["pokemon_ids"] = ids_res
        cfg["incluir_shundos_100"] = bool(datos_preset.get("incluir_shundos_100", True))
        cfg["incluir_pvp_gl"] = bool(datos_preset.get("incluir_pvp_gl", True))
        cfg["incluir_pvp_ul"] = bool(datos_preset.get("incluir_pvp_ul", True))
        cfg["activo"] = True
        guardar_config_evento(cfg)
        limpiar_alertas_evento_discord()
        publicar_o_actualizar_panel_control()
        sincronizar_estado_remoto_push(asincrono=True)
        return True

    # 4. Comando de cambio de modo
    if low.startswith("modo "):
        sub = low.replace("modo ", "").strip()
        if sub in ("todo", "all", "todos", "completo"):
            cfg["incluir_shundos_100"] = True
            cfg["incluir_pvp_gl"] = True
            cfg["incluir_pvp_ul"] = True
        elif sub in ("shundo", "shundos", "100", "100%"):
            cfg["incluir_shundos_100"] = True
            cfg["incluir_pvp_gl"] = False
            cfg["incluir_pvp_ul"] = False
        elif sub in ("pvp", "ligas"):
            cfg["incluir_shundos_100"] = False
            cfg["incluir_pvp_gl"] = True
            cfg["incluir_pvp_ul"] = True
        elif sub in ("gl", "great"):
            cfg["incluir_shundos_100"] = False
            cfg["incluir_pvp_gl"] = True
            cfg["incluir_pvp_ul"] = False
        elif sub in ("ul", "ultra"):
            cfg["incluir_shundos_100"] = False
            cfg["incluir_pvp_gl"] = False
            cfg["incluir_pvp_ul"] = True
        guardar_config_evento(cfg)
        publicar_o_actualizar_panel_control()
        sincronizar_estado_remoto_push(asincrono=True)
        return bool(cfg.get("activo"))

    # 5. Agregar Pokémon (+Nombre o agregar Nombre)
    if low.startswith("+") or low.startswith("agregar ") or low.startswith("add "):
        resto = re.sub(r"^(\+|agregar\s+|add\s+)", "", limpio, flags=re.IGNORECASE)
        partes = [p.strip() for p in re.split(r"[,;\s]+", resto) if p.strip()]
        nuevos_nom, nuevos_ids = resolver_nombres_e_ids(partes)
        actuales_nom = list(cfg.get("pokemon_nombres") or [])
        actuales_ids = list(cfg.get("pokemon_ids") or [])
        for n in nuevos_nom:
            if n not in actuales_nom:
                actuales_nom.append(n)
        for i in nuevos_ids:
            if i not in actuales_ids:
                actuales_ids.append(i)
        cfg["pokemon_nombres"] = actuales_nom
        cfg["pokemon_ids"] = actuales_ids
        cfg["activo"] = bool(actuales_nom or actuales_ids)
        guardar_config_evento(cfg)
        publicar_o_actualizar_panel_control()
        sincronizar_estado_remoto_push(asincrono=True)
        return bool(cfg["activo"])

    # 6. Quitar Pokémon (-Nombre o quitar Nombre)
    if low.startswith("-") or low.startswith("quitar ") or low.startswith("remove "):
        resto = re.sub(r"^(-|quitar\s+|remove\s+)", "", limpio, flags=re.IGNORECASE)
        partes = [p.strip() for p in re.split(r"[,;\s]+", resto) if p.strip()]
        quitar_nom, quitar_ids = resolver_nombres_e_ids(partes)
        cfg["pokemon_nombres"] = [n for n in (cfg.get("pokemon_nombres") or []) if n not in quitar_nom]
        cfg["pokemon_ids"] = [i for i in (cfg.get("pokemon_ids") or []) if i not in quitar_ids]
        cfg["activo"] = bool(cfg["pokemon_nombres"] or cfg["pokemon_ids"])
        guardar_config_evento(cfg)
        publicar_o_actualizar_panel_control()
        sincronizar_estado_remoto_push(asincrono=True)
        return bool(cfg["activo"])

    # 7. Lista directa de Pokémon (ej. "Mankey, Beldum, Ralts" o "Pikachu")
    partes = [p.strip() for p in re.split(r"[,;\s]+", limpio) if p.strip()]
    if partes:
        nombres_res, ids_res = resolver_nombres_e_ids(partes)
        if nombres_res or ids_res:
            cfg["nombre_evento"] = "Community Day / Evento Personalizado"
            cfg["pokemon_nombres"] = nombres_res
            cfg["pokemon_ids"] = ids_res
            cfg["activo"] = True
            guardar_config_evento(cfg)
            limpiar_alertas_evento_discord()
            publicar_o_actualizar_panel_control()
            sincronizar_estado_remoto_push(asincrono=True)
            return True

    return False


def coincide_con_evento(mon: Dict[str, Any], cfg_evento: Dict[str, Any]) -> bool:
    """Verifica si un Pokémon pertenece a la lista configurada del Evento o Community Day."""
    if not cfg_evento.get("activo"):
        return False

    ids_objetivo: List[int] = [int(x) for x in (cfg_evento.get("pokemon_ids") or []) if str(x).isdigit()]
    nombres_objetivo: List[str] = [str(n).strip().lower() for n in (cfg_evento.get("pokemon_nombres") or []) if n]

    if not ids_objetivo and not nombres_objetivo:
        return False

    poke_id = int(mon.get("pokemon_id") or 0)
    nombre_salvaje = str(mon.get("pokemon_name") or "").strip().lower()
    pvp = mon.get("pvp") or {}
    pvp_id = int(pvp.get("pokemon_id") or 0)
    pvp_nombre = str(pvp.get("pokemon_name") or "").strip().lower()

    if ids_objetivo and (poke_id in ids_objetivo or pvp_id in ids_objetivo):
        return True

    for buscado in nombres_objetivo:
        if buscado and not buscado.startswith("#") and (buscado in nombre_salvaje or buscado in pvp_nombre):
            return True

    return False


def _worker_lector_comandos_discord() -> None:
    """
    Hilo en segundo plano que escucha cada 2.5s los mensajes enviados por el usuario
    en el canal #🎉-evento-cd.
    """
    if not DISCORD_BOT_TOKEN.strip():
        return

    headers_bot = {"Authorization": f"Bot {DISCORD_BOT_TOKEN.strip()}"}
    canal_evento = DISCORD_EVENTO_CHANNEL_ID.strip()
    canal_general_fallback = "929565903325126717"
    ultimos_vistos: Dict[str, str] = {}

    r_test = _SESION_BOT.get(f"https://discord.com/api/v10/channels/{canal_evento}/messages?limit=1", headers=headers_bot, timeout=6)
    sin_permiso_canal_privado = r_test.status_code == 403

    while True:
        try:
            canales_a_revisar = [canal_evento]
            if sin_permiso_canal_privado:
                canales_a_revisar.append(canal_general_fallback)

            for ch_id in canales_a_revisar:
                r = _SESION_BOT.get(
                    f"https://discord.com/api/v10/channels/{ch_id}/messages?limit=5",
                    headers=headers_bot,
                    timeout=6,
                )
                if r.status_code == 200:
                    if ch_id == canal_evento and sin_permiso_canal_privado:
                        sin_permiso_canal_privado = False
                        publicar_o_actualizar_panel_control(aviso_permisos=False)

                    mensajes = r.json()
                    if not isinstance(mensajes, list) or not mensajes:
                        continue

                    if ch_id not in ultimos_vistos:
                        ultimos_vistos[ch_id] = str(mensajes[0]["id"])
                        continue

                    ultimo_id_conocido = int(ultimos_vistos[ch_id])
                    nuevos_msgs = [
                        m for m in reversed(mensajes)
                        if int(m["id"]) > ultimo_id_conocido and not m.get("author", {}).get("bot", False)
                    ]

                    if mensajes:
                        ultimos_vistos[ch_id] = str(mensajes[0]["id"])

                    for m in nuevos_msgs:
                        contenido = str(m.get("content") or "").strip()
                        if not contenido:
                            continue
                        if ch_id == canal_general_fallback and not contenido.lower().startswith(("!evento", "/evento")):
                            continue

                        # Borrar primero el mensaje del usuario (especialmente importante si envió un token JWT)
                        if ch_id == canal_evento:
                            try:
                                _SESION_BOT.delete(
                                    f"https://discord.com/api/v10/channels/{ch_id}/messages/{m['id']}",
                                    headers=headers_bot,
                                    timeout=5,
                                )
                            except Exception:
                                pass

                        es_token = contenido.lower().startswith(("token ", "jwt ")) or contenido.startswith("eyJ")
                        log_txt = "token JWT (oculto por seguridad)" if es_token else contenido
                        print(f"   🎛️ [Bot-Evento] Comando recibido en Discord: '{log_txt}'")
                        disparar_escaneo = procesar_comando_texto_evento(contenido)

                        if disparar_escaneo and _CALLBACK_ESCANEO_INMEDIATO:
                            threading.Thread(target=_CALLBACK_ESCANEO_INMEDIATO, daemon=True).start()
        except Exception:
            pass

        time.sleep(2.5)


def iniciar_hilo_bot_eventos(callback_escaneo_inmediato: Optional[Callable[[], None]] = None) -> None:
    """Inicia el hilo daemon de ScrasherBOT que escucha comandos en tiempo real."""
    global _HILO_BOT_INICIADO, _CALLBACK_ESCANEO_INMEDIATO
    _CALLBACK_ESCANEO_INMEDIATO = callback_escaneo_inmediato
    if _HILO_BOT_INICIADO or not DISCORD_BOT_TOKEN.strip():
        return
    t = threading.Thread(target=_worker_lector_comandos_discord, name="BotEventosDiscord", daemon=True)
    t.start()
    _HILO_BOT_INICIADO = True
