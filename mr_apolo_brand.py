"""
Mr. Apolo — Brand Voice & System Prompt
========================================
Edita este archivo para ajustar la voz, tono y reglas de contenido de Mr. Apolo.
"""

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

## Reglas de contenido
1. Siempre hablar de complemento/upgrade, nunca de reemplazo
2. Beneficio concreto y real en cada post
3. Nunca atacar directamente a otras marcas
4. Llamada a la acción clara al final (WhatsApp, DM o bio)
5. Los emojis complementan, no saturan (máx 4-5 por caption)
6. Hashtags al final, separados del texto. MÁXIMO 5 hashtags.
7. Horarios ideales: 8:00am / 7:00pm (hora CDMX)
8. PROHIBIDO usar guiones (-) en el texto. Usar punto, coma o salto de línea.
9. No sonar como IA. Escribir como persona real que ama a los perros.

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

BRAND_STYLE = """Estilo visual Mr. Apolo (basado en www.mrapolo.com):
- Fondo oscuro (#1C1C1C o #0A0A0A), estética premium y oscura
- Acentos y títulos en dorado (#C9A84C)
- Tipografía bold, grande, impactante — estilo editorial
- Ingredientes frescos reales visibles: pollo, zanahoria, espinaca, carne
- Mascota: perro negro con pecho blanco, lengua afuera, expresivo y feliz
- Sobres del producto como elemento visual cuando aplique
- Sin filtros excesivos. Limpio, apetitoso, directo.
- Composición ordenada con jerarquía visual clara
- Estilo: entre premium mexicano y marca de athleisure — serio pero accesible
- Tagline disponible: 'Comida de campeones, al alcance de todos.'"""

# ─────────────────────────────────────────
# DESCRIPCIÓN EXACTA DEL EMPAQUE (Sobre Olímpico)
# Usar esta descripción en prompts de imagen para que la IA lo replique
# ─────────────────────────────────────────
DESCRIPCION_EMPAQUE = {
    "olimpico": """Bolsa transparente de plástico sellada al vacío.
A través de la bolsa se ve la comida fresca: mezcla rústica en tonos café, naranja y verde oscuro.
Etiqueta cuadrada negra (#0A0A0A) al centro con:
  - 'MR APOLO' en letras grandes doradas (#C9A84C) arriba
  - Logo circular: perro negro con pecho blanco y lengua afuera, rodeado de zanahorias, verduras y carne cruda, borde dorado
  - 'Comida de campeones, al alcance de todos.' en dorado curvo abajo del círculo
  - www.mrapolo.com y redes sociales en texto blanco pequeño en la base
Bolsa sobre madera rústica, fondo beige/crema neutro.""",

    "titan": """Bolsa transparente de plástico sellada al vacío.
A través de la bolsa se ve la comida fresca: mezcla con trozos visibles de pollo desmenuzado, zanahoria naranja, calabacita verde en cubos, en caldo claro.
Etiqueta cuadrada negra (#0A0A0A) al centro con:
  - 'MR APOLO' en letras grandes doradas (#C9A84C) arriba
  - Logo circular: perro negro con pecho blanco y lengua afuera, rodeado de zanahorias, calabacita y trozos de pollo, borde dorado
  - 'Comida de campeones, al alcance de todos.' en dorado curvo abajo del círculo
  - www.mrapole.com y redes sociales en texto blanco pequeño en la base
Bolsa sobre tabla de madera de cocina, con zanahorias y romero frescos al lado derecho, cocina de fondo desenfocada."""
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
