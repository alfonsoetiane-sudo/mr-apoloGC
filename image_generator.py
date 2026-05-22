"""
Mr. Apolo — Generador de Infografías con DALL-E
=================================================
Analiza el estilo de las infografías top de competidores
y genera imágenes originales con el branding de Mr. Apolo.

Uso:
    python image_generator.py                    # Genera una infografía del día
    python image_generator.py --tema "proteínas" # Genera sobre un tema específico

Requiere:
    pip install openai anthropic requests pillow
    Variables de entorno:
        OPENAI_API_KEY=sk-...
        ANTHROPIC_API_KEY=sk-ant-...
"""

import os
import json
import datetime
import requests
import anthropic
from openai import OpenAI
from pathlib import Path
from mr_apolo_brand import BRAND_COLORS, BRAND_STYLE, BRAND_SYSTEM_PROMPT, DESCRIPCION_EMPAQUE

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
IMAGENES_DIR    = Path("imagenes_generadas")
TENDENCIAS_FILE = "tendencias_competidores.json"
ROTACION_FILE   = "rotacion_temas.json"

openai_client    = OpenAI(api_key=OPENAI_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY, max_retries=5)

IMAGENES_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────
# TIPOS DE INFOGRAFÍA Y TEMAS POR CATEGORÍA
# ─────────────────────────────────────────
TIPOS_INFOGRAFIA = {
    "comparacion":    "Comparación visual entre comida fresca Mr. Apolo vs croquetas procesadas",
    "beneficios":     "Lista visual de beneficios del alimento fresco con iconos",
    "ingredientes":   "Ingredientes frescos del día destacados con colores vibrantes",
    "mito_vs_realidad": "Formato mito vs realidad sobre alimentación canina",
    "antes_despues":  "Transformación visible en el perro al cambiar a Mr. Apolo",
    "nutricion":      "Infografía educativa sobre nutrición canina",
    "receta":         "Paso a paso visual de cómo se prepara Mr. Apolo",
}

# Banco de temas balanceados por categoría.
# El sistema rota entre categorías para nunca repetir el mismo tipo dos días seguidos.
BANCO_TEMAS = {
    "educacion": [
        "por qué las proteínas animales son esenciales para los perros",
        "cuánta agua necesita tu perro al día",
        "diferencia entre alimento fresco y ultra procesado",
        "qué son los aminoácidos esenciales en la dieta canina",
        "por qué el intestino de tu perro es su segundo cerebro",
        "cuántas calorías necesita tu perro según su tamaño",
    ],
    "ingredientes": [
        "pollo fresco: el rey de la proteína canina",
        "zanahoria: beneficios para la vista de tu perro",
        "espinaca: hierro natural para perros activos",
        "arroz integral: energía limpia sin picos de glucosa",
        "hígado de res: la multivitamina natural para perros",
        "calabaza: aliada de la digestión canina",
    ],
    "mitos": [
        "mito: los perros pueden comer cualquier cosa",
        "mito: la comida casera es peligrosa para los perros",
        "mito: las croquetas premium son suficientes",
        "mito: todos los perros necesitan el mismo alimento",
        "mito: la comida fresca es solo para perros grandes",
        "mito: cambiar de alimento es malo para los perros",
    ],
    "beneficios_visibles": [
        "pelo más brillante en 3 semanas con comida fresca",
        "más energía y menos letargo al cambiar de alimento",
        "mejor digestión: menos gases y heces más firmes",
        "músculos más definidos con proteína de calidad",
        "dientes más limpios con alimento natural",
        "sistema inmune más fuerte con nutrición real",
    ],
    "comparacion": [
        "comida fresca vs croquetas: lo que el empaque no te dice",
        "ingredientes que reconoces vs ingredientes que no puedes pronunciar",
        "costo real de croquetas premium vs Mr. Apolo",
        "lo que comes tú vs lo que le das a tu perro",
        "alimento procesado vs alimento fresco: diferencia en energía",
    ],
    "transicion": [
        "cómo cambiar a tu perro de croquetas a comida fresca en 7 días",
        "señales de que tu perro está listo para comida fresca",
        "qué esperar la primera semana con Mr. Apolo",
        "cómo saber si la porción de tu perro es correcta",
    ],
}


# ─────────────────────────────────────────
# SISTEMA DE ROTACIÓN DE TEMAS
# ─────────────────────────────────────────

def cargar_rotacion() -> dict:
    """Carga el estado actual de la rotación de temas."""
    if not os.path.exists(ROTACION_FILE):
        return {"categorias_usadas": [], "temas_usados": {}}
    with open(ROTACION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_rotacion(estado: dict):
    with open(ROTACION_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)

HORARIOS_DIA = {
    "manana": "8:00am — mayor apertura matutina",
    "tarde":  "7:00pm — mayor engagement nocturno",
}

MAPA_TIPO = {
    "educacion":          "nutricion",
    "ingredientes":       "ingredientes",
    "mitos":              "mito_vs_realidad",
    "beneficios_visibles":"beneficios",
    "comparacion":        "comparacion",
    "transicion":         "antes_despues",
}

def seleccionar_temas_del_dia() -> list[tuple[str, str, str]]:
    """
    Selecciona 2 temas balanceados para el día: uno de mañana y uno de tarde.
    Nunca repite categoría en el mismo día ni en días consecutivos.
    Retorna lista de (tema, tipo_infografia, horario).
    """
    estado = cargar_rotacion()
    categorias_usadas = estado.get("categorias_usadas", [])
    temas_usados      = estado.get("temas_usados", {})
    categorias        = list(BANCO_TEMAS.keys())

    # Reiniciar ciclo si ya se agotaron todas las categorías
    if set(categorias_usadas) >= set(categorias):
        print("🔄 Ciclo completo — reiniciando rotación")
        categorias_usadas = []

    seleccionados = []
    categorias_hoy = []

    for horario_key, horario_label in HORARIOS_DIA.items():
        # Disponibles: no usadas en días anteriores ni en este mismo día
        disponibles = [c for c in categorias
                       if c not in categorias_usadas and c not in categorias_hoy]

        # Si no quedan, tomar de las no usadas hoy aunque ya se hayan cicleado
        if not disponibles:
            disponibles = [c for c in categorias if c not in categorias_hoy]

        categoria = disponibles[0]
        categorias_hoy.append(categoria)

        # Elegir tema no usado dentro de la categoría
        temas_cat      = BANCO_TEMAS[categoria]
        usados_en_cat  = temas_usados.get(categoria, [])
        temas_disp     = [t for t in temas_cat if t not in usados_en_cat]

        if not temas_disp:          # Reiniciar temas de esa categoría
            temas_disp = temas_cat
            temas_usados[categoria] = []

        tema = temas_disp[0]
        tipo = MAPA_TIPO.get(categoria, "beneficios")

        # Registrar uso
        categorias_usadas.append(categoria)
        temas_usados.setdefault(categoria, []).append(tema)

        seleccionados.append((tema, tipo, horario_label))

        print(f"\n🎯 Post {horario_key}:")
        print(f"   Categoría : {categoria}")
        print(f"   Tema      : {tema}")
        print(f"   Tipo      : {tipo}")
        print(f"   Horario   : {horario_label}")

    guardar_rotacion({
        "categorias_usadas": categorias_usadas,
        "temas_usados":      temas_usados,
        "ultima_fecha":      datetime.datetime.now().isoformat(),
        "posts_hoy":         [s[0] for s in seleccionados],
    })

    return seleccionados


# ─────────────────────────────────────────
# ANALIZAR TENDENCIAS GUARDADAS
# ─────────────────────────────────────────

def cargar_tendencias() -> dict:
    if not os.path.exists(TENDENCIAS_FILE):
        return {}
    with open(TENDENCIAS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tendencias", {})


# ─────────────────────────────────────────
# GENERAR PROMPT PARA DALL-E
# ─────────────────────────────────────────

def generar_prompt_dalle(tema: str, tipo_infografia: str, tendencias: dict, con_referencia: bool = False, feedback_extra: str = None) -> str:
    """Claude genera el prompt optimizado para gpt-image-1 basado en el tema y tendencias."""
    from mr_apolo_brand import INGREDIENTES_RECETAS

    tendencias_str = json.dumps(tendencias, ensure_ascii=False) if tendencias else "Sin tendencias previas"
    ingredientes_str = ", ".join(INGREDIENTES_RECETAS["comunes"])

    modo = "ADAPTAR la imagen de referencia del competidor" if con_referencia else "CREAR una infografía de Instagram"

    feedback_str = f"\nFEEDBACK DEL USUARIO (CORRIGE ESTO en la nueva versión): {feedback_extra}" if feedback_extra else ""

    instruccion = f"""Genera un prompt detallado en inglés para gpt-image-1 que sirva para {modo} para Mr. Apolo.

Tema: {tema}
Tipo de infografía: {tipo_infografia} — {TIPOS_INFOGRAFIA.get(tipo_infografia, '')}
Ingredientes reales del producto (úsalos como elementos visuales): {ingredientes_str}
Tendencias detectadas en competidores: {tendencias_str}{feedback_str}

Estilo visual de la marca:
{BRAND_STYLE}

Colores: fondo {BRAND_COLORS['negro_fondo']}, acentos dorados {BRAND_COLORS['dorado']}, texto {BRAND_COLORS['blanco']}

Descripción exacta del empaque Mr. Apolo (úsala si el producto debe aparecer en la imagen):
{DESCRIPCION_EMPAQUE}

REGLAS CRÍTICAS para el prompt:
0. Los elementos visuales deben mostrar los ingredientes reales del producto: pollo fresco, zanahoria, calabacita, espinaca, hígado. Nunca inventar ingredientes.
1. TODO el texto visible en la imagen debe estar en ESPAÑOL. Nunca en inglés.
2. {"Si hay imagen de referencia: mantener exactamente el mismo layout, estructura y composición del competidor. Solo cambiar branding, colores y contenido a Mr. Apolo." if con_referencia else "Describir la composición visual en detalle (qué va arriba, al centro, abajo)."}
3. Colores Mr. Apolo: fondo oscuro #1C1C1C, acentos dorados #C9A84C, texto blanco.
4. Si aparece el producto Mr. Apolo, usar esta descripción exacta del empaque: bolsa transparente sellada al vacío con etiqueta negra cuadrada, logo circular del perro negro con pecho blanco y lengua afuera rodeado de ingredientes frescos, texto 'MR APOLO' en dorado arriba, 'Comida de campeones, al alcance de todos.' en dorado abajo.
5. Eliminar cualquier branding del competidor. Reemplazar con Mr. Apolo.
6. Formato cuadrado 1:1 para Instagram.
7. Máximo 900 caracteres.
8. Incluir: "All visible text in the image must be in Spanish only, not English."

Responde SOLO con el prompt en inglés, sin explicaciones."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": instruccion}]
    )

    return response.content[0].text.strip()


# ─────────────────────────────────────────
# GENERAR IMAGEN CON DALL-E
# ─────────────────────────────────────────

def _guardar_respuesta_openai(response, ruta: Path, prompt: str) -> tuple[str, str]:
    """Guarda la imagen de respuesta de OpenAI (base64 o URL)."""
    import base64
    imagen = response.data[0]
    if getattr(imagen, "b64_json", None):
        img_data = base64.b64decode(imagen.b64_json)
        with open(ruta, "wb") as f:
            f.write(img_data)
    elif getattr(imagen, "url", None):
        img_data = requests.get(imagen.url, timeout=30).content
        with open(ruta, "wb") as f:
            f.write(img_data)
    else:
        raise ValueError("La respuesta de OpenAI no contiene imagen en b64 ni URL.")
    prompt_revisado = getattr(imagen, "revised_prompt", prompt) or prompt
    return str(ruta), prompt_revisado


def generar_imagen(prompt: str, nombre_archivo: str, imagen_referencia: str = None) -> tuple[str, str]:
    """
    Genera o adapta una imagen con gpt-image-1.
    Si se proporciona imagen_referencia (ruta local de post de competidor),
    usa el endpoint de edición para adaptar ese estilo a Mr. Apolo.
    Si no, genera desde cero.
    """
    import base64
    ruta = IMAGENES_DIR / nombre_archivo

    if imagen_referencia and os.path.exists(imagen_referencia):
        print(f"\n🎨 Adaptando imagen de competidor con gpt-image-1...")
        print(f"   Referencia: {imagen_referencia}")
        print(f"   Prompt: {prompt[:100]}...")

        with open(imagen_referencia, "rb") as img_file:
            response = openai_client.images.edit(
                model="gpt-image-1",
                image=img_file,
                prompt=prompt,
                size="1024x1024",
            )
    else:
        print(f"\n🎨 Generando imagen con gpt-image-1...")
        print(f"   Prompt: {prompt[:100]}...")

        response = openai_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="high",
            n=1,
        )

    print(f"✅ Imagen guardada: {ruta}")
    return _guardar_respuesta_openai(response, ruta, prompt)


# ─────────────────────────────────────────
# GENERAR CAPTION PARA LA INFOGRAFÍA
# ─────────────────────────────────────────

def generar_caption_infografia(tema: str, tipo_infografia: str, feedback_extra: str = None) -> dict:
    """Genera el caption de Instagram que acompaña la infografía."""
    from content_generator import generar_contenido
    from mr_apolo_brand import INGREDIENTES_RECETAS

    ingredientes_str = ", ".join(INGREDIENTES_RECETAS["comunes"])
    contexto = (
        f"Este post es una infografía tipo '{tipo_infografia}'. "
        f"El texto debe complementar la imagen visual, no repetir lo que ya se ve en ella. "
        f"Ser más corto de lo normal ya que la imagen ya comunica mucho. "
        f"Ingredientes reales del producto (solo menciona estos): {ingredientes_str}."
    )
    if feedback_extra:
        contexto += f" IMPORTANTE: el usuario rechazó la versión anterior porque '{feedback_extra}'. Corrígelo en esta nueva versión."

    return generar_contenido(tema, contexto_extra=contexto)


# ─────────────────────────────────────────
# GUARDAR RESULTADO
# ─────────────────────────────────────────

def guardar_resultado(tema: str, tipo: str, ruta_imagen: str, caption: dict, prompt_usado: str):
    historial_file = "imagenes_historial.json"
    historial = []
    if os.path.exists(historial_file):
        with open(historial_file, "r", encoding="utf-8") as f:
            historial = json.load(f)

    historial.append({
        "fecha": datetime.datetime.now().isoformat(),
        "tema": tema,
        "tipo": tipo,
        "ruta_imagen": ruta_imagen,
        "prompt_dalle": prompt_usado,
        "caption": caption.get("caption", ""),
        "hashtags": caption.get("hashtags", []),
        "horario_sugerido": caption.get("horario_sugerido", ""),
    })

    with open(historial_file, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# MOSTRAR RESULTADO FINAL
# ─────────────────────────────────────────

def mostrar_resultado(ruta_imagen: str, caption: dict, tipo: str):
    print("\n" + "═" * 55)
    print("🖼️   INFOGRAFÍA GENERADA — Mr. Apolo")
    print("═" * 55)
    print(f"\n📁 Imagen guardada en: {ruta_imagen}")
    print(f"\n📝 CAPTION:\n{caption.get('caption', '')}")
    print(f"\n#️⃣  HASHTAGS:\n{' '.join(caption.get('hashtags', []))}")
    print(f"\n🕐 HORARIO: {caption.get('horario_sugerido', '')}")
    print("═" * 55)


# ─────────────────────────────────────────
# FLUJO PRINCIPAL
# ─────────────────────────────────────────

def main():
    import sys

    print("\n🐾 Mr. Apolo — Generador de Infografías")
    print("─" * 40)

    # Cargar tendencias de competidores si existen
    tendencias = cargar_tendencias()
    if tendencias:
        print("\n📊 Usando tendencias de competidores como referencia")

    # Seleccionar 2 temas del día automáticamente
    posts_dia = seleccionar_temas_del_dia()

    # Buscar imágenes de competidores disponibles para usar como referencia
    imagenes_competidores = []
    carpeta_comp = Path("imagenes_competidores")
    if carpeta_comp.exists():
        imagenes_competidores = sorted(
            [str(p) for p in carpeta_comp.glob("*.jpg") if p.stat().st_size > 10000],
            key=lambda x: os.path.getmtime(x),
            reverse=True
        )

    if imagenes_competidores:
        print(f"\n📸 {len(imagenes_competidores)} imágenes de competidores disponibles como referencia")
    else:
        print("\n⚠️  Sin imágenes de competidores. Corre competitor_monitor.py primero para descargarlas.")

    for i, (tema, tipo, horario) in enumerate(posts_dia, 1):
        print(f"\n{'═'*55}")
        print(f"  GENERANDO POST {i} de 2 — {horario}")
        print(f"{'═'*55}")

        # Usar imagen de competidor como referencia si está disponible
        # Rotar entre las imágenes disponibles para no repetir
        img_ref = imagenes_competidores[(i - 1) % len(imagenes_competidores)] if imagenes_competidores else None
        con_referencia = img_ref is not None

        if con_referencia:
            print(f"   Adaptando estilo de: {os.path.basename(img_ref)}")

        # Generar prompt y imagen
        print("\n🧠 Claude generando prompt...")
        prompt = generar_prompt_dalle(tema, tipo, tendencias, con_referencia=con_referencia)

        fecha_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"mrapolo_post{i}_{tipo}_{fecha_str}.png"
        ruta_imagen, prompt_revisado = generar_imagen(prompt, nombre_archivo, imagen_referencia=img_ref)

        # Generar caption
        print("\n✍️  Generando caption...")
        caption = generar_caption_infografia(tema, tipo)
        caption["horario_sugerido"] = horario

        mostrar_resultado(ruta_imagen, caption, tipo)
        guardar_resultado(tema, tipo, ruta_imagen, caption, prompt_revisado)

        if i < len(posts_dia):
            input("\n⏎  Presiona Enter para generar el siguiente post...")

    print(f"\n✅ 2 posts del día generados y guardados en: imagenes_generadas/")


if __name__ == "__main__":
    main()
