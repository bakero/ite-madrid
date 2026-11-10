"""Edificios que cubre cada contrato de servicios de distrito, leídos de sus pliegos y estudios económicos
(texto de pdftotext -layout), para cualquier distrito.

Uso: python reparto_generico.py <carpeta_txt> <empresas_distritos.json> <salida.json>
  Los textos se llaman <exp con _ en vez de />__<n>.txt (p. ej. 300_2024_00101__ppt0.txt).

Para cada expediente:
  1. Recorre las líneas de todos sus documentos y busca edificios del distrito del contrato (edificios.match
     restringido a ese distrito). Una línea solo cuenta si cita un único edificio.
  2. Si la línea pertenece a un bloque «LOTE n» del documento, el edificio se asigna a ese lote.
  3. Peso: si en un mismo documento al menos el 60 % de los edificios encontrados tienen en su línea un número
     final que no es de la dirección (horas, m², euros), se usa ese número como peso de reparto y se anota el método;
     si no, el contrato queda con «edificios cubiertos» y reparto a partes iguales (marcado como tal).
Salida: {exp: {'metodo', 'edif': [{'key','lote','peso','texto'}], 'docs': [...]}}
"""
import json, re, sys, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'inversiones'))
import edificios as E

NUM = r'(?<![\d.,/])(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+,\d{1,2}|\d{2,7})(?![\d.,/%])'
def num(s):
    return float(s.replace('.', '').replace(',', '.'))

def cola(line, why):
    """Número final de la línea que no forma parte de la dirección ni es código postal/año."""
    l = re.sub(r'\b28\d{3}\b', ' ', line)                       # códigos postales
    if why.startswith('dirección'):
        st, nu = why.split(': ', 1)[1].rsplit(' ', 1)
        l = re.sub(re.escape(nu) + r'\b', ' ', l, count=1)
    l = re.sub(r'(?:C/|CALLE|AVDA\.?|AVENIDA|PASEO|PLAZA|Pº|PZA\.?|CTRA\.?|CAMINO|RONDA)[^0-9|]{2,45}?\d+[A-Z]?\b', ' ', l, flags=re.I)  # «C/ Yuste, 8»
    l = re.sub(r'\b(19|20)\d\d\b', ' ', l)
    xs = re.findall(NUM, l)
    return num(xs[-1]) if xs else None

def lotes_de(lines):
    """Lote vigente en cada línea según los encabezados «LOTE n» del documento."""
    out, cur = [], None
    for l in lines:
        m = re.match(r'^\s*LOTE\s*(?:N[º°O]\.?\s*)?(\d{1,2})\b', l, re.I)
        if m: cur = m.group(1)
        out.append(cur)
    return out

def main():
    D = pathlib.Path(sys.argv[1]); C = json.load(open(sys.argv[2])); dst = sys.argv[3]
    dist = {}
    for c in C: dist.setdefault(c['exp'], E.cod_distrito(c['distrito']))
    docs = collections.defaultdict(list)
    for p in sorted(D.glob('*.txt')):
        exp = p.name.split('__')[0].replace('_', '/', 2)
        docs[exp].append(p)
    out = {}
    for exp, ps in sorted(docs.items()):
        cd = dist.get(exp)
        if not cd: continue
        best = None
        for p in ps:
            lines = p.read_text(encoding='utf-8', errors='replace').split('\n')
            lts = lotes_de(lines)
            hits = {}
            for i, l in enumerate(lines):
                if len(l.strip()) < 6: continue
                h = E.match(E.nrm(l), cd)
                if len(h) != 1: continue
                k, why = h[0]
                w = cola(l, why)
                prev = hits.get(k)
                if not prev or (prev['peso'] is None and w is not None):
                    hits[k] = {'key': k, 'lote': lts[i], 'peso': w, 'texto': re.sub(r'\s+', ' ', l).strip()[:160], 'why': why}
            if not hits: continue
            conw = sum(1 for x in hits.values() if x['peso'])
            score = (len(hits), conw / len(hits))
            if not best or score > best[0]: best = (score, p.name, hits)
        if not best: continue
        (n, frac), name, hits = best
        # la unión de edificios de todos los documentos (algunos pliegos tienen la lista en un anexo aparte)
        allk = {}
        for p in ps:
            if p.name == name: continue
        usa_peso = frac >= 0.6
        ed = []
        for x in hits.values():
            ed.append({'key': x['key'], 'lote': x['lote'], 'peso': (x['peso'] if usa_peso and x['peso'] else (None if usa_peso else 1)), 'texto': x['texto'], 'why': x['why']})
        out[exp] = {'distrito': cd, 'doc': name, 'metodo': 'pesos del documento (columna final)' if usa_peso else 'a partes iguales',
                    'edif': ed, 'docs': [p.name for p in ps]}
    json.dump(out, open(dst, 'w'), ensure_ascii=False, indent=0)
    print(len(out), 'contratos con edificios ·', sum(len(v['edif']) for v in out.values()), 'asignaciones ·',
          collections.Counter(v['metodo'] for v in out.values()))

if __name__ == '__main__':
    main()
