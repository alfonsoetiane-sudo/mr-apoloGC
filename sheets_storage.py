"""
Mr. Apolo — Persistencia en Google Sheets
==========================================
Reemplaza los archivos JSON locales (que Railway borra en cada deploy)
con hojas de Google Sheets que persisten para siempre.

Hojas requeridas en el spreadsheet:
  - rotacion_temas   → estado de qué categorías/temas ya se usaron
  - feedback_history → historial de aprobaciones/rechazos del usuario
  - estado_pipeline  → posts del día pendientes de aprobación

Variable de entorno requerida:
  GOOGLE_SHEETS_ID   → ID del spreadsheet (ya lo tienes del agente de ventas)
  GOOGLE_CREDENTIALS_BASE64 → credenciales de service account (ya las tienes)
"""

import os
import json
import base64
import logging
from datetime import datetime

log = logging.getLogger("sheets_storage")

# ──────────────────────────────────────────
# INICIALIZACIÓN DEL CLIENTE DE SHEETS
# ──────────────────────────────────────────

_gc = None  # cliente gspread cacheado
_sh = None  # spreadsheet cacheado


def _get_sheet():
    """Devuelve el spreadsheet. Inicializa la conexión si aún no existe."""
    global _gc, _sh
    if _sh is not None:
        return _sh

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds_b64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
        if not creds_b64:
            raise ValueError("GOOGLE_CREDENTIALS_BASE64 no configurado")

        creds_json = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
        creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
        _gc = gspread.authorize(creds)

        sheet_id = os.environ.get("GOOGLE_SHEETS_ID") or os.environ.get("SHEET_ID")
        if not sheet_id:
            raise ValueError("SHEET_ID no configurado")

        _sh = _gc.open_by_key(sheet_id)
        log.info("✅ Google Sheets conectado")
        return _sh

    except Exception as e:
        log.error(f"❌ Error conectando a Google Sheets: {e}")
        raise


def _get_or_create_tab(nombre: str):
    """Obtiene o crea una pestaña en el spreadsheet."""
    sh = _get_sheet()
    try:
        return sh.worksheet(nombre)
    except Exception:
        log.info(f"📋 Creando pestaña '{nombre}'...")
        ws = sh.add_worksheet(title=nombre, rows=1000, cols=10)
        return ws


# ──────────────────────────────────────────
# ROTACIÓN DE TEMAS
# ──────────────────────────────────────────

ROTACION_TAB = "rotacion_temas"


def cargar_rotacion() -> dict:
    """Lee el estado de rotación de temas desde Google Sheets."""
    try:
        ws = _get_or_create_tab(ROTACION_TAB)
        data = ws.get_all_values()
        if not data or len(data) < 2:
            return {"categorias_usadas": [], "temas_usados": {}}
        # Fila 1: headers, Fila 2: JSON con el estado
        json_str = data[1][0] if data[1] else ""
        if not json_str:
            return {"categorias_usadas": [], "temas_usados": {}}
        return json.loads(json_str)
    except Exception as e:
        log.error(f"❌ Error cargando rotación: {e}")
        return {"categorias_usadas": [], "temas_usados": {}}


def guardar_rotacion(estado: dict):
    """Escribe el estado de rotación en Google Sheets."""
    try:
        ws = _get_or_create_tab(ROTACION_TAB)
        ws.clear()
        ws.update("A1", [["estado_json"], [json.dumps(estado, ensure_ascii=False)]])
        log.info("💾 Rotación guardada en Sheets")
    except Exception as e:
        log.error(f"❌ Error guardando rotación: {e}")


# ──────────────────────────────────────────
# FEEDBACK HISTORY
# ──────────────────────────────────────────

FEEDBACK_TAB = "feedback_history"


def cargar_feedback() -> list:
    """Lee el historial de feedback desde Google Sheets."""
    try:
        ws = _get_or_create_tab(FEEDBACK_TAB)
        data = ws.get_all_values()
        if not data or len(data) < 2:
            return []
        # Cada fila (desde fila 2) es un JSON de entrada de feedback
        resultado = []
        for fila in data[1:]:
            if fila and fila[0]:
                try:
                    resultado.append(json.loads(fila[0]))
                except Exception:
                    pass
        return resultado
    except Exception as e:
        log.error(f"❌ Error cargando feedback: {e}")
        return []


def agregar_feedback(entrada: dict):
    """Agrega una entrada de feedback en Google Sheets (append)."""
    try:
        ws = _get_or_create_tab(FEEDBACK_TAB)
        data = ws.get_all_values()
        if not data:
            # Crear header si la hoja está vacía
            ws.update("A1", [["entrada_json"]])
        ws.append_row([json.dumps(entrada, ensure_ascii=False)])
        log.info(f"✅ Feedback guardado en Sheets ({entrada.get('tipo', '?')})")
    except Exception as e:
        log.error(f"❌ Error guardando feedback: {e}")


# ──────────────────────────────────────────
# ESTADO DEL PIPELINE
# ──────────────────────────────────────────

PIPELINE_TAB = "estado_pipeline"


def cargar_estado() -> dict | None:
    """Lee el estado del pipeline desde Google Sheets."""
    try:
        ws = _get_or_create_tab(PIPELINE_TAB)
        data = ws.get_all_values()
        if not data or len(data) < 2:
            return None
        json_str = data[1][0] if data[1] else ""
        if not json_str:
            return None
        return json.loads(json_str)
    except Exception as e:
        log.error(f"❌ Error cargando estado pipeline: {e}")
        return None


def guardar_estado(estado: dict):
    """Escribe el estado completo del pipeline en Google Sheets."""
    try:
        ws = _get_or_create_tab(PIPELINE_TAB)
        ws.clear()
        ws.update("A1", [["estado_json"], [json.dumps(estado, ensure_ascii=False)]])
        log.info("💾 Estado pipeline guardado en Sheets")
    except Exception as e:
        log.error(f"❌ Error guardando estado pipeline: {e}")
