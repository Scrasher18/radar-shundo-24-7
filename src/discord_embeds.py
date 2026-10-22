"""
Constructores desacoplados de Embeds para Discord:
- Shundos 100% IV
- PvP Great League (1500 CP, Rank #1-#5)
- PvP Ultra League (2500 CP, Rank #1-#5)
- Actualización en tiempo real del contador de segundos restantes
"""

import copy
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple


def obtener_etiquetas_rareza(mon: Dict[str, Any], etiqueta_base: str = "✨ **SHUNDO 100% IV**") -> str:
    """Genera las insignias de rareza (Fondo Especial, Disfraz, Talla XXL/XXS, Clima)."""
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


def construir_estado_despawn(mon: Dict[str, Any]) -> Tuple[str, int]:
    """Construye el texto del semáforo de urgencia y el contador con minutos y segundos exactos."""
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

    if despawn_unix:
        estado_tiempo = f"{semaforo}\n⏱️ **Desaparece:** <t:{despawn_unix}:R> (`{ttl_con_segundos}`)\n🕒 **Hora exacta:** <t:{despawn_unix}:T>"
    else:
        estado_tiempo = f"{semaforo}\n⏱️ **Desaparece en:** `{ttl_con_segundos}`"
    return estado_tiempo, color_urgencia


def construir_embed_shundo(mon: Dict[str, Any]) -> Dict[str, Any]:
    """Construye el Embed de Discord para un Pokémon Shundo 100% IV."""
    origen_txt = "☁️ Nube 24/7"
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
            {
                "name": "📊 Estadísticas",
                "value": f"**IV:** `100% (15/15/15)`\n**CP:** `{cp}` | **Nivel:** `{nivel}`\n**Talla:** `{size}` ({gender})",
                "inline": True,
            },
            {"name": "⏳ Estado Despawn", "value": estado_tiempo, "inline": True},
            {"name": "📍 Ubicación", "value": f"{ubicacion} • [🗺️ Ver en Google Maps]({maps_url})", "inline": False},
            {"name": "🎯 Coordenadas Exactas", "value": f"```\n{coords}\n```", "inline": False},
        ],
        "footer": {"text": f"Radar Shundo Pro ({origen_txt}) • Se eliminará automáticamente al desaparecer"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def construir_embed_pvp(mon: Dict[str, Any], league: str) -> Dict[str, Any]:
    """Construye el Embed de Discord para un Pokémon Shiny Top 1-5 de Great League o Ultra League."""
    origen_txt = "☁️ Nube 24/7"
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
    pvp_pct = float(pvp.get("percent") or 100.0)

    es_gl = league == "great"
    liga_nombre = "🔵 GREAT LEAGUE (1500 CP)" if es_gl else "🟣 ULTRA LEAGUE (2500 CP)"
    color_liga = 0x3B82F6 if es_gl else 0xA855F7
    medalla_rank = "🥇 **RANK #1 (100% STAT PRODUCT)**" if rank == 1 else f"🏆 **RANK #{rank}** (`{pvp_pct:.2f}%` PvP)"

    try:
        requiere_xl = float(pvp_lvl) > 40.0
    except Exception:
        requiere_xl = False
    etiqueta_xl = "🍬 **REQUIERE CARAMELOS XL**" if requiere_xl else "✅ **SIN CARAMELOS XL (≤ Nivel 40)**"
    coste_xl_corto = "🍬 Sí (> Nivel 40)" if requiere_xl else "✅ No (≤ Nivel 40)"

    evolucion_txt = (
        f"🔄 **Para Liga:** Evolucionar a **{pvp_poke_name}** (`CP {pvp_cp}` a Nivel `{pvp_lvl}`)"
        if int(pvp_poke_id) != int(poke_id)
        else f"⚔️ **En Liga:** **{pvp_poke_name}** alcanza `CP {pvp_cp}` en Nivel `{pvp_lvl}`"
    )

    icon_url = f"https://raw.githubusercontent.com/PokeMiners/pogo_assets/master/Images/Pokemon/Addressable%20Assets/pm{pvp_poke_id}.s.icon.png"
    estado_tiempo, _ = construir_estado_despawn(mon)
    rareza_txt = obtener_etiquetas_rareza(mon, f"✨ **SHINY GARANTIZADO** • {medalla_rank} • {etiqueta_xl}")

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
                    f"**Final en Liga:** `CP {pvp_cp}` | `Nivel {pvp_lvl}`\n"
                    f"**Caramelos XL:** `{coste_xl_corto}`"
                ),
                "inline": True,
            },
            {"name": "⏳ Estado Despawn", "value": estado_tiempo, "inline": True},
            {"name": "📍 Ubicación", "value": f"{ubicacion} • [🗺️ Ver en Google Maps]({maps_url})", "inline": False},
            {"name": "🎯 Coordenadas Exactas", "value": f"```\n{coords}\n```", "inline": False},
        ],
        "footer": {"text": f"Radar PvP Shiny Pro ({origen_txt}) • Se eliminará automáticamente al desaparecer"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def actualizar_embed_con_segundos_reales(
    embed_base: Dict[str, Any],
    despawn_unix: int,
    canal_tipo: str
) -> Dict[str, Any]:
    """Recalcula los segundos exactos restantes hasta despawn_unix y actualiza el campo Estado Despawn."""
    ahora_actual = int(time.time())
    seg_rest = max(0, int(despawn_unix) - ahora_actual)
    estado_tiempo, color_urgencia = construir_estado_despawn(
        {"ttl_segundos": seg_rest, "despawn_unix": despawn_unix}
    )
    nuevo_embed = copy.deepcopy(embed_base)
    if canal_tipo == "shundo":
        nuevo_embed["color"] = color_urgencia
    for field in nuevo_embed.get("fields", []):
        if "Estado Despawn" in str(field.get("name", "")):
            field["value"] = estado_tiempo
            break
    return nuevo_embed
