/*
 * 03 · Calles (ejes de viario) del callejero oficial, con su nombre
 * -----------------------------------------------------------------
 * Descarga las geometrías de viario del servicio ArcGIS del Ayuntamiento y
 * genera el fichero que usa la app (app/calles.js):
 *
 *   window.CALLES = { fuente, escala: 1e5, k: [...], p: [...], n: [...], names: [...] }
 *   - p: cada línea es [x0,y0, dx1,dy1, ...] en enteros (lng/lat × 1e5),
 *        con el primer punto absoluto y el resto como diferencias.
 *   - k: jerarquía de la línea: 2 = la vía figura en la capa 1:25.000,
 *        1 = en la capa 1:20.000, 0 = resto.
 *   - n: índice del nombre de la vía en `names` (rótulo oficial DEN_TX_ETIQUETA).
 *
 * Geometría: capa 0 (VIARIO_EJES_1000). Las capas 2 (VIARIO_EJES_20000) y
 * 3 (VIARIO_EJES_25000) solo se usan para saber qué vías son principales.
 *
 * Uso: abrir https://sigma.madrid.es/hosted/rest/services/CALLEJERO/CALLEJERO_ROTULACION_GEOMETRIAS/MapServer?f=json
 *      en el navegador, consola (F12), pegar este archivo. Se descarga
 *      calles_madrid_con_nombres.json (el contenido es JavaScript): copiarlo
 *      como app/calles.js (y en datos/ como referencia).
 */
(async () => {
  const B = 'https://sigma.madrid.es/hosted/rest/services/CALLEJERO/CALLEJERO_ROTULACION_GEOMETRIAS/MapServer';
  const ESC = 1e5, PAGE = 2000;
  async function query(id, geo) {
    const out = [];
    for (let off = 0; ; off += PAGE) {
      const q = new URLSearchParams({ where: '1=1', outFields: 'DEN_TX_ETIQUETA', returnGeometry: geo ? 'true' : 'false', outSR: '4326', f: 'json',
        maxAllowableOffset: '0.00004', geometryPrecision: '5', resultOffset: String(off), resultRecordCount: String(PAGE) });
      const j = await (await fetch(`${B}/${id}/query?${q}`)).json();
      const fs = j.features || []; out.push(...fs);
      console.log('capa', id, 'offset', off, '+', fs.length);
      if (fs.length < PAGE && !j.exceededTransferLimit) break;
    }
    return out;
  }
  const L0 = await query(0, true);
  const n20 = new Set((await query(2, false)).map(f => f.attributes.DEN_TX_ETIQUETA));
  const n25 = new Set((await query(3, false)).map(f => f.attributes.DEN_TX_ETIQUETA));

  const k = [], p = [], n = [], names = [], idx = new Map();
  for (const f of L0) {
    const nm = f.attributes.DEN_TX_ETIQUETA || '';
    const kk = n25.has(nm) ? 2 : n20.has(nm) ? 1 : 0;
    for (const path of (f.geometry?.paths || [])) {
      if (path.length < 2) continue;
      let px = 0, py = 0; const d = [];
      for (const [lng, lat] of path) { const x = Math.round(lng * ESC), y = Math.round(lat * ESC); d.push(x - px, y - py); px = x; py = y; }
      if (!idx.has(nm)) { idx.set(nm, names.length); names.push(nm); }
      k.push(kk); p.push(d); n.push(idx.get(nm));
    }
  }
  const C = { fuente: 'Ayuntamiento de Madrid, Geoportal - Callejero oficial, geometrías de viario (VIARIO_EJES_1000) con nombre de vía (DEN_TX_ETIQUETA)', escala: ESC, k, p, n, names };
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['window.CALLES=' + JSON.stringify(C) + ';'], { type: 'application/json' }));
  a.download = 'calles_madrid_con_nombres.json';   // .json: el navegador bloquea a veces la descarga de .js; renombrar a calles.js
  a.click();
  console.log('líneas:', p.length, '· vías con nombre:', names.length);
})();
