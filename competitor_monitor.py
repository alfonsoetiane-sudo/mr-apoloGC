"""
Mr. Apolo — Monitor de Competidores
=====================================
Scrapeea las cuentas configuradas en mr_apolo_brand.py,
rankea los posts por engagement y extrae los patrones
de los más exitosos para alimentar al generador de contenido.

Uso:
    python competitor_monitor.py              # Analiza y guarda tendencias
    python competitor_monitor.py --generar    # Analiza + genera contenido del día

Requiere:
    pip install anthropic requests
    Variables de entorno:
        ANTHROPIC_API_KEY=sk-ant-...
        APIFY_TOKEN=apify_api_...   (obtén en https://console.apify.com/account/integrations)
"""

import os
import json
import time
import datetime
import requests
import anthropic
from mr_apolo_brand import (
    COMPETIDORES,
    HASHTAGS_MONITOREAR,
    ENGAGEMENT_MINIMO_LIKES,
    POSTS_POR_CUENTA,
    BRAND_SYSTEM_PROMPT,
    HASHTAGS_BASE,
)

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
TENDENCIAS_FILE = "tendencias_competidores.json"

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# ─────────────────────────────────────────
# APIFY — Scraping de Instagram
# ─────────────────────────────────────────

def scrapeear_cuenta(username: str, max_posts: int = POSTS_POR_CUENTA) -> list:
    """Scrapeea los últimos N posts de una cuenta de Instagram via Apify."""
    print(f"  📥 Scrapeando @{username}...")

    url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs?token={APIFY_TOKEN}"
    payload = {
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsLimit": max_posts,
        "addParentData": False,
        "expandOwners": False,
        "enhanceUserSearchWithFacebookPage": False,
    }

    # Iniciar el run
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]

    # Esperar a que termine (polling)
    for _ in range(30):
        time.sleep(6)
        status_url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs/{run_id}?token={APIFY_TOKEN}"
        status = requests.get(status_url, timeout=15).json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        elif status in ("FAILED", "ABORTED"):
            print(f"  ❌ Error scrapeando @{username}: {status}")
            return []

    # Obtener resultados
    dataset_id = requests.get(status_url, timeout=15).json()["data"]["defaultDatasetId"]
    items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&format=json"
    items = requests.get(items_url, timeout=30).json()
    return items


def scrapeear_hashtag(hashtag: str, max_posts: int = 20) -> list:
    """Scrapeea posts recientes de un hashtag de Instagram."""
    print(f"  🔍 Scrapeando #{hashtag}...")

    url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs?token={APIFY_TOKEN}"
    payload = {
        "directUrls": [f"https://www.instagram.com/explore/tags/{hashtag}/"],
        "resultsLimit": max_posts,
        "addParentData": False,
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]

    for _ in range(30):
        time.sleep(6)
        status_url = f"https://api.apify.com/v2/acts/apify~instagram-scraper/runs/{run_id}?token={APIFY_TOKEN}"
        status = requests.get(status_url, timeout=15).json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        elif status in ("FAILED", "ABORTED"):
            return []

    dataset_id = requests.get(status_url, timeout=15).json()["data"]["defaultDatasetId"]
    items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&format=json"
    return requests.get(items_url, timeout=30).json()


# ─────────────────────────────────────────
# ANÁLISIS DE ENGAGEMENT
# ─────────────────────────────────────────

def calcular_engagement(post: dict) -> float:
    """
    Engagement Rate = (likes + comentarios) / seguidores * 100
    Si no tenemos seguidores, usamos solo likes + comentarios.
    """
    likes = post.get("likesCount", 0) or 0
    comentarios = post.get("commentsCount", 0) or 0
    seguidores = post.get("ownerFollowersCount", 0) or 1
    return round((likes + comentarios) / seguidores * 100, 4)


def rankear_posts(posts: list) -> list:
    """Filtra posts con engagement mínimo y los ordena de mayor a menor."""
    filtrados = [
        p for p in posts
        if (p.get("likesCount") or 0) >= ENGAGEMENT_MINIMO_LIKES
        and p.get("caption")
    ]
    for p in filtrados:
        p["_engagement_rate"] = calcular_engagement(p)
    return sorted(filtrados, key=lambda x: x["_engagement_rate"], reverse=True)


def descargar_imagen_post(post: dict, ruta_destino: str) -> str | None:
    """Descarga la imagen de un post de Instagram. Retorna la ruta si tuvo éxito."""
    url_img = (
        post.get("displayUrl") or
        post.get("images", [None])[0] if post.get("images") else None or
        post.get("thumbnailUrl")
    )
    if not url_img:
        return None
    try:
        resp = requests.get(url_img, timeout=20)
        resp.raise_for_status()
        with open(ruta_destino, "wb") as f:
            f.write(resp.content)
        return ruta_destino
    except Exception:
        return None


def extraer_datos_post(post: dict, fuente: str, descargar_img: bool = True) -> dict:
    """Extrae los campos relevantes de un post scrapeado e intenta descargar su imagen."""
    import os
    from pathlib import Path

    img_dir = Path("imagenes_competidores")
    img_dir.mkdir(exist_ok=True)

    ruta_img = None
    if descargar_img and post.get("type", "image") == "image":
        nombre = f"{fuente.replace('@','').replace('#','')}_{post.get('id','')[:8]}.jpg"
        ruta_candidata = str(img_dir / nombre)
        if not os.path.exists(ruta_candidata):
            ruta_img = descargar_imagen_post(post, ruta_candidata)
        else:
            ruta_img = ruta_candidata

    return {
        "fuente": fuente,
        "url": post.get("url", ""),
        "tipo": post.get("type", "image"),
        "caption": (post.get("caption") or "")[:500],
        "likes": post.get("likesCount", 0),
        "comentarios": post.get("commentsCount", 0),
        "engagement_rate": post.get("_engagement_rate", 0),
        "fecha": post.get("timestamp", ""),
        "ruta_imagen_local": ruta_img,
        "hashtags_usados": [
            w.lstrip("#") for w in (post.get("caption") or "").split()
            if w.startswith("#")
        ],
    }


# ─────────────────────────────────────────
# ANÁLISIS CON CLAUDE
# ─────────────────────────────────────────

def analizar_tendencias_con_claude(posts_top: list) -> dict:
    """Claude analiza los posts más exitosos y extrae patrones accionables."""
    print("\n🧠 Claude analizando patrones de éxito...")

    posts_json = json.dumps(posts_top[:15], ensure_ascii=False, indent=2)

    prompt = f"""Analiza estos posts de Instagram de marcas de comida fresca para perros que tuvieron mayor engagement.
Identifica patrones accionables para Mr. Apolo (marca mexicana de comida fresca para perros en CDMX).

Posts más exitosos:
{posts_json}

Responde con este JSON exacto:
{{
  "formatos_que_funcionan": ["formato1", "formato2"],
  "temas_populares": ["tema1", "tema2", "tema3"],
  "estructura_caption_exitosa": "descripción de cómo están estructurados los captions con más likes",
  "emojis_frecuentes": ["emoji1", "emoji2"],
  "hashtags_mas_usados": ["hashtag1", "hashtag2"],
  "hora_publicacion_tendencia": "observación sobre cuándo publican",
  "tipo_contenido_top": "image / video / carrusel — cuál domina",
  "gancho_de_apertura": "patrón de cómo abren los captions más exitosos",
  "llamada_a_accion_top": "qué tipo de CTA usan más",
  "oportunidad_para_mr_apolo": "qué está haciendo la competencia que Mr. Apolo NO está haciendo y podría aprovechar"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = response.content[0].text.strip()
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]

    return json.loads(texto.strip())


# ─────────────────────────────────────────
# GUARDAR Y CARGAR TENDENCIAS
# ─────────────────────────────────────────

def guardar_tendencias(tendencias: dict, posts_top: list):
    data = {
        "fecha_analisis": datetime.datetime.now().isoformat(),
        "tendencias": tendencias,
        "posts_referencia": posts_top[:10],
    }
    with open(TENDENCIAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Tendencias guardadas en {TENDENCIAS_FILE}")


def cargar_tendencias() -> dict | None:
    if not os.path.exists(TENDENCIAS_FILE):
        return None
    with open(TENDENCIAS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Si el análisis tiene más de 24 horas, avisar
    fecha = datetime.datetime.fromisoformat(data["fecha_analisis"])
    horas = (datetime.datetime.now() - fecha).total_seconds() / 3600
    if horas > 24:
        print(f"⚠️  Las tendencias tienen {int(horas)}h. Considera re-analizar.")
    return data


# ─────────────────────────────────────────
# MOSTRAR REPORTE DE TENDENCIAS
# ─────────────────────────────────────────

def mostrar_reporte(tendencias: dict):
    t = tendencias
    print("\n" + "═" * 55)
    print("📊  REPORTE DE COMPETIDORES — Mr. Apolo")
    print("═" * 55)
    print(f"\n🎯 Oportunidad detectada:\n   {t.get('oportunidad_para_mr_apolo')}")
    print(f"\n📝 Estructura de caption exitosa:\n   {t.get('estructura_caption_exitosa')}")
    print(f"\n🔑 Gancho de apertura top:\n   {t.get('gancho_de_apertura')}")
    print(f"\n📌 Temas populares: {', '.join(t.get('temas_populares', []))}")
    print(f"🎬 Tipo de contenido dominante: {t.get('tipo_contenido_top')}")
    print(f"📣 CTA más usada: {t.get('llamada_a_accion_top')}")
    print(f"#️⃣  Hashtags frecuentes: {' '.join(['#' + h for h in t.get('hashtags_mas_usados', [])])}")
    print("═" * 55)


# ─────────────────────────────────────────
# GENERAR CONTENIDO CON TENDENCIAS
# ─────────────────────────────────────────

def generar_con_tendencias(tendencias: dict, posts_top: list) -> dict:
    """Genera un post usando las tendencias detectadas de la competencia."""
    from content_generator import generar_contenido, mostrar_contenido, loop_feedback

    t = tendencias
    contexto = f"""Tendencias detectadas en la competencia hoy:
- Temas populares: {', '.join(t.get('temas_populares', []))}
- Estructura exitosa: {t.get('estructura_caption_exitosa')}
- Gancho de apertura: {t.get('gancho_de_apertura')}
- Tipo de contenido que más funciona: {t.get('tipo_contenido_top')}
- Oportunidad específica para Mr. Apolo: {t.get('oportunidad_para_mr_apolo')}

Posts de referencia (adapta el estilo, NO copies):
{json.dumps([{'caption': p['caption'][:200], 'likes': p['likes'], 'tipo': p['tipo']} for p in posts_top[:3]], ensure_ascii=False)}"""

    tema = t.get("temas_populares", ["bienestar canino"])[0]
    contenido = generar_contenido(tema, contexto_extra=contexto)
    mostrar_contenido(contenido)
    loop_feedback(contenido, tema)
    return contenido


# ─────────────────────────────────────────
# FLUJO PRINCIPAL
# ─────────────────────────────────────────

def analizar_competidores() -> tuple[dict, list]:
    """Scrapeea todas las cuentas configuradas y analiza con Claude."""
    if not APIFY_TOKEN:
        raise ValueError("Falta APIFY_TOKEN. Obtén tu token en https://console.apify.com/account/integrations")

    todos_los_posts = []

    print(f"\n🔍 Analizando {len(COMPETIDORES)} cuentas de competidores...")
    for username, descripcion in COMPETIDORES.items():
        print(f"\n  Cuenta: @{username} — {descripcion}")
        posts = scrapeear_cuenta(username)
        rankeados = rankear_posts(posts)
        for p in rankeados[:5]:  # Top 5 por cuenta
            todos_los_posts.append(extraer_datos_post(p, f"@{username}"))

    print(f"\n🔍 Analizando {len(HASHTAGS_MONITOREAR)} hashtags...")
    for hashtag in HASHTAGS_MONITOREAR[:3]:  # Solo los primeros 3 para no tardar demasiado
        posts = scrapeear_hashtag(hashtag)
        rankeados = rankear_posts(posts)
        for p in rankeados[:3]:
            todos_los_posts.append(extraer_datos_post(p, f"#{hashtag}"))

    # Ordenar todos por engagement
    posts_top = sorted(todos_los_posts, key=lambda x: x["engagement_rate"], reverse=True)

    print(f"\n✅ {len(posts_top)} posts relevantes encontrados")
    print(f"   Top post: {posts_top[0]['likes']} likes — @{posts_top[0]['fuente']}" if posts_top else "")

    tendencias = analizar_tendencias_con_claude(posts_top)
    return tendencias, posts_top


def main():
    import sys
    generar = "--generar" in sys.argv

    print("\n🐾 Mr. Apolo — Monitor de Competidores")
    print("─" * 40)

    # ¿Usar análisis guardado o hacer uno nuevo?
    datos_guardados = cargar_tendencias()
    usar_guardado = False

    if datos_guardados:
        fecha = datos_guardados["fecha_analisis"][:16].replace("T", " ")
        respuesta = input(f"\nExiste un análisis de {fecha}. ¿Usar ese o hacer uno nuevo? (g=guardado / n=nuevo): ").strip().lower()
        usar_guardado = respuesta != "n"

    if usar_guardado and datos_guardados:
        tendencias = datos_guardados["tendencias"]
        posts_top = datos_guardados["posts_referencia"]
        print("📂 Usando análisis guardado")
    else:
        tendencias, posts_top = analizar_competidores()
        guardar_tendencias(tendencias, posts_top)

    mostrar_reporte(tendencias)

    if generar or input("\n¿Generar el post del día basado en estas tendencias? (s/n): ").strip().lower() == "s":
        generar_con_tendencias(tendencias, posts_top)


if __name__ == "__main__":
    main()
