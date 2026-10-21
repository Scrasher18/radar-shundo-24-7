"""
Punto de entrada principal (CLI / Cloud Runner 24/7) para el Radar Pro Multi-Canal.
Delega la lógica a la arquitectura modular ubicada en el paquete `src/`.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import (  # noqa: F401, E402
    CACHE_FILE,
    DISCORD_WEBHOOK_GL,
    DISCORD_WEBHOOK_UL,
    DISCORD_WEBHOOK_URL,
    INTERVALO_SEGUNDOS,
    NOTIFICADOS_FILE,
    PVP_TOP_RANK_MAX,
    WEBHOOKS_POR_CANAL,
)
from src.discord_service import (  # noqa: F401, E402
    eliminar_mensajes_expirados_discord,
    iniciar_hilos_reloj_tiempo_real,
    procesar_canal_discord,
)
from src.scanner_engine import (  # noqa: F401, E402
    ejecutar_ciclo_radar,
    esperar_con_limpieza_despawn,
    iniciar_radar,
)
from src.state_manager import (  # noqa: F401, E402
    cargar_json,
    fusionar_notificados,
    guardar_json,
    limpiar_archivos_antiguos,
    sincronizar_estado_remoto_pull,
    sincronizar_estado_remoto_push,
    ya_fue_notificado,
)

if __name__ == "__main__":
    iniciar_radar()
