"""Descarga y normaliza la ejecución presupuestaria de inversiones por proyecto (datos.madrid.es, conjunto 211496),
años 2014 en adelante, todos los distritos.

Uso: python descarga_inversiones.py [carpeta_csv]
  Sin carpeta descarga los CSV «Inversiones. AAAA» del catálogo. Escribe datos/inversiones/inversiones_2014_2025.json
  con columnas: anio, proyecto, titulo, distrito, linea, sublinea, programa, subconcepto, cred_definitivo, obl_reconocidas.
"""
import csv, io, json, os, pathlib, re, sys, urllib.request

BASE = pathlib.Path(__file__).resolve().parents[2]
PKG = 'https://datos.madrid.es/api/3/action/package_show?id=211496-0-ejecucion-presupuestaria-histori'
COLS = ['anio', 'proyecto', 'titulo', 'distrito', 'linea', 'sublinea', 'programa', 'subconcepto', 'cred_definitivo', 'obl_reconocidas']


def leer(b):
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass


def norm_h(h):
    return re.sub(r'[^a-z]', '', h.lower().replace('í', 'i').replace('ó', 'o').replace('é', 'e').replace('ú', 'u').replace('á', 'a').replace('�', ''))


def filas(texto):
    r = list(csv.reader(io.StringIO(texto), delimiter=';'))
    h = [norm_h(x) for x in r[0]]
    def idx(*c):
        for x in c:
            for i, y in enumerate(h):
                if y.startswith(x):
                    return i
        raise KeyError(c)
    I = dict(proyecto=idx('definicionproyecto', 'definicinproyecto'), titulo=idx('titulo', 'ttulo'), distrito=idx('textodistrito'),
             linea=idx('descripcionlinea', 'descripcinlnea', 'descripcinlinea'), sublinea=idx('descripcionsubl', 'descripcinsubl'),
             programa=idx('programa'), subconcepto=idx('subconcepto'), cred_definitivo=idx('cdefinitivo'), obl_reconocidas=idx('oblreconoc'))
    for row in r[1:]:
        if len(row) <= max(I.values()) or not row[I['proyecto']].strip():
            continue
        yield {k: row[i].strip() for k, i in I.items()}


def main():
    carpeta = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    urls = {}
    if not carpeta:
        pkg = json.load(urllib.request.urlopen(PKG))['result']
        for x in pkg['resources']:
            t = (x.get('description') or '') + (x.get('title') or '')
            if t.startswith('Inversiones.') and x['url'].endswith('.csv'):
                urls[t.split()[-1]] = x['url']
    out = []
    anios = sorted(urls) if urls else sorted(re.search(r'(\d{4})', p.name).group(1) for p in carpeta.glob('inv*.csv'))
    for y in anios:
        b = urllib.request.urlopen(urls[y]).read() if urls else (carpeta / f'inv{y}.csv').read_bytes()
        n = 0
        for f in filas(leer(b)):
            out.append([int(y), f['proyecto'], f['titulo'], f['distrito'], f['linea'], f['sublinea'], f['programa'], f['subconcepto'], f['cred_definitivo'], f['obl_reconocidas']])
            n += 1
        print(y, n)
    dst = BASE / 'datos' / 'inversiones' / 'inversiones_2014_2025.json'
    json.dump({'cols': COLS, 'rows': out}, open(dst, 'w'), ensure_ascii=False)
    print(len(out), 'filas →', dst)


if __name__ == '__main__':
    main()
