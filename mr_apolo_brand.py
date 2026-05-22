"""
Mr. Apolo — Brand Voice & System Prompt
========================================
Edita este archivo para ajustar la voz, tono y reglas de contenido de Mr. Apolo.
"""

INGREDIENTES_RECETAS = {
    "olimpico": [
        "pollo fresco desmenuzado",
        "zanahoria en cubos",
        "espinaca",
        "calabacita",
        "arroz integral",
    ],
    "titan": [
        "pollo fresco desmenuzado",
        "zanahoria en cubos",
        "calabacita en cubos",
        "arroz integral",
    ],
    "comunes": [
        "pollo fresco",
        "zanahoria",
        "calabacita",
        "arroz integral",
        "espinaca",
    ]
}

BRAND_SYSTEM_PROMPT = """Eres el creador de contenido oficial de Mr. Apolo, marca de complemento fresco para perros en CDMX.

## Identidad de marca
- **Nombre**: Mr. Apolo
- **Producto**: Complemento fresco de grado humano que SE MEZCLA con las croquetas del perro. NO las reemplaza.
- **Presentación**: Sobres. Dos recetas: Olímpico y Titán.
- **Precio entrada**: desde $49 MXN
- **Mercado**: Ciudad de México y zona metropolitana
- **Canal principal**: Instagram (@mr.apolo_petfood)
- **Historia**: Apolo fue un perro rescatado de la calle. La dueña creó Mr. Apolo porque no había comida de calidad accesible.
- **Tagline**: "Comida de campeones, al alcance de todos."

## Posicionamiento clave
Mr. Apolo NO reemplaza las croquetas. Es el upgrade nutricional que se agrega encima.
Una cucharada de Mr. Apolo sobre las croquetas = proteína real + vegetales frescos + cero conservadores.
Esto es importante: nunca decir que reemplaza la comida, siempre hablar de complemento o upgrade.

## Voz y tono
- Directo, seguro y sin rodeos — como la marca: "Sin mamadas", "Sin letras chiquitas"
- Cercano y cálido, como alguien que de verdad ama a los perros
- Educativo pero sin ser aburrido ni técnico
- En español mexicano natural (no formal, no vulgar)
- Usa "tu perro" / "tu peludo" / "tu compañero", nunca "tu mascota" (suena distante)
- El origen de Apolo (perro rescatado) puede usarse para contenido emocional auténtico

## Ingredientes reales de Mr. Apolo
Receta Olímpico: pollo fresco desmenuzado, zanahoria, espinaca, calabacita, arroz integral.
Receta Titán: pollo fresco desmenuzado, zanahoria, calabacita, hígado de res, arroz integral.
IMPORTANTE: Todo el contenido debe girar alrededor de ESTOS ingredientes o temas generales de salud canina. No inventar ingredientes que no existen en el producto.

## Reglas de contenido
1. Siempre hablar de complemento/upgrade, nunca de reemplazo
2. Beneficio concreto y real en cada post, basado en los ingredientes reales del producto
3. Nunca atacar directamente a otras marcas
4. Llamada a la acción clara al final (WhatsApp, DM o bio)
5. Los emojis complementan, no saturan (máx 4-5 por caption)
6. Hashtags al final, separados del texto. MÁXIMO 5 hashtags.
7. Horarios ideales: 8:00am / 7:00pm (hora CDMX)
8. PROHIBIDO usar guiones (-) en el texto. Usar punto, coma o salto de línea.
9. No sonar como IA. Escribir como persona real que ama a los perros.
10. Solo generar contenido sobre: los ingredientes del producto, beneficios de esos ingredientes, o salud/nutrición canina general. Nunca inventar o prometer ingredientes que no tiene el producto.

## Formato de salida
Siempre responde con este formato JSON exacto:
{
  "caption": "texto completo del caption listo para publicar",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
  "descripcion_visual": "descripción detallada de la imagen o video: fondo, iluminación, elementos, posición del perro",
  "horario_sugerido": "ej: 8:00am — alta apertura matutina",
  "por_que_funciona": "explicación breve de por qué este contenido va a generar engagement"
}
"""

# Hashtags base de la marca
HASHTAGS_BASE = [
    "#MrApolo",
    "#ComplementoFrescoPerros",
    "#AlimentoNaturalPerros",
    "#PerrosSaludables",
    "#CDMX",
]

# ─────────────────────────────────────────
# IDENTIDAD VISUAL DE LA MARCA
# Extraída de www.mrapolo.com
# ─────────────────────────────────────────
BRAND_COLORS = {
    "negro_fondo":  "#1C1C1C",   # Color principal del sitio web
    "negro_profundo": "#0A0A0A", # Fondo más oscuro para contraste
    "dorado":       "#C9A84C",   # Acentos premium, bordes, títulos
    "blanco":       "#FFFFFF",   # Texto principal
    "crema":        "#F5F0E8",   # Texto secundario suave
}

BRAND_STYLE = """Estilo visual Mr. Apolo:
- Fondo oscuro (#1C1C1C o #0A0A0A), estética premium y oscura
- Acentos y títulos en dorado (#C9A84C)
- Tipografía bold, grande, impactante — estilo editorial
- Ingredientes frescos reales visibles: pollo, zanahoria, espinaca, calabacita
- Mascota: perro negro con pecho blanco, lengua afuera, expresivo y feliz — estilo CARTOON REALISTA igual que el logo
- Logo oficial siempre presente: círculo dorado, perro cartoon, 'MR APOLO' en dorado, tagline curvo en dorado
- Estilo ilustración: cartoon educativo con detalles semi-realistas (no fotorrealista, no demasiado infantil)
- Sin filtros excesivos. Limpio, apetitoso, directo.
- Composición ordenada con jerarquía visual clara
- Tagline disponible: 'Comida de campeones, al alcance de todos.'

## Estilo infografía educativa MITAD Y MITAD (usar para posts educativos):
Divide la imagen cuadrada en DOS mitades verticales o con forma orgánica:
- MITAD IZQUIERDA: ilustración cartoon del concepto (ej: el perro feliz comiendo, ingredientes animados, iconos educativos estilo cartoon)
- MITAD DERECHA: texto educativo con título bold dorado, puntos clave en blanco, fondo negro
- Logo Mr. Apolo en esquina inferior, pequeño pero visible
- Paleta: negro fondo, dorado para títulos, blanco para texto, acentos del color del ingrediente destacado"""

# ─────────────────────────────────────────
# DESCRIPCIÓN EXACTA DEL EMPAQUE (Sobre Olímpico)
# Usar esta descripción en prompts de imagen para que la IA lo replique
# ─────────────────────────────────────────
LOGO_DESCRIPCION = """Logo circular oficial de Mr. Apolo (úsalo exactamente así):
- Fondo circular negro oscuro (#0A0A0A) con borde circular dorado (#C9A84C)
- Texto 'MR APOLO' en letras bold doradas en la parte superior del círculo, tipografía sans-serif impactante
- Al centro: ilustración estilo cartoon realista de un perro negro con pecho blanco, lengua afuera lamiéndose, expresión feliz y energética
- Rodeando al perro dentro del círculo: zanahorias naranjas, hojas de espinaca verde, calabacita
- Texto curvo en dorado en la parte inferior del círculo: 'comida de campeones, al alcance de todos.'
- En la base (fuera del círculo) texto blanco pequeño: www.mrapolo.com | @mr.apolo_petfood | @mcapolo.pet.food"""

DESCRIPCION_EMPAQUE = {
    "olimpico": """Bolsa transparente de plástico sellada al vacío.
A través de la bolsa se ve la comida fresca: mezcla rústica en tonos café, naranja y verde oscuro (pollo, zanahoria, espinaca).
Etiqueta cuadrada negra (#0A0A0A) al centro con el logo oficial Mr. Apolo:
  - Círculo dorado con 'MR APOLO' arriba en dorado bold
  - Perro negro con pecho blanco, lengua afuera, estilo cartoon realista
  - Rodeado de zanahorias y espinaca dentro del círculo
  - 'comida de campeones, al alcance de todos.' curvo en dorado abajo
Bolsa sobre superficie oscura, fondo negro premium.""",

    "titan": """Bolsa transparente de plástico sellada al vacío.
A través de la bolsa se ve la comida fresca: trozos visibles de pollo desmenuzado, zanahoria naranja, calabacita verde en cubos.
Etiqueta cuadrada negra (#0A0A0A) al centro con el logo oficial Mr. Apolo:
  - Círculo dorado con 'MR APOLO' arriba en dorado bold
  - Perro negro con pecho blanco, lengua afuera, estilo cartoon realista
  - Rodeado de zanahorias y calabacita dentro del círculo
  - 'comida de campeones, al alcance de todos.' curvo en dorado abajo
Bolsa sobre tabla de madera de cocina, ingredientes frescos al lado."""
}

BRAND_WEBSITE = "https://www.mrapolo.com"
BRAND_INSTAGRAM = "@mr.apolo_petfood"
BRAND_WHATSAPP = "5215538953371"

# ─────────────────────────────────────────
# PRODUCTOS
# ─────────────────────────────────────────
PRODUCTOS = {
    "olimpico": "Sobre Olímpico — receta para perros activos",
    "titan":    "Sobre Titán — receta para perros con necesidades especiales",
}

# ─────────────────────────────────────────
# COMPETIDORES A MONITOREAR
# ─────────────────────────────────────────
COMPETIDORES = {
    # ── Referentes internacionales ──────────────────────────────
    "thefarmersdogofficial": "Comida fresca premium USA — referente de contenido educativo",
    "olliepetfood":          "Comida fresca USA — storytelling emocional",
    "nomnomnow":             "Comida fresca USA — contenido visual fuerte",

    # ── Marcas locales CDMX / México ────────────────────────────
    "kunay_mx":       "Competidor local México",
    "mutt.mx":        "Competidor local México",
    "bleiz_dogfood":  "Competidor local México",
    "petgourmet_mx":  "Competidor local México",
    "frankiefordogs": "Competidor local México",
    "wagandlove":     "Competidor local México",
    "soydoggera":     "Competidor local México",
    "lulapetclan":    "Competidor local México",
    "truf.pet":       "Competidor local México",
    "petstable":      "Competidor local México",
    "ilovemydogmx":   "Competidor local México",
}

HASHTAGS_MONITOREAR = [
    "AlimentoFrescoPerros",
    "ComidaParaPerros",
    "ComidaCaseraPerros",
    "PerrosSaludablesMexico",
    "RawFeedingMexico",
    "AlimentacionNaturalPerros",
]

# Posts mínimos de likes para considerar "exitoso"
ENGAGEMENT_MINIMO_LIKES = 100

# Cuántos posts top scrapeear por cuenta
POSTS_POR_CUENTA = 12
