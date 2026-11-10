// Enlaces públicos de la Plataforma de Contratación del Sector Público por número de expediente.
// Uso: abrir https://contrataciondelestado.es → Licitaciones → Formulario de búsqueda (página con el campo «Expediente»),
// pegar este script en la consola, asignar antes la lista:  window.EXPS = ["300/2024/00101", ...]
// Al terminar descarga enlaces.json: { expediente: [[idEvl, texto de la fila], ...] }.
// La página es JSF: cada respuesta trae un ViewState nuevo que hay que reenviar en la siguiente búsqueda.
(async () => {
  const EXPS = window.EXPS || [];
  const inp = [...document.querySelectorAll('input')].find(i => i.id.endsWith('text71ExpMAQ'));
  if (!inp) { console.error('No encuentro el campo Expediente: abre el formulario de búsqueda de licitaciones'); return; }
  const st = { vs: document.querySelector('input[name="javax.faces.ViewState"]').value, action: inp.form.action };
  const q = async exp => {
    const f = inp.form, fd = new FormData(f);
    fd.set(inp.name, exp); fd.set('javax.faces.ViewState', st.vs);
    const btn = [...f.querySelectorAll('input[type=submit]')].find(b => b.id.endsWith(':button1'));
    fd.set(btn.name, btn.value);
    const h = await (await fetch(st.action, { method: 'POST', body: new URLSearchParams(fd), credentials: 'include' })).text();
    const d = new DOMParser().parseFromString(h, 'text/html');
    const nv = d.querySelector('input[name="javax.faces.ViewState"]'); if (nv) st.vs = nv.value;
    const ni = [...d.querySelectorAll('input')].find(i => i.id.endsWith('text71ExpMAQ'));
    if (ni && ni.form && ni.form.getAttribute('action')) st.action = new URL(ni.form.getAttribute('action'), location.href).href;
    return [...d.querySelectorAll('a[href*="detalle_licitacion"]')].map(a => {
      const tr = a.closest('tr'); const t = (tr ? tr.textContent : '').replace(/\s+/g, ' ').trim();
      return [decodeURIComponent(a.href.split('idEvl=')[1] || ''), t.slice(0, 300)];
    }).filter(x => x[1].includes(exp));
  };
  const L = {};
  for (const [i, e] of EXPS.entries()) {
    try { L[e] = await q(e); } catch (x) { L[e] = null; }
    if (i % 20 === 0) console.log(i, '/', EXPS.length);
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(L)], { type: 'application/json' }));
  a.download = 'enlaces.json'; a.click();
})();
