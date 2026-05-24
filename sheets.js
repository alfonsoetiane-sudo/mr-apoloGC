import { google } from 'googleapis';
import dotenv from 'dotenv';
dotenv.config();

function getAuth() {
  if (process.env.GOOGLE_CREDENTIALS_BASE64) {
    try {
      const credentials = JSON.parse(
        Buffer.from(process.env.GOOGLE_CREDENTIALS_BASE64, 'base64').toString()
      );
      return new google.auth.GoogleAuth({ credentials, scopes: ['https://www.googleapis.com/auth/spreadsheets'] });
    } catch (e) {
      console.warn('GOOGLE_CREDENTIALS_BASE64 inválido, usando archivo credentials.json');
    }
  }
  return new google.auth.GoogleAuth({
    keyFile: process.env.GOOGLE_CREDENTIALS_PATH || './credentials.json',
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
}

const sheets = google.sheets({ version: 'v4', auth: getAuth() });
const SHEET_ID = process.env.SHEET_ID;
const TAB_PEDIDOS = 'Pedidos';
const TAB_CONFIG  = 'Config';
const TAB_INVENTARIO = 'Inventario';

async function geocodeDireccion(calle, colonia, cp, alcaldia) {
  const API_KEY = process.env.GOOGLE_MAPS_API_KEY;
  if (!API_KEY) {
    console.warn('geocodeDireccion: falta API Key');
    return { lat: '', lng: '' };
  }
  const partes = [calle, colonia, cp, alcaldia, 'Ciudad de México', 'México'].filter(Boolean);
  const direccionCompleta = partes.join(', ');
  const address = encodeURIComponent(direccionCompleta);
  const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${address}&key=${API_KEY}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === 'OK' && data.results.length > 0) {
      const location = data.results[0].geometry.location;
      console.log(`📍 Geocodificado: ${direccionCompleta} → ${location.lat}, ${location.lng}`);
      return { lat: location.lat.toString(), lng: location.lng.toString() };
    } else {
      console.warn(`⚠️ Geocoding sin resultados para: ${direccionCompleta}`);
    }
  } catch (e) {
    console.error('❌ Geocoding error:', e.message);
  }
  return { lat: '', lng: '' };
}

export async function initSheet() {
  try {
    const encabezados = [
      'Fecha',                // A
      'Nombre Cliente',       // B
      'Nombre Perro',         // C
      'Telefono',             // D
      'Receta',               // E
      'Tamaño',               // F
      'Cantidad',             // G
      'Total MXN',            // H
      'Forma de Pago',        // I
      'Pagado',               // J
      'Lead Score',           // K
      'Recurrente',           // L
      'Estado',               // M
      'Notas',                // N
      'Calle y número',       // O
      'Colonia',              // P
      'Código Postal',        // Q
      'Alcaldía',             // R
      'Latitud',              // S
      'Longitud',             // T
      'Link MAPS',            // U
      'Fecha de Entrega del Pedido', // V
      'Pedido Entregado'            // W (checkbox — trigger de encuesta)
    ];

    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `${TAB_PEDIDOS}!A1:W1`
    });

    if (!res.data.values || res.data.values.length === 0) {
      await sheets.spreadsheets.values.update({
        spreadsheetId: SHEET_ID,
        range: `${TAB_PEDIDOS}!A1:V1`,
        valueInputOption: 'USER_ENTERED',
        requestBody: { values: [encabezados] }
      });
      console.log('✅ Encabezados de Pedidos creados con nueva estructura');
    }
  } catch (err) {
    console.error('Error initSheet:', err.message);
  }
}

export async function registerOrder(data) {
  try {
    const { lat, lng } = await geocodeDireccion(
      data.calle || '',
      data.colonia || '',
      data.cp || '',
      data.alcaldia || ''
    );

    const mapsLink = lat && lng
      ? `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`
      : '';

    // Solo fecha (sin hora) en la columna A
    const fecha = new Date().toLocaleDateString('es-MX', { timeZone: 'America/Mexico_City' });

    await sheets.spreadsheets.values.append({
      spreadsheetId: SHEET_ID,
      range: `${TAB_PEDIDOS}!A:V`,
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: [[
          fecha,                     // A: Fecha
          data.nombre || '',         // B: Nombre Cliente
          data.nombrePerro || '',    // C: Nombre Perro
          data.telefono || '',       // D: Telefono
          data.receta || '',         // E: Receta
          data.tamano || '',         // F: Tamano
          data.cantidad || '',       // G: Cantidad
          data.total || '',          // H: Total MXN
          data.formaPago || '',      // I: Forma de Pago
          data.pagado || 'No',       // J: Pagado
          data.leadScore || 'frio',  // K: Lead Score
          data.recurrente || 'No',   // L: Recurrente
          data.estado || 'Pendiente',// M: Estado
          data.notas || '',          // N: Notas
          data.calle || '',          // O: Calle y número
          data.colonia || '',        // P: Colonia
          data.cp || '',             // Q: Código Postal
          data.alcaldia || '',       // R: Alcaldía
          lat ? `'${lat}` : '',      // S: Latitud (texto forzado)
          lng ? `'${lng}` : '',      // T: Longitud (texto forzado)
          mapsLink,                  // U: Link MAPS
          data.fechaEntrega || ''    // V: Fecha de Entrega
        ]]
      }
    });

    console.log(`✅ Pedido registrado: ${data.nombre} (entrega: ${data.fechaEntrega})`);
    return { lat, lng };
  } catch (err) {
    console.error('Error registerOrder:', err.message);
    throw err;
  }
}

export async function getOrders() {
  try {
    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `${TAB_PEDIDOS}!A:V`
    });
    const rows = res.data.values || [];
    const headers = rows[0] || [];
    return rows.slice(1).map(row => {
      const obj = {};
      headers.forEach((h, i) => obj[h] = row[i] || '');
      return obj;
    });
  } catch (err) {
    console.error('Error getOrders:', err.message);
    return [];
  }
}

export async function getInventory() {
  try {
    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `${TAB_INVENTARIO}!A:D`
    });
    const rows = res.data.values || [];
    if (rows.length === 0) return { estandar: true, familiar: true };
    const headers = rows[0] || [];
    const data = {};
    rows.slice(1).forEach(row => {
      const obj = {};
      headers.forEach((h, i) => obj[h] = row[i] || '');
      if (obj.Producto) data[obj.Producto] = obj;
    });
    return data;
  } catch (err) {
    console.error('Error getInventory:', err.message);
    return { estandar: true, familiar: true };
  }
}

export async function getConfig() {
  try {
    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEET_ID,
      range: `${TAB_CONFIG}!A:B`
    });
    const rows = res.data.values || [];
    const config = {};
    rows.forEach(([key, value]) => { if (key) config[key] = value || ''; });
    return config;
  } catch (err) {
    console.error('Error getConfig:', err.message);
    return {};
  }
}

export async function saveConfig(data) {
  try {
    const rows = Object.entries(data).map(([k, v]) => [k, v]);
    await sheets.spreadsheets.values.clear({
      spreadsheetId: SHEET_ID,
      range: `${TAB_CONFIG}!A:B`
    });
    await sheets.spreadsheets.values.update({
      spreadsheetId: SHEET_ID,
      range: `${TAB_CONFIG}!A1`,
      valueInputOption: 'USER_ENTERED',
      requestBody: { values: rows }
    });
  } catch (err) {
    console.error('Error saveConfig:', err.message);
  }
}

export async function getCustomerByPhone(phone) {
  try {
    const orders = await getOrders();
        return orders.find(o => o["Telefono"] === phone) || null;
  } catch (err) {
    return null;
  }
}
