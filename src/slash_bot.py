"""
Servicio oficial de Discord Slash Commands (/) mediante discord.py:
- Soporte completo de la Pokédex Nacional (1025 Pokémon de Gen 1 a Gen 9 con autocompletado en tiempo real).
- Comandos intuitivos modernos: /pokemon, /preset, /apagar, /reanudar, /tiempo, /canal, /pvp_rank, /scan, /panel, /cuotas.
- Sincronización instantánea con el servidor de Discord.
- Respuestas efímeras (ephemeral) para mantener los canales 100% limpios de spam.
"""

import asyncio
from datetime import datetime, timezone
import os
import threading
from typing import Any, Callable, Dict, List, Optional
import discord
from discord import app_commands
from discord.ext import commands

from src.api_client import obtener_resumen_cuentas_pool
from src.config import (
    CONTROL_CONFIG_FILE,
    DISCORD_BOT_TOKEN,
    DISCORD_EVENTO_CHANNEL_ID,
    DISCORD_WEBHOOK_EVENTO,
    EVENTO_CONFIG_FILE,
)
from src.control_panel import (
    cargar_config_control,
    guardar_config_control,
    publicar_o_actualizar_panel_maestro,
)
from src.event_manager import (
    cargar_config_evento,
    guardar_config_evento,
    limpiar_alertas_evento_discord,
    publicar_o_actualizar_panel_control,
)
from src.pokedex_data import (
    ID_TO_NAME,
    POKEDEX_1025,
    SLUG_TO_ID,
    buscar_pokemon_autocomplete,
    resolver_cadena_pokemon,
)
from src.presets_catalog import FAMILIAS_POKEDEX, PRESETS_EVENTO, obtener_preset, resolver_nombres_e_ids
from src.state_manager import sincronizar_estado_remoto_push

GUILD_ID = 929565902880518186

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

_CALLBACK_ESCANEO_EVENTO: Optional[Callable[[], None]] = None
_CALLBACK_ESCANEO_GLOBAL: Optional[Callable[[], None]] = None
_SLASH_BOT_INICIADO = False
_LOCK_SLASH = threading.RLock()


# ==============================================================================
# AUTOCOMPLETADOS
# ==============================================================================

async def autocomplete_pokemon(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    """Devuelve los 25 Pokémon (oficiales + regionales) que mejor coinciden con lo que el usuario está escribiendo."""
    coincidencias = buscar_pokemon_autocomplete(current, limite=25)
    return [
        app_commands.Choice(name=label, value=label)
        for label, _val in coincidencias
    ]


async def autocomplete_presets(
    interaction: discord.Interaction,
    current: str
) -> List[app_commands.Choice[str]]:
    """Devuelve los presets temáticos disponibles."""
    presets = [
        ("👑 Master League & Raids (Legendarios Top)", "master"),
        ("⚡ Mega Evoluciones Competitivas", "mega"),
        ("🛡️ Meta PvP Great/Ultra League (GBL)", "meta"),
        ("🌱 Iniciales de Kanto a Paldea (Gen 1-9)", "iniciales"),
        ("🐉 Dragones Meta (Dratini, Bagon, Gible...)", "dragones"),
        ("👻 Fantasmas (Gengar, Chandelure, Trevenant...)", "fantasmas"),
    ]
    q = (current or "").lower()
    return [
        app_commands.Choice(name=name, value=key)
        for name, key in presets
        if q in name.lower() or q in key
    ][:25]


# ==============================================================================
# COMANDOS SLASH (/)
# ==============================================================================

@bot.tree.command(
    name="pokemon",
    description="🎯 Configura el radar de Eventos/CD para buscar una o varias especies (lista o hasta 5 a la vez)."
)
@app_commands.describe(
    nombre="Especie o lista separada por comas (ej: Charmander, Squirtle, Bulbasaur)",
    pokemon_2="Segunda especie opcional (con autocompletado)",
    pokemon_3="Tercera especie opcional (con autocompletado)",
    pokemon_4="Cuarta especie opcional (con autocompletado)",
    pokemon_5="Quinta especie opcional (con autocompletado)",
    acumular="Si es True, suma estos Pokémon a la lista actual sin borrar nada",
    incluir_familia="Si es True, incluye evoluciones de cada especie (recomendado para CD)",
    shundo="Si es True, rastrea 100% IV Shundos de estas especies",
    pvp_gl="Si es True, rastrea Top Ranks para Great League (1500 CP)",
    pvp_ul="Si es True, rastrea Top Ranks para Ultra League (2500 CP)"
)
@app_commands.autocomplete(
    nombre=autocomplete_pokemon,
    pokemon_2=autocomplete_pokemon,
    pokemon_3=autocomplete_pokemon,
    pokemon_4=autocomplete_pokemon,
    pokemon_5=autocomplete_pokemon,
)
async def cmd_pokemon(
    interaction: discord.Interaction,
    nombre: str,
    pokemon_2: Optional[str] = None,
    pokemon_3: Optional[str] = None,
    pokemon_4: Optional[str] = None,
    pokemon_5: Optional[str] = None,
    acumular: bool = False,
    incluir_familia: bool = True,
    shundo: bool = True,
    pvp_gl: bool = True,
    pvp_ul: bool = True,
):
    await interaction.response.defer(ephemeral=True)
    # Recolectar todas las entradas de Pokémon
    entradas = [nombre]
    for extra in (pokemon_2, pokemon_3, pokemon_4, pokemon_5):
        if extra:
            entradas.append(extra)

    res = resolver_cadena_pokemon(entradas, incluir_familia=incluir_familia, familias_dict=FAMILIAS_POKEDEX)
    if not res["exito"]:
        await interaction.followup.send(
            f"❌ No se reconoció ningún Pokémon válido en `{nombre}`.\n"
            f"💡 **Opciones válidas:**\n"
            f"• Selección de lista: `#704 Goomy`, `#705 Sliggoo (Hisui)`, `#004 Charmander`\n"
            f"• Formas regionales: `Sliggoo Hisui`, `Goodra de Hisui`, `Vulpix Alola`, `Zigzagoon Galar`\n"
            f"• Nombres y números: `Charmander`, `Beldum`, `#704`, `704`\n"
            f"• Listas combinadas: `Goomy de Hisui, Charmander, Squirtle`",
            ephemeral=True
        )
        return

    nombres_oficiales = res["nombres_principales"]
    ids_totales = res["ids_totales"]
    nombres_completos = res["nombres_completos"]
    titulo_evento = res["titulo_evento"]

    cfg_ev = cargar_config_evento()
    if acumular and cfg_ev.get("activo"):
        act_ids = list(cfg_ev.get("pokemon_ids") or [])
        act_noms = list(cfg_ev.get("pokemon_nombres") or [])
        for i in ids_totales:
            if i not in act_ids:
                act_ids.append(i)
        for n in nombres_completos:
            if n not in act_noms:
                act_noms.append(n)
        ids_totales = act_ids
        nombres_completos = act_noms
        titulo_evento = f"Evento ({len(ids_totales)} especies activas)"

    cfg_ev["nombre_evento"] = titulo_evento
    cfg_ev["pokemon_nombres"] = nombres_completos
    cfg_ev["pokemon_ids"] = ids_totales
    cfg_ev["incluir_shundos_100"] = shundo
    cfg_ev["incluir_pvp_gl"] = pvp_gl
    cfg_ev["incluir_pvp_ul"] = pvp_ul
    cfg_ev["activo"] = True

    guardar_config_evento(cfg_ev)
    limpiar_alertas_evento_discord()
    publicar_o_actualizar_panel_control()
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)

    if _CALLBACK_ESCANEO_EVENTO:
        threading.Thread(target=_CALLBACK_ESCANEO_EVENTO, daemon=True).start()

    resumen_pokes = ", ".join(nombres_oficiales)
    fases_txt = f"con su línea evolutiva completa ({len(ids_totales)} IDs)" if incluir_familia else f"solo especie exacta ({len(ids_totales)} IDs)"

    await interaction.followup.send(
        f"✅ **Radar de Eventos configurado para {len(nombres_oficiales)} Pokémon:**\n"
        f"• 📋 **Especies activas:** **{resumen_pokes}** ({fases_txt})\n"
        f"• 🎯 **Filtros:** Shundo 100% (`{shundo}`) | Great League (`{pvp_gl}`) | Ultra League (`{pvp_ul}`)\n"
        f"• ⚡ **Escaneo prioritario iniciado de inmediato en `#🎉-evento-cd`...**",
        ephemeral=True
    )




@bot.tree.command(
    name="agregar",
    description="➕ Suma una o varias especies a la lista activa de Eventos sin borrar las existentes."
)
@app_commands.describe(
    nombre="Especie o lista separada por comas a agregar (ej: Beldum, Larvitar, #705)",
    pokemon_2="Segunda especie opcional a agregar",
    pokemon_3="Tercera especie opcional a agregar",
    incluir_familia="Si es True, incluye evoluciones de las nuevas especies"
)
@app_commands.autocomplete(
    nombre=autocomplete_pokemon,
    pokemon_2=autocomplete_pokemon,
    pokemon_3=autocomplete_pokemon,
)
async def cmd_agregar(
    interaction: discord.Interaction,
    nombre: str,
    pokemon_2: Optional[str] = None,
    pokemon_3: Optional[str] = None,
    incluir_familia: bool = True,
):
    await interaction.response.defer(ephemeral=True)
    entradas = [nombre]
    for extra in (pokemon_2, pokemon_3):
        if extra:
            entradas.append(extra)

    res = resolver_cadena_pokemon(entradas, incluir_familia=incluir_familia, familias_dict=FAMILIAS_POKEDEX)
    if not res["exito"]:
        await interaction.followup.send(
            f"❌ No se reconoció ningún Pokémon válido en `{nombre}`.",
            ephemeral=True
        )
        return

    nuevos_ids = res["ids_totales"]
    nuevos_noms = res["nombres_completos"]
    nombres_agregados = res["nombres_principales"]

    cfg_ev = cargar_config_evento()
    act_ids = list(cfg_ev.get("pokemon_ids") or [])
    act_noms = list(cfg_ev.get("pokemon_nombres") or [])

    for i in nuevos_ids:
        if i not in act_ids:
            act_ids.append(i)
    for n in nuevos_noms:
        if n not in act_noms:
            act_noms.append(n)

    cfg_ev["pokemon_ids"] = act_ids
    cfg_ev["pokemon_nombres"] = act_noms
    cfg_ev["activo"] = True
    guardar_config_evento(cfg_ev)

    limpiar_alertas_evento_discord()
    publicar_o_actualizar_panel_control()
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)

    if _CALLBACK_ESCANEO_EVENTO:
        threading.Thread(target=_CALLBACK_ESCANEO_EVENTO, daemon=True).start()

    lista_agregada = ", ".join(nombres_agregados)
    await interaction.followup.send(
        f"➕ **Agregado con éxito sin borrar lo anterior:**\n"
        f"• 📋 **Nuevas especies sumadas:** **{lista_agregada}**\n"
        f"• 🎯 **Total especies activas ahora:** {len(act_ids)} Pokémon en `#🎉-evento-cd`\n"
        f"• ⚡ **Escaneo prioritario disparado de inmediato.**",
        ephemeral=True
    )


@bot.tree.command(
    name="quitar",
    description="➖ Quita una o varias especies de la lista activa de Eventos sin tocar las demás."
)
@app_commands.describe(
    nombre="Especie o lista a quitar (ej: Deino, Aron, Beldum)",
    pokemon_2="Segunda especie opcional a quitar"
)
@app_commands.autocomplete(
    nombre=autocomplete_pokemon,
    pokemon_2=autocomplete_pokemon,
)
async def cmd_quitar(
    interaction: discord.Interaction,
    nombre: str,
    pokemon_2: Optional[str] = None,
):
    await interaction.response.defer(ephemeral=True)
    entradas = [nombre]
    if pokemon_2:
        entradas.append(pokemon_2)

    res = resolver_cadena_pokemon(entradas, incluir_familia=True, familias_dict=FAMILIAS_POKEDEX)
    quitar_ids = set(res["ids_totales"])
    quitar_noms = set(res["nombres_completos"])

    cfg_ev = cargar_config_evento()
    act_ids = [i for i in (cfg_ev.get("pokemon_ids") or []) if i not in quitar_ids]
    act_noms = [n for n in (cfg_ev.get("pokemon_nombres") or []) if n not in quitar_noms]

    cfg_ev["pokemon_ids"] = act_ids
    cfg_ev["pokemon_nombres"] = act_noms
    cfg_ev["activo"] = bool(act_ids)
    guardar_config_evento(cfg_ev)

    limpiar_alertas_evento_discord()
    publicar_o_actualizar_panel_control()
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)

    lista_quitada = ", ".join(res["nombres_principales"])
    await interaction.followup.send(
        f"➖ **Eliminado de la lista activa:**\n"
        f"• 📋 **Especies quitadas:** **{lista_quitada}**\n"
        f"• 🎯 **Total especies que quedan:** {len(act_ids)} Pokémon en `#🎉-evento-cd`",
        ephemeral=True
    )
@bot.tree.command(
    name="preset",
    description="📦 Activa un paquete temático preconfigurado de Pokémon populares o del Meta."
)
@app_commands.describe(opcion="Elige el paquete temático que deseas activar")
@app_commands.autocomplete(opcion=autocomplete_presets)
async def cmd_preset(interaction: discord.Interaction, opcion: str):
    await interaction.response.defer(ephemeral=True)
    datos_preset = obtener_preset(opcion)
    if not datos_preset:
        await interaction.followup.send(
            f"❌ El preset `{opcion}` no existe. Opciones: `master`, `mega`, `meta`, `iniciales`, `dragones`, `fantasmas`.",
            ephemeral=True
        )
        return

    nombres_res, ids_res = resolver_nombres_e_ids(datos_preset["pokemones"])
    cfg_ev = cargar_config_evento()
    cfg_ev["nombre_evento"] = datos_preset["titulo"]
    cfg_ev["pokemon_nombres"] = nombres_res
    cfg_ev["pokemon_ids"] = ids_res
    cfg_ev["incluir_shundos_100"] = bool(datos_preset.get("incluir_shundos_100", True))
    cfg_ev["incluir_pvp_gl"] = bool(datos_preset.get("incluir_pvp_gl", True))
    cfg_ev["incluir_pvp_ul"] = bool(datos_preset.get("incluir_pvp_ul", True))
    cfg_ev["activo"] = True

    guardar_config_evento(cfg_ev)
    limpiar_alertas_evento_discord()
    publicar_o_actualizar_panel_control()
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)

    if _CALLBACK_ESCANEO_EVENTO:
        threading.Thread(target=_CALLBACK_ESCANEO_EVENTO, daemon=True).start()

    await interaction.followup.send(
        f"✅ **Preset Activado:** **{datos_preset['titulo']}**\n"
        f"• 📋 **Pokémon rastreados:** `{len(ids_res)} especies`\n"
        f"• ⚡ **Escaneo inmediato iniciado en `#🎉-evento-cd`...**",
        ephemeral=True
    )




@bot.tree.command(
    name="limpiar",
    description="🧹 Limpia a cero la lista de especies de Eventos o limpia mensajes huérfanos del canal."
)
@app_commands.describe(
    objetivo="Qué deseas limpiar: la lista de Pokémon de eventos, el chat de control, o todo"
)
@app_commands.choices(objetivo=[
    app_commands.Choice(name="🎯 Lista de Pokémon de Eventos (dejar en cero para empezar de nuevo)", value="evento"),
    app_commands.Choice(name="💬 Mensajes huérfanos del chat de Control", value="chat"),
    app_commands.Choice(name="🧹 Limpieza Total (Lista a cero + alertas + chat)", value="todo"),
])
async def cmd_limpiar(interaction: discord.Interaction, objetivo: str = "evento"):
    await interaction.response.defer(ephemeral=True)
    if objetivo in ("evento", "todo"):
        cfg_ev = cargar_config_evento()
        cfg_ev["activo"] = False
        cfg_ev["nombre_evento"] = "Community Day / Evento Especial"
        cfg_ev["pokemon_nombres"] = []
        cfg_ev["pokemon_ids"] = []
        guardar_config_evento(cfg_ev)
        limpiar_alertas_evento_discord()
        publicar_o_actualizar_panel_control()

    if objetivo in ("chat", "todo"):
        cfg_ctrl = cargar_config_control()
        from src.control_panel import limpiar_mensajes_canal_control
        limpiar_mensajes_canal_control(cfg_ctrl.get("panel_msg_id"))

    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)

    if objetivo == "evento":
        await interaction.followup.send(
            "🧹 **Lista de Pokémon de Eventos reseteada a cero.** El radar está listo para recibir nuevas especies cuando gustes.",
            ephemeral=True
        )
    elif objetivo == "chat":
        await interaction.followup.send(
            "🧹 **Canal limpiado.** Se eliminaron los mensajes sueltos y quedó el panel maestro visible.",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            "🧹 **Limpieza total completada:** Lista de eventos reseteada a cero, alertas anteriores eliminadas y chat limpio.",
            ephemeral=True
        )
@bot.tree.command(
    name="apagar",
    description="🛑 Apaga el filtro de Eventos/CD o pausa el radar completo."
)
@app_commands.describe(objetivo="Elige si deseas apagar solo el canal de eventos o pausar todo el radar")
@app_commands.choices(objetivo=[
    app_commands.Choice(name="🎉 Apagar solo Evento / Community Day (#🎉-evento-cd)", value="evento"),
    app_commands.Choice(name="⏸️ Pausar todo el radar globalmente", value="todo"),
])
async def cmd_apagar(interaction: discord.Interaction, objetivo: str):
    await interaction.response.defer(ephemeral=True)
    if objetivo == "evento":
        cfg_ev = cargar_config_evento()
        cfg_ev["activo"] = False
        cfg_ev["nombre_evento"] = "Community Day / Evento Especial"
        cfg_ev["pokemon_nombres"] = []
        cfg_ev["pokemon_ids"] = []
        guardar_config_evento(cfg_ev)
        limpiar_alertas_evento_discord()
        publicar_o_actualizar_panel_control()
        publicar_o_actualizar_panel_maestro()
        sincronizar_estado_remoto_push(asincrono=True)
        await interaction.followup.send("🛑 **Canal de Eventos & CD apagado.** No se enviarán alertas hasta activar una especie.", ephemeral=True)
    else:
        cfg_ctrl = cargar_config_control()
        cfg_ctrl["pausa_global"] = True
        guardar_config_control(cfg_ctrl)
        publicar_o_actualizar_panel_maestro()
        sincronizar_estado_remoto_push(asincrono=True)
        await interaction.followup.send("⏸️ **Radar pausado globalmente.** No se enviarán alertas en ningún canal.", ephemeral=True)


@bot.tree.command(
    name="reanudar",
    description="▶️ Reanuda el radar si estaba pausado globalmente."
)
async def cmd_reanudar(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    cfg_ctrl = cargar_config_control()
    cfg_ctrl["pausa_global"] = False
    guardar_config_control(cfg_ctrl)
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)
    await interaction.followup.send("▶️ **Radar reanudado.** El escaneo 24/7 en todos los canales activos continúa normalmente.", ephemeral=True)


@bot.tree.command(
    name="tiempo",
    description="⏱️ Cambia el intervalo de tiempo entre cada escaneo del radar."
)
@app_commands.describe(minutos="Intervalo en minutos entre cada búsqueda")
@app_commands.choices(minutos=[
    app_commands.Choice(name="⚡ 3 minutos (Ultra Rápido)", value=3),
    app_commands.Choice(name="🚀 5 minutos (Rápido)", value=5),
    app_commands.Choice(name="🟢 7 minutos (Recomendado y Óptimo)", value=7),
    app_commands.Choice(name="🛡️ 10 minutos (Económico)", value=10),
    app_commands.Choice(name="☕ 15 minutos (Bajo consumo)", value=15),
    app_commands.Choice(name="🐢 20 minutos (Muy espaciado)", value=20),
])
async def cmd_tiempo(interaction: discord.Interaction, minutos: int):
    await interaction.response.defer(ephemeral=True)
    cfg_ctrl = cargar_config_control()
    cfg_ctrl["intervalo_minutos"] = minutos
    guardar_config_control(cfg_ctrl)
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)
    await interaction.followup.send(f"⏱️ **Intervalo de escaneo actualizado:** `{minutos} minutos`.", ephemeral=True)


@bot.tree.command(
    name="canal",
    description="🔴/🟢 Activa o pausa un canal específico del radar."
)
@app_commands.describe(
    canal="Canal a configurar",
    estado="Activar (ON) o pausar (OFF)"
)
@app_commands.choices(
    canal=[
        app_commands.Choice(name="🌟 Shundos 100% IV", value="shundo"),
        app_commands.Choice(name="🔵 Great League (1500 CP)", value="great"),
        app_commands.Choice(name="🟣 Ultra League (2500 CP)", value="ultra"),
        app_commands.Choice(name="🎉 Eventos / CD", value="evento"),
    ],
    estado=[
        app_commands.Choice(name="🟢 Activar (ON)", value="on"),
        app_commands.Choice(name="🔴 Pausar (OFF)", value="off"),
    ]
)
async def cmd_canal(interaction: discord.Interaction, canal: str, estado: str):
    await interaction.response.defer(ephemeral=True)
    cfg_ctrl = cargar_config_control()
    canales = cfg_ctrl.setdefault("canales", {"shundo": True, "great": True, "ultra": True, "evento": True})
    activar = (estado == "on")
    canales[canal] = activar
    guardar_config_control(cfg_ctrl)

    if canal == "evento":
        try:
            cfg_ev = cargar_config_evento()
            cfg_ev["activo"] = activar
            guardar_config_evento(cfg_ev)
            publicar_o_actualizar_panel_control()
        except Exception:
            pass

    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)

    nombres = {"shundo": "Shundos 100% IV", "great": "Great League", "ultra": "Ultra League", "evento": "Eventos & CD"}
    tag = "🟢 Activado" if activar else "🔴 Pausado"
    await interaction.followup.send(f"{tag}: Canal **{nombres.get(canal, canal)}**.", ephemeral=True)


@bot.tree.command(
    name="pvp_rank",
    description="🏆 Configura el rango máximo para alertas de PvP en Great y Ultra League."
)
@app_commands.describe(top="Rango máximo que deseas recibir")
@app_commands.choices(top=[
    app_commands.Choice(name="🥇 Top 1 (Solo el Rank #1 absoluto)", value=1),
    app_commands.Choice(name="🥈 Top 2 (Rank #1 y #2)", value=2),
    app_commands.Choice(name="🥉 Top 3 (Rank #1 al #3)", value=3),
    app_commands.Choice(name="🏆 Top 5 (Rank #1 al #5 - Estándar)", value=5),
    app_commands.Choice(name="🎖️ Top 10 (Rank #1 al #10 - Amplio)", value=10),
])
async def cmd_pvp_rank(interaction: discord.Interaction, top: int):
    await interaction.response.defer(ephemeral=True)
    cfg_ctrl = cargar_config_control()
    cfg_ctrl["pvp_top_rank"] = top
    guardar_config_control(cfg_ctrl)
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)
    await interaction.followup.send(f"🏆 **Filtro PvP actualizado:** Recibirás spawns de `Rank #1 al #{top}`.", ephemeral=True)


@bot.tree.command(
    name="scan",
    description="⚡ Dispara un escaneo global forzado en todos los canales en este segundo."
)
async def cmd_scan(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send("⚡ **Escaneo global forzado iniciado.** Buscando nuevos spawns en los 5 continentes...", ephemeral=True)
    if _CALLBACK_ESCANEO_GLOBAL:
        threading.Thread(target=_CALLBACK_ESCANEO_GLOBAL, daemon=True).start()


@bot.tree.command(
    name="panel",
    description="🎛️ Muestra o refresca el Panel Maestro de Control en #🎛️-panel-control."
)
async def cmd_panel(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    mid = publicar_o_actualizar_panel_maestro()
    await interaction.followup.send("✅ **Panel Maestro de Control actualizado en `#🎛️-panel-control`**.", ephemeral=True)


@bot.tree.command(
    name="cuotas",
    description="📊 Muestra el estado en vivo de tus 3 cuentas del Pool de reveals exactos."
)
async def cmd_cuotas(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    resumen = obtener_resumen_cuentas_pool()
    embed = discord.Embed(
        title="🔑 Estado del Pool de Cuentas (3 Cuentas)",
        description=f"```\n{resumen}\n```\nCapacidad total: **30 reveals exactos por hora**.",
        color=0x2563EB,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


# ==============================================================================
# EVENTOS DEL BOT Y SINCRONIZACIÓN
# ==============================================================================

@bot.event
async def on_ready():
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"   🤖 [SlashBot] Conectado como {bot.user} | {len(synced)} comandos '/' sincronizados en el servidor!")
    except Exception as e:
        print(f"   ⚠️ [SlashBot] Error al sincronizar slash commands: {e}")


def _ejecutar_loop_slash_bot() -> None:
    """Ejecuta el bot en un bucle asyncio dedicado dentro de su propio hilo."""
    if not DISCORD_BOT_TOKEN.strip():
        return
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot.start(DISCORD_BOT_TOKEN.strip()))
    except Exception as e:
        print(f"   ⚠️ [SlashBot] Error en bucle asyncio: {e}")


def iniciar_hilo_slash_bot(
    callback_escaneo_evento: Optional[Callable[[], None]] = None,
    callback_escaneo_global: Optional[Callable[[], None]] = None
) -> None:
    """Inicia el bot de Slash Commands en un hilo en segundo plano."""
    global _SLASH_BOT_INICIADO, _CALLBACK_ESCANEO_EVENTO, _CALLBACK_ESCANEO_GLOBAL
    with _LOCK_SLASH:
        if callback_escaneo_evento:
            _CALLBACK_ESCANEO_EVENTO = callback_escaneo_evento
        if callback_escaneo_global:
            _CALLBACK_ESCANEO_GLOBAL = callback_escaneo_global
        if _SLASH_BOT_INICIADO:
            return
        t = threading.Thread(target=_ejecutar_loop_slash_bot, name="DiscordSlashBot", daemon=True)
        t.start()
        _SLASH_BOT_INICIADO = True
