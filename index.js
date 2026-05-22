import express from 'express';
import dotenv from 'dotenv';
import cron from 'node-cron';
dotenv.config();

// Debug: forzar flush de stdout en Railway
process.stdout._handle?.setBlocking?.(true);
console.log('🚀 Iniciando... PORT=' + process.env.PORT);

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const WA_VERIFY_TOKEN = process.env.WA_VERIFY_TOKEN || 'mrapolo2025';
let WA_TOKEN = process.env.WA_ACCESS_TOKEN || '';
const WA_PHONE_ID = process.env.WA_PHONE_NUMBER_ID || '';

// Filtro anti‑números y frases de derivación
function filtrarRespuesta(texto) {
  if (!texto) return texto;
  return texto
    .replace(/escr[íi]benos (al|a nuestro|por)\s*(WhatsApp|wh?at?sa?pp?)?\s*[\d\s\-\.\+]*/gi, '')
    .replace(/cont[áa]ctanos (al|a|por)\s*(WhatsApp|wh?at?sa?pp?)?\s*[\d\s\-\.\+]*/gi, '')
    .replace(/comun[íi]cate (al|a|por)\s*(WhatsApp|wh?at?sa?pp?)?\s*[\d\s\-\.\+]*/gi, '')
    .replace(/ll[áa]manos (al|a)?\s*[\d\s\-\.\+]*/gi, '')
    .replace(/nuestro\s*(n[úu]mero|WhatsApp|wh?at?sa?pp?)\s*(es|al)?\s*[\d\s\-\.\+]*/gi, '')
    .replace(/al\s*(n[úu]mero|WhatsApp)?\s*\+?52\s*1?\s*55\s*[\d\s\-\.]{6,}/gi, '')
    .replace(/\+?52[\s\-]?1?[\s\-]?55[\s\-]?3[89]\d{2}[\s\-]?\d{4}/gi, '')
    .replace(/5536953371|5538953371|55 3695 3371|55 3895 3371|55 3895-3371|55 3695-3371/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

// Verificación del webhook (GET)
app.get('/webhook', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];
  if (mode === 'subscribe' && token === WA_VERIFY_TOKEN) {
    console.log('✅ Webhook verificado');
    return res.status(200).send(challenge);
  }
  res.sendStatus(403);
});

// Status
app.get('/status', (req, res) => res.json({ status: 'online', ts: new Date().toISOString() }));

// Transcripción de audio
async function transcribeAudio(audioId) {
  try {
    const mediaResp = await fetch(`https://graph.facebook.com/v21.0/${audioId}`, {
      headers: { Authorization: `Bearer ${WA_TOKEN}` }
    });
    const mediaData = await mediaResp.json();
    if (!mediaData.url) return null;
    const audioResp = await fetch(mediaData.url, {
      headers: { Authorization: `Bearer ${WA_TOKEN}` }
    });
    const audioBuffer = await audioResp.arrayBuffer();
    const { OpenAI } = await import('openai');
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const file = new File([audioBuffer], 'audio.ogg', { type: 'audio/ogg' });
    const result = await openai.audio.transcriptions.create({
      file, model: 'whisper-1', language: 'es'
    });
    return result.text;
  } catch(e) {
    console.error('transcribeAudio error:', e.message);
    return null;
  }
}

async function sendMessage(to, text) {
  try {
    const phone = to.replace('@s.whatsapp.net', '').replace(/\D/g, '');
    console.log(`📤 Enviando a ${phone}: ${String(text).substring(0, 80)}${text?.length > 80 ? '...' : ''}`);
    const r = await fetch(`https://graph.facebook.com/v21.0/${WA_PHONE_ID}/messages`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${WA_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ messaging_product: 'whatsapp', to: phone, type: 'text', text: { body: text } })
    });
    const d = await r.json();
    if (!r.ok) console.error('sendMessage error:', JSON.stringify(d));
    return d;
  } catch (e) { console.error('sendMessage exception:', e.message); }
}

async function sendImage(to, imageUrl, caption) {
  try {
    const phone = to.replace('@s.whatsapp.net', '').replace(/\D/g, '');
    const r = await fetch(`https://graph.facebook.com/v21.0/${WA_PHONE_ID}/messages`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${WA_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messaging_product: 'whatsapp', to: phone, type: 'image',
        image: { link: imageUrl, caption: caption || '' }
      })
    });
    const d = await r.json();
    if (!r.ok) console.error('sendImage error:', JSON.stringify(d));
    return d;
  } catch (e) { console.error('sendImage exception:', e.message); }
}

async function sendImageById(to, mediaId, caption) {
  try {
    const phone = to.replace('@s.whatsapp.net', '').replace(/\D/g, '');
    const r = await fetch(`https://graph.facebook.com/v21.0/${WA_PHONE_ID}/messages`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${WA_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messaging_product: 'whatsapp', to: phone, type: 'image',
        image: { id: mediaId, caption: caption || '' }
      })
    });
    const d = await r.json();
    if (!r.ok) console.error('sendImageById error:', JSON.stringify(d));
    return d;
  } catch (e) { console.error('sendImageById exception:', e.message); }
}

// Mapa de autorizaciones pendientes
const pendingAuthorizations = new Map();

// Mapa de leads cálidos (mostraron interés pero no completaron pedido)
const warmLeads = new Map(); // phone → { timestamp, texto, intentos }

async function handleAuthorizationReply(from, text) {
  const phoneMatch = text.match(/\d{10,}/);
  if (!phoneMatch) return false;
  
  const clientPhone = phoneMatch[0];
  if (!pendingAuthorizations.has(clientPhone)) return false;
  
  await sendMessage(clientPhone, `¡Buenas noticias! Tu colonia fue autorizada. ¿Seguimos con tu pedido? 🐾`);
  pendingAuthorizations.delete(clientPhone);
  return true;
}

// =====================================================
//  WEBHOOK POST – recibir mensajes de WhatsApp
// =====================================================
app.post('/webhook', async (req, res) => {
  res.sendStatus(200);
  try {
    const body = req.body;
    if (body.object !== 'whatsapp_business_account') return;
    const entry = body.entry?.[0];
    const change = entry?.changes?.[0];
    const value = change?.value;
    const messages = value?.messages;
    if (!messages?.length) return;

    const msg = messages[0];
    const from = msg.from;
    let text;
    if (msg.type === 'text') {
      text = msg.text?.body || '';
    } else if (msg.type === 'audio') {
      console.log('🎤 Audio recibido, transcribiendo...');
      text = await transcribeAudio(msg.audio.id);
      if (!text) { console.log('No se pudo transcribir el audio'); return; }
      console.log(`🎤 Audio transcrito: ${text}`);
    } else if (msg.type === 'image') {
      // comprobante de transferencia se procesa abajo
    } else {
      console.log('⚠️ Tipo de mensaje no soportado:', msg.type, 'de', from);
      await sendMessage(from, '¡Hola! 🐾 No pude leer ese mensaje. ¿Puedes escribirme con texto?');
      return;
    }
    console.log(`📩 Mensaje de ${from}: ${text}`);

    // Cargar módulos dinámicos
    try {
      const { runAgent, addMessageToHistory } = await import('./agent.js');
      const { isDentroDeHorario, getMensajeFueraDeHorario, OWNER_PHONE, HILARY_PHONE } = await import('./business-rules.js');
      const { pendingPayments } = await import('./pending-payments.js');

      // Comprobante de transferencia (imagen)
      if (msg.type === 'image') {
        if (pendingPayments.has(from)) {
          await sendImageById(HILARY_PHONE, msg.image.id, `Comprobante de ${from}`);
          await sendMessage(from, 'Comprobante recibido 📸 En cuanto Hilary confirme tu pago registramos tu pedido 🐾');
        }
        return;
      }

      // Respuestas de autorización de Alfonso o Hilary
      const ownerPhoneRaw = (process.env.OWNER_PHONE || '5215614512925').replace(/\D/g, '');
      const hilaryPhoneRaw = (process.env.HILARY_PHONE || '5215634101531').replace(/\D/g, '');
      
      if (from === ownerPhoneRaw || from === hilaryPhoneRaw) {
        const authHandled = await handleAuthorizationReply(from, text);
        if (authHandled) {
          console.log('✅ Autorización procesada');
          return;
        }
        
        if (from === hilaryPhoneRaw) {
          const confirmRegex = /\b(ok|sí|si|listo|confirmado|acepta|confirmo|aprobado)\b/i;
          if (text && confirmRegex.test(text)) {
            const phoneMatch = text.match(/\d{10,}/);
            let clientPhone = phoneMatch ? phoneMatch[0] : null;
            if (!clientPhone) {
              let oldestTime = Infinity;
              for (const [phone, data] of pendingPayments) {
                if (data.timestamp < oldestTime) { clientPhone = phone; oldestTime = data.timestamp; }
              }
            }
            if (clientPhone && pendingPayments.has(clientPhone)) {
              const { orderData } = pendingPayments.get(clientPhone);
              pendingPayments.delete(clientPhone);
              if (orderData) {
                const { registerOrder } = await import('./sheets.js');
                await registerOrder(orderData);
              }
              await sendMessage(clientPhone, '¡Tu pago fue confirmado! Tu pedido está registrado 🐾✨');
              await sendMessage(hilaryPhoneRaw, `✅ Pedido de ${clientPhone} registrado.`);
            }
          }
          return;
        }
        return;
      }

      // Mensaje normal de cliente
      const fromJid = from + '@s.whatsapp.net';

      if (!isDentroDeHorario()) {
        await sendMessage(from, getMensajeFueraDeHorario());
        addMessageToHistory(fromJid, 'user', text);
        return;
      }

      const reply = await runAgent(fromJid, text, sendMessage);
      if (reply) {
        const replyFiltrado = filtrarRespuesta(reply);
        await sendMessage(from, replyFiltrado);

        // ── Tracking de leads cálidos ──────────────────────────────────
        const intencionCompra = /precio|cu[áa]nto|cuesta|vale|pedido|ordenar|quiero|comprar|domicilio|colonia|entrega|s[áa]bado|pago|transferencia/i;
        const pedidoCompleto = /registrado|confirmado|pedido anotado|a domicilio|te llega|tu pedido est[áa]/i;

        if (pedidoCompleto.test(replyFiltrado)) {
          warmLeads.delete(from);
          console.log(`✅ Pedido completado → lead eliminado: ${from}`);
        } else if (intencionCompra.test(text)) {
          const prev = warmLeads.get(from) || { intentos: 0 };
          warmLeads.set(from, { timestamp: Date.now(), texto: text.substring(0, 200), intentos: prev.intentos });
          console.log(`🌡️ Lead cálido registrado/actualizado: ${from}`);
        }
        // ───────────────────────────────────────────────────────────────
      }

    } catch (modErr) {
      console.error('Error en módulos:', modErr.message);
      await sendMessage(from, '¡Hola! 🐾 Gracias por escribirnos. En este momento estamos configurando nuestro sistema. Te contactamos pronto.');
    }
  } catch (err) {
    console.error('Error webhook POST:', err.message);
  }
});

// =====================================================
// REACTIVACIÓN DE CLIENTES INACTIVOS (CADA LUNES 10 AM)
// =====================================================
cron.schedule('0 10 * * 1', async () => {
  console.log('⏰ [CRON] Iniciando reactivación de clientes inactivos...');
  try {
    const { getOrders } = await import('./sheets.js');
    const pedidos = await getOrders();
    
    const clientes = new Map();
    
    for (const pedido of pedidos) {
      const tel = (pedido['Telefono'] || '').replace(/\D/g, '');
      if (!tel || tel.length < 10) continue;
      
      let fechaPedido = null;
      const fechaStr = pedido['Fecha'] || '';
      
      // Intento con formato dd/mm/aaaa
      const partes1 = fechaStr.split('/');
      if (partes1.length === 3) {
        fechaPedido = new Date(`${partes1[2]}-${partes1[1]}-${partes1[0]}T00:00:00-06:00`);
      }
      
      // Intento con formato aaaa-mm-dd
      if (!fechaPedido || isNaN(fechaPedido.getTime())) {
        const partes2 = fechaStr.split('-');
        if (partes2.length === 3) {
          fechaPedido = new Date(`${partes2[0]}-${partes2[1]}-${partes2[2]}T00:00:00-06:00`);
        }
      }
      
      if (!fechaPedido || isNaN(fechaPedido.getTime())) continue;
      
      if (!clientes.has(tel) || clientes.get(tel).fecha < fechaPedido) {
        clientes.set(tel, {
          nombre: pedido['Nombre Cliente'] || 'cliente',
          perro: pedido['Nombre Perro'] || 'tu campeón',
          fecha: fechaPedido,
          receta: pedido['Receta'] || 'nuestra comida fresca',
          direccion: pedido['Calle y número'] || pedido['Dirección completa'] || '',
          tamano: pedido['Tamaño'] || 'Estándar 250g'
        });
      }
    }
    
    const ahora = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Mexico_City' }));
    let enviados = 0;
    let errores = 0;
    
    for (const [tel, data] of clientes) {
      const diasSinPedir = Math.floor((ahora - data.fecha) / (1000 * 60 * 60 * 24));
      
      if (diasSinPedir >= 14 && diasSinPedir <= 60) {
        const mensaje = `¡Hola ${data.nombre}! 🐾\n\nHace ${diasSinPedir} días que ${data.perro} probó ${data.receta} y le encantó.\n\n¿Le repetimos para este sábado? Ya tengo tus datos guardados, solo dime "sí" y te lo preparo 😊`;
        
        try {
          await sendMessage(tel, mensaje);
          console.log(`✅ [CRON] Reactivación enviada a ${tel} (${data.nombre}, ${diasSinPedir} días)`);
          enviados++;
          await new Promise(resolve => setTimeout(resolve, 1500));
        } catch (e) {
          console.error(`❌ [CRON] Error enviando a ${tel}:`, e.message);
          errores++;
        }
      }
    }
    
    console.log(`⏰ [CRON] Reactivación completada: ${enviados} enviados, ${errores} errores`);
  } catch (err) {
    console.error('❌ [CRON] Error general en reactivación:', err.message);
  }
}, {
  scheduled: true,
  timezone: 'America/Mexico_City'
});

console.log('⏰ Cron job de reactivación configurado (lunes 10 AM CDMX)');

// =====================================================
// SEGUIMIENTO DE LEADS CÁLIDOS (CADA 2 HORAS)
// =====================================================
cron.schedule('0 */2 * * *', async () => {
  const cuantos = warmLeads.size;
  if (cuantos === 0) return;
  console.log(`⏰ [CRON] Revisando ${cuantos} leads cálidos...`);

  const ahora = Date.now();
  const DOS_HORAS   = 2 * 60 * 60 * 1000;
  const OCHO_HORAS  = 8 * 60 * 60 * 1000;

  for (const [phone, data] of warmLeads) {
    const elapsed = ahora - data.timestamp;

    if (elapsed >= DOS_HORAS && elapsed < OCHO_HORAS && (data.intentos || 0) < 2) {
      try {
        await sendMessage(phone, '¡Hola! 🐾 ¿Te quedó alguna duda sobre el pedido? Puedo ayudarte a terminarlo en un momento 😊');
        warmLeads.set(phone, { ...data, intentos: (data.intentos || 0) + 1 });
        console.log(`✅ [CRON] Follow-up enviado a ${phone} (intento ${data.intentos + 1})`);
        await new Promise(r => setTimeout(r, 1500));
      } catch (e) {
        console.error(`❌ [CRON] Error follow-up ${phone}:`, e.message);
      }
    } else if (elapsed >= OCHO_HORAS) {
      warmLeads.delete(phone);
      console.log(`🗑️ [CRON] Lead expirado eliminado: ${phone}`);
    }
  }
}, {
  scheduled: true,
  timezone: 'America/Mexico_City'
});
console.log('⏰ Cron job de leads cálidos configurado (cada 2 horas)');

// Arrancar servidor
const server = app.listen(PORT, '0.0.0.0', async () => {
  console.log(`🐾 Mr. Apolo corriendo en puerto ${PORT}`);

  try {
    const { dashRouter } = await import('./dashboard-server.js');
    app.use('/', dashRouter);
    console.log('✅ Dashboard montado');
  } catch (e) { console.warn('Dashboard no disponible:', e.message); }

  try {
    const { initSheet } = await import('./sheets.js');
    await initSheet();
    console.log('✅ Google Sheets conectado');
  } catch (e) { console.warn('Sheets no disponible:', e.message); }
});

server.on('error', (err) => {
  console.error('❌ Error en app.listen:', err.message, err.code);
  process.exit(1);
});
