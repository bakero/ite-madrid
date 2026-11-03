/*
 * 02 · Consulta de la última ITE/IEE en el Registro de Edificios y Construcciones
 * ------------------------------------------------------------------------------
 * Para cada dirección pendiente consulta el formulario público
 * https://servpub.madrid.es/GITEP_WBFICHA/SGiteCons (opción 2 → vial,
 * opción 4 → números de portal, opción 6 → ficha) y descarga
 * ite_resultados_AAAAMMDD_HHMM.json  ({"<dirección>": [26 campos]}).
 *
 * Uso:
 *   1. python3 scripts/build_db.py   → genera datos/pendientes_ite.json
 *   2. Abrir https://servpub.madrid.es/GITEP_WBFICHA/SGiteCons en el navegador
 *      (las peticiones tienen que salir desde ese origen), abrir la consola (F12)
 *      y pegar este archivo entero.
 *   3. Elegir datos/pendientes_ite.json en el selector de archivo que aparece.
 *   4. Al terminar (o con ITE.descargar() en cualquier momento) se descarga el
 *      volcado. Cargarlo con scripts/sync.sh o
 *      python3 scripts/ingest_export.py <volcado.json>
 *
 * Notas:
 *   - El servidor es lento (de 1 a 55 s por ficha). Las fichas (opción 6) se
 *     piden de una en una (mutex) y con un tiempo máximo de 150 s.
 *   - «ERROR con BDC» lo devuelve el propio Registro para ciertos edificios y no
 *     se arregla reintentando: se guarda como "Error: Registro: error BDC…".
 *   - El progreso se guarda en localStorage (ITE_RES) cada 50 direcciones.
 *   - Los datos del Registro no tienen carácter de certificado.
 *
 * Campos de cada resultado (índice → significado), los mismos que lee ingest_export.py:
 *  0 resultado de la consulta · 1 dirección en el Registro · 2 denominación ·
 *  3 año construcción · 4 año 1ª obligación · 5 año próxima ITE · 6 fecha máx. IEE ·
 *  7 nº de ITE/IEE · 8 nº expediente · 9 fecha presentación · 10 tipo expediente ·
 *  11 dictamen · 12 parcial/total · 13 causa desfavorable · 14 situación administrativa ·
 *  15 dependencia actual · 16 expediente orden de ejecución · 17 nº órdenes ·
 *  18 estado orden · 19 dependencia orden · 20 fecha resolución · 21 resolución ·
 *  22 deficiencias subsanadas · 23 ITE/IEE anteriores · 24 código postal · 25 distrito
 */
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const P = new DOMParser(), parse = h => P.parseFromString(h, 'text/html');
  // El formulario espera ISO-8859-1 en la URL-encoding
  const enc = s => [...String(s)].map(c => { const n = c.charCodeAt(0); if (/[A-Za-z0-9\-_.*]/.test(c)) return c; if (c === ' ') return '+'; return '%' + n.toString(16).toUpperCase().padStart(2, '0'); }).join('');
  const clean = s => (s || '').replace(/ /g, ' ').replace(/\s+/g, ' ').trim();
  const nrm = s => clean(s).toUpperCase().normalize('NFD').replace(/[̀-̂̄-ͯ]/g, '').normalize('NFC'); // conserva la Ñ
  const strip = n => n.replace(/^(DE LA|DE LOS|DE LAS|DEL|DE|LA|EL|LAS|LOS) /, '');
  const IP = { done: 0, start: Date.now(), timeouts: 0, bad: 0 };

  const post = async (p, timeout = 30000) => {
    const body = Object.entries(p).map(([k, v]) => k + '=' + enc(v ?? '')).join('&');
    for (let i = 0; i < 2; i++) {
      const ac = new AbortController(), to = setTimeout(() => ac.abort(), timeout);
      try {
        const r = await fetch('SGiteCons', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body, signal: ac.signal });
        const b = await r.arrayBuffer(); clearTimeout(to);
        return new TextDecoder('iso-8859-1').decode(b);
      } catch (e) {
        clearTimeout(to);
        if (e.name === 'AbortError') { IP.timeouts++; throw new Error('Timeout del Registro (>' + timeout / 1000 + ' s)'); }
        await sleep(2000);
      }
    }
    throw new Error('post failed');
  };
  // Comprueba que la respuesta es la página esperada; BDC = error persistente del Registro
  const postChk = async (p, marker, timeout) => {
    for (let i = 0; i < 4; i++) {
      const h = await post(p, timeout);
      if (h.includes('ERROR con BDC')) throw new Error('Registro: error BDC al mostrar los datos');
      if (h.includes(marker)) return h;
      IP.bad++; await sleep(1500 * (i + 1));
    }
    throw new Error('respuesta inválida');
  };
  // Mutex para la opción 6 (ficha): el servidor se satura con fichas en paralelo
  let lock = Promise.resolve();
  const exclusive = fn => { const r = lock.then(fn, fn); lock = r.catch(() => {}); return r; };

  const parseAddr = a => {
    const m = a.replace(/\([^)]*\)/g, '').match(/^\s*(\S+)\s+(.*?)(?:\s+(\d+|S\/N))?\s*,/i);
    if (!m) return null;
    let tipo = nrm(m[1]); if (tipo === 'C/') tipo = 'CALLE';
    return { tipo, nombre: nrm(m[2]).replace(/\s+/g, ' '), num: m[3] ? m[3].toUpperCase() : null };
  };

  const vialCache = {};
  const findVial = async (tipo, nombre0) => {
    const nombre = strip(nombre0), key = tipo + '|' + nombre0;
    if (vialCache[key]) return await vialCache[key];
    const pr = (async () => {
      const h = await postChk({ opcion: 2, tipo_via: tipo, nombre_via: nombre, exped3: '', exped4: '', exped5: '', registro: '', expediente: '' }, '02. Selecci');
      const vs = [...h.matchAll(/verNumeros\((\d+),\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)/g)].map(m => ({ cod: m[1], tipo: m[2], part: m[3], nom: m[4] }));
      const full = x => nrm(x.part + ' ' + x.nom);
      const nm = x => [nrm(x.nom), strip(nrm(x.nom)), full(x), strip(full(x))].some(s => s == nombre0 || s == nombre);
      let v = vs.find(x => nrm(x.tipo) == tipo && nm(x)) || null;
      if (!v) { const same = vs.filter(x => nrm(x.tipo) == tipo); if (same.length == 1 && vs.length == 1) v = same[0]; }
      return { v, n: vs.length, cands: vs.slice(0, 4).map(x => clean(x.tipo + ' ' + x.part + ' ' + x.nom)).join(' / ') };
    })();
    vialCache[key] = pr;
    try { return await pr; } catch (e) { delete vialCache[key]; throw e; }
  };

  const parseFicha = h => {
    const d = parse(h), o = { ites: [], ordenes: [] };
    for (const t of d.querySelectorAll('table.tablaDatoTipo1')) {
      const txt = t.innerText || t.textContent;
      if (txt.includes('Tipo Incumplimiento')) {           // órdenes de ejecución
        let cur = null;
        for (const tr of t.rows) {
          const v = [...tr.cells].filter(c => c.classList.contains('celdaValor')).map(c => clean(c.textContent));
          if (v.length == 8) {
            if (!v[1] && cur) cur.otras.push([v[5], v[6], v[7]].join(' | '));
            else { cur = { tipoInc: v[0], exp: v[1], estado: v[2], dep: v[3], antecedente: v[4], fechaRes: v[5], res: v[6], subs: v[7], otras: [] }; o.ordenes.push(cur); }
          } else if (v.length == 3 && cur) cur.otras.push(v.join(' | '));
        }
      } else if (txt.includes('de Expediente')) {          // una ITE/IEE
        const e = {}, cs = [...t.querySelectorAll('td')];
        for (let i = 0; i < cs.length; i++) if (cs[i].classList.contains('celdaTitulo') && cs[i + 1]?.classList.contains('celdaValor')) e[clean(cs[i].textContent)] = clean(cs[i + 1].textContent);
        o.ites.push(e);
      } else {                                             // datos del edificio
        let titles = null;
        for (const tr of t.rows) {
          const ti = [...tr.cells].filter(c => c.classList.contains('celdaTitulo')).map(c => clean(c.textContent));
          const va = [...tr.cells].filter(c => c.classList.contains('celdaValor')).map(c => clean(c.textContent));
          if (ti.length && !va.length) titles = ti;
          else if (va.length && titles) { titles.forEach((k, i) => o[k] = va[i]); titles = null; }
          else if (ti.length && va.length) ti.forEach((k, i) => o[k] = va[i]);
        }
      }
    }
    return o;
  };

  const dt = s => { const m = /(\d\d)\/(\d\d)\/(\d{4})/.exec(s || ''); return m ? m[3] + m[2] + m[1] : ''; };
  const summ = r => {
    const ites = (r.ites || []).slice().sort((a, b) => dt(b['Fecha presentación']).localeCompare(dt(a['Fecha presentación'])));
    const L = ites[0] || {}, oe = L['Expediente de orden de ejecución/seguimiento de las obras'], ords = r.ordenes || [];
    const O = ords.find(o => o.exp && o.exp == oe) || ords.find(o => o.antecedente && o.antecedente == L['Nº de Expediente']) || {};
    return [r.status, r.vial || r.cands || '', r['Denominación del Edificio'] || '', r['Año de Construcción a efectos de la inspección'] || '',
      r['Año de 1ª Obligación'] || '', r['Año Próxima I.T.E.'] || '', r['Fecha MÁXIMA Presentación I.E.E.'] || '', ites.length,
      L['Nº de Expediente'] || '', L['Fecha presentación'] || '', L['Tipo de Expediente'] || '', L['Dictamen'] || '', L['PARCIAL/TOTAL'] || '',
      (L['Causa/s dictamen desfavorable'] || '').replace(/^\[|\]$/g, ''), L['Situación Administrativa'] || '', L['Dependencia Actual'] || '',
      oe || '', ords.length, O.estado || '', (O.dep || '').replace(/^-/, ''), O.fechaRes || '', O.res || '', O.subs || '',
      ites.slice(1).map(i => i['Nº de Expediente'] + ' ' + i['Fecha presentación'] + ' ' + i['Dictamen']).join('; '),
      r['Código Postal'] || '', r['Distrito'] || ''];
  };

  const lookup = async a => {
    try {
      if (!a) return { status: 'Sin dirección' };
      if (!a.num || a.num == '0' || a.num == 'S/N') return { status: 'Sin número de portal consultable' };
      const fv = await findVial(a.tipo, a.nombre);
      if (!fv.v) return { status: fv.n ? 'Vial ambiguo' : 'Vial no encontrado', cands: fv.cands };
      const v = fv.v;
      const base = { opcion: 4, origen: 'I', pagina: '', tipo_via: a.tipo, nombre_via: strip(a.nombre), codVial: v.cod, particula: v.part, tipoVia: v.tipo, nombreVia: v.nom };
      if (!v.nums) {
        v.nums = (async () => { const h = await postChk(base, '03. Selecci'); return [...(parse(h).querySelector('select[name=ndp]')?.options || [])].map(o => [clean(o.text), o.value]); })();
        v.nums.catch(() => { v.nums = null; });
      }
      const nums = await v.nums, m = nums.find(x => x[0] == a.num);
      if (!m) return { status: 'Número no encontrado en el vial', vial: clean(v.tipo + ' ' + v.part + ' ' + v.nom) };
      const h = await exclusive(() => postChk({ ...base, opcion: 6, ndp: m[1] }, 'DATOS DEL ACCESO', 150000));
      const f = parseFicha(h); f.status = 'OK'; f.vial = clean(v.tipo + ' ' + v.part + ' ' + v.nom) + ' ' + a.num;
      return f;
    } catch (e) { return { status: 'Error: ' + e.message }; }
  };

  // Lista de direcciones pendientes (datos/pendientes_ite.json)
  const pend = await new Promise(res => {
    const inp = document.createElement('input'); inp.type = 'file'; inp.accept = '.json';
    inp.style.cssText = 'position:fixed;top:10px;left:10px;z-index:99999;background:#fff;padding:8px;border:2px solid #333';
    inp.onchange = async () => { res(JSON.parse(await inp.files[0].text())); inp.remove(); };
    document.body.appendChild(inp);
    console.log('Elige datos/pendientes_ite.json en el selector de arriba a la izquierda');
  });

  let RES = {}; try { RES = JSON.parse(localStorage.getItem('ITE_RES') || '{}'); } catch (e) {}
  const descargar = () => {
    const ts = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 13).replace(/(\d{8})(\d{4})/, '$1_$2');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(RES)], { type: 'application/json' }));
    a.download = 'ite_resultados_' + ts + '.json'; a.click();
  };
  window.ITE = { RES, IP, descargar, lookup, summ };

  const keys = pend.filter(k => !RES[k]); let qi = 0;
  const worker = async () => {
    while (qi < keys.length) {
      const k = keys[qi++];
      RES[k] = summ(await lookup(parseAddr(k)));
      IP.done++;
      if (IP.done % 50 == 0) {
        try { localStorage.setItem('ITE_RES', JSON.stringify(RES)); } catch (e) {}
        console.log(IP.done + '/' + keys.length, ((Date.now() - IP.start) / 60000).toFixed(1) + ' min');
      }
    }
  };
  await Promise.all([worker(), worker(), worker()]);
  try { localStorage.setItem('ITE_RES', JSON.stringify(RES)); } catch (e) {}
  descargar();
})();
