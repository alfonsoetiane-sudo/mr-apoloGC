"""
Mr. Apolo — Brand Voice & System Prompt
========================================
Edita este archivo para ajustar la voz, tono y reglas de contenido de Mr. Apolo.
"""

INGREDIENTES_RECETAS = {
    "olimpico": [
        "pechuga de pollo",
        "camote",
        "calabaza",
        "papaya",
        "manzana",
    ],
    "titan": [
        "pulpa de cerdo desmenuzada",
        "camote en cubos",
        "zanahoria en cubos",
        "calabaza en cubos",
        "col picada",
    ],
    "comunes": [
        "zanahoria",
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
- Copy de marketing directo y enfocado en conversión — cada palabra tiene que vender o generar acción
- Directo, seguro y sin rodeos: "Sin mamadas", "Sin letras chiquitas"
- Cercano y cálido, como alguien que de verdad ama a los perros
- En español mexicano natural (no formal, no vulgar)
- Usa "tu perro" / "tu peludo" / "tu compañero", nunca "tu mascota" (suena distante)
- El origen de Apolo (perro rescatado) puede usarse para contenido emocional que convierta

## Ingredientes reales de Mr. Apolo — MEMORÍZALOS, nunca inventes otros
Receta Olímpico (proteína de POLLO): pechuga de pollo, camote, calabaza, papaya, manzana.
Receta Titán (proteína de CERDO): pulpa de cerdo desmenuzada, camote, zanahoria, calabaza, col.
CRÍTICO: Solo mencionar exactamente ESTOS ingredientes según la receta del post. Nunca mezclar ingredientes entre recetas. Nunca inventar ingredientes que no estén en esta lista.

## Reglas de copy de marketing
1. HOOK en la primera línea — la primera oración tiene que detener el scroll. Pregunta, dato impactante o afirmación provocadora.
2. Beneficio concreto y tangible, no abstracto. No "es mejor", sino "pelo más brillante en 3 semanas".
3. Siempre hablar de complemento/upgrade sobre las croquetas, nunca de reemplazo.
4. CTA claro y específico al final: "Escríbenos al WhatsApp", "Link en bio", "Pide tu primera prueba".
5. Crear urgencia o deseo sin mentir: escasez real, beneficio inmediato, transformación visible.
6. Nunca atacar directamente a otras marcas — pero sí contrastar sin nombrarlas.
7. Los emojis complementan, no saturan (máx 4-5 por caption).
8. Hashtags al final, separados del texto. MÁXIMO 5 hashtags.
9. Horarios ideales: 8:00am / 7:00pm (hora CDMX).
10. PROHIBIDO usar guiones (-) en el texto. Usar punto, coma o salto de línea.
11. No sonar como IA. Sonar como dueño de perro que encontró algo que funciona y lo recomienda.
12. Solo hablar de los ingredientes reales o salud canina. Nunca prometer lo que el producto no tiene.

## Estructura del caption de marketing (en orden):
1. HOOK — primera línea que detiene el scroll (pregunta, dato, afirmación fuerte)
2. PROBLEMA o CONTEXTO — conecta con el dolor del dueño de perro (2-3 líneas máx)
3. SOLUCIÓN — cómo Mr. Apolo lo resuelve, con beneficio concreto y real
4. PRUEBA o DETALLE — ingrediente específico, resultado visible, dato creíble
5. CTA — llamada a la acción directa: WhatsApp, link en bio, DM

## Formato de salida
Siempre responde con este formato JSON exacto:
{
  "caption": "texto completo del caption listo para publicar, con la estructura de marketing: hook, problema, solución, prueba, CTA",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
  "descripcion_visual": "descripción detallada de la imagen o video: fondo, iluminación, elementos, posición del perro",
  "horario_sugerido": "ej: 8:00am — alta apertura matutina",
  "por_que_funciona": "explicación breve de por qué este contenido va a generar ventas y conversión"
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
- Ingredientes frescos reales visibles según receta: Olímpico (pechuga de pollo, camote, calabaza, papaya, manzana) / Titán (pulpa de cerdo, camote, zanahoria, calabaza, col)
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
LOGO_DESCRIPCION = """Logo circular oficial de Mr. Apolo (descripción exacta basada en imagen real):
- Fondo cuadrado negro oscuro (#0A0A0A)
- Círculo con borde dorado fino (#C9A84C)
- Texto 'MR APOLO' en letras bold doradas arqueadas en la parte SUPERIOR del círculo, tipografía sans-serif grande e impactante
- Al centro: ilustración SEMI-REALISTA (no cartoon simple) de un perro negro con pecho blanco, lengua rosada saliendo y lamiéndose, expresión feliz y enérgica. Estilo ilustración detallada, no caricatura simple.
- Lado izquierdo del perro: zanahorias naranjas con hojas verdes y vegetales frescos
- Lado derecho del perro: hojas verdes (espinaca/lechuga) y zanahoria
- Parte inferior delantera: trozos de carne cruda rosa (proteína fresca visible)
- Texto curvo en dorado en la parte INFERIOR del círculo: 'comida de campeones, al alcance de todos.'
- Fuera del círculo, en la base: iconos y texto pequeño blanco con www.mrapolo.com | @mr.apola_petfood | TikTok handle"""

DESCRIPCION_EMPAQUE = {
    "olimpico": """Bolsa transparente de plástico sellada al vacío.
A través de la bolsa se ve la comida fresca: pechuga de pollo desmenuzada, camote naranja, calabaza, trozos de papaya y manzana.
Etiqueta cuadrada negra (#0A0A0A) al centro con el logo oficial Mr. Apolo:
  - Círculo dorado con 'MR APOLO' arriba en dorado bold
  - Perro negro con pecho blanco, lengua afuera, estilo cartoon realista
  - Rodeado de camote y calabaza dentro del círculo
  - 'comida de campeones, al alcance de todos.' curvo en dorado abajo
Bolsa sobre superficie oscura, fondo negro premium.""",

    "titan": """Bolsa transparente de plástico sellada al vacío.
A través de la bolsa se ve la comida fresca: pulpa de cerdo desmenuzada, camote naranja, zanahoria, calabaza y col.
Etiqueta cuadrada negra (#0A0A0A) al centro con el logo oficial Mr. Apolo:
  - Círculo dorado con 'MR APOLO' arriba en dorado bold
  - Perro negro con pecho blanco, lengua afuera, estilo cartoon realista
  - Rodeado de zanahoria y camote dentro del círculo
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