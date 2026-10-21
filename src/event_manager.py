"""
Módulo escalable para Eventos Especiales y Community Days (CD):
- Panel de Control interactivo en el canal #🎉-evento-cd
- Lector en tiempo real de comandos escritos en Discord mediante ScrasherBOT
- Traductor automático de nombres de Pokémon a IDs de Pokédex y familias evolutivas
- Escaneo instantáneo al cambiar la configuración desde el celular o PC
"""

from datetime import datetime, timezone
import json
import os
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
import requests

from src.config import (
    DISCORD_BOT_TOKEN,
    DISCORD_EVENTO_CHANNEL_ID,
    DISCORD_WEBHOOK_EVENTO,
    EVENTO_CONFIG_FILE,
    NOTIFICADOS_FILE,
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

# Diccionario de especies frecuentes, Community Days, iniciales y Meta PvP (Nombre -> Familia de IDs Pokédex)
FAMILIAS_POKEDEX: Dict[str, List[int]] = {
    "bulbasaur": [1, 2, 3], "ivysaur": [1, 2, 3], "venusaur": [1, 2, 3],
    "charmander": [4, 5, 6], "charmeleon": [4, 5, 6], "charizard": [4, 5, 6],
    "squirtle": [7, 8, 9], "wartortle": [7, 8, 9], "blastoise": [7, 8, 9],
    "caterpie": [10, 11, 12], "weedle": [13, 14, 15], "beedrill": [13, 14, 15],
    "pidgey": [16, 17, 18], "pidgeot": [16, 17, 18],
    "pikachu": [25, 26, 172], "raichu": [25, 26, 172],
    "sandshrew": [27, 28], "sandslash": [27, 28],
    "nidoran": [29, 30, 31, 32, 33, 34], "nidoking": [32, 33, 34], "nidoqueen": [29, 30, 31],
    "clefairy": [35, 36, 173], "clefable": [35, 36, 173],
    "vulpix": [37, 38], "ninetales": [37, 38],
    "jigglypuff": [39, 40, 174], "wigglytuff": [39, 40, 174],
    "zubat": [41, 42, 169], "oddish": [43, 44, 45, 182],
    "diglett": [50, 51], "meowth": [52, 53, 863], "persian": [52, 53, 863],
    "psyduck": [54, 55], "mankey": [56, 57, 979], "primeape": [56, 57, 979], "annihilape": [56, 57, 979],
    "growlithe": [58, 59], "arcanine": [58, 59],
    "poliwag": [60, 61, 62, 186], "poliwrath": [60, 61, 62, 186], "politoed": [60, 61, 62, 186],
    "abra": [63, 64, 65], "alakazam": [63, 64, 65],
    "machop": [66, 67, 68], "machamp": [66, 67, 68],
    "bellsprout": [69, 70, 71], "victreebel": [69, 70, 71],
    "tentacool": [72, 73], "tentacruel": [72, 73],
    "geodude": [74, 75, 76], "golem": [74, 75, 76],
    "ponyta": [77, 78], "rapidash": [77, 78],
    "slowpoke": [79, 80, 199], "slowbro": [79, 80, 199], "slowking": [79, 80, 199],
    "magnemite": [81, 82, 462], "magnezone": [81, 82, 462],
    "seel": [86, 87], "dewgong": [86, 87],
    "grimer": [88, 89], "muk": [88, 89],
    "gastly": [92, 93, 94], "haunter": [92, 93, 94], "gengar": [92, 93, 94],
    "onix": [95, 208], "steelix": [95, 208],
    "cubone": [104, 105], "marowak": [104, 105],
    "hitmonlee": [106, 236], "hitmonchan": [107, 236],
    "lickitung": [108, 463], "lickilicky": [108, 463],
    "koffing": [109, 110], "weezing": [109, 110],
    "rhyhorn": [111, 112, 464], "rhyperior": [111, 112, 464],
    "chansey": [113, 242, 440], "blissey": [113, 242, 440],
    "horsea": [116, 117, 230], "kingdra": [116, 117, 230],
    "scyther": [123, 212, 900], "scizor": [123, 212, 900],
    "electabuzz": [125, 239, 466], "electivire": [125, 239, 466],
    "magmar": [126, 240, 467], "magmortar": [126, 240, 467],
    "magikarp": [129, 130], "gyarados": [129, 130],
    "lapras": [131], "eevee": [133, 134, 135, 136, 196, 197, 470, 471, 700],
    "umbreon": [133, 197], "sylveon": [133, 700],
    "porygon": [137, 233, 474], "snorlax": [143, 446],
    "dratini": [147, 148, 149], "dragonair": [147, 148, 149], "dragonite": [147, 148, 149],
    "chikorita": [152, 153, 154], "meganium": [152, 153, 154],
    "cyndaquil": [155, 156, 157], "typhlosion": [155, 156, 157],
    "totodile": [158, 159, 160], "feraligatr": [158, 159, 160],
    "sentret": [161, 162], "hoothoot": [163, 164], "noctowl": [163, 164],
    "chinchou": [170, 171], "lanturn": [170, 171],
    "togetic": [175, 176, 468], "togekiss": [175, 176, 468],
    "mareep": [179, 180, 181], "ampharos": [179, 180, 181],
    "marill": [183, 184, 298], "azumarill": [183, 184, 298],
    "hoppip": [187, 188, 189], "jumpluff": [187, 188, 189],
    "wooper": [194, 195, 980], "quagsire": [194, 195, 980], "clodsire": [194, 195, 980],
    "gligar": [207, 472], "gliscor": [207, 472],
    "sneasel": [215, 461, 903], "weavile": [215, 461], "sneasler": [215, 903],
    "teddiursa": [216, 217, 901], "ursaluna": [216, 217, 901],
    "swinub": [220, 221, 473], "mamoswine": [220, 221, 473],
    "skarmory": [227], "larvitar": [246, 247, 248], "tyranitar": [246, 247, 248],
    "treecko": [252, 253, 254], "sceptile": [252, 253, 254],
    "torchic": [255, 256, 257], "blaziken": [255, 256, 257],
    "mudkip": [258, 259, 260], "swampert": [258, 259, 260],
    "zigzagoon": [263, 264, 862], "obstagoon": [263, 264, 862],
    "lotad": [270, 271, 272], "seedot": [273, 274, 275], "wingull": [278, 279], "pelipper": [278, 279],
    "ralts": [280, 281, 282, 475], "gardevoir": [280, 281, 282, 475], "gallade": [280, 281, 282, 475],
    "slakoth": [287, 288, 289], "vigoroth": [287, 288, 289],
    "whismur": [293, 294, 295], "exploud": [293, 294, 295],
    "makuhita": [296, 297], "hariyama": [296, 297],
    "sableye": [302], "aron": [304, 305, 306], "meditite": [307, 308], "medicham": [307, 308],
    "roselia": [315, 406, 407], "roserade": [315, 406, 407],
    "trapinch": [328, 329, 330], "flygon": [328, 329, 330],
    "swablu": [333, 334], "altaria": [333, 334],
    "barboach": [339, 340], "whiscash": [339, 340],
    "feebas": [349, 350], "milotic": [349, 350],
    "shuppet": [353, 354], "banette": [353, 354],
    "duskull": [355, 356, 477], "dusknoir": [355, 356, 477],
    "spheal": [363, 364, 365], "walrein": [363, 364, 365],
    "bagon": [371, 372, 373], "salamence": [371, 372, 373],
    "beldum": [374, 375, 376], "metang": [374, 375, 376], "metagross": [374, 375, 376],
    "turtwig": [387, 388, 389], "torterra": [387, 388, 389],
    "chimchar": [390, 391, 392], "infernape": [390, 391, 392],
    "piplup": [393, 394, 395], "empoleon": [393, 394, 395],
    "starly": [396, 397, 398], "shinx": [403, 404, 405], "luxray": [403, 404, 405],
    "cranidos": [408, 409], "shieldon": [410, 411], "bastiodon": [410, 411],
    "drifloon": [425, 426], "drifblim": [425, 426],
    "buneary": [427, 428], "lopunny": [427, 428],
    "gible": [443, 444, 445], "garchomp": [443, 444, 445],
    "riolu": [447, 448], "lucario": [447, 448],
    "snover": [459, 460], "abomasnow": [459, 460],
    "snivy": [495, 496, 497], "serperior": [495, 496, 497],
    "tepig": [498, 499, 500], "emboar": [498, 499, 500],
    "oshawott": [501, 502, 503], "samurott": [501, 502, 503],
    "lillipup": [506, 507, 508], "roggenrola": [524, 525, 526], "gigalith": [524, 525, 526],
    "timburr": [532, 533, 534], "conkeldurr": [532, 533, 534],
    "tympole": [535, 536, 537], "seismitoad": [535, 536, 537],
    "sewaddle": [540, 541, 542], "leavanny": [540, 541, 542],
    "venipede": [543, 544, 545], "cottonee": [546, 547], "whimsicott": [546, 547],
    "sandile": [551, 552, 553], "scraggy": [559, 560], "scrafty": [559, 560],
    "yamask": [562, 563, 867], "cofagrigus": [562, 563, 867], "runerigus": [562, 563, 867],
    "frillish": [592, 593], "jellicent": [592, 593],
    "ferroseed": [597, 598], "ferrothorn": [597, 598],
    "tynamo": [602, 603, 604], "litwick": [607, 608, 609], "chandelure": [607, 608, 609],
    "axew": [610, 611, 612], "haxorus": [610, 611, 612],
    "shelmet": [616, 617], "accelgor": [616, 617],
    "stunfisk": [618], "mienfoo": [619, 620], "mienshao": [619, 620],
    "deino": [633, 634, 635], "hydreigon": [633, 634, 635],
    "chespin": [650, 651, 652], "chesnaught": [650, 651, 652],
    "fennekin": [653, 654, 655], "delphox": [653, 654, 655],
    "froakie": [656, 657, 658], "greninja": [656, 657, 658],
    "bunnelby": [659, 660], "diggersby": [659, 660],
    "fletchling": [661, 662, 663], "talonflame": [661, 662, 663],
    "phantump": [708, 709], "trevenant": [708, 709],
    "goomy": [704, 705, 706], "goodra": [704, 705, 706],
    "noibat": [714, 715], "noivern": [714, 715],
    "rowlet": [722, 723, 724], "decidueye": [722, 723, 724],
    "litten": [725, 726, 727], "incineroar": [725, 726, 727],
    "popplio": [728, 729, 730], "primarina": [728, 729, 730],
    "grubbin": [736, 737, 738], "charjabug": [736, 737, 738], "vikavolt": [736, 737, 738],
    "mareanie": [747, 748], "toxapex": [747, 748],
    "stufful": [759, 760], "bewear": [759, 760],
    "bounsweet": [761, 762, 763], "tsareena": [761, 762, 763],
    "jangmo-o": [782, 783, 784], "kommo-o": [782, 783, 784],
    "rookidee": [821, 822, 823], "corviknight": [821, 822, 823],
    "dreepy": [885, 886, 887], "dragapult": [885, 886, 887],
    "sprigatito": [906, 907, 908], "fuecoco": [909, 910, 911], "quaxly": [912, 913, 914],
    "lechonk": [915, 916], "smoliv": [928, 929, 930], "frigibax": [996, 997, 998],
}


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


def resolver_nombres_e_ids(entradas_crudas: List[str]) -> Tuple[List[str], List[int]]:
    """Convierte una lista de nombres o IDs (ej. ['Mankey', '374']) en nombres limpios e IDs de Pokédex."""
    nombres_finales: List[str] = []
    ids_finales: List[int] = []

    for item in entradas_crudas:
        limpio = item.strip().lower()
        if not limpio:
            continue
        if limpio.isdigit():
            pid = int(limpio)
            if pid not in ids_finales:
                ids_finales.append(pid)
            etiqueta = f"#{pid}"
            for nom_k, fam_ids in FAMILIAS_POKEDEX.items():
                if pid == fam_ids[0]:
                    etiqueta = nom_k.capitalize()
                    for fid in fam_ids:
                        if fid not in ids_finales:
                            ids_finales.append(fid)
                    break
            if etiqueta not in nombres_finales:
                nombres_finales.append(etiqueta)
        else:
            nom_cap = limpio.capitalize()
            if nom_cap not in nombres_finales:
                nombres_finales.append(nom_cap)
            if limpio in FAMILIAS_POKEDEX:
                for fid in FAMILIAS_POKEDEX[limpio]:
                    if fid not in ids_finales:
                        ids_finales.append(fid)
            else:
                try:
                    r_poke = requests.get(f"https://pokeapi.co/api/v2/pokemon/{limpio}", timeout=4)
                    if r_poke.status_code == 200:
                        pid_api = int(r_poke.json().get("id") or 0)
                        if pid_api > 0 and pid_api not in ids_finales:
                            ids_finales.append(pid_api)
                except Exception:
                    pass

    return nombres_finales, ids_finales


def construir_embed_panel_evento(cfg: Dict[str, Any], aviso_permisos: bool = False) -> Dict[str, Any]:
    """Construye el Embed del Panel de Control Fijo en #🎉-evento-cd."""
    activo = bool(cfg.get("activo"))
    nombres = cfg.get("pokemon_nombres") or []
    ids = cfg.get("pokemon_ids") or []

    estado_str = "🟢 **ACTIVO — ESCANEANDO EN VIVO**" if activo and (nombres or ids) else "⏸️ **EN ESPERA (Sin Pokémon asignados)**"
    color = 0x10B981 if (activo and (nombres or ids)) else 0x6366F1

    if nombres:
        lista_pokes_str = ", ".join(f"**{n}**" for n in nombres)
        if ids:
            lista_pokes_str += f"\n*(IDs Pokédex incluidos con evoluciones: `{', '.join(map(str, ids[:18]))}`)*"
    elif ids:
        lista_pokes_str = ", ".join(f"`#{i}`" for i in ids)
    else:
        lista_pokes_str = "*Ninguno configurado actualmente. Escribe los nombres en este canal para empezar.*"

    modos = []
    if cfg.get("incluir_shundos_100", True):
        modos.append("🌟 `100% Shundo IV`")
    if cfg.get("incluir_pvp_gl", True):
        modos.append("🔵 `Great League (Top 1-5 Shiny)`")
    if cfg.get("incluir_pvp_ul", True):
        modos.append("🟣 `Ultra League (Top 1-5 Shiny)`")
    modos_str = " • ".join(modos) if modos else "Ninguno"

    guia_comandos = (
        "Escribe directamente en este canal cualquiera de estos comandos:\n"
        "• **`Mankey, Beldum, Ralts`** ➔ Activa la búsqueda de esos Pokémon (y sus evoluciones)\n"
        "• **`+Bagon`** o **`-Bagon`** ➔ Agrega o quita un Pokémon sin borrar los demás\n"
        "• **`modo todo`** ➔ Busca 100% Shundo + GL + UL *(por defecto)*\n"
        "• **`modo shundo`** | **`modo pvp`** | **`modo gl`** | **`modo ul`** ➔ Cambia el filtro\n"
        "• **`off`** o **`apagar`** ➔ Detiene el evento y limpia las alertas"
    )

    fields = [
        {"name": "📡 Estado del Evento / CD", "value": estado_str, "inline": True},
        {"name": "⚙️ Filtros Activos", "value": modos_str, "inline": True},
        {"name": "🎯 Pokémon del Evento / CD", "value": lista_pokes_str, "inline": False},
        {"name": "⌨️ Cómo Configurar desde tu Celular o PC", "value": guia_comandos, "inline": False},
    ]

    if aviso_permisos:
        fields.append({
            "name": "🔑 Nota única para activar lectura en este canal privado",
            "value": (
                "Como la categoría **Pogo** es privada, haz clic derecho en **`#🎉-evento-cd`** ➔ "
                "**Editar canal** ➔ **Permisos** ➔ **Añadir miembros o roles** ➔ agrega a **`ScrasherBOT`** "
                "*(mientras tanto también puedes escribir tus comandos en `#general`)*."
            ),
            "inline": False,
        })

    return {
        "title": "🎛️ PANEL DE CONTROL — EVENTOS Y COMMUNITY DAY",
        "description": "Configura en tiempo real qué Pokémon de **Evento o Community Day** quieres rastrear en **100% Shundo, Great League y Ultra League**.",
        "color": color,
        "fields": fields,
        "footer": {"text": "ScrasherBOT • Radar Eventos & CD 24/7 (☁️ Nube)"},
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
                # Si no fue borrado (ej. rate limit o timeout temporal), NO crear otro mensaje
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
    """Elimina del canal #🎉-evento-cd los mensajes de spawns cuando se apaga el evento."""
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

    cfg = cargar_config_evento()

    # 1. Comando de apagado
    if low in ("off", "apagar", "stop", "desactivar", "limpiar", "none", "ninguno"):
        cfg["activo"] = False
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

    # 3. Comando de cambio de modo
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

    # 4. Agregar Pokémon (+Nombre o agregar Nombre)
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

    # 5. Quitar Pokémon (-Nombre o quitar Nombre)
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

    # 6. Lista directa de Pokémon (ej. "Mankey, Beldum, Ralts" o "Pikachu")
    partes = [p.strip() for p in re.split(r"[,;\s]+", limpio) if p.strip()]
    if partes:
        nombres_res, ids_res = resolver_nombres_e_ids(partes)
        if nombres_res or ids_res:
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
    en el canal #🎉-evento-cd (o #general si aún no se dio permiso al bot en la categoría privada).
    """
    if not DISCORD_BOT_TOKEN.strip():
        return

    headers_bot = {"Authorization": f"Bot {DISCORD_BOT_TOKEN.strip()}"}
    canal_evento = DISCORD_EVENTO_CHANNEL_ID.strip()
    canal_general_fallback = "929565903325126717"
    ultimos_vistos: Dict[str, str] = {}

    # Verificar si ScrasherBOT ya tiene acceso al canal #🎉-evento-cd (sin reenviar ni tocar el panel al iniciar)
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

                    # En la primera lectura de este canal, registrar el último ID sin re-ejecutar historial viejo
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
                        # En #general solo procesar si empieza con !evento o /evento para no interferir con charlas
                        if ch_id == canal_general_fallback and not contenido.lower().startswith(("!evento", "/evento")):
                            continue

                        print(f"   🎛️ [Bot-Evento] Comando recibido en Discord: '{contenido}'")
                        disparar_escaneo = procesar_comando_texto_evento(contenido)

                        # Borrar el mensaje de comando del usuario para mantener limpio el canal #🎉-evento-cd
                        if ch_id == canal_evento:
                            try:
                                _SESION_BOT.delete(
                                    f"https://discord.com/api/v10/channels/{ch_id}/messages/{m['id']}",
                                    headers=headers_bot,
                                    timeout=5,
                                )
                            except Exception:
                                pass

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
