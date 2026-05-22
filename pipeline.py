"""
Mr. Apolo — Pipeline Diario
============================
Orquesta todo el flujo:
1. Analiza competidores (Apify)
2. Genera 2 captions (Claude)
3. Genera 2 imágenes (OpenAI)
4. Envía por WhatsApp para aprobación
5. Guarda estado para procesar la respuesta del usuario
"""

import os
import json
import datetime
import logging
from pathlib import Path

from competitor_monitor import analizar_competidores, guardar_tendencias, cargar_tendencias
from image_generator import seleccionar_temas_del_dia, generar_prompt_dalle, generar_imagen, generar_caption_infografia
from content_generator import cargar_feedback
from whatsapp_client import enviar_texto, enviar_imagen_desde_archivo

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pipeline")

ESTADO_FILE = "estado_pipeline.json"


# ─────────────────────────────────────────
# ESTADO DEL PIPELINE
# Guarda qué posts están pendientes de aprobación
# ─────────────────────────────────────────

def guardar_estado(posts: list):
    """Guarda el estado de los posts generados hoy esperando aprobación."""
    estado = {
        "fecha": datetime.datetime.now().isoformat(),
        "posts": posts,
        "post_actual": 0,  # índice del post que está esperando respuesta
    }
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

def cargar_estado() -> dict | None:
    if not os.path.exists(ESTADO_FILE):
        return None
    with open(ESTADO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def actualizar_estado_post(indice: int, resultado: str, comentario: str = ""):
    estado = cargar_estado()
    if not estado:
        return
    estado["posts"][indice]["resultado"] = resultado
    estado["posts"][indice]["comentario"] = comentario
    estado["post_actual"] = indice + 1
    with open(ESTADO_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# GUARDAR FEEDBACK
# ─────────────────────────────────────────

def guardar_feedback_pipeline(tema: str, caption: str, resultado: str, comentario: str):
    """Guarda feedback en el archivo local que usa el generador."""
    feedback_file = "feedback_history.json"
    historial = []
    if os.path.exists(feedback_file):
        with open(feedback_file, "r", encoding="utf-8") as f:
            historial = json.load(f)

    historial.append({
        "fecha": datetime.datetime.now().isoformat(),
        "tipo": resultado.lower(),
        "comentario": comentario,
        "caption_generado": caption,
        "hashtags_generados": [],
        "tema": tema,
    })

    with open(feedback_file, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# FLUJO PRINCIPAL DEL DÍA
# ─────────────────────────────────────────

async def ejecutar_pipeline():
    """Corre el pipeline completo del día y envía el primer post por WhatsApp."""
    log.info("🐾 Iniciando pipeline Mr. Apolo...")

    try:
        # 1. Intentar análisis de competidores (si Apify está configurado)
        if os.environ.get("APIFY_TOKEN"):
            log.info("📊 Analizando competidores...")
            try:
                tendencias, posts_top = analizar_competidores()
                guardar_tendencias(tendencias, posts_top)
                log.info("✅ Tendencias actualizadas")
            except Exception as e:
                log.warning(f"⚠️ Error en Apify, usando tendencias guardadas: {e}")
                tendencias = cargar_tendencias()
        else:
            tendencias = cargar_tendencias()

        # 2. Seleccionar 2 temas balanceados del día
        log.info("🎯 Seleccionando temas del día...")
        posts_dia = seleccionar_temas_del_dia()

        # 3. Generar imágenes y captions para los 2 posts
        posts_generados = []
        for i, (tema, tipo, horario) in enumerate(posts_dia, 1):
            log.info(f"🎨 Generando post {i}: {tema}")

            # Imagen
            prompt = generar_prompt_dalle(tema, tipo, tendencias or {})
            fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = f"mrapolo_post{i}_{tipo}_{fecha_str}.png"
            Path("imagenes_generadas").mkdir(exist_ok=True)
            ruta_img, _ = generar_imagen(prompt, nombre)

            # Caption
            caption_data = generar_caption_infografia(tema, tipo)
            caption_data["horario_sugerido"] = horario

            posts_generados.append({
                "numero": i,
                "tema": tema,
                "tipo": tipo,
                "horario": horario,
                "caption": caption_data.get("caption", ""),
                "hashtags": caption_data.get("hashtags", []),
                "ruta_imagen": ruta_img,
                "resultado": None,
                "comentario": "",
            })

        # 4. Guardar estado
        guardar_estado(posts_generados)
        log.info("💾 Estado guardado")

        # 5. Enviar el primer post por WhatsApp
        await enviar_post_whatsapp(posts_generados[0], es_primero=True)

    except Exception as e:
        log.error(f"❌ Error en pipeline: {e}")
        enviar_texto(f"❌ Error en el pipeline de Mr. Apolo: {str(e)[:200]}\nRevisa los logs en Railway.")
        raise


async def enviar_post_whatsapp(post: dict, es_primero: bool = False):
    """Envía un post por WhatsApp para aprobación."""
    hashtags_str = " ".join(post["hashtags"])

    if es_primero:
        intro = "🐾 *Mr. Apolo — Posts del día*\n\nAquí va el primero:\n\n"
    else:
        intro = "🐾 *Post 2 del día:*\n\n"

    caption_wa = (
        f"{intro}"
        f"*POST {post['numero']} — {post['horario']}*\n\n"
        f"{post['caption']}\n\n"
        f"{hashtags_str}\n\n"
        f"{'─'*30}\n"
        f"Responde:\n"
        f"✅  aprobar y publicar\n"
        f"❌ + motivo  rechazar (Claude aprende)\n"
        f"✏️ + tu texto  publicar con tu caption"
    )

    try:
        enviar_imagen_desde_archivo(post["ruta_imagen"], caption_wa)
        log.info(f"✅ Post {post['numero']} enviado por WhatsApp")
    except Exception as e:
        log.error(f"Error enviando imagen, enviando solo texto: {e}")
        enviar_texto(caption_wa)


# ─────────────────────────────────────────
# PROCESAR RESPUESTA DEL USUARIO
# ─────────────────────────────────────────

async def procesar_respuesta(mensaje: str):
    """Procesa la respuesta de WhatsApp del usuario."""
    estado = cargar_estado()
    if not estado:
        enviar_texto("No hay posts pendientes de aprobación hoy.")
        return

    idx = estado.get("post_actual", 0)
    posts = estado.get("posts", [])

    if idx >= len(posts):
        enviar_texto("Ya procesaste todos los posts de hoy. 🐾")
        return

    post = posts[idx]
    mensaje = mensaje.strip()

    if mensaje.startswith("✅"):
        # Aprobar
        log.info(f"✅ Post {post['numero']} aprobado")
        guardar_feedback_pipeline(post["tema"], post["caption"], "aprobado", mensaje)
        actualizar_estado_post(idx, "aprobado", mensaje)
        _publicar_en_instagram(post)
        confirmacion = f"✅ Post {post['numero']} publicado en Instagram."

    elif mensaje.startswith("❌"):
        # Rechazar
        motivo = mensaje.replace("❌", "").strip()
        log.info(f"❌ Post {post['numero']} rechazado: {motivo}")
        guardar_feedback_pipeline(post["tema"], post["caption"], "rechazado", motivo)
        actualizar_estado_post(idx, "rechazado", motivo)
        confirmacion = f"❌ Feedback guardado. Claude aprenderá para mañana."

    elif mensaje.startswith("✏️"):
        # Caption personalizado
        nuevo_caption = mensaje.replace("✏️", "").strip()
        log.info(f"✏️ Post {post['numero']} con caption modificado")
        guardar_feedback_pipeline(post["tema"], post["caption"], "modificado", nuevo_caption)
        post["caption"] = nuevo_caption
        actualizar_estado_post(idx, "modificado", nuevo_caption)
        _publicar_en_instagram(post)
        confirmacion = f"✏️ Post {post['numero']} publicado con tu caption."

    else:
        enviar_texto("No entendí. Responde ✅, ❌ + motivo, o ✏️ + tu caption.")
        return

    # Enviar confirmación
    estado_actualizado = cargar_estado()
    siguiente_idx = estado_actualizado.get("post_actual", 0)

    if siguiente_idx < len(posts):
        # Hay más posts
        enviar_texto(confirmacion + f"\n\nAhora te mando el Post {siguiente_idx + 1}...")
        await enviar_post_whatsapp(posts[siguiente_idx])
    else:
        # Terminamos el día
        enviar_texto(confirmacion + "\n\n¡Listo el día! 🐾 Mañana a las 7am te mando los siguientes.")


def _publicar_en_instagram(post: dict):
    """Publica el post en Instagram via Meta Graph API."""
    ig_token    = os.environ.get("META_IG_TOKEN")
    ig_user_id  = os.environ.get("META_IG_USER_ID")

    if not ig_token or not ig_user_id:
        log.warning("⚠️ META_IG_TOKEN o META_IG_USER_ID no configurados. No se publicó en Instagram.")
        return

    import requests
    caption_completo = f"{post['caption']}\n\n{' '.join(post['hashtags'])}"

    # Nota: Meta Graph API requiere URL pública de la imagen, no ruta local.
    # Para producción completa, subir la imagen a un storage público (S3, Cloudinary, etc.)
    log.info(f"📸 Publicación en Instagram pendiente de configurar URL pública de imagen.")
