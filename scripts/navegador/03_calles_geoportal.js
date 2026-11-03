/*
 * 03 · Calles (ejes de viario) del callejero oficial del Geoportal
 * ----------------------------------------------------------------
 * Descarga las geometrías de viario del servicio ArcGIS del Ayuntamiento y
 * genera calles_madrid_viario_ejes_1000.js con el formato que usa la app:
 *
 *   window.CALLES = { fuente, escala: 1e5, k: [jerarquía por línea], p: [líneas] }
 *   - k: 0 = calle local (solo se dibuja con zoom), 1 = secundaria, 2 = principal
 *   - p: cada línea es [x0,y0, dx1,dy1, dx2,dy2, ...] en enteros (lng/lat × 1e5),
 *        primer punto absoluto y el resto como diferencias con el anterior.
 *
 * Uso: abrir https://sigma.madrid.es/hosted/rest/services/CALLEJERO/CALLEJERO_ROTULACION_GEOMETRIAS/MapServer
 *      en el navegador, consola (F12), pegar este archivo. Copiar el .js
 *      descargado a app/calles.js (y a datos/ como referencia).
 *
 * IMPORTANTE: el reparto capa → jerarquía de CAPAS es el que se usó en la
 * extracción (capas 0, 2 y 3). Antes de regenerar, revisar en la página del
 * MapServer el nombre de cada capa y ajustar CAPAS si el servicio ha cambiado.
 */
(async () => {
  const BASE = 'https://sigma.madrid.es/hosted/rest/services/CALLEJERO/CALLEJERO_ROTULACION_GEOMETRIAS/MapServer';
  const CAPAS = [{ id: 3, k: 0 }, { id: 2, k: 1 }, { id: 0, k: 2 }];   // revisar (ver nota)
  const ESC = 1e5, PAGE = 2000;

  for (const c of CAPAS) {
    const meta = await (await fetch(`${BASE}/${c.id}?f=json`)).json();
    console.log('capa', c.id, '→ jerarquía', c.k, ':', meta.name, meta.geometryType);
  }

  const k = [], p = [];
  for (const c of CAPAS) {
    for (let off = 0; ; off += PAGE) {
      const q = new URLSearchParams({
        where: '1=1', outFields: '', returnGeometry: 'true', outSR: '4326', f: 'json',
        maxAllowableOffset: '0.00004', geometryPrecision: '5',
        resultOffset: String(off), resultRecordCount: String(PAGE)
      });
      const j = await (await fetch(`${BASE}/${c.id}/query?${q}`)).json();
      const feats = j.features || [];
      for (const f of feats) for (const path of (f.geometry?.paths || [])) {
        if (path.length < 2) continue;
        let px = 0, py = 0; const d = [];
        for (const [lng, lat] of path) { const x = Math.round(lng * ESC), y = Math.round(lat * ESC); d.push(x - px, y - py); px = x; py = y; }
        k.push(c.k); p.push(d);
      }
      console.log('capa', c.id, 'offset', off, '+', feats.length);
      if (feats.length < PAGE && !j.exceededTransferLimit) break;
    }
  }

  const fuente = 'Ayuntamiento de Madrid, Geoportal - Callejero oficial, geometrías de viario (VIARIO_EJES_1000)';
  const js = 'window.CALLES=' + JSON.stringify({ fuente, escala: ESC, k, p }) + ';';
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([js], { type: 'text/javascript' }));
  a.download = 'calles_madrid_viario_ejes_1000.json';   // .json: el navegador bloquea a veces la descarga de .js; renombrar a .js
  a.click();
  console.log('líneas:', p.length);
})();
