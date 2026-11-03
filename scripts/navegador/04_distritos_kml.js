/*
 * 04 · Contornos de los 21 distritos (KML del Geoportal)
 * ------------------------------------------------------
 * Descarga el KML oficial de distritos, simplifica cada contorno con
 * Douglas-Peucker (tolerancia 0.00006°, ≈ 5 m) y genera
 * distritos_madrid_simpl.json:  [{cod, nom, lines: [[[lng,lat], ...], ...]}]
 *
 * Uso: abrir https://geoportal.madrid.es/ en el navegador, consola (F12),
 *      pegar este archivo y copiar el JSON descargado a datos/.
 *      Conjunto de datos: https://datos.madrid.es/dataset/300497-0-distritos-municipales-madrid
 */
(async () => {
  const URL_KML = 'https://geoportal.madrid.es/fsdescargas/IDEAM_WBGEOPORTAL/LIMITES_ADMINISTRATIVOS/Distritos/distritos.kml';
  const TOL = 0.00006;
  const round5 = v => Math.round(v * 1e5) / 1e5;

  const dp = (pts, tol) => {             // Douglas-Peucker
    if (pts.length < 3) return pts;
    const keep = new Uint8Array(pts.length); keep[0] = keep[pts.length - 1] = 1;
    const st = [[0, pts.length - 1]];
    while (st.length) {
      const [a, b] = st.pop(); const [ax, ay] = pts[a], [bx, by] = pts[b];
      const dx = bx - ax, dy = by - ay, L = Math.hypot(dx, dy) || 1e-12;
      let md = 0, mi = -1;
      for (let i = a + 1; i < b; i++) { const d = Math.abs(dy * pts[i][0] - dx * pts[i][1] + bx * ay - by * ax) / L; if (d > md) { md = d; mi = i; } }
      if (md > tol) { keep[mi] = 1; st.push([a, mi], [mi, b]); }
    }
    return pts.filter((_, i) => keep[i]);
  };

  const xml = new DOMParser().parseFromString(await (await fetch(URL_KML)).text(), 'application/xml');
  const val = (pm, names) => {
    for (const d of pm.querySelectorAll('SimpleData, Data')) {
      const n = (d.getAttribute('name') || '').toUpperCase();
      if (names.includes(n)) return (d.querySelector('value')?.textContent ?? d.textContent).trim();
    }
    return '';
  };
  const out = [];
  for (const pm of xml.querySelectorAll('Placemark')) {
    const cod = val(pm, ['COD_DIS', 'CODDISTRIT', 'COD_DIS_TX']) || '';
    const nom = val(pm, ['NOMBRE', 'NOM_DIS', 'DISTRITO']) || pm.querySelector('name')?.textContent.trim() || '';
    const lines = [...pm.querySelectorAll('coordinates')].map(c =>
      dp(c.textContent.trim().split(/\s+/).map(s => s.split(',').slice(0, 2).map(Number)), TOL).map(([x, y]) => [round5(x), round5(y)]));
    out.push({ cod: String(+cod || cod), nom, lines });
  }
  console.log(out.map(d => d.cod + ' ' + d.nom + ' (' + d.lines.reduce((s, l) => s + l.length, 0) + ' pts)').join('\n'));
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out)], { type: 'application/json' }));
  a.download = 'distritos_madrid_simpl.json'; a.click();
})();
