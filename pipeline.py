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
import sheets_storage

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pipeline")


# ─────────────────────────────────────────
# ESTADO DEL PIPELINE (via Google Sheets)
# Persiste entre deploys y restarts de Railway
# ─────────────────────────────────────────

def guardar_estado(posts: list):
    """Guarda el estado de los posts generados hoy esperando aprobación."""
    estado = {
        "fecha": datetime.datetime.now().isoformat(),
        "posts": posts,
        "post_actual": 0,  # índice del post que está esperando respuesta
        "post2_enviado": False,  # evitar enviar el post 2 dos veces
    }
    sheets_storage.guardar_estado(estado)

def cargar_estado() -> dict | None:
    return sheets_storage.cargar_estado()

def actualizar_estado_post(indice: int, resultado: str, comentario: str = ""):
    estado = cargar_estado()
    if not estado:
        return
    estado["posts"][indice]["resultado"] = resultado
    estado["posts"][indice]["comentario"] = comentario
    estado["post_actual"] = indice + 1
    sheets_storage.guardar_estado(estado)


# ─────────────────────────────────────────
# GUARDAR FEEDBACK
# ─────────────────────────────────────────

def guardar_feedback_pipeline(tema: str, caption: str, resultado: str, comentario: str):
    """Guarda feedback en Google Sheets para que persista entre deploys de Railway."""
    entrada = {
        "fecha": datetime.datetime.now().isoformat(),
        "tipo": resultado.lower(),
        "comentario": comentario,
        "caption_generado": caption,
        "hashtags_generados": [],
        "tema": tema,
    }
    sheets_storage.agregar_feedback(entrada)


# ─────────────────────────────────────────
# FLUJO PRINCIPAL DEL DÍA
# ─────────────────────────────────────────

async def enviar_post2_tarde():
    """
    Corre a las 7pm CDMX.
    Envía el Post 2 que fue generado esta mañana a las 7am.
    Si el Post 1 todavía no fue aprobado, avisa al usuario.
    """
    log.info("🌙 Enviando Post 2 del día (7pm)...")
    estado = cargar_estado()

    if not estado:
        log.warning("⚠️ No hay pipeline activo hoy — ¿corrió el pipeline de las 7am?")
        enviar_texto("⚠️ No encontré posts generados para hoy. ¿Ocurrió algún error a las 7am?")
        return

    posts = estado.get("posts", [])
    if len(posts) < 2:
        log.warning("⚠️ Solo hay 1 post en el estado, no hay Post 2 para enviar")
        return

    # Verificar si el post 2 ya fue enviado antes
    if estado.get("post2_enviado"):
        log.info("ℹ️ Post 2 ya fue enviado antes, omitiendo")
        return

    post2 = posts[1]

    # Si el Post 1 todavía no fue resuelto, avisar
    if post2.get("resultado") is None and posts[0].get("resultado") is None:
        enviar_texto(
            "🕖 Son las 7pm — aquí va el segundo post del día.\n"
            "⚠️ Nota: aún no respondiste al Post 1 de esta mañana. "
            "Respóndelo cuando puedas para no perderlo.\n\n"
        )

    # Marcar como enviado en el estado antes de mandar (para evitar doble envío)
    estado["post2_enviado"] = True
    sheets_storage.guardar_estado(estado)

    await enviar_post_whatsapp(post2, es_primero=False)
    log.info("✅ Post 2 enviado a las 7pm")


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
        # Post 1 siempre cartoon educativo, Post 2 fotorrealista premium
        ESTILOS_DIA = ["cartoon", "realista"]
        posts_generados = []
        for i, (tema, tipo, horario, receta) in enumerate(posts_dia, 1):
            log.info(f"🎨 Generando post {i}: {tema} | Receta: {receta}")
            estilo = ESTILOS_DIA[(i - 1) % len(ESTILOS_DIA)]
            log.info(f"🎨 Estilo: {estilo}")

            # Imagen
            prompt = generar_prompt_dalle(tema, tipo, tendencias or {}, estilo=estilo, receta=receta)
            fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre = f"mrapolo_post{i}_{receta}_{tipo}_{fecha_str}.png"
            Path("imagenes_generadas").mkdir(exist_ok=True)
            ruta_img, _ = generar_imagen(prompt, nombre, es_producto=(tipo == "producto"))

            # Caption
            caption_data = generar_caption_infografia(tema, tipo, receta=receta)
            caption_data["horario_sugerido"] = horario

            posts_generados.append({
                "numero": i,
                "tema": tema,
                "tipo": tipo,
                "receta": receta,
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
        # Rechazar → regenerar inmediatamente con el feedback
        motivo = mensaje.replace("❌", "").strip()
        log.info(f"❌ Post {post['numero']} rechazado: {motivo}. Regenerando...")
        guardar_feedback_pipeline(post["tema"], post["caption"], "rechazado", motivo)
        actualizar_estado_post(idx, "rechazado", motivo)
        enviar_texto(f"❌ Entendido: {motivo}\n\n🔄 Regenerando el post con tu feedback...")
        await _regenerar_post(post, idx, motivo)
        return

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


async def _regenerar_post(post: dict, idx: int, motivo: str):
    """Regenera un post rechazado usando el feedback del usuario."""
    try:
        tendencias = cargar_tendencias()
        tema = post["tema"]
        tipo = post["tipo"]

        # Generar nueva imagen con contexto del rechazo
        prompt = generar_prompt_dalle(tema, tipo, tendencias or {}, feedback_extra=motivo)
        fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"mrapolo_regen{post['numero']}_{tipo}_{fecha_str}.png"
        Path("imagenes_generadas").mkdir(exist_ok=True)
        ruta_img, _ = generar_imagen(prompt, nombre)

        # Generar nuevo caption con contexto del rechazo
        caption_data = generar_caption_infografia(tema, tipo, feedback_extra=motivo)
        caption_data["horario_sugerido"] = post.get("horario", "")

        # Actualizar el post en el estado
        estado = cargar_estado()
        estado["posts"][idx].update({
            "caption": caption_data.get("caption", ""),
            "hashtags": caption_data.get("hashtags", []),
            "ruta_imagen": ruta_img,
            "resultado": None,
        })
        estado["post_actual"] = idx  # Volver al mismo post
        sheets_storage.guardar_estado(estado)

        # Reenviar el post regenerado para aprobación
        await enviar_post_whatsapp(post)
        enviar_texto("✅ Post regenerado con tu feedback. ¿Qué te parece?")

    except Exception as e:
        log.error(f"❌ Error regenerando post: {e}")
        enviar_texto(f"❌ Error regenerando el post: {str(e)[:200]}")


# ─────────────────────────────────────────
# PUBLICAR EN INSTAGRAM
# ─────────────────────────────────────────

def _publicar_en_instagram(post: dict):
    """
    Publica la imagen en Instagram vía Meta Graph API.
    Requiere: META_IG_TOKEN y META_IG_USER_ID en Railway env vars.
    La imagen se sirve como archivo estático desde Railway.
    """
    import httpx

    ig_token   = os.environ.get("META_IG_TOKEN")
    ig_user_id = os.environ.get("META_IG_USER_ID")
    railway_url = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "mr-apolo-production.up.railway.app")

    if not ig_token or not ig_user_id:
        log.warning("⚠️ META_IG_TOKEN o META_IG_USER_ID no configurados — omitiendo publicación en Instagram")
        return

    ruta = post.get("ruta_imagen", "")
    nombre_archivo = Path(ruta).name
    imagen_url = f"https://{railway_url}/imagenes/{nombre_archivo}"

    caption_texto = post.get("caption", "")
    hashtags_str  = " ".join(post.get("hashtags", []))
    caption_final = f"{caption_texto}\n\n{hashtags_str}"

    try:
        # Paso 1: Crear el contenedor de media
        r1 = httpx.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            params={
                "image_url":  imagen_url,
                "caption":    caption_final,
                "access_token": ig_token,
            },
            timeout=30,
        )
        r1.raise_for_status()
        creation_id = r1.json().get("id")
        if not creation_id:
            log.error(f"❌ Instagram no devolvió creation_id: {r1.text}")
            return

        log.info(f"📸 Media container creado: {creation_id}")

        # Paso 2: Publicar el contenedor
        r2 = httpx.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
            params={
                "creation_id": creation_id,
                "access_token": ig_token,
            },
            timeout=30,
        )
        r2.raise_for_status()
        post_id = r2.json().get("id")
        log.info(f"✅ Publicado en Instagram — post_id: {post_id}")

    except Exception as e:
        log.error(f"❌ Error publicando en Instagram: {e}")