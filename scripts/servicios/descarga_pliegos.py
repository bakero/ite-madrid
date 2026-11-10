"""Descarga de la Plataforma de Contratación del Sector Público el pliego de prescripciones técnicas y los estudios
económicos / anexos de cada licitación, y los pasa a texto (pdftotext -layout).

Uso: python descarga_pliegos.py <lista.json> <carpeta_salida>
  lista.json: {expediente: idEvl}  (idEvl de enlaces.json)
Salida: <carpeta>/<exp con _>__ppt0.txt, __otro1.txt ...
"""
import json, re, sys, pathlib, subprocess, tempfile, urllib.parse, urllib.request
from html.parser import HTMLParser

BASE = 'https://contrataciondelestado.es'
UA = {'User-Agent': 'Mozilla/5.0 (mapa ITE Madrid; datos públicos)'}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


class Filas(HTMLParser):
    """Filas <tr> con su texto y sus enlaces."""
    def __init__(self):
        super().__init__(); self.rows = []; self.cur = None; self.a = []; self.links = []; self.atext = None
    def handle_starttag(self, tag, at):
        at = dict(at)
        if tag == 'tr': self.cur = []; self.a = []
        if tag == 'a':
            self.atext = [at.get('href') or '', '']
    def handle_endtag(self, tag):
        if tag == 'a' and self.atext:
            (self.a if self.cur is not None else []).append(tuple(self.atext)); self.links.append(tuple(self.atext)); self.atext = None
        if tag == 'tr' and self.cur is not None:
            self.rows.append((re.sub(r'\s+', ' ', ''.join(self.cur)).strip(), self.a)); self.cur = None
    def handle_data(self, d):
        if self.cur is not None: self.cur.append(d)
        if self.atext is not None: self.atext[1] += d


def documentos(id_evl, exp):
    url = f'{BASE}/wps/poc?uri=deeplink:detalle_licitacion&idEvl={urllib.parse.quote(id_evl, safe="")}'
    h = get(url).decode('utf-8', 'replace')
    if exp not in h:
        return None
    p = Filas(); p.feed(h)
    out = []
    for t, links in p.rows:
        doc = next((urllib.parse.urljoin(url, a) for a, _ in links if 'GetDocumentByIdServlet' in a), None)
        if not doc: continue
        if re.search(r'\d\d:\d\d:\d\d\s*(Rectificación de )?Pliego', t):
            try:
                hh = get(doc).decode('utf-8', 'replace'); q = Filas(); q.feed(hh)
                for a, tx in q.links:
                    if re.search(r'Prescripciones T', tx, re.I): out.append(('ppt', urllib.parse.urljoin(doc, a)))
            except Exception:
                pass
        elif re.search(r'Estudio (econ|de cost)|Informe econ|Anexo|Relaci[oó]n de (edificios|centros|equipamientos)|Inventario|Prescripciones', t, re.I) \
                and not re.search(r'Acta|Recurso|Resoluci|subrogar|Diligencia', t, re.I):
            out.append(('otro', doc))
    ppt = [x for x in out if x[0] == 'ppt'][:1]
    otros = [x for x in out if x[0] == 'otro'][:4]
    return ppt + otros


def main():
    lista = json.load(open(sys.argv[1])); dst = pathlib.Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
    for exp, id_evl in sorted(lista.items()):
        try:
            docs = documentos(id_evl, exp)
        except Exception as e:
            print(exp, 'error', e); continue
        if docs is None:
            print(exp, 'la página no corresponde al expediente'); continue
        for i, (k, u) in enumerate(docs):
            out = dst / f"{exp.replace('/', '_')}__{k}{i}.txt"
            if out.exists(): continue
            try:
                b = get(u)
            except Exception as e:
                print(exp, k, 'error', e); continue
            if not b.startswith(b'%PDF'):
                out.with_suffix('.skip').write_bytes(b[:200]); continue
            with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
                f.write(b); f.flush()
                subprocess.run(['pdftotext', '-layout', f.name, str(out)], capture_output=True)
        print(exp, len(docs), 'documentos')


if __name__ == '__main__':
    main()
