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
from src.pokedex_data import ID_TO_NAME, POKEDEX_1025, SLUG_TO_ID, buscar_pokemon_autocomplete
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
    """Devuelve los 25 Pokémon que mejor coinciden con lo que el usuario está escribiendo."""
    coincidencias = buscar_pokemon_autocomplete(current, limite=25)
    return [
        app_commands.Choice(name=label, value=slug)
        for label, slug in coincidencias
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
    incluir_familia: bool = True,
    shundo: bool = True,
    pvp_gl: bool = True,
    pvp_ul: bool = True,
):
    import re
    # 1. Recolectar todos los candidatos
    entradas = [nombre]
    for extra in (pokemon_2, pokemon_3, pokemon_4, pokemon_5):
        if extra:
            entradas.append(extra)

    slugs_limpios = []
    for item in entradas:
        partes = [p.strip().lower() for p in re.split(r"[,;]+", item) if p.strip()]
        slugs_limpios.extend(partes)

    ids_totales = []
    nombres_oficiales = []

    for s in slugs_limpios:
        s_norm = s.replace(" ", "-")
        poke_id = SLUG_TO_ID.get(s_norm) or SLUG_TO_ID.get(s)
        if not poke_id and s.isdigit():
            poke_id = int(s)

        if not poke_id:
            continue

        nom = ID_TO_NAME.get(poke_id, s.capitalize())
        if nom not in nombres_oficiales:
            nombres_oficiales.append(nom)

        fam_ids = [poke_id]
        if incluir_familia:
            if s in FAMILIAS_POKEDEX:
                fam_ids = FAMILIAS_POKEDEX[s]
            elif s_norm in FAMILIAS_POKEDEX:
                fam_ids = FAMILIAS_POKEDEX[s_norm]
            else:
                for f_slug, f_ids in FAMILIAS_POKEDEX.items():
                    if poke_id in f_ids:
                        fam_ids = f_ids
                        break
        for fid in fam_ids:
            if fid not in ids_totales:
                ids_totales.append(fid)

    if not ids_totales:
        await interaction.response.send_message(
            f"❌ No se reconoció ningún Pokémon válido en `{nombre}`. Puedes usar nombres de la Pokédex (ej. Charmander, Beldum, Ralts).",
            ephemeral=True
        )
        return

    nombres_completos = [ID_TO_NAME.get(i, f"#{i}") for i in ids_totales]
    titulo_evento = "Evento: " + ", ".join(nombres_oficiales[:3])
    if len(nombres_oficiales) > 3:
        titulo_evento += f" (+{len(nombres_oficiales) - 3})"

    cfg_ev = cargar_config_evento()
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
    fases_txt = "con toda su línea evolutiva" if incluir_familia else "solo especies seleccionadas"

    await interaction.response.send_message(
        f"✅ **Radar de Eventos configurado para {len(nombres_oficiales)} Pokémon:**\n"
        f"• 📋 **Especies seleccionadas:** **{resumen_pokes}** ({fases_txt} • {len(ids_totales)} IDs)\n"
        f"• 🎯 **Ligas:** Shundo 100% (`{shundo}`) | Great League (`{pvp_gl}`) | Ultra League (`{pvp_ul}`)\n"
        f"• ⚡ **Escaneo forzado iniciado de inmediato en `#🎉-evento-cd`...**",
        ephemeral=True
    )


@bot.tree.command(
    name="preset",
    description="📦 Activa un paquete temático preconfigurado de Pokémon populares o del Meta."
)
@app_commands.describe(opcion="Elige el paquete temático que deseas activar")
@app_commands.autocomplete(opcion=autocomplete_presets)
async def cmd_preset(interaction: discord.Interaction, opcion: str):
    datos_preset = obtener_preset(opcion)
    if not datos_preset:
        await interaction.response.send_message(
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

    await interaction.response.send_message(
        f"✅ **Preset Activado:** **{datos_preset['titulo']}**\n"
        f"• 📋 **Pokémon rastreados:** `{len(ids_res)} especies`\n"
        f"• ⚡ **Escaneo inmediato iniciado en `#🎉-evento-cd`...**",
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
        await interaction.response.send_message("🛑 **Canal de Eventos & CD apagado.** No se enviarán alertas hasta activar una especie.", ephemeral=True)
    else:
        cfg_ctrl = cargar_config_control()
        cfg_ctrl["pausa_global"] = True
        guardar_config_control(cfg_ctrl)
        publicar_o_actualizar_panel_maestro()
        sincronizar_estado_remoto_push(asincrono=True)
        await interaction.response.send_message("⏸️ **Radar pausado globalmente.** No se enviarán alertas en ningún canal.", ephemeral=True)


@bot.tree.command(
    name="reanudar",
    description="▶️ Reanuda el radar si estaba pausado globalmente."
)
async def cmd_reanudar(interaction: discord.Interaction):
    cfg_ctrl = cargar_config_control()
    cfg_ctrl["pausa_global"] = False
    guardar_config_control(cfg_ctrl)
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)
    await interaction.response.send_message("▶️ **Radar reanudado.** El escaneo 24/7 en todos los canales activos continúa normalmente.", ephemeral=True)


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
    cfg_ctrl = cargar_config_control()
    cfg_ctrl["intervalo_minutos"] = minutos
    guardar_config_control(cfg_ctrl)
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)
    await interaction.response.send_message(f"⏱️ **Intervalo de escaneo actualizado:** `{minutos} minutos`.", ephemeral=True)


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
    cfg_ctrl = cargar_config_control()
    canales = cfg_ctrl.setdefault("canales", {"shundo": True, "great": True, "ultra": True, "evento": True})
    activar = (estado == "on")
    canales[canal] = activar
    guardar_config_control(cfg_ctrl)
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)

    nombres = {"shundo": "Shundos 100% IV", "great": "Great League", "ultra": "Ultra League", "evento": "Eventos & CD"}
    tag = "🟢 Activado" if activar else "🔴 Pausado"
    await interaction.response.send_message(f"{tag}: Canal **{nombres.get(canal, canal)}**.", ephemeral=True)


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
    cfg_ctrl = cargar_config_control()
    cfg_ctrl["pvp_top_rank"] = top
    guardar_config_control(cfg_ctrl)
    publicar_o_actualizar_panel_maestro()
    sincronizar_estado_remoto_push(asincrono=True)
    await interaction.response.send_message(f"🏆 **Filtro PvP actualizado:** Recibirás spawns de `Rank #1 al #{top}`.", ephemeral=True)


@bot.tree.command(
    name="scan",
    description="⚡ Dispara un escaneo global forzado en todos los canales en este segundo."
)
async def cmd_scan(interaction: discord.Interaction):
    await interaction.response.send_message("⚡ **Escaneo global forzado iniciado.** Buscando nuevos spawns en los 5 continentes...", ephemeral=True)
    if _CALLBACK_ESCANEO_GLOBAL:
        threading.Thread(target=_CALLBACK_ESCANEO_GLOBAL, daemon=True).start()


@bot.tree.command(
    name="panel",
    description="🎛️ Muestra o refresca el Panel Maestro de Control en #🎛️-panel-control."
)
async def cmd_panel(interaction: discord.Interaction):
    mid = publicar_o_actualizar_panel_maestro()
    await interaction.response.send_message("✅ **Panel Maestro de Control actualizado en `#🎛️-panel-control`**.", ephemeral=True)


@bot.tree.command(
    name="cuotas",
    description="📊 Muestra el estado en vivo de tus 3 cuentas del Pool de reveals exactos."
)
async def cmd_cuotas(interaction: discord.Interaction):
    resumen = obtener_resumen_cuentas_pool()
    embed = discord.Embed(
        title="🔑 Estado del Pool de Cuentas (3 Cuentas)",
        description=f"```\n{resumen}\n```\nCapacidad total: **30 reveals exactos por hora**.",
        color=0x2563EB,
        timestamp=datetime.now(timezone.utc)
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


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
