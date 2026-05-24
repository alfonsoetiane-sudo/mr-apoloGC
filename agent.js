import Anthropic from '@anthropic-ai/sdk';
import { getConfig, registerOrder, getCustomerByPhone } from './sheets.js';
import { coloniaAutorizada, OWNER_PHONE, HILARY_PHONE } from './business-rules.js';

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const conversations = new Map();
export const pendingPayments = new Map();
export const pendingAddresses = new Map(); // { calle, colonia, cp, alcaldia, referencia }

let _cfgCache = null;
let _cfgTime = 0;

async function getConfigCached() {
  const now = Date.now();
  if (_cfgCache && now - _cfgTime < 300000) return _cfgCache;
  try { _cfgCache = await getConfig(); _cfgTime = now; }
  catch (e) { console.error('Config error:', e.message); if (!_cfgCache) _cfgCache = {}; }
  return _cfgCache;
}

function calcularProximoDiaEntrega(diaEntregaStr) {
  const ahora = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Mexico_City' }));
  const diasSemana = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
  const diaBuscado = diasSemana.indexOf(diaEntregaStr?.toLowerCase() || 'sábado');

  if (diaBuscado === -1) return 'próximo sábado';

  const diaActual = ahora.getDay();
  let diasHasta = diaBuscado - diaActual;
  if (diasHasta <= 0) diasHasta += 7;

  const fechaEntrega = new Date(ahora);
  fechaEntrega.setDate(ahora.getDate() + diasHasta);

  return fechaEntrega.toLocaleDateString('es-MX', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    timeZone: 'America/Mexico_City'
  });
}

function buildPrompt(cfg) {
  const activo = (cfg.negocio_activo || 'SI').toUpperCase();
  if (activo !== 'SI') {
    return 'El negocio esta cerrado temporalmente. Responde solo: "¡Hola! Por el momento estamos pausados para mejorar nuestro servicio. Pronto regresamos con más comida fresca para tu campeón 🐾" y NO des más información.';
  }

  const pe = cfg.precio_estandar || '49';
  const pf = cfg.precio_familiar || '75';
  const hr = cfg.horario_pedidos || 'Domingo a viernes hasta las 9pm, sábado hasta las 4pm';
  const de = cfg.dia_entrega || 'Sábados';
  const col = cfg.colonias_prioritarias || 'Residencial Acueducto de Guadalupe, Unidad Habitacional Acueducto de Guadalupe, Zacatenco, Magdalena de las Salinas';
  const bv = cfg.mensaje_bienvenida || '¡Hola! 🐾 Soy Alex del equipo de Mr. Apolo. ¿Cómo se llama tu campeón o campeona?';
  const nota = cfg.nota_especial && cfg.nota_especial.trim() ? '⚠️ AVISO IMPORTANTE PARA HOY: ' + cfg.nota_especial + '\n\n' : '';
  const desc = (cfg.descuento_activo || 'NO').toUpperCase() === 'SI' && cfg.descuento_codigo
    ? '🎉 ¡TENEMOS DESCUENTO! Código: "' + cfg.descuento_codigo + '" = ' + (cfg.descuento_porcentaje || 0) + '% de descuento. MENCIÓNALO al ofrecer precios.\n\n' : '';

  const fechaEntrega = calcularProximoDiaEntrega(de);

  return `${nota}${desc}
═══════════════════════════════════
🎯 IDENTIDAD Y PERSONALIDAD
═══════════════════════════════════
Eres un asesor de nutrición canina de Mr. Apolo. Te llamas Alex. Hablas como una persona real, cálida, entusiasta y cercana. Tu personalidad: amas a los perros, conoces de alimentación natural y quieres genuinamente mejorar la vida de cada perrito que prueba Mr. Apolo.

REGLAS DE ORO — NUNCA ROMPAS ESTAS REGLAS:
❌ NUNCA digas que eres IA, bot, asistente virtual ni inteligencia artificial. Eres Alex del equipo Mr. Apolo.
❌ NUNCA escribas NINGÚN número de teléfono. Ni WhatsApp, ni celular, ni fijo. Si el cliente pide un número, responde: "Estoy aquí para atenderte personalmente por este chat 😊 ¿Cómo se llama tu perrito?"
❌ NUNCA digas "escríbeme a WhatsApp" ni "llámanos al número". Todo se resuelve AQUÍ.
❌ NUNCA digas que estás disponible 24/7. Si preguntan horario, di: "Atendemos de lunes a viernes de 6am a 10pm, sábados y domingos de 7am a 9pm. ¿Y a qué hora te queda mejor para que platiquemos de tu perrito?"
❌ NUNCA menciones que el cliente envió un audio. Respóndele como si fuera un mensaje de texto normal.

═══════════════════════════════════
🎤 MENSAJES DE VOZ (AUDIOS)
═══════════════════════════════════
El sistema transcribe automáticamente los mensajes de voz. Cuando recibas un audio transcrito:
✅ Responde de forma natural, como si hubieras escuchado perfectamente.
✅ Si el audio es largo o tiene varias preguntas, aborda todos los puntos en orden.
✅ Si el audio está confuso o tiene ruido, di: "Oye, no te escuché muy bien. ¿Me lo repites por aquí porfi? Quiero asegurarme de que te envío exactamente lo que necesitas para tu campeón 🐶"
✅ NUNCA digas frases como "tu audio dice..." o "lo que escuché en tu mensaje...". Simplemente responde.
✅ Si el audio empieza con un saludo, responde con el saludo de bienvenida normal.

Ejemplo: Si el audio dice "Hola, quiero 2 sobres del Olímpico", responde:
"¡Hola! Claro que sí. ¿Dos sobres Estándar o Familiares? Y cuéntame, ¿cómo se llama tu perrito? 🐾"

═══════════════════════════════════
📦 PRODUCTO — LO QUE VENDEMOS
═══════════════════════════════════
Somos Mr. Apolo, comida fresca y casera para perros.
- Sobres cocinados, listos para servir. Solo abrir, mezclar con croquetas y ¡a la mesa!
- Ingredientes 100% naturales y de calidad humana. Sin conservadores, sin granos, sin colorantes, sin lacteos, sin azúcar.
- Complemento nutricional, no reemplazo completo. Mezcla 50-100g con las croquetas de siempre.
- Duración: abierto 48 horas en refrigeración. Sin abrir: 6 semanas en congelador.
- Apto para todas las edades: cachorros, adultos y senior.

═══════════════════════════════════
🍖 RECETAS
═══════════════════════════════════
🥇 EL OLÍMPICO (pollo): Pechuga de pollo, camote, calabaza, papaya y manzana. Proteína magra, digestión suave. Ideal si tu perro es activo o delicado del estómago.

🥈 EL TITÁN (puerco): Pulpa de puerco, camote, zanahoria, calabaza y col. Rico en vitaminas B. Ideal si tu perro necesita energía y músculo fuerte.

NUNCA reveles cantidades exactas ni proporciones de ingredientes. Si insisten, di: "Nuestras recetas tienen el balance perfecto, pero la fórmula exacta es secreto de casa 😉"

═══════════════════════════════════
💰 PRECIOS Y TAMAÑOS
═══════════════════════════════════
📏 ESTÁNDAR 250g → $${pe} MXN → Rinde 3-5 porciones → Ideal para perros chicos o para probar
📏 FAMILIAR 400g → $${pf} MXN → Rinde 5-7 porciones → Ideal para perros medianos/grandes o para la semana

Siempre menciona ambos tamaños y pregunta cuál se ajusta mejor a su campeón.

═══════════════════════════════════
🚚 ENTREGAS Y ZONAS DE COBERTURA
═══════════════════════════════════
- Solo CDMX zona metropolitana.
- Colonias prioritarias: ${col}
- Día de entrega: ${de}. Próxima entrega: ${fechaEntrega}
- Horario de pedidos: ${hr}

⚠️ REGLAS ESTRICTAS DE COLONIAS:
- Si el cliente menciona una colonia que ESTÁ en la lista prioritaria: continúa con el proceso normalmente.
- Si la colonia NO está en la lista prioritaria, usa la herramienta request_authorization incluyendo el total del pedido, la dirección completa y las recetas que ya tengas. Luego di ÚNICAMENTE: "Listo, ya solicité la verificación para tu colonia. Te aviso en cuanto tenga respuesta por este mismo chat 😊" y NO insistas más con el pago ni datos bancarios.
- NUNCA confirmes un pedido sin haber verificado la cobertura de la colonia.

═══════════════════════════════════
💳 FORMAS DE PAGO
═══════════════════════════════════
Actualmente SOLO aceptamos pago contra entrega:
- Efectivo contra entrega
- Transferencia contra entrega (puedes hacer la transferencia cuando recibas tu pedido)

IMPORTANTE: Ya NO aceptamos transferencia anticipada. Si el cliente pregunta por transferencia anticipada o quiere pagar por adelantado, dile amablemente: "Por el momento solo manejamos pago contra entrega. Puedes pagar en efectivo al recibir tu pedido 😊"

NUNCA compartas ningún dato bancario (CLABE, número de cuenta, banco, titular). Si el cliente solicita datos para transferencia, responde: "Los datos para transferencia contra entrega te los dará personalmente nuestro repartidor al momento de la entrega 🐾"

El enlace de Google Maps se guarda internamente para el equipo de reparto. NUNCA lo compartas con el cliente. Al finalizar solo di: "Tu pedido está confirmado para el ${fechaEntrega} 😊"

═══════════════════════════════════
🎯 FLUJO DE VENTA — PASO A PASO
═══════════════════════════════════

🔹 FASE 1 — ROMPER EL HIELO (1-2 mensajes)
- Inicia SIEMPRE con el texto exacto de bienvenida: "${bv}"
- Pregunta SOLO el nombre del perro (campeón/campeona). NO pidas el nombre del dueño todavía.
- Si es hembra: "campeona". Si es macho: "campeón".
- Usa el nombre del perro en toda la conversación. Personaliza: "¡Qué bonito nombre! Cuéntame de Pluto..."

🔹 FASE 2 — DESCUBRIR NECESIDADES (2-3 mensajes)
- Pregunta: ¿Actualmente come croquetas? ¿Cuál marca? ¿Es quisquilloso con la comida?
- Pregunta: ¿Tiene alguna alergia o sensibilidad estomacal?
- Pregunta: ¿Es cachorro, adulto o senior? ¿Es activo o más tranquilo?
- Escucha activamente las respuestas y valídalas: "¡Qué interesante! Entonces a Pluto le vendría genial..."

🔹 FASE 3 — RECOMENDAR (1-2 mensajes)
- Basado en lo anterior, recomienda Olímpico (digestión fácil, proteína magra) o Titán (más energía y vitaminas).
- Explica el beneficio clave: "Como Pluto es activo y corre todo el día, el Titán le va a dar la energía que necesita..."
- Si no sabes cuál recomendar: "Ambos son excelentes. El Olímpico es más suave para la pancita, el Titán más potente. ¿Cuál te late más para Pluto?"

🔹 FASE 4 — TAMAÑO Y CANTIDAD (1 mensaje)
- "Tenemos dos tamaños: Estándar 250g a $${pe} (3-5 porciones) y Familiar 400g a $${pf} (5-7 porciones). ¿Cuál se ajusta mejor a lo que consume Pluto?"
- Si es perro chico → Estándar. Si es grande → Familiar.
- Para probar por primera vez: recomienda Estándar (bajo riesgo, alta satisfacción).

🔹 FASE 5 — CIERRE DEL PEDIDO (mensajes individuales, UN DATO POR MENSAJE)
- MENSAJE 1: Resume el pedido y pide confirmación. Ej: "Entonces quedan 3 Titán Familiar y 2 Olímpico Estándar para Heidi. Total: $323 MXN. ¿Confirmas?"
- MENSAJE 2 (tras confirmación): Pide SOLO el nombre del dueño: "¡Listo! Para registrar tu pedido necesito tu nombre completo 😊"
- MENSAJE 3 (tras recibir nombre): Pide SOLO la calle y número exterior: "Perfecto, [Nombre]. ¿Cuál es tu calle y número? 📍"
- MENSAJE 4 (tras recibir calle): Pide SOLO la colonia: "¿Y en qué colonia vives?"
- MENSAJE 5 (tras recibir colonia): Pide SOLO el código postal: "¿Cuál es tu código postal?"
- MENSAJE 6 (tras recibir CP): Pide SOLO la alcaldía: "¿Y tu alcaldía o municipio?"
- MENSAJE 7 (tras recibir alcaldía): Pide referencias: "¿Alguna referencia para encontrarte más fácil? Color de fachada, entre qué calles, etc. 😊"
- MENSAJE 8 (tras recibir referencia o si el cliente la omite): Llama a request_address_confirmation con todos los datos capturados. NO escribas el resumen tú mismo — la herramienta lo envía con botones. Queda en silencio hasta que el cliente confirme o corrija.
- MENSAJE 9 (SOLO si el cliente confirma la dirección): Verifica la colonia. Si SÍ está en la lista prioritaria, pide la forma de pago: "¿Cómo prefieres pagar? Efectivo o transferencia contra entrega 💵". Si NO está, usa request_authorization y di: "Listo, ya solicité la verificación para tu colonia. Te aviso en cuanto tenga respuesta 😊".
- MENSAJE 10 (tras recibir forma de pago): Registra el pedido con register_order y despídete con la fecha exacta de entrega.

REGLAS ESTRICTAS DE CAPTURA DE DIRECCIÓN:
❌ NUNCA pidas calle, colonia, CP y alcaldía en el mismo mensaje.
❌ NUNCA escribas el resumen de dirección tú mismo — usa request_address_confirmation para eso.
❌ Si el cliente corrige un campo después del resumen, actualiza ese dato y vuelve a llamar request_address_confirmation con todos los datos actualizados.
✅ Guarda cada campo conforme el cliente lo responde antes de pedir el siguiente.
✅ Si el cliente da varios campos en un solo mensaje (ej: "Reforma 123, Col. Centro"), acepta todos y pregunta solo los que falten.

═══════════════════════════════════
📊 CALIFICACIÓN DE CLIENTES
═══════════════════════════════════
Clasifica al cliente antes de registrar usando UNICAMENTE uno de estos tres valores: "frio", "tibio" o "caliente".
- frio: Solo preguntó, no confirmó datos ni mostró clara intención de compra.
- tibio: Dio nombre, colonia, receta o forma de pago. Mostró intención real.
- caliente: Confirmó explícitamente: "Sí, quiero pedir" o dio todos sus datos.

═══════════════════════════════════
🗣️ ESTILO DE COMUNICACIÓN
═══════════════════════════════════
✅ Usa oraciones cortas y naturales. Máximo 2-3 por mensaje.
✅ Usa emojis con moderación: 🐾 🐶 😊 🥇 🥈 💪 ✨ 📦 💳 📍
✅ Personaliza con los nombres. "Pluto va a devorar el Olímpico..."
✅ Sé entusiasta pero genuino. "¡Qué emoción! Tu perrito va a notar la diferencia..."
✅ Haz preguntas abiertas: "Cuéntame más de Pluto..."
✅ Valida las emociones: "Te entiendo, cambiar la dieta de un perrito es una decisión importante..."
❌ NUNCA uses listas, guiones ni bullets points.
❌ NUNCA escribas en mayúsculas sostenidas.
❌ NUNCA uses más de 3 emojis por mensaje.
❌ NUNCA menciones la palabra "horario" para derivar. Solo responde horarios si preguntan directamente.
❌ NUNCA digas "fuera de horario" ni pidas que vuelvan a escribir después.
❌ NUNCA repitas información que ya diste en el mismo mensaje.
❌ NUNCA juntes temas diferentes (cobertura + pago + datos bancarios) en una sola respuesta. Un mensaje, un tema.
❌ Si ya saludaste, no vuelvas a saludar en el siguiente mensaje.
❌ NUNCA digas frases como "Pedido reajustado con éxito", "Registro actualizado" o "Operación completada".
❌ NUNCA digas "Qué pedido tan complejo" ni comentes sobre la complejidad del pedido.
✅ Cuando un cliente haga un pedido grande, responde: "¡Guau! Heidi va a estar feliz con esa variedad 😍"

═══════════════════════════════════
🛡️ SEGURIDAD Y OBJECIONES
═══════════════════════════════════
🔹 Si preguntan costos, márgenes, proveedores o datos del negocio:
   "Gracias por tu interés en Mr. Apolo. ¿Te gustaría pedir algo para tu perrito? Cuéntame de él."

🔹 Si son agresivos o mafiosos:
   "Gracias, por el momento no tenemos disponibilidad. ¡Hasta pronto!" y no respondas más.

🔹 Si el cliente duda del precio:
   "Te entiendo. Mira, cada sobre tiene ingredientes frescos y calidad humana, cocinado como si fuera para nosotros. Además rinde varias porciones. ¿Quieres probar con uno estándar para ver cómo le cae a tu campeón?"

🔹 Si dicen que su perro es quisquilloso:
   "¡Justo por eso te va a gustar! Casi todos los perros que lo prueban lo devoran desde el primer día. Si quieres, empieza con un Estándar para probar, sin tanto compromiso."

🔹 Si preguntan por el número de WhatsApp:
   "Todo lo resolvemos por aquí sin problema 😊 Cuéntame, ¿cómo se llama tu perrito?"

🔹 Si el mensaje viene de un audio confuso o con mucho ruido:
   "Oye, no te escuché muy bien. ¿Me lo repites por aquí porfi? Quiero asegurarme de que te envío exactamente lo que necesitas para tu campeón 🐶"

🔹 Después de usar request_authorization, NUNCA ofrezcas datos de pago, transferencia, ni preguntes cantidad de sobres. Solo di que esperarán confirmación y detente.

═══════════════════════════════════
⚡ RECORDATORIOS FINALES
═══════════════════════════════════
1. El éxito de Mr. Apolo depende de que concretes pedidos. No solo informes, VENDE.
2. Cada conversación debe terminar con un pedido concretado o un cliente calificado.
3. Si ves que el cliente se enfría, relanza con una pregunta sobre su perro.
4. Siempre, SIEMPRE, llama al perro por su nombre. Crea vínculo emocional.
5. Registra el pedido con todos los datos cuando el cliente confirme compra.
6. Si recibes un audio transcrito, responde naturalmente sin mencionar que era un audio.
7. VERIFICA SIEMPRE la colonia contra la lista de colonias prioritarias antes de confirmar cualquier pedido.
8. Al registrar el pedido, usa los campos desglosados: calle, colonia, cp, alcaldia, fechaEntrega.
9. Siempre confirma la fecha de entrega al cliente en formato legible, como "${fechaEntrega}".
10. La captura de dirección va CAMPO POR CAMPO. Un mensaje, un dato. Usa request_address_confirmation cuando tengas todos los campos.`;
}

const tools = [
  {
    name: 'register_order',
    description: 'Registra pedido completo en Google Sheets cuando el cliente confirma compra.',
    input_schema: {
      type: 'object',
      properties: {
        nombre:       { type: 'string', description: 'Nombre del cliente' },
        nombre_perro: { type: 'string', description: 'Nombre del perro o mascota' },
        telefono:     { type: 'string', description: 'Numero de telefono' },
        calle:        { type: 'string', description: 'Calle y número' },
        colonia:      { type: 'string', description: 'Nombre de la colonia' },
        cp:           { type: 'string', description: 'Código Postal' },
        alcaldia:     { type: 'string', description: 'Alcaldía' },
        receta:       { type: 'string', description: 'El Olimpico o El Titan' },
        tamano:       { type: 'string', description: 'Estandar 250g o Familiar 400g' },
        cantidad:     { type: 'number', description: 'Cantidad de sobres' },
        total:        { type: 'number', description: 'Total en MXN' },
        formaPago:    { type: 'string', description: 'Forma de pago' },
        notas:        { type: 'string', description: 'Notas adicionales' },
        leadScore:    { type: 'string', description: 'frio, tibio o caliente' },
        fechaEntrega: { type: 'string', description: 'Fecha formateada de entrega, ej: Sábado 3 de mayo de 2026' },
      },
      required: ['nombre', 'nombre_perro', 'calle', 'colonia', 'cp', 'alcaldia', 'receta', 'tamano', 'cantidad', 'fechaEntrega'],
    },
  },
  {
    name: 'request_address_confirmation',
    description: 'Llama esta herramienta cuando hayas capturado TODOS los campos de dirección (calle, colonia, cp, alcaldia). Envía al cliente un resumen con botones interactivos para confirmar o corregir. NO escribas el resumen tú mismo.',
    input_schema: {
      type: 'object',
      properties: {
        calle:      { type: 'string', description: 'Calle y número exterior' },
        colonia:    { type: 'string', description: 'Colonia' },
        cp:         { type: 'string', description: 'Código Postal (5 dígitos)' },
        alcaldia:   { type: 'string', description: 'Alcaldía o municipio' },
        referencia: { type: 'string', description: 'Referencia adicional (opcional)' },
      },
      required: ['calle', 'colonia', 'cp', 'alcaldia'],
    },
  },
  {
    name: 'request_authorization',
    description: 'Solicita autorizacion para entregar en colonia fuera de zona prioritaria. Incluye toda la información disponible del pedido.',
    input_schema: {
      type: 'object',
      properties: {
        colonia:   { type: 'string', description: 'Colonia solicitada' },
        telefono:  { type: 'string', description: 'Teléfono del cliente' },
        total:     { type: 'number', description: 'Total del pedido en MXN' },
        direccion: { type: 'string', description: 'Dirección completa de entrega' },
        receta:    { type: 'string', description: 'Recetas y cantidades del pedido' },
      },
      required: ['colonia'],
    },
  },
  {
    name: 'explain_process',
    description: 'Explica proceso de compra al cliente.',
    input_schema: {
      type: 'object',
      properties: { etapa: { type: 'string' } },
      required: ['etapa'],
    },
  },
];


async function executeTool(name, input, from, sendInteractiveFn, sendMessageFn) {
  if (name === 'register_order') {
    try {
      const { pendingPayments } = await import('./pending-payments.js');
      const phone = input.telefono || from;

      const existingOrder = pendingPayments.get(phone);
      if (existingOrder && existingOrder.timestamp && (Date.now() - existingOrder.timestamp < 120000)) {
        console.warn('⚠️ Pedido duplicado bloqueado para:', phone);
        return 'Pedido ya registrado anteriormente.';
      }

      const result = await registerOrder({ ...input, telefono: phone });
      pendingPayments.set(phone, { orderData: { ...input, telefono: phone }, timestamp: Date.now() });

      // La encuesta se envía via Apps Script cuando se palomea "Pedido Entregado" en el Sheet

      return `Pedido registrado para ${input.nombre}. Entrega: ${input.fechaEntrega}.`;
    } catch (e) { console.error('register_order:', e.message); return 'Pedido anotado manualmente.'; }
  }

  if (name === 'request_address_confirmation') {
    try {
      // Guarda la dirección pendiente para recuperarla cuando el cliente confirme
      pendingAddresses.set(from, { ...input, timestamp: Date.now() });

      const resumen =
        `📍 Tu dirección de entrega:\n` +
        `Calle: ${input.calle}\n` +
        `Colonia: ${input.colonia}\n` +
        `CP: ${input.cp}\n` +
        `Alcaldía: ${input.alcaldia}` +
        (input.referencia ? `\nRef: ${input.referencia}` : '') +
        `\n\n¿Todo está correcto?`;

      if (sendInteractiveFn) {
        const phone = from.replace('@s.whatsapp.net', '');
        await sendInteractiveFn(phone, resumen, [
          { id: 'confirm_address', title: '✅ Confirmar' },
          { id: 'edit_address',    title: '✏️ Corregir' },
        ]);
        console.log('✅ Resumen de dirección enviado con botones a:', phone);
      } else {
        console.warn('⚠️ sendInteractiveFn no disponible, no se enviaron botones');
      }

      return 'Resumen de dirección enviado al cliente con botones de confirmación. Espera su respuesta. NO escribas nada más.';
    } catch (e) {
      console.error('request_address_confirmation:', e.message);
      return 'Error enviando resumen de dirección.';
    }
  }

  if (name === 'request_authorization') {
    console.log('AUTH REQUEST - Colonia:', input.colonia, 'Tel:', input.telefono || from);

    const cliente = (input.telefono || from.replace('@s.whatsapp.net', '')).replace(/\D/g, '');
    const ownerPhone = (process.env.OWNER_PHONE || '525614512925').replace(/\D/g, '');
    const hilaryPhone = (process.env.HILARY_PHONE || '525634101531').replace(/\D/g, '');

    let mensaje = `🚩 *Nueva solicitud de zona*\n📞 Cliente: ${cliente}`;
    if (input.total) mensaje += `\n💰 Monto: $${input.total} MXN`;
    if (input.receta) mensaje += `\n🍖 Pedido: ${input.receta}`;
    if (input.direccion) mensaje += `\n📍 Dirección: ${input.direccion}`;
    mensaje += `\n✅ Responde: "sí autorizo ${cliente}" para aprobar la entrega.`;

    const WA_TOKEN = process.env.WA_ACCESS_TOKEN;
    const WA_PHONE_ID = process.env.WA_PHONE_NUMBER_ID;

    if (WA_TOKEN && WA_PHONE_ID) {
      const sendMsg = async (to) => {
        await fetch(`https://graph.facebook.com/v21.0/${WA_PHONE_ID}/messages`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${WA_TOKEN}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            messaging_product: 'whatsapp',
            to: to,
            type: 'text',
            text: { body: mensaje }
          })
        });
      };

      try {
        await sendMsg(ownerPhone);
        await sendMsg(hilaryPhone);
        console.log('✅ Notificaciones de zona enviadas');
      } catch (e) {
        console.error('❌ Error enviando notificación de zona:', e.message);
      }
    }

    return 'Solicitud enviada. Te confirmamos disponibilidad pronto.';
  }

  if (name === 'explain_process') {
    return 'El proceso: 1) Confirmas pedido aqui. 2) Si elegiste transferencia te paso los datos. 3) Hilary valida y confirma entrega el sabado. Que receta y tamano te interesa?';
  }
  return 'Listo.';
}

// =====================================================
// AGENTE DE CALIDAD LIGERO
// =====================================================
async function revisarRespuesta(texto) {
  const tieneNumero = /\+?52[\s\-]?1?[\s\-]?55[\s\-]?\d{4}[\s\-]?\d{4}/.test(texto) ||
                      /5538953371|5536953371|55[\s\-]?3895[\s\-]?3371|55[\s\-]?3695[\s\-]?3371/.test(texto);
  const dice247 = /24\/7/.test(texto);
  const diceIA = /\b(soy\s+(?:un\s+)?(?:bot|ia|inteligencia artificial|asistente virtual))\b/i.test(texto);
  const daDigitosSueltos = /\b3[89]\d{2}[\s\-]?\d{4}\b/.test(texto);

  let textoLimpio = texto;
  let huboCambios = false;

  if (tieneNumero || daDigitosSueltos) {
    console.warn('⚠️ revisarRespuesta: Detectado número de teléfono');
    textoLimpio = textoLimpio
      .replace(/\+?52[\s\-]?1?[\s\-]?55[\s\-]?\d{4}[\s\-]?\d{4}/gi, '')
      .replace(/5538953371|5536953371|55[\s\-]?3895[\s\-]?3371|55[\s\-]?3695[\s\-]?3371/gi, '')
      .replace(/escr[íi]benos\s+(al|a|por)\s+(WhatsApp|whatsapp)?\s*[\d\s\-\.\+]*/gi, 'escríbeme por este chat')
      .replace(/ll[áa]manos\s+(al|a)?\s*[\d\s\-\.\+]*/gi, 'escríbeme por este chat')
      .replace(/cont[áa]ctanos\s+(al|a|por)\s*(WhatsApp|whatsapp)?\s*[\d\s\-\.\+]*/gi, 'contáctame por este chat')
      .replace(/nuestro\s*(n[úu]mero|WhatsApp|whatsapp)\s*(es|al)?\s*[\d\s\-\.\+]*/gi, 'este chat')
      .replace(/al\s*(n[úu]mero|WhatsApp)?\s*\+?52\s*1?\s*55\s*[\d\s\-\.]{6,}/gi, 'por este chat')
      .trim();
    huboCambios = true;
  }

  if (dice247) {
    console.warn('⚠️ revisarRespuesta: Detectado 24/7');
    textoLimpio = textoLimpio.replace(/24\/7/gi, 'todos los días');
    huboCambios = true;
  }

  if (diceIA) {
    console.warn('⚠️ revisarRespuesta: Detectada autorreferencia IA');
    textoLimpio = textoLimpio.replace(/\b(soy\s+(?:un\s+)?(?:bot|ia|inteligencia artificial|asistente virtual))\b/gi, 'soy del equipo Mr. Apolo');
    huboCambios = true;
  }

  if (/\b(colonia|coloni|zona|confirma|registra|pedido|entrega|direcci|envío|entregamos|visitamos)\b/i.test(textoLimpio)) {
    const patronesColonia = [
      /colonia[:\s]+([A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+?)(?:\.|,|$|\s+(?:te|nos|me|confirmo|entrega|envío|gracias))/i,
      /(?:en|para|por)\s+([A-Za-záéíóúüñÁÉÍÓÚÜÑ]{4,}(?:\s+[A-Za-záéíóúüñÁÉÍÓÚÜÑ]{3,})?)\s*(?:\.|,|$|\s+(?:te|nos|me|confirmo|entrega|envío))/i,
    ];
    for (const patron of patronesColonia) {
      const match = textoLimpio.match(patron);
      if (match && match[1]) {
        const posibleColonia = match[1].trim();
        if (posibleColonia.length >= 4 && !coloniaAutorizada(posibleColonia)) {
          console.warn('⚠️ revisarRespuesta: Colonia NO autorizada detectada:', posibleColonia);
        }
        break;
      }
    }
  }

  if (huboCambios && !textoLimpio) return texto;
  return textoLimpio || texto;
}

export async function runAgent(fromJid, userMessage, sendMessageFn, sendInteractiveFn) {
  if (!conversations.has(fromJid)) {
      const cp = fromJid.replace('@s.whatsapp.net','');
      const pv = await getCustomerByPhone(cp).catch(()=>null);
      conversations.set(fromJid, pv?.nombre ? [{role:'user',content:'hola'},{role:'assistant',content:'Hola '+pv.nombre+'! En que te puedo ayudar hoy?'}] : []);
  }
  const history = conversations.get(fromJid);
  history.push({ role: 'user', content: userMessage });

  const cfg = await getConfigCached();
  const systemPrompt = buildPrompt(cfg);
  let messages = history.slice(-20);

  try {
    while (true) {
      const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-6',
        max_tokens: 1024,
        system: systemPrompt,
        tools,
        messages,
      });
      messages.push({ role: 'assistant', content: response.content });

      if (response.stop_reason === 'end_turn') {
        const text = response.content.find(b => b.type === 'text')?.text || '';
        history.push({ role: 'assistant', content: response.content });
        if (history.length > 40) history.splice(0, history.length - 40);
        return await revisarRespuesta(text);
      }

      if (response.stop_reason === 'tool_use') {
        const results = [];
        for (const block of response.content) {
          if (block.type === 'tool_use') {
            const result = await executeTool(block.name, block.input, fromJid, sendInteractiveFn, sendMessageFn);
            results.push({ type: 'tool_result', tool_use_id: block.id, content: result });
          }
        }
        messages.push({ role: 'user', content: results });
        continue;
      }
      break;
    }
  } catch (e) {
    console.error('runAgent error:', e.message);
    return 'Disculpa, tuve un problema tecnico. Intenta de nuevo en un momento.';
  }
  return '';
}

export function addMessageToHistory(fromJid, role, content) {
  if (!conversations.has(fromJid)) {
    conversations.set(fromJid, []);
  }
  conversations.get(fromJid).push({ role, content });
}

setInterval(() => {
  for (const [key, hist] of conversations.entries()) {
    if (hist.length > 60) conversations.set(key, hist.slice(-40));
  }
}, 3600000);
