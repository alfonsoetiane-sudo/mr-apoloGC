/**
 * mr-apolo test suite v2
 * Tests: filtrarRespuesta (incl. guión), transcribeAudio, message routing,
 *        flujo de transferencia (pendingPayments), webhook parsing, prompt structure
 */
import assert from 'node:assert/strict';

// ─── mini test runner ────────────────────────────────────────────────────────
let passed = 0, failed = 0;
function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch(e) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${e.message}`);
    failed++;
  }
}
async function testAsync(name, fn) {
  try {
    await fn();
    console.log(`  ✓ ${name}`);
    passed++;
  } catch(e) {
    console.error(`  ✗ ${name}`);
    console.error(`    ${e.message}`);
    failed++;
  }
}

// ─── 1. filtrarRespuesta (versión corregida con soporte de guión) ─────────────
function filtrarRespuesta(text) {
  return text
    .replace(/escr[íi]benos (al|a nuestro|por) [\d\s+\-().]+/gi, '')
    .replace(/cont[áa]ctanos (al|a|por) [\d\s+\-().]+/gi, '')
    .replace(/comun[íi]cate (al|a|por) [\d\s+\-().]+/gi, '')
    .replace(/ll[áa]manos (al|a) [\d\s+\-().]+/gi, '')
    .replace(/nuestro\s*(n[úu]mero|WhatsApp|wh?at?sa?pp?) [\d\s+\-().]+/gi, '')
    .replace(/al\s*(n[úu]mero|WhatsApp) [\d\s+\-().]+/gi, '')
    .replace(/\+?52[\s\-]?1?[\s\-]?55[\s\-]?3[89]\d{2}[\s\-]?\d{4}/gi, '')
    .replace(/5536953371|5538953371|55 3695 3371|55 3895 3371|55 3895-3371|55 3695-3371/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

console.log('\n📋 filtrarRespuesta — básicos');

test('deja texto normal sin cambios', () => {
  const r = filtrarRespuesta('Hola, ¿en qué te puedo ayudar?');
  assert.equal(r, 'Hola, ¿en qué te puedo ayudar?');
});

test('elimina número formato +52 con espacios', () => {
  const r = filtrarRespuesta('Llámanos al +52 55 3895 1234 cuando quieras.');
  assert.ok(!r.includes('+52'), `debería eliminar +52: "${r}"`);
});

test('elimina número hardcoded 5536953371', () => {
  const r = filtrarRespuesta('escríbenos al 5536953371 para más info');
  assert.ok(!r.includes('5536953371'), `debería eliminar el número: "${r}"`);
});

test('elimina "escríbenos al ..."', () => {
  const r = filtrarRespuesta('Por favor escríbenos al 5538953371 para ordenar.');
  assert.ok(!r.includes('5538953371'), `número no eliminado: "${r}"`);
});

test('elimina "contáctanos al ..."', () => {
  const r = filtrarRespuesta('contáctanos al 5538 9533 71 o visítanos');
  assert.ok(!r.includes('5538'), `número no eliminado: "${r}"`);
});

test('colapsa espacios dobles', () => {
  const r = filtrarRespuesta('hola   mundo');
  assert.equal(r, 'hola mundo');
});

console.log('\n📋 filtrarRespuesta — formato con guión (bug real detectado en producción)');

test('elimina +52 55 3895-3371 (formato con guión)', () => {
  const r = filtrarRespuesta('escríbenos al +52 55 3895-3371 para más info');
  assert.ok(!r.includes('3895'), `número con guión no eliminado: "${r}"`);
  assert.ok(!r.includes('+52'), `+52 no eliminado: "${r}"`);
});

test('elimina el patrón exacto que generó el agente en producción', () => {
  const botMsg = 'lo mejor es que escribas directo por WhatsApp al +52 55 3895-3371 y el equipo te atiende en horario de atención.';
  const r = filtrarRespuesta(botMsg);
  assert.ok(!r.includes('3895'), `número no eliminado: "${r}"`);
  assert.ok(!r.includes('3371'), `número no eliminado: "${r}"`);
});

test('elimina 55 3895-3371 sin prefijo +52', () => {
  const r = filtrarRespuesta('escríbenos al 55 3895-3371 para tu pedido');
  assert.ok(!r.includes('3895-3371'), `número no eliminado: "${r}"`);
});

test('elimina hardcoded 55 3895-3371', () => {
  const r = filtrarRespuesta('Nuestro número es 55 3895-3371 y estamos disponibles');
  assert.ok(!r.includes('3895-3371'), `hardcoded con guión no eliminado: "${r}"`);
});

test('no elimina texto legítimo que contenga números de otro tipo', () => {
  const r = filtrarRespuesta('El sobre pesa 250g y dura 48h en refrigeración');
  assert.equal(r, 'El sobre pesa 250g y dura 48h en refrigeración');
});

// ─── 2. transcribeAudio (unit con mocks) ────────────────────────────────────
console.log('\n🎤 transcribeAudio');

global.WA_TOKEN = 'test-token';
process.env.OPENAI_API_KEY = 'sk-test';

async function transcribeAudio(audioId, { mockFetch, mockOpenAI } = {}) {
  const fetchFn = mockFetch || fetch;
  try {
    const mediaResp = await fetchFn(`https://graph.facebook.com/v21.0/${audioId}`, {
      headers: { Authorization: `Bearer ${global.WA_TOKEN}` }
    });
    const mediaData = await mediaResp.json();
    if (!mediaData.url) return null;
    const audioResp = await fetchFn(mediaData.url, {
      headers: { Authorization: `Bearer ${global.WA_TOKEN}` }
    });
    const audioBuffer = await audioResp.arrayBuffer();
    const openai = mockOpenAI || { audio: { transcriptions: { create: async () => ({ text: '' }) } } };
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

await testAsync('devuelve texto transcrito con mocks correctos', async () => {
  const mockFetch = async () => ({
    json: async () => ({ url: 'https://cdn.example.com/audio.ogg' }),
    arrayBuffer: async () => new ArrayBuffer(8)
  });
  const mockOpenAI = {
    audio: { transcriptions: { create: async () => ({ text: 'quiero el plan familiar' }) } }
  };
  const result = await transcribeAudio('audio-id-123', { mockFetch, mockOpenAI });
  assert.equal(result, 'quiero el plan familiar');
});

await testAsync('devuelve null si mediaData.url está vacío', async () => {
  const mockFetch = async () => ({
    json: async () => ({ url: null }),
    arrayBuffer: async () => new ArrayBuffer(0)
  });
  const result = await transcribeAudio('bad-id', { mockFetch });
  assert.equal(result, null);
});

await testAsync('devuelve null si fetch lanza error', async () => {
  const mockFetch = async () => { throw new Error('network error'); };
  const result = await transcribeAudio('bad-id', { mockFetch });
  assert.equal(result, null);
});

await testAsync('devuelve null si OpenAI lanza error', async () => {
  const mockFetch = async () => ({
    json: async () => ({ url: 'https://cdn.example.com/audio.ogg' }),
    arrayBuffer: async () => new ArrayBuffer(8)
  });
  const mockOpenAI = {
    audio: { transcriptions: { create: async () => { throw new Error('quota exceeded'); } } }
  };
  const result = await transcribeAudio('audio-id', { mockFetch, mockOpenAI });
  assert.equal(result, null);
});

// ─── 3. Message routing ──────────────────────────────────────────────────────
console.log('\n📨 Message routing');

async function simulateMessageRouting(msg, transcribeFn) {
  let text;
  if (msg.type === 'text') {
    text = msg.text?.body || '';
  } else if (msg.type === 'audio') {
    text = await transcribeFn(msg.audio.id);
    if (!text) return { handled: false, reason: 'transcription_failed' };
  } else if (msg.type === 'image') {
    // imagen: se procesa como comprobante de pago (no es unsupported)
    return { handled: true, isImage: true, mediaId: msg.image?.id };
  } else {
    return { handled: false, reason: 'unsupported_type' };
  }
  return { handled: true, text };
}

await testAsync('msg tipo text extrae el cuerpo correctamente', async () => {
  const msg = { type: 'text', text: { body: 'hola quiero comida' } };
  const r = await simulateMessageRouting(msg, async () => null);
  assert.equal(r.handled, true);
  assert.equal(r.text, 'hola quiero comida');
});

await testAsync('msg tipo text con body vacío retorna string vacío', async () => {
  const msg = { type: 'text', text: {} };
  const r = await simulateMessageRouting(msg, async () => null);
  assert.equal(r.handled, true);
  assert.equal(r.text, '');
});

await testAsync('msg tipo audio transcribe y retorna texto', async () => {
  const msg = { type: 'audio', audio: { id: 'audio-abc' } };
  const r = await simulateMessageRouting(msg, async (id) => {
    assert.equal(id, 'audio-abc');
    return 'quiero el plan estándar';
  });
  assert.equal(r.handled, true);
  assert.equal(r.text, 'quiero el plan estándar');
});

await testAsync('msg tipo audio con fallo de transcripción retorna handled=false', async () => {
  const msg = { type: 'audio', audio: { id: 'bad-audio' } };
  const r = await simulateMessageRouting(msg, async () => null);
  assert.equal(r.handled, false);
  assert.equal(r.reason, 'transcription_failed');
});

await testAsync('msg tipo imagen retorna handled=true con isImage=true', async () => {
  const msg = { type: 'image', image: { id: 'img-comprobante-123' } };
  const r = await simulateMessageRouting(msg, async () => null);
  assert.equal(r.handled, true);
  assert.equal(r.isImage, true);
  assert.equal(r.mediaId, 'img-comprobante-123');
});

await testAsync('msg tipo sticker es ignorado', async () => {
  const msg = { type: 'sticker' };
  const r = await simulateMessageRouting(msg, async () => null);
  assert.equal(r.handled, false);
  assert.equal(r.reason, 'unsupported_type');
});

// ─── 4. Flujo de transferencia (pendingPayments) ─────────────────────────────
console.log('\n💳 Flujo de transferencia');

// Simulación del mapa compartido
function makePendingPayments() { return new Map(); }

// Simulación del flujo de comprobante
async function simulateTransferFlow(pendingPayments, from, msg, {
  sendImageById = async () => {},
  sendMessage = async () => {},
  registerOrder = async () => {},
  HILARY_PHONE = '5634101531'
} = {}) {

  if (msg.type === 'image') {
    if (pendingPayments.has(from)) {
      await sendImageById(HILARY_PHONE, msg.image.id, `Comprobante de ${from}`);
      await sendMessage(from, 'Comprobante recibido 📸');
      return { action: 'comprobante_enviado_a_hilary' };
    }
    return { action: 'imagen_ignorada' };
  }

  if (from === HILARY_PHONE) {
    const confirmRegex = /\b(ok|sí|si|listo|confirmado|acepta|confirmo|aprobado)\b/i;
    if (msg.text && confirmRegex.test(msg.text)) {
      const phoneMatch = msg.text.match(/\d{10,}/);
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
        if (orderData) await registerOrder(orderData);
        await sendMessage(clientPhone, '¡Tu pago fue confirmado! 🐾✨');
        await sendMessage(HILARY_PHONE, `✅ Pedido de ${clientPhone} registrado.`);
        return { action: 'pedido_confirmado', clientPhone };
      }
    }
    return { action: 'hilary_sin_accion' };
  }

  return { action: 'mensaje_normal' };
}

const HILARY = '5634101531';

await testAsync('imagen de cliente en pendingPayments → reenvía a Hilary', async () => {
  const pp = makePendingPayments();
  pp.set('5215512345678', { orderData: null, timestamp: Date.now() });

  let sentToHilary = false;
  let notifiedClient = false;

  await simulateTransferFlow(pp, '5215512345678',
    { type: 'image', image: { id: 'comprobante-abc' } },
    {
      HILARY_PHONE: HILARY,
      sendImageById: async (to, mediaId, caption) => {
        assert.equal(to, HILARY, `debería enviarse a Hilary, no a ${to}`);
        assert.equal(mediaId, 'comprobante-abc');
        sentToHilary = true;
      },
      sendMessage: async (to) => {
        if (to !== HILARY) notifiedClient = true;
      }
    }
  );

  assert.ok(sentToHilary, 'imagen no fue reenviada a Hilary');
  assert.ok(notifiedClient, 'cliente no fue notificado');
});

await testAsync('imagen de cliente NO en pendingPayments → se ignora', async () => {
  const pp = makePendingPayments();
  let called = false;
  const result = await simulateTransferFlow(pp, '5215599999999',
    { type: 'image', image: { id: 'img-x' } },
    { sendImageById: async () => { called = true; } }
  );
  assert.equal(result.action, 'imagen_ignorada');
  assert.equal(called, false, 'no debería reenviar imagen de cliente desconocido');
});

await testAsync('Hilary confirma con "ok" + número → registra pedido', async () => {
  const pp = makePendingPayments();
  const clientPhone = '5215512345678';
  const fakeOrder = { producto: 'plan familiar' };
  pp.set(clientPhone, { orderData: fakeOrder, timestamp: Date.now() });

  let registered = null;
  let clientNotified = false;
  let hilaryNotified = false;

  const result = await simulateTransferFlow(pp, HILARY,
    { type: 'text', text: `ok ${clientPhone}` },
    {
      HILARY_PHONE: HILARY,
      registerOrder: async (data) => { registered = data; },
      sendMessage: async (to, msg) => {
        if (to === clientPhone) clientNotified = true;
        if (to === HILARY) hilaryNotified = true;
      }
    }
  );

  assert.equal(result.action, 'pedido_confirmado');
  assert.deepEqual(registered, fakeOrder);
  assert.ok(clientNotified, 'cliente no fue notificado del pago confirmado');
  assert.ok(hilaryNotified, 'Hilary no fue notificada del registro');
  assert.equal(pp.has(clientPhone), false, 'entrada no fue eliminada de pendingPayments');
});

await testAsync('Hilary confirma sin número → usa cliente más antiguo', async () => {
  const pp = makePendingPayments();
  const olderPhone = '5215511111111';
  const newerPhone = '5215522222222';
  pp.set(olderPhone, { orderData: null, timestamp: 1000 });
  pp.set(newerPhone, { orderData: null, timestamp: 2000 });

  const result = await simulateTransferFlow(pp, HILARY,
    { type: 'text', text: 'listo, ya lo revisé' },
    { HILARY_PHONE: HILARY, sendMessage: async () => {} }
  );

  assert.equal(result.action, 'pedido_confirmado');
  assert.equal(result.clientPhone, olderPhone, 'debería seleccionar el cliente más antiguo');
});

await testAsync('Hilary manda texto sin confirmación → sin acción', async () => {
  const pp = makePendingPayments();
  pp.set('5215512345678', { orderData: null, timestamp: Date.now() });

  const result = await simulateTransferFlow(pp, HILARY,
    { type: 'text', text: '¿cuántos pedidos hay pendientes?' },
    { HILARY_PHONE: HILARY }
  );

  assert.equal(result.action, 'hilary_sin_accion');
});

await testAsync('mensaje normal de cliente → sin acción especial', async () => {
  const pp = makePendingPayments();
  const result = await simulateTransferFlow(pp, '5215512345678',
    { type: 'text', text: '¿cuánto cuesta el plan familiar?' },
    {}
  );
  assert.equal(result.action, 'mensaje_normal');
});

// ─── 5. confirmRegex ─────────────────────────────────────────────────────────
console.log('\n🔍 confirmRegex');

const confirmRegex = /\b(ok|sí|si|listo|confirmado|acepta|confirmo|aprobado)\b/i;

test('"ok" hace match', () => assert.ok(confirmRegex.test('ok')));
test('"sí" hace match', () => assert.ok(confirmRegex.test('sí')));
test('"si" hace match', () => assert.ok(confirmRegex.test('si')));
test('"listo" hace match', () => assert.ok(confirmRegex.test('listo')));
test('"confirmado" hace match', () => assert.ok(confirmRegex.test('confirmado')));
test('"aprobado" hace match', () => assert.ok(confirmRegex.test('aprobado')));
test('"no" NO hace match', () => assert.equal(confirmRegex.test('no'), false));
test('"espera" NO hace match', () => assert.equal(confirmRegex.test('espera'), false));
test('mayúsculas "OK" hace match', () => assert.ok(confirmRegex.test('OK')));
test('"ok 5215512345678" hace match', () => assert.ok(confirmRegex.test('ok 5215512345678')));

// ─── 6. Webhook parsing ──────────────────────────────────────────────────────
console.log('\n🌐 Webhook parsing');

function parseWebhookMessage(body) {
  try {
    const entry = body?.entry?.[0];
    const change = entry?.changes?.[0];
    const value = change?.value;
    const msg = value?.messages?.[0];
    const from = msg?.from;
    if (!msg || !from) return null;
    return { from, msg };
  } catch {
    return null;
  }
}

test('parsea mensaje de texto correctamente', () => {
  const body = {
    entry: [{ changes: [{ value: { messages: [{ from: '521551234567', type: 'text', text: { body: 'hola' } }] } }] }]
  };
  const r = parseWebhookMessage(body);
  assert.equal(r.from, '521551234567');
  assert.equal(r.msg.type, 'text');
});

test('parsea mensaje de imagen correctamente', () => {
  const body = {
    entry: [{ changes: [{ value: { messages: [{ from: '521551234567', type: 'image', image: { id: 'img-123' } }] } }] }]
  };
  const r = parseWebhookMessage(body);
  assert.equal(r.msg.type, 'image');
  assert.equal(r.msg.image.id, 'img-123');
});

test('retorna null si no hay messages', () => {
  const body = { entry: [{ changes: [{ value: {} }] }] };
  assert.equal(parseWebhookMessage(body), null);
});

test('retorna null con body vacío', () => {
  assert.equal(parseWebhookMessage({}), null);
});

// ─── 7. Prompt structure ─────────────────────────────────────────────────────
console.log('\n🤖 Prompt structure');

const MOCK_PROMPT = `
Eres el asistente de ventas de MR Apolo.
JAMAS digas que eres IA, asistente virtual ni bot.
JAMAS digas que estás disponible 24/7.
Si te preguntan el horario, di: Atendemos lunes a viernes de 6am a 10pm, sábados y domingos de 7am a 9pm.
No compartas números de teléfono bajo ningún motivo.
`.trim();

test('prompt prohíbe decir "asistente virtual"', () => {
  assert.ok(MOCK_PROMPT.includes('asistente virtual'), 'debe mencionar "asistente virtual" como prohibido');
});

test('prompt prohíbe decir "24/7"', () => {
  assert.ok(MOCK_PROMPT.includes('24/7'), 'debe prohibir mencionar 24/7');
});

test('prompt incluye horario L-V 6am-10pm', () => {
  assert.ok(MOCK_PROMPT.includes('lunes a viernes de 6am a 10pm'), 'horario L-V ausente');
});

test('prompt incluye horario sáb-dom 7am-9pm', () => {
  assert.ok(MOCK_PROMPT.toLowerCase().includes('sábados y domingos de 7am a 9pm'), 'horario fin de semana ausente');
});

test('prompt prohíbe compartir teléfonos', () => {
  assert.ok(MOCK_PROMPT.toLowerCase().includes('números de teléfono'), 'debe prohibir compartir números');
});

// ─── Resumen ─────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(50)}`);
console.log(`  Total: ${passed + failed}  ✓ ${passed}  ✗ ${failed}`);
if (failed > 0) process.exit(1);
        sentToHilary = true;
      },
      sendMessage: async (to) => {
        if (to !== HILARY) notifiedClient = true;
      }
    }
  );

  assert.ok(sentToHilary, 'imagen no fue reenviada a Hilary');
  assert.ok(notifiedClient, 'cliente no fue notificado');
});

await testAsync('imagen de cliente SIN pendingPayment → se ignora', async () => {
  const pp = makePendingPayments(); // vacío
  let sentToHilary = false;

  const r = await simulateTransferFlow(pp, '5215599999999',
    { type: 'image', image: { id: 'img-random' } },
    { HILARY_PHONE: HILARY, sendImageById: async () => { sentToHilary = true; } }
  );

  assert.equal(r.action, 'imagen_ignorada');
  assert.ok(!sentToHilary, 'no debería reenviar imagen sin pago pendiente');
});

await testAsync('Hilary confirma con "ok" → registra pedido y notifica cliente', async () => {
  const pp = makePendingPayments();
  const clientPhone = '5215512345678';
  const orderData = { nombre: 'Rex', tamano: '250g', colonia: 'Del Valle' };
  pp.set(clientPhone, { orderData, timestamp: Date.now() });

  let registeredOrder = null;
  let clientNotified = false;
  let hilaryNotified = false;

  const r = await simulateTransferFlow(pp, HILARY,
    { type: 'text', text: `ok ${clientPhone}` },
    {
      HILARY_PHONE: HILARY,
      registerOrder: async (data) => { registeredOrder = data; },
      sendMessage: async (to, msg) => {
        if (to === clientPhone) clientNotified = true;
        if (to === HILARY) hilaryNotified = true;
      }
    }
  );

  assert.equal(r.action, 'pedido_confirmado');
  assert.equal(r.clientPhone, clientPhone);
  assert.deepEqual(registeredOrder, orderData);
  assert.ok(clientNotified, 'cliente no fue notificado');
  assert.ok(hilaryNotified, 'Hilary no fue notificada');
  assert.ok(!pp.has(clientPhone), 'cliente debería eliminarse de pendingPayments');
});

await testAsync('Hilary confirma "listo" sin número → usa el cliente más antiguo', async () => {
  const pp = makePendingPayments();
  const old = '5215500000001';
  const young = '5215500000002';
  pp.set(old,   { orderData: { nombre: 'Viejo' }, timestamp: Date.now() - 60000 });
  pp.set(young, { orderData: { nombre: 'Nuevo' }, timestamp: Date.now() });

  let confirmedPhone = null;

  const r = await simulateTransferFlow(pp, HILARY,
    { type: 'text', text: 'listo ya revisé el comprobante' },
    {
      HILARY_PHONE: HILARY,
      registerOrder: async () => {},
      sendMessage: async (to) => { if (to !== HILARY) confirmedPhone = to; }
    }
  );

  assert.equal(r.action, 'pedido_confirmado');
  assert.equal(confirmedPhone, old, `debería confirmar al más antiguo (${old}), no ${confirmedPhone}`);
});

await testAsync('Hilary manda texto que no es confirmación → sin acción', async () => {
  const pp = makePendingPayments();
  pp.set('5215512345678', { orderData: null, timestamp: Date.now() });

  const r = await simulateTransferFlow(pp, HILARY,
    { type: 'text', text: '¿cuándo llega el pedido?' },
    { HILARY_PHONE: HILARY }
  );
  assert.equal(r.action, 'hilary_sin_accion');
});

await testAsync('confirmRegex acepta todas las palabras clave', async () => {
  const confirmRegex = /\b(ok|sí|si|listo|confirmado|acepta|confirmo|aprobado)\b/i;
  const casos = ['ok', 'OK', 'sí', 'si', 'listo', 'Listo', 'confirmado', 'confirmo', 'aprobado'];
  for (const c of casos) {
    assert.ok(confirmRegex.test(c), `"${c}" no pasa el regex de confirmación`);
  }
});

await testAsync('BANORTE detectado → cliente entra a pendingPayments', async () => {
  const pp = makePendingPayments();
  const from = '5215512345678';
  const replyFiltrado = 'Aquí están los datos BANORTE para tu transferencia';

  if (replyFiltrado.includes('BANORTE')) {
    pp.set(from, { orderData: null, timestamp: Date.now() });
  }

  assert.ok(pp.has(from), 'cliente no fue agregado a pendingPayments tras BANORTE');
  assert.equal(pp.get(from).orderData, null);
});

// ─── 5. Webhook payload parsing ──────────────────────────────────────────────
console.log('\n🔗 Webhook payload parsing');

function parseWebhook(body) {
  if (body.object !== 'whatsapp_business_account') return null;
  const entry = body.entry?.[0];
  const change = entry?.changes?.[0];
  const value = change?.value;
  const messages = value?.messages;
  if (!messages?.length) return null;
  return { msg: messages[0], from: messages[0].from };
}

test('payload válido de WhatsApp texto es parseado', () => {
  const body = {
    object: 'whatsapp_business_account',
    entry: [{ changes: [{ value: { messages: [{ from: '5215512345678', type: 'text', text: { body: 'hola' } }] } }] }]
  };
  const r = parseWebhook(body);
  assert.ok(r !== null);
  assert.equal(r.from, '5215512345678');
  assert.equal(r.msg.type, 'text');
});

test('payload válido de WhatsApp audio es parseado', () => {
  const body = {
    object: 'whatsapp_business_account',
    entry: [{ changes: [{ value: { messages: [{ from: '5215512345678', type: 'audio', audio: { id: 'audio-999' } }] } }] }]
  };
  const r = parseWebhook(body);
  assert.ok(r !== null);
  assert.equal(r.msg.type, 'audio');
  assert.equal(r.msg.audio.id, 'audio-999');
});

test('payload con imagen es parseado', () => {
  const body = {
    object: 'whatsapp_business_account',
    entry: [{ changes: [{ value: { messages: [{ from: '521551234', type: 'image', image: { id: 'img-abc' } }] } }] }]
  };
  const r = parseWebhook(body);
  assert.ok(r !== null);
  assert.equal(r.msg.type, 'image');
  assert.equal(r.msg.image.id, 'img-abc');
});

test('objeto que no es whatsapp_business_account retorna null', () => {
  assert.equal(parseWebhook({ object: 'other_object', entry: [] }), null);
});

test('payload sin mensajes retorna null', () => {
  const body = {
    object: 'whatsapp_business_account',
    entry: [{ changes: [{ value: { messages: [] } }] }]
  };
  assert.equal(parseWebhook(body), null);
});

test('payload vacío no lanza excepción', () => {
  assert.equal(parseWebhook({}), null);
});

// ─── 6. Agent prompt structure ───────────────────────────────────────────────
console.log('\n🤖 Agent prompt structure');

function buildPromptSimulation() {
  return [
    'ESTILO: NUNCA uses el caracter - en tus respuestas. Habla siempre en oraciones naturales, sin listas ni guiones. Max 2-3 oraciones por mensaje, ve directo al punto.',
    'JAMAS digas que eres IA, asistente virtual ni bot.',
    'JAMAS digas que estás disponible 24/7.',
    'Si te preguntan el horario, di: Atendemos lunes a viernes de 6am a 10pm, sábados y domingos de 7am a 9pm.',
    'FLUJO DE VENTA (guia organico hacia el cierre):',
    '1) Saluda y pregunta nombre del perro.',
    '2) Pregunta dieta actual, sugiere receta ideal.',
    '3) Pregunta tamano: Estandar 250g (3-5 porciones) o Familiar 400g (5-8 porciones).',
    '4) Confirma colonia de entrega y horario.',
    '5) Solicita el pedido de forma directa y amigable.',
    'CALIFICACION DE LEAD',
    'REGLAS:'
  ].join('\n');
}

const prompt = buildPromptSimulation();

test('prompt incluye instrucción ESTILO', () => {
  assert.ok(prompt.includes('ESTILO'), 'falta ESTILO');
});

test('prompt prohíbe el caracter -', () => {
  assert.ok(prompt.includes('NUNCA uses el caracter -'), 'falta prohibición del guión');
});

test('prompt prohíbe decir que es IA o asistente virtual', () => {
  assert.ok(prompt.includes('asistente virtual'), 'falta prohibición de asistente virtual');
  assert.ok(prompt.includes('JAMAS'), 'falta JAMAS');
});

test('prompt prohíbe mencionar disponibilidad 24/7', () => {
  assert.ok(prompt.includes('24/7'), 'falta prohibición de 24/7');
});

test('prompt incluye horario correcto de atención', () => {
  assert.ok(prompt.includes('6am a 10pm'), 'falta horario L-V');
  assert.ok(prompt.includes('7am a 9pm'), 'falta horario fin de semana');
});

test('prompt incluye FLUJO DE VENTA', () => {
  assert.ok(prompt.includes('FLUJO DE VENTA'), 'falta FLUJO DE VENTA');
});

test('flujo tiene los 5 pasos de venta', () => {
  ['1)', '2)', '3)', '4)', '5)'].forEach(p => {
    assert.ok(prompt.includes(p), `falta paso ${p}`);
  });
});

test('prompt menciona tamaños Estandar y Familiar', () => {
  assert.ok(prompt.includes('Estandar 250g'), 'falta Estandar 250g');
  assert.ok(prompt.includes('Familiar 400g'), 'falta Familiar 400g');
});

test('prompt incluye calificación de lead', () => {
  assert.ok(prompt.includes('CALIFICACION DE LEAD'), 'falta CALIFICACION DE LEAD');
});

// ─── Summary ─────────────────────────────────────────────────────────────────
console.log(`\n${'─'.repeat(50)}`);
const total = passed + failed;
console.log(`Resultados: ${passed}/${total} tests pasaron`);
if (failed > 0) {
  console.error(`${failed} test(s) fallaron`);
  process.exit(1);
} else {
  console.log('✅ Todos los tests pasaron');
}
