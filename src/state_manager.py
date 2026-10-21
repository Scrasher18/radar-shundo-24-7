"""
Gestor Thread-Safe de estado persistente, caché de coordenadas, deduplicación doble
y sincronización no bloqueante con GitHub (origin/main).
"""

import json
import os
import subprocess
import threading
import time
from typing import Any, Dict

from src.config import (
    BASE_DIR,
    CACHE_FILE,
    ES_MODO_NUBE,
    NOTIFICADOS_FILE,
    TTL_LIMPIEZA_CACHE_SEGUNDOS,
)

_LOCK_ESTADO = threading.RLock()
_LOCK_GIT = threading.Lock()


def cargar_json(ruta: str) -> Dict[str, Any]:
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def guardar_json(ruta: str, datos: Dict[str, Any]) -> None:
    with _LOCK_ESTADO:
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def limpiar_diccionario_notificados(notificados: Dict[str, Any]) -> Dict[str, Any]:
    """Elimina registros antiguos (>2h) o ya borrados de Discord hace más de 1h para mantener el JSON ligero."""
    ahora = int(time.time())
    limpio: Dict[str, Any] = {}
    for k, v in notificados.items():
        if k.startswith("_meta_"):
            limpio[k] = v
            continue
        if not isinstance(v, dict):
            continue
        edad = ahora - int(v.get("ts", ahora))
        ya_borrado = bool(v.get("eliminado_de_discord", False))
        if edad > TTL_LIMPIEZA_CACHE_SEGUNDOS:
            continue
        if ya_borrado and edad > 3600:
            continue
        limpio[k] = v
    return limpio


def limpiar_archivos_antiguos(cache_coords: Dict[str, Any], notificados: Dict[str, Any]) -> None:
    """Purga en sitio entradas antiguas tanto de caché de coordenadas como de notificados."""
    ahora = int(time.time())
    claves_borrar_cache = [
        k for k, v in cache_coords.items()
        if isinstance(v, dict) and (ahora - int(v.get("ts", ahora))) > TTL_LIMPIEZA_CACHE_SEGUNDOS
    ]
    for k in claves_borrar_cache:
        del cache_coords[k]

    limpios = limpiar_diccionario_notificados(notificados)
    notificados.clear()
    notificados.update(limpios)


def fusionar_notificados(base_dict: Dict[str, Any], nuevo_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Fusiona diccionarios de notificados preservando todos los discord_msg_ids y estados de borrado."""
    base_limpio = limpiar_diccionario_notificados(base_dict)
    nuevo_limpio = limpiar_diccionario_notificados(nuevo_dict)
    resultado = dict(base_limpio)

    for k, v in nuevo_limpio.items():
        if k not in resultado or not isinstance(v, dict) or not isinstance(resultado.get(k), dict):
            resultado[k] = v
        else:
            prev = resultado[k]
            mids = []
            for m in (
                (prev.get("discord_msg_ids") or [])
                + [prev.get("discord_msg_id")]
                + (v.get("discord_msg_ids") or [])
                + [v.get("discord_msg_id")]
            ):
                if m and m not in mids:
                    mids.append(m)
            combinado = {**prev, **v}
            if mids:
                combinado["discord_msg_id"] = mids[-1]
                combinado["discord_msg_ids"] = mids
            combinado["eliminado_de_discord"] = bool(
                prev.get("eliminado_de_discord") or v.get("eliminado_de_discord")
            )
            resultado[k] = combinado
    return limpiar_diccionario_notificados(resultado)


def sincronizar_estado_remoto_pull() -> None:
    """Descarga y fusiona el estado más reciente desde origin/main."""
    if not ES_MODO_NUBE:
        return
    with _LOCK_GIT:
        try:
            subprocess.run(["git", "fetch", "origin", "main"], cwd=BASE_DIR, timeout=15, capture_output=True)
            r_notif = subprocess.run(
                ["git", "show", "origin/main:shundos_notificados.json"],
                cwd=BASE_DIR,
                text=True,
                capture_output=True,
                encoding="utf-8",
                timeout=10,
            )
            if r_notif.returncode == 0:
                with _LOCK_ESTADO:
                    remoto_notif = json.loads(r_notif.stdout)
                    local_notif = cargar_json(NOTIFICADOS_FILE)
                    guardar_json(NOTIFICADOS_FILE, fusionar_notificados(remoto_notif, local_notif))
        except Exception:
            pass


def _worker_git_push() -> None:
    if not ES_MODO_NUBE:
        return
    if not _LOCK_GIT.acquire(blocking=False):
        return
    try:
        subprocess.run(["git", "fetch", "origin", "main"], cwd=BASE_DIR, timeout=15, capture_output=True)
        r_notif = subprocess.run(
            ["git", "show", "origin/main:shundos_notificados.json"],
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            encoding="utf-8",
            timeout=10,
        )
        if r_notif.returncode == 0:
            with _LOCK_ESTADO:
                remoto_notif = json.loads(r_notif.stdout)
                local_notif = cargar_json(NOTIFICADOS_FILE)
                guardar_json(NOTIFICADOS_FILE, fusionar_notificados(remoto_notif, local_notif))

        subprocess.run(["git", "reset", "--soft", "origin/main"], cwd=BASE_DIR, timeout=10, capture_output=True)
        subprocess.run(
            ["git", "add", "shundos_notificados.json", "cache_coordenadas.json"],
            cwd=BASE_DIR,
            timeout=10,
            capture_output=True,
        )
        diff = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=BASE_DIR, timeout=10)
        if diff.returncode != 0:
            subprocess.run(
                ["git", "commit", "-m", "chore: sync estado en vivo [skip ci]"],
                cwd=BASE_DIR,
                timeout=10,
                capture_output=True,
            )
            subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, timeout=20, capture_output=True)
    except Exception:
        pass
    finally:
        _LOCK_GIT.release()


def sincronizar_estado_remoto_push(asincrono: bool = True) -> None:
    """Sube el estado actualizado a origin/main en segundo plano sin bloquear el reloj de 1 segundo."""
    if not ES_MODO_NUBE:
        return
    if asincrono:
        threading.Thread(target=_worker_git_push, daemon=True).start()
    else:
        _worker_git_push()


def ya_fue_notificado(mon: Dict[str, Any], canal_tipo: str, notificados: Dict[str, Any]) -> bool:
    """Doble filtro anti-duplicados: verifica por encounter_id y por especie + coordenadas cercanas."""
    eid = str(mon.get("encounter_id"))
    if f"{canal_tipo}:{eid}" in notificados:
        return True
    if canal_tipo == "shundo" and eid in notificados:
        return True

    ahora = int(time.time())
    nombre = mon.get("nombre_completo") or mon.get("pokemon_name")
    lat = mon.get("lat_final")
    lng = mon.get("lng_final")

    for k, info in notificados.items():
        if k.startswith("_meta_") or not isinstance(info, dict):
            continue
        if info.get("canal", "shundo") != canal_tipo:
            continue
        if (ahora - int(info.get("ts", 0))) > 3600:
            continue
        if info.get("pokemon") == nombre and lat is not None and lng is not None:
            coords_prev = str(info.get("coords") or "")
            if "," in coords_prev:
                try:
                    plat, plng = map(float, coords_prev.split(",", 1))
                    if abs(lat - plat) <= 0.008 and abs(lng - plng) <= 0.008:
                        return True
                except Exception:
                    pass
    return False
