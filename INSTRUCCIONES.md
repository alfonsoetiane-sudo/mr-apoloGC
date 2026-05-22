# Mr. Apolo — Sistema de Contenido con IA

## Cómo empezar HOY (5 minutos)

### 1. Instala la dependencia
```bash
pip install anthropic
```

### 2. Configura tu API key
```bash
# Mac/Linux:
export ANTHROPIC_API_KEY=sk-ant-tu-key-aqui

# Windows CMD:
set ANTHROPIC_API_KEY=sk-ant-tu-key-aqui

# Windows PowerShell:
$env:ANTHROPIC_API_KEY="sk-ant-tu-key-aqui"
```
Obtén tu API key en: https://console.anthropic.com

### 3. Corre el generador
```bash
python content_generator.py
```

El sistema te pregunta el tema del post, genera el contenido completo y te permite aprobarlo o pedir cambios. **Cada feedback que das queda guardado y mejora los próximos posts automáticamente.**

---

## Archivos del sistema

| Archivo | Qué hace |
|---|---|
| `mr_apolo_brand.py` | Voz de marca, reglas y hashtags base. **Edita aquí para ajustar el tono.** |
| `content_generator.py` | Generador principal. Córrelo para generar contenido. |
| `feedback_history.json` | Se crea automáticamente. Guarda todo tu feedback. |
| `contenido_aprobado.json` | Historial de posts aprobados. |
| `make_blueprint.json` | Blueprint para importar en Make.com (fase de automatización). |

---

## Loop de feedback

Cuando generas un post tienes 5 opciones:

1. **✅ Aprobar** — Guarda y listo
2. **✏️ Aprobar con comentario** — Guarda + agrega nota para mejorar futuros
3. **🔄 Rechazar y regenerar** — Das la razón, el agente genera uno nuevo inmediatamente
4. **📝 Rechazar y modificar** — Copias el texto y lo editas tú
5. **🚪 Salir sin guardar**

Cada rechazo o aprobación alimenta el historial de feedback. Después de 3-5 posts el agente ya conoce tu gusto.

---

## Cuándo conectar Make.com (Fase 2)

Cuando el generador te esté dando posts buenos consistentemente, conectas Make.com con:
1. **Apify** — Scraping de Instagram de competidores
2. **Claude API** — Ya integrado en el generador
3. **WhatsApp** — Entrega diaria a tu teléfono
4. **Meta Graph API** — Publicación automática al aprobar

Importa `make_blueprint.json` en Make.com y configura las credenciales marcadas con `{{MAYÚSCULAS}}`.
