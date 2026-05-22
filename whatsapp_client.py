"""
Mr. Apolo — Cliente de WhatsApp (Meta Cloud API)
=================================================
Maneja el envío y recepción de mensajes via Meta WhatsApp Business API.
"""

import os
import requests

WA_TOKEN     = os.environ.get("WHATSAPP_TOKEN")       # Token de acceso de Meta
WA_PHONE_ID  = os.environ.get("WHATSAPP_PHONE_ID")    # ID del número de WhatsApp Business
WA_TO        = os.environ.get("WHATSAPP_TO")          # Tu número personal (con código de país, ej: 521XXXXXXXXXX)
BASE_URL     = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {WA_TOKEN}",
    "Content-Type": "application/json",
}


def enviar_texto(mensaje: str) -> dict:
    """Envía un mensaje de texto simple."""
    payload = {
        "messaging_product": "whatsapp",
        "to": WA_TO,
        "type": "text",
        "text": {"body": mensaje}
    }
    resp = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def enviar_imagen_con_caption(imagen_b64: str, caption: str) -> dict:
    """
    Sube una imagen en base64 y la envía por WhatsApp con caption.
    Meta requiere subir la imagen primero como media, luego enviarla.
    """
    import base64

    # Paso 1: Subir la imagen a Meta Media API
    upload_url = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/media"
    img_bytes = base64.b64decode(imagen_b64) if isinstance(imagen_b64, str) else imagen_b64

    upload_resp = requests.post(
        upload_url,
        headers={"Authorization": f"Bearer {WA_TOKEN}"},
        files={"file": ("post.png", img_bytes, "image/png")},
        data={"messaging_product": "whatsapp"},
        timeout=30,
    )
    upload_resp.raise_for_status()
    media_id = upload_resp.json()["id"]

    # Paso 2: Enviar la imagen con caption
    payload = {
        "messaging_product": "whatsapp",
        "to": WA_TO,
        "type": "image",
        "image": {
            "id": media_id,
            "caption": caption,
        }
    }
    resp = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def enviar_imagen_desde_archivo(ruta_archivo: str, caption: str) -> dict:
    """Envía una imagen desde archivo local."""
    with open(ruta_archivo, "rb") as f:
        img_bytes = f.read()

    upload_url = f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/media"
    upload_resp = requests.post(
        upload_url,
        headers={"Authorization": f"Bearer {WA_TOKEN}"},
        files={"file": ("post.png", img_bytes, "image/png")},
        data={"messaging_product": "whatsapp"},
        timeout=30,
    )
    upload_resp.raise_for_status()
    media_id = upload_resp.json()["id"]

    payload = {
        "messaging_product": "whatsapp",
        "to": WA_TO,
        "type": "image",
        "image": {"id": media_id, "caption": caption}
    }
    resp = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def extraer_mensaje(webhook_data: dict) -> str | None:
    """Extrae el texto del mensaje recibido desde el webhook de Meta."""
    try:
        entry = webhook_data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        message = value["messages"][0]
        return message.get("text", {}).get("body", "").strip()
    except (KeyError, IndexError):
        return None
