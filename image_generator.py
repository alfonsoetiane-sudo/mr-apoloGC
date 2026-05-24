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
from mr_apolo_brand import BRAND_COLORS, BRAND_STYLE, BRAND_SYSTEM_PROMPT, DESCRIPCION_EMPAQUE, LOGO_DESCRIPCION
from sheets_storage import cargar_rotacion, guardar_rotacion

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
IMAGENES_DIR    = Path("imagenes_generadas")
TENDENCIAS_FILE = "tendencias_competidores.json"

openai_client    = OpenAI(api_key=OPENAI_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY, max_retries=5)

IMAGENES_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────
# TIPOS DE INFOGRAFÍA Y TEMAS POR CATEGORÍA
# ─────────────────────────────────────────
TIPOS_INFOGRAFIA = {
    "comparacion":      "Comparación visual entre comida fresca Mr. Apolo vs croquetas procesadas",
    "beneficios":       "Lista visual de beneficios del alimento fresco con iconos",
    "ingredientes":     "Ingredientes frescos del día destacados con colores vibrantes",
    "mito_vs_realidad": "Formato mito vs realidad sobre alimentación canina",
    "antes_despues":    "Transformación visible en el perro al cambiar a Mr. Apolo",
    "nutricion":        "Infografía educativa sobre nutrición canina",
    "receta":           "Paso a paso visual de cómo se prepara Mr. Apolo",
    "producto":         "Presentación del sobre Mr. Apolo con ingredientes alrededor",
    "historia":         "Post emocional sobre la historia de Apolo y la marca",
    "comunidad":        "Post para conectar con la comunidad de dueños de perros",
}

# Banco de temas — cada entrada indica (tema, receta) para alternar Olímpico y Titán.
# El sistema rota entre categorías para nunca repetir el mismo tipo dos días seguidos.
BANCO_TEMAS = {
    "educacion": [
        ("por qué las proteínas animales son esenciales para los perros", "olimpico"),
        ("cuánta agua necesita tu perro al día y cómo la alimentación ayuda", "titan"),
        ("diferencia entre alimento fresco y ultra procesado para perros", "olimpico"),
        ("qué son los aminoácidos esenciales en la dieta canina", "titan"),
        ("por qué el intestino de tu perro es su segundo cerebro", "olimpico"),
        ("cuántas calorías necesita tu perro según su tamaño y actividad", "titan"),
        ("por qué el cerdo es una proteína excelente para perros", "titan"),
        ("beneficios del camote para la digestión de tu perro", "titan"),
    ],
    "ingredientes_olimpico": [
        ("pechuga de pollo: la proteína premium que tu perro merece — Receta Olímpico", "olimpico"),
        ("camote en la dieta de tu perro: energía natural y digestión sana — Olímpico", "olimpico"),
        ("papaya para perros: la fruta que cuida su estómago — Olímpico", "olimpico"),
        ("manzana en la dieta canina: antioxidantes y vitaminas reales", "olimpico"),
        ("calabaza Olímpico: fibra natural para una digestión perfecta", "olimpico"),
        ("por qué la pechuga de pollo fresca es mejor que el pollo deshidratado", "olimpico"),
    ],
    "ingredientes_titan": [
        ("pulpa de cerdo: proteína suave y digestible para tu perro — Receta Titán", "titan"),
        ("camote: el superalimento para perros que aún no conoces — Titán", "titan"),
        ("col en la dieta canina: fibra natural que cuida el intestino", "titan"),
        ("calabaza para perros: digestión, vitaminas y sin rellenos", "titan"),
        ("por qué Titán es ideal para perros con estómago sensible", "titan"),
    ],
    "mitos": [
        ("mito: el cerdo es malo para los perros — realidad Titán", "titan"),
        ("mito: las croquetas premium son suficientes para tu perro", "olimpico"),
        ("mito: la comida casera es peligrosa — Mr. Apolo lo resuelve", "olimpico"),
        ("mito: todos los perros necesitan el mismo alimento", "titan"),
        ("mito: la comida fresca es solo para perros grandes o caros", "olimpico"),
        ("mito: cambiar de alimento daña el estómago del perro", "titan"),
    ],
    "beneficios_visibles": [
        ("pelo más brillante en 3 semanas con la Receta Olímpico", "olimpico"),
        ("más energía y menos letargo con la Receta Titán", "titan"),
        ("mejor digestión con Titán: menos gases, heces más firmes", "titan"),
        ("músculos más definidos con proteína de pollo fresco — Olímpico", "olimpico"),
        ("sistema inmune más fuerte con nutrición real Mr. Apolo", "olimpico"),
        ("perros con estómago sensible: cómo Titán los transforma", "titan"),
    ],
    "comparacion": [
        ("Receta Olímpico vs croquetas: lo que el empaque no te dice", "olimpico"),
        ("Titán vs alimento de tienda: ingredientes que sí puedes pronunciar", "titan"),
        ("costo real de croquetas premium vs Mr. Apolo al mes", "olimpico"),
        ("lo que comes tú vs lo que le das a tu perro — cambia eso", "titan"),
        ("alimento procesado vs comida fresca: diferencia en energía real", "olimpico"),
    ],
    "transicion": [
        ("cómo cambiar a tu perro a Olímpico en 7 días sin problemas", "olimpico"),
        ("guía para empezar con Titán si tu perro tiene estómago sensible", "titan"),
        ("qué esperar la primera semana con Mr. Apolo", "olimpico"),
        ("cómo elegir entre Olímpico y Titán para tu perro", "titan"),
        ("señales de que tu perro está listo para comida fresca", "olimpico"),
    ],
    "historia_marca": [
        ("la historia de Apolo: el perro rescatado que inspiró una marca", "olimpico"),
        ("cómo nació Mr. Apolo y por qué importa lo que le das a tu perro", "titan"),
        ("comida de campeones al alcance de todos — nuestra misión", "olimpico"),
    ],
    "comunidad": [
        ("muéstranos a tu perro disfrutando Mr. Apolo — comparte su historia", "olimpico"),
        ("¿tu perro es más Olímpico o más Titán? descúbrelo aquí", "titan"),
        ("los perros de nuestra comunidad ya lo saben — ¿el tuyo también?", "olimpico"),
        ("dueños de perros en CDMX: esto es para ustedes", "titan"),
    ],
}


# ─────────────────────────────────────────
# SISTEMA DE ROTACIÓN DE TEMAS
# (cargar_rotacion / guardar_rotacion vienen de sheets_storage)
# ─────────────────────────────────────────

HORARIOS_DIA = {
    "manana": "8:00am — mayor apertura matutina",
    "tarde":  "7:00pm — mayor engagement nocturno",
}

MAPA_TIPO = {
    "educacion":             "nutricion",
    "ingredientes_olimpico": "ingredientes",
    "ingredientes_titan":    "ingredientes",
    "mitos":                 "mito_vs_realidad",
    "beneficios_visibles":   "beneficios",
    "comparacion":           "comparacion",
    "transicion":            "antes_despues",
    "historia_marca":        "historia",
    "comunidad":             "comunidad",
}

def seleccionar_temas_del_dia() -> list[tuple[str, str, str, str]]:
    """
    Selecciona 2 temas balanceados para el día: uno de mañana y uno de tarde.
    Nunca repite categoría en el mismo día ni en días consecutivos.
    Garantiza que un post sea de Olímpico y otro de Titán.
    Retorna lista de (tema, tipo_infografia, horario, receta).
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
    recetas_hoy = []  # para garantizar variedad Olímpico/Titán

    for horario_key, horario_label in HORARIOS_DIA.items():
        # Disponibles: no usadas en días anteriores ni en este mismo día
        disponibles = [c for c in categorias
                       if c not in categorias_usadas and c not in categorias_hoy]

        if not disponibles:
            disponibles = [c for c in categorias if c not in categorias_hoy]

        # Si ya tenemos un post de una receta, preferir categorías de la otra
        if recetas_hoy:
            receta_necesaria = "titan" if "olimpico" in recetas_hoy else "olimpico"
            disponibles_pref = [
                c for c in disponibles
                if any(t[1] == receta_necesaria for t in BANCO_TEMAS[c])
            ]
            if disponibles_pref:
                disponibles = disponibles_pref

        categoria = disponibles[0]
        categorias_hoy.append(categoria)

        # Elegir tema no usado dentro de la categoría
        temas_cat     = BANCO_TEMAS[categoria]
        usados_en_cat = temas_usados.get(categoria, [])
        temas_disp    = [t for t in temas_cat if t[0] not in usados_en_cat]

        if not temas_disp:
            temas_disp = temas_cat
            temas_usados[categoria] = []

        # Si ya hay una receta elegida hoy, preferir la opuesta
        if recetas_hoy:
            receta_necesaria = "titan" if "olimpico" in recetas_hoy else "olimpico"
            pref = [t for t in temas_disp if t[1] == receta_necesaria]
            if pref:
                temas_disp = pref

        tema_str, receta = temas_disp[0]
        tipo = MAPA_TIPO.get(categoria, "beneficios")

        # Registrar uso
        categorias_usadas.append(categoria)
        temas_usados.setdefault(categoria, []).append(tema_str)
        recetas_hoy.append(receta)

        seleccionados.append((tema_str, tipo, horario_label, receta))

        print(f"\n🎯 Post {horario_key}:")
        print(f"   Categoría : {categoria}")
        print(f"   Receta    : {receta}")
        print(f"   Tema      : {tema_str}")
        print(f"   Tipo      : {tipo}")
        print(f"   Horario   : {horario_label}")

    guardar_rotacion({
        "categorias_usadas": categorias_usadas,
        "temas_usadas":      temas_usados,
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

def generar_prompt_dalle(tema: str, tipo_infografia: str, tendencias: dict, con_referencia: bool = False, feedback_extra: str = None, estilo: str = "cartoon", receta: str = "olimpico") -> str:
    """Claude genera el prompt optimizado para gpt-image-1 basado en el tema y tendencias."""
    from mr_apolo_brand import INGREDIENTES_RECETAS

    tendencias_str = json.dumps(tendencias, ensure_ascii=False) if tendencias else "Sin tendencias previas"
    ingredientes_receta = INGREDIENTES_RECETAS.get(receta, INGREDIENTES_RECETAS["olimpico"])
    ingredientes_str = ", ".join(ingredientes_receta)
    nombre_receta = "Olímpico (proteína de pollo)" if receta == "olimpico" else "Titán (proteína de cerdo)"

    modo = "ADAPTAR la imagen de referencia del competidor" if con_referencia else "CREAR una infografía de Instagram"
    feedback_str = f"\nFEEDBACK DEL USUARIO (CORRIGE ESTO en la nueva versión): {feedback_extra}" if feedback_extra else ""

    instruccion = f"""Genera un prompt detallado en inglés para gpt-image-1 que sirva para {modo} para Mr. Apolo.

Tema: {tema}
Receta destacada: {nombre_receta}
Tipo de infografía: {tipo_infografia} — {TIPOS_INFOGRAFIA.get(tipo_infografia, '')}
Ingredientes reales de ESTA receta (úsalos como elementos visuales, NO otros): {ingredientes_str}
Tendencias detectadas en competidores: {tendencias_str}{feedback_str}

Estilo visual de la marca:
{BRAND_STYLE}

Descripción exacta del empaque (si el producto aparece en la imagen):
{DESCRIPCION_EMPAQUE.get(receta, DESCRIPCION_EMPAQUE['olimpico'])}

{"ESTILO DEL POST: INFOGRAFÍA CARTOON EDUCATIVA" if estilo == "cartoon" else "ESTILO DEL POST: INFOGRAFÍA FOTORREALISTA PREMIUM"}

REGLAS CRÍTICAS para el prompt:
{"0. Estilo CARTOON EDUCATIVO completo — toda la imagen es una ilustración. Semi-realista, no infantil. Perro negro con pecho blanco y lengua afuera cuando aparezca. Ingredientes ilustrados. Texto educativo bold en dorado y blanco." if estilo == "cartoon" else "0. Estilo FOTORREALISTA premium — fotografía editorial de alta calidad. Ingredientes frescos en primer plano, iluminación de estudio profesional, fondo oscuro limpio."}
1. Los ingredientes visibles deben ser EXACTAMENTE los de la receta {nombre_receta}: {ingredientes_str}. Nunca mezcles con otras recetas.
2. TODO el texto visible en la imagen debe estar en ESPAÑOL. Nunca en inglés.
3. {"Si hay imagen de referencia: mantener layout y composición. Solo cambiar branding a Mr. Apolo." if con_referencia else "Describir la composición visual completa de la infografía."}
4. Colores: fondo #1C1C1C, títulos #C9A84C dorado, texto blanco.
5. NO incluir ningún logotipo, emblema circular ni texto de marca en la imagen. El logo se agrega digitalmente después. Dejar espacio limpio en la esquina inferior derecha.
6. Formato cuadrado 1:1 para Instagram.
7. Máximo 900 caracteres.
8. Incluir al final: "All visible text in the image must be in Spanish only, not English. Do NOT include any logo, circular emblem, or brand watermark in the image."

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


def generar_imagen(prompt: str, nombre_archivo: str, imagen_referencia: str = None, es_producto: bool = False) -> tuple[str, str]:
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
    ruta_str, prompt_rev = _guardar_respuesta_openai(response, ruta, prompt)
    agregar_watermark(ruta_str, usar_logo=es_producto)
    return ruta_str, prompt_rev


# ─────────────────────────────────────────
# WATERMARK — overlay de etiqueta real o texto de respaldo
# ─────────────────────────────────────────

LOGO_FILE = "mr_apolo_logo.png"   # etiqueta oficial Mr. Apolo
LOGO_SIZE_RATIO = 0.22            # el logo ocupa 22% del ancho de la imagen

def agregar_watermark(ruta_imagen: str, usar_logo: bool = False):
    """
    usar_logo=True  → pega mr_apolo_logo.png CENTRADO en la imagen (simula
                      la etiqueta pegada al centro del sobre generado por IA).
    usar_logo=False → pone '@mr.apolo_petfood' en dorado en la esquina inferior.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(ruta_imagen).convert("RGBA")
        w, h = img.size
        margin = w // 40

        if usar_logo and os.path.exists(LOGO_FILE):
            # ── Etiqueta centrada sobre el sobre (imagen de producto) ──
            logo = Image.open(LOGO_FILE).convert("RGBA")
            # Ocupa ~45% del ancho — tamaño natural de una etiqueta en un sobre
            logo_w = int(w * 0.45)
            logo_h = int(logo.height * logo_w / logo.width)
            logo = logo.resize((logo_w, logo_h), Image.LANCZOS)

            # Centro horizontal, ligeramente por debajo del centro vertical
            x = (w - logo_w) // 2
            y = (h - logo_h) // 2 + int(h * 0.05)

            logo_semi = logo.copy()
            alpha = logo_semi.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.90))
            logo_semi.putalpha(alpha)

            img.paste(logo_semi, (x, y), logo_semi)
            img.convert("RGB").save(ruta_imagen, "PNG")
            print(f"✅ Etiqueta añadida (imagen de producto)")

        else:
            # ── Texto @mr.apolo_petfood para infografías y demás ─────
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            texto = "@mr.apolo_petfood"
            font_size = max(24, w // 38)
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
         