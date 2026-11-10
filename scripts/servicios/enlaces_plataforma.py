"""Busca cada número de expediente en el buscador de licitaciones de la Plataforma de Contratación del Sector Público
y guarda el identificador público de la licitación (idEvl). Versión de servidor de scripts/navegador/05_plataforma_enlaces.js.

Uso: python enlaces_plataforma.py <expedientes.json> <enlaces.json>
  expedientes.json: lista de números de expediente. enlaces.json se completa (no se repiten los ya buscados).
La página es JSF: cada respuesta trae un ViewState nuevo que se reenvía en la siguiente búsqueda.
"""
import json, re, sys, http.cookiejar, urllib.parse, urllib.request
from html.parser import HTMLParser

URL = 'https://contrataciondelestado.es/wps/portal/plataforma/buscadores/busqueda'
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
op.addheaders = [('User-Agent', 'Mozilla/5.0 (mapa ITE Madrid; datos públicos)')]


class Form(HTMLParser):
    def __init__(self):
        super().__init__(); self.forms = []; self.cur = None; self.rows = []; self.tr = None; self.links = []
    def handle_starttag(self, t, a):
        a = dict(a)
        if t == 'form': self.cur = {'action': a.get('action'), 'fields': [], 'submits': []}; self.forms.append(self.cur)
        if t == 'input' and self.cur is not None:
            if a.get('type') == 'submit': self.cur['submits'].append((a.get('id') or '', a.get('name'), a.get('value') or ''))
            elif a.get('name') and a.get('type') not in ('checkbox', 'radio', 'button', 'image'): self.cur['fields'].append((a.get('id') or '', a['name'], a.get('value') or ''))
        if t == 'select' and self.cur is not None and a.get('name'):
            self.cur['fields'].append([a.get('id') or '', a['name'], None]); self.sel = self.cur['fields'][-1]
        if t == 'option' and getattr(self, 'sel', None) is not None:
            if self.sel[2] is None or 'selected' in a: self.sel[2] = a.get('value') or ''
        if t == 'textarea' and self.cur is not None and a.get('name'): self.cur['fields'].append((a.get('id') or '', a['name'], ''))
        if t == 'tr': self.tr = []; self.links = []
        if t == 'a' and self.tr is not None and 'detalle_licitacion' in (a.get('href') or ''): self.links.append(a['href'])
    def handle_endtag(self, t):
        if t == 'select': self.sel = None
        if t == 'form': self.cur = None
        if t == 'tr' and self.tr is not None:
            self.rows.append((re.sub(r'\s+', ' ', ''.join(self.tr)).strip(), self.links)); self.tr = None
    def handle_data(self, d):
        if self.tr is not None: self.tr.append(d)


def parse(h):
    p = Form(); p.feed(h); return p


def formulario(p):
    for f in p.forms:
        if any(i.endswith('text71ExpMAQ') for i, _, _ in f['fields']):
            return f


def main():
    exps = json.load(open(sys.argv[1]))
    try: L = json.load(open(sys.argv[2]))
    except FileNotFoundError: L = {}
    h = op.open(URL, timeout=60).read().decode('utf-8', 'replace')
    p = parse(h); f = formulario(p); base = URL
    if not f:  # la portada muestra enlaces JSF (commandLink): se envía el formulario como si se pulsara «Licitaciones»
        m = re.search(r'id="([^"]*:linkFormularioBusqueda)"', h)
        f0 = next((x for x in p.forms if m and m.group(1).startswith((x['action'] and '') or '')), None) if m else None
        f0 = p.forms[0] if p.forms else None
        if m and f0:
            fid = m.group(1).rsplit(':', 1)[0]
            data = [(n, v) for i, n, v in f0['fields']] + [(fid + ':_idcl', m.group(1))]
            base = urllib.parse.urljoin(URL, f0['action'])
            h = op.open(base, data=urllib.parse.urlencode(data).encode(), timeout=60).read().decode('utf-8', 'replace'); p = parse(h); f = formulario(p)
    if not f:
        sys.exit('No encuentro el formulario con el campo Expediente')
    for e in exps:
        if isinstance(L.get(e), list): continue
        data = [(n, e if i.endswith('text71ExpMAQ') else (v or '')) for (i, n, v) in f['fields']]
        sub = next(s for s in f['submits'] if s[0].endswith(':button1'))
        data.append((sub[1], sub[2]))
        act = urllib.parse.urljoin(base, f['action'])
        try:
            h = op.open(act, data=urllib.parse.urlencode(data).encode(), timeout=90).read().decode('utf-8', 'replace')
        except Exception as ex:
            print(e, 'error', ex); continue
        p = parse(h); f2 = formulario(p)
        if f2: f, base = f2, act
        L[e] = [[urllib.parse.unquote(lk[0].split('idEvl=')[1]), t[:300]] for t, lk in p.rows if lk and e in t]
        print(e, len(L[e]))
        json.dump(L, open(sys.argv[2], 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
