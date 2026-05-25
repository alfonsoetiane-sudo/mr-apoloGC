"""
Mr. Apolo — Servidor Principal (FastAPI + Railway)
===================================================
Punto de entrada del servidor. Maneja:
- Webhook de WhatsApp (Meta Cloud API)
- Scheduler diario a las 7am CDMX
- Endpoint para disparar el pipeline manualmente

Deploy en Railway: conecta este repo, Railway detecta el Procfile automáticamente.
"""

import os
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from pipeline import ejecutar_pipeline, procesar_respuesta, enviar_post2_tarde
from whatsapp_client import extraer_mensaje, enviar_texto

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

WA_VERIFY_TOKEN  = os.environ.get("WHATSAPP_VERIFY_TOKEN", "mrapolo_webhook_2026")
SALES_AGENT_URL  = os.environ.get("SALES_AGENT_WEBHOOK_URL", "https://mr-apolo-production.up.railway.app/webhook")

# Prefijos que pertenecen al pipeline de contenido
CONTENT_PREFIXES = ("✅", "❌", "✏️")

# ─────────────────────────────────────────
# SCHEDULER — Corre el pipeline diario
# ─────────────────────────────────────────

scheduler = AsyncIOScheduler(timezone="America/Mexico_City")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Job 1: genera ambos posts y envía Post 1 a las 7am
    scheduler.add_job(
        ejecutar_pipeline,
        CronTrigger(hour=7, minute=0, timezone="America/Mexico_City"),
        id="pipeline_manana",
        replace_existing=True,
    )
    # Job 2: envía Post 2 a las 7pm (el que quedó guardado desde la mañana)
    scheduler.add_job(
        enviar_post2_tarde,
        CronTrigger(hour=19, minute=0, timezone="America/Mexico_City"),
        id="pipeline_tarde",
        replace_existing=True,
    )
    scheduler.start()
    log.info("✅ Scheduler iniciado — Post 1 a las 7:00am · Post 2 a las 7:00pm CDMX")
    yield
    scheduler.shutdown()


# ─────────────────────────────────────────
# APP
# ─────────────────────────────────────────

app = FastAPI(title="Mr. Apolo Content Pipeline", lifespan=lifespan)


@app.get("/")
def root():
    return {"status": "🐾 Mr. Apolo Pipeline corriendo", "scheduler": scheduler.running}


# ─────────────────────────────────────────
# WEBHOOK DE WHATSAPP
# ─────────────────────────────────────────

@app.get("/webhook")
def verificar_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None,
):
    """Meta llama a este endpoint para verificar el webhook."""
    if hub_mode == "subscribe" and hub_verify_token == WA_VERIFY_TOKEN:
        log.info("✅ Webhook verificado por Meta")
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


@app.post("/webhook")
async def recibir_mensaje(request: Request):
    """
    Recibe todos los mensajes de WhatsApp.
    - Si empieza con ✅, ❌ o ✏️ → lo procesa el pipeline de contenido.
    - Cualquier otro mensaje → se reenvía al agente de ventas.
    """
    data = await request.json()
    body_bytes = await request.body()
    log.info(f"📩 Webhook recibido: {str(data)[:200]}")

    mensaje = extraer_mensaje(data)

    if mensaje:
        if mensaje.startswith(CONTENT_PREFIXES):
            # Es una respuesta al pipeline de contenido
            log.info(f"🎯 Mensaje de contenido capturado: {mensaje}")
            asyncio.create_task(procesar_respuesta(mensaje))
        else:
            # Reenviar al agente de ventas
            log.info(f"➡️  Reenviando al agente de ventas: {mensaje[:50]}")
            asyncio.create_task(_reenviar_al_agente(data))
    else:
        # Sin texto (puede ser imagen, audio, etc.) → reenviar al agente
        asyncio.create_task(_reenviar_al_agente(data))

    return {"status": "ok"}


async def _reenviar_al_agente(data: dict):
    """Reenvía el mensaje al agente de ventas de forma asíncrona."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(SALES_AGENT_URL, json=data)
            log.info("✅ Mensaje reenviado al agente de ventas")
    except Exception as e:
        log.error(f"❌ Error reenviando al agente de ventas: {e}")


# ─────────────────────────────────────────
# ENDPOINTS DE CONTROL MANUAL
# ─────────────────────────────────────────

@app.post("/pipeline/run")
async def correr_pipeline_manual(secret: str = ""):
    """Dispara el pipeline manualmente. Útil para probar sin esperar las 7am."""
    if secret != os.environ.get("ADMIN_SECRET", "mrapolo2026"):
        raise HTTPException(status_code=401, detail="No autorizado")
    asyncio.create_task(ejecutar_pipeline())
    return {"status": "Pipeline iniciado en background"}


@app.get("/pipeline/estado")
def ver_estado(secret: str = ""):
    """Muestra el estado actual del pipeline (posts pendientes)."""
    if secret != os.environ.get("ADMIN_SECRET", "mrapolo2026"):
        raise HTTPException(status_code=401, detail="No autorizado")
    import sheets_storage
    estado = sheets_storage.cargar_estado()
    if not estado:
        return {"status": "Sin pipeline activo hoy"}
    try:
        return estado
    except Exception as e:
        return {"status": "Error leyendo estado", "error": str(e)}