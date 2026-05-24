"""
Mr. Apolo — Generador de Contenido con Feedback Loop
======================================================
Uso:
    python content_generator.py

Requiere:
    pip install anthropic
    Variable de entorno: ANTHROPIC_API_KEY=sk-ant-...

El feedback que des se guarda en feedback_history.json y mejora
automáticamente los próximos contenidos.
"""

import os
import json
import datetime
import anthropic
from mr_apolo_brand import BRAND_SYSTEM_PROMPT, HASHTAGS_BASE
import sheets_storage

# ─────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────
HISTORIAL_FILE = "contenido_aprobado.json"
MAX_FEEDBACK_EN_CONTEXTO = 5   # Cuántos feedbacks recientes incluir al generar

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


# ─────────────────────────────────────────
# FEEDBACK — Cargar y guardar (via Google Sheets)
# ─────────────────────────────────────────

def cargar_feedback():
    """Lee el historial de feedback desde Google Sheets."""
    return sheets_storage.cargar_feedback()

def agregar_feedback(contenido_generado: dict, tipo: str, comentario: str):
    """
    tipo: 'aprobado' | 'rechazado' | 'modificado'
    Guarda en Google Sheets para que persista entre deploys de Railway.
    """
    entrada = {
        "fecha": datetime.datetime.now().isoformat(),
        "tipo": tipo,
        "comentario": comentario,
        "caption_generado": contenido_generado.get("caption", ""),
        "hashtags_generados": contenido_generado.get("hashtags", []),
    }
    sheets_storage.agregar_feedback(entrada)
    print(f"✓ Feedback guardado ({tipo})")


# ─────────────────────────────────────────
# HISTORIAL — Guardar contenido aprobado
# ─────────────────────────────────────────

def guardar_aprobado(contenido: dict, tema: str):
    historial = []
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            historial = json.load(f)
    historial.append({
        "fecha": datetime.datetime.now().isoformat(),
        "tema": tema,
        **contenido
    })
    with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────
# GENERAR CONTENIDO
# ─────────────────────────────────────────

def construir_contexto_feedback() -> str:
    """Toma los últimos N feedbacks y los convierte en instrucciones para el modelo."""
    feedback_list = cargar_feedback()
    if not feedback_list:
        return ""

    recientes = feedback_list[-MAX_FEEDBACK_EN_CONTEXTO:]
    partes = ["\n## Retroalimentación de publicaciones anteriores (aprende de esto):\n"]

    for fb in recientes:
        emoji = "✅" if fb["tipo"] == "aprobado" else "❌" if fb["tipo"] == "rechazado" else "✏️"
        partes.append(f"{emoji} [{fb['tipo'].upper()}] {fb['fecha'][:10]}")
        if fb["comentario"]:
            partes.append(f"   Comentario: {fb['comentario']}")
        partes.append(f"   Caption anterior: {fb['caption_generado'][:120]}...")
        partes.append("")

    return "\n".join(partes)


def generar_contenido(tema: str, contexto_extra: str = "") -> dict:
    """Genera un post completo para Mr. Apolo dado un tema."""

    feedback_contexto = construir_contexto_feedback()
    hashtags_base_str = " ".join(HASHTAGS_BASE)

    prompt_usuario = f"""Genera un post de Instagram para Mr. Apolo sobre el siguiente tema:

**Tema**: {tema}
{f"**Contexto adicional**: {contexto_extra}" if contexto_extra else ""}

Hashtags base de la marca (incluye algunos de estos): {hashtags_base_str}

{feedback_contexto}

Responde ÚNICAMENTE con el JSON en el formato especificado, sin texto adicional."""

    system_completo = BRAND_SYSTEM_PROMPT

    print("\n⏳ Generando contenido...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_completo,
        messages=[{"role": "user", "content": prompt_usuario}]
    )

    texto = response.content[0].text.strip()

    # Limpiar si viene envuelto en ```json
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    texto = texto.strip()

    return json.loads(texto)


# ─────────────────────────────────────────
# MOSTRAR CONTENIDO
# ─────────────────────────────────────────

def mostrar_contenido(contenido: dict):
    print("\n" + "═" * 55)
    print("📱  CONTENIDO GENERADO — Mr. Apolo")
    print("═" * 55)
    print(f"\n📝 CAPTION:\n{contenido['caption']}")
    print(f"\n#️⃣  HASHTAGS:\n{' '.join(contenido['hashtags'])}")
    print(f"\n🎥 DESCRIPCIÓN VISUAL:\n{contenido['descripcion_visual']}")
    print(f"\n🕐 HORARIO SUGERIDO: {contenido['horario_sugerido']}")
    print(f"\n💡 POR QUÉ FUNCIONA:\n{contenido['por_que_funciona']}")
    print("═" * 55)


# ─────────────────────────────────────────
# LOOP DE FEEDBACK INTERACTIVO
# ─────────────────────────────────────────

def loop_feedback(contenido: dict, tema: str):
    """Pide retroalimentación y permite regenerar si es necesario."""
    while True:
        print("\n¿Qué quieres hacer con este contenido?")
        print("  [1] ✅ Aprobar y guardar")
        print("  [2] ✏️  Aprobar con comentario (para mejorar próximos)")
        print("  [3] 🔄 Rechazar y regenerar (dar razón)")
        print("  [4] 📝 Rechazar y modificar manualmente")
        print("  [5] 🚪 Salir sin guardar")

        opcion = input("\nOpción: ").strip()

        if opcion == "1":
            agregar_feedback(contenido, "aprobado", "")
            guardar_aprobado(contenido, tema)
            print("\n✅ Guardado en contenido_aprobado.json")
            return contenido, False  # (contenido, seguir_generando)

        elif opcion == "2":
            comentario = input("Comentario para mejorar próximos posts: ").strip()
            agregar_feedback(contenido, "aprobado", comentario)
            guardar_aprobado(contenido, tema)
            print("\n✅ Guardado con comentario")
            return contenido, False

        elif opcion == "3":
            razon = input("¿Por qué no te gustó? (el agente aprenderá): ").strip()
            agregar_feedback(contenido, "rechazado", razon)
            print("\n🔄 Regenerando con tu feedback...")
            nuevo = generar_contenido(tema, contexto_extra=f"El usuario rechazó el anterior porque: {razon}")
            mostrar_contenido(nuevo)
            contenido = nuevo  # Actualiza para el siguiente loop

        elif opcion == "4":
            razon = input("¿Qué cambiarías?: ").strip()
            agregar_feedback(contenido, "modificado", razon)
            print("\n📋 Caption copiado para editar manualmente:")
            print(contenido["caption"])
            print("\nHashtags:", " ".join(contenido["hashtags"]))
            guardar_aprobado(contenido, tema)
            return contenido, False

        elif opcion == "5":
            print("Saliendo sin guardar.")
            return contenido, False

        else:
            print("Opción no válida, intenta de nuevo.")


# ─────────────────────────────────────────
# PUNTO DE ENTRADA PRINCIPAL
# ─────────────────────────────────────────

def main():
    print("\n🐾 Mr. Apolo — Generador de Contenido")
    print("─" * 40)
    print("Escribe 'salir' en cualquier momento para terminar\n")

    while True:
        tema = input("📌 Tema del post (ej: 'beneficios del pollo fresco', 'comparar con croquetas'): ").strip()
        if tema.lower() == "salir":
            break
        if not tema:
            print("Por favor escribe un tema.")
            continue

        contexto = input("📎 Contexto adicional (opcional, Enter para omitir): ").strip()

        try:
            contenido = generar_contenido(tema, contexto)
            mostrar_contenido(contenido)
            loop_feedback(contenido, tema)
        except json.JSONDecodeError:
            print("❌ Error al parsear la respuesta. Intenta de nuevo.")
        except anthropic.APIError as e:
            print(f"❌ Error de API: {e}")

        continuar = input("\n¿Generar otro post? (s/n): ").strip().lower()
        if continuar != "s":
            break

    print("\n¡Hasta luego! 🐾")


if __name__ == "__main__":
    main()
                                                                                                                                                                                                 