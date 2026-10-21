# 🌍 Radar Pro Multi-Canal 24/7 (Shundos 100% + PvP Great League + Ultra League)

Arquitectura modular en Python diseñada para ejecutarse **24/7 en la nube (GitHub Actions)** con relojes de cuenta regresiva en tiempo real (`1s`) y auto-eliminación automática de Pokémon desaparecidos en Discord.

## 🏗️ Estructura del Proyecto

```text
├── .github/
│   └── workflows/
│       └── radar_24_7.yml       # Pipeline 24/7 auto-encadenado en GitHub Actions
├── src/                         # Paquete modular (Clean Architecture)
│   ├── __init__.py
│   ├── config.py                # Configuración centralizada, constantes, regiones y webhooks
│   ├── models.py                # Cálculos geográficos (Haversine), tiempos de despawn y normalización
│   ├── api_client.py            # Cliente HTTP con Connection Pooling para /search, /map/lookup y /reveal
│   ├── discord_embeds.py        # Constructores de tarjetas Embed y semáforo dinámico en tiempo real
│   ├── discord_service.py       # Servicio multihilo: 3 hilos dedicados (1s) con sesiones Keep-Alive y auto-delete
│   ├── state_manager.py         # Gestión Thread-Safe de estado, deduplicación doble y Git Sync asíncrono
│   └── scanner_engine.py        # Orquestador del escaneo mundial por oleadas y ciclo continuo
├── radar.py                     # Punto de entrada principal (compatible con CLI y GitHub Actions)
├── requirements.txt             # Dependencias del sistema
├── cache_coordenadas.json       # Caché persistente de coordenadas reveladas
└── shundos_notificados.json     # Registro sincronizado de spawns activos y mensajes de Discord
```

## ✨ Características Principales

1. **Escaneo Mundial Multi-Canal (cada 8 minutos):**
   - 🌟 **Canal 1:** Shundos (`100% IV + Shiny`).
   - 🔵 **Canal 2:** PvP Great League (`1500 CP` — `Rank #1 al #5 Shiny`).
   - 🟣 **Canal 3:** PvP Ultra League (`2500 CP` — `Rank #1 al #5 Shiny`).
2. **Reloj en Tiempo Real (`1s`) Independiente por Canal:**
   - 3 hilos `daemon` dedicados (uno por webhook) con sesiones HTTP persistentes (`Keep-Alive`) actualizan `⏱️ Desaparece en: X min Y seg` segundo a segundo sin bloquearse durante los escaneos ni los commits.
3. **Auto-Eliminación Instantánea:**
   - Al llegar el contador a `0 min 00 seg`, el mensaje es eliminado automáticamente de su canal de Discord (`DELETE`).
4. **Deduplicación Doble y Sincronización Asíncrona:**
   - Evita alertas repetidas verificando tanto `encounter_id` como especie + coordenadas cercanas en una ventana de 60 minutos.
