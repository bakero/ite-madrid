"""Cruce de textos (títulos de proyectos de inversión, objetos de contratos, anuncios del BOE) con los edificios del mapa.

Todo el municipio de Madrid. API:
  B                       {(lat,lng): {'key','cents','tipos','addr','cd','dist'}}  edificios (una entrada por coordenada)
  match(txt, cd)          [(key, motivo)]  edificios citados en txt (normalizado con nrm)
                          cd: código de distrito (int) si el texto es de un distrito conocido; None si no se sabe
                          (entonces se deduce de «Distrito de X» / «Junta Municipal de X» y, si no, se exigen pruebas fuertes).
                          cd=True equivale a «el distrito del edificio»: solo para compatibilidad.
  distrito_de(txt)        código de distrito citado explícitamente en el texto, o None
  cod_distrito(nombre)    código a partir de un nombre de distrito tal como lo escriben las fuentes
"""
import json, re, sqlite3, unicodedata, os, pathlib, collections
from normaliza import nrm

BASE = pathlib.Path(__file__).resolve().parents[2]
DB = os.environ.get('ITE_DB', str(BASE / 'ite_madrid.sqlite'))
con = sqlite3.connect(DB)

# ---- distritos y barrios
DIST = {int(c): n for c, n in con.execute('select cod,nombre from distritos')}
def _dv(n):
    """Variantes de escritura de un nombre de distrito (ya normalizado)."""
    n = nrm(n); v = {n, n.replace(' - ', '-'), n.replace(' - ', ' ')}
    if ' - ' in n: v |= {p for p in n.split(' - ') if len(p) > 4}
    return v
DVAR = {c: _dv(n) for c, n in DIST.items()}
_DN = {}
for c, vs in DVAR.items():
    for v in vs: _DN[v] = c
_DN.update({'FUENCARRAL': 8, 'EL PARDO': 8, 'MONCLOA': 9, 'ARAVACA': 9, 'SAN BLAS': 20, 'CANILLEJAS': 20})
def cod_distrito(s):
    s = nrm(s or '').replace('DISTRITO DE ', '').replace('DISTRITO ', '').strip()
    return _DN.get(s) or _DN.get(s.replace('-', ' - ')) or _DN.get(s.replace(' - ', '-'))
_DRX = sorted(((v, c) for c, vs in DVAR.items() for v in vs if v not in ('CENTRO', 'RETIRO', 'SALAMANCA', 'LATINA', 'USERA', 'BARAJAS', 'HORTALEZA', 'TETUAN', 'CHAMBERI', 'CHAMARTIN')), key=lambda x: -len(x[0]))
def distrito_de(txt):
    """Distrito citado de forma explícita («DISTRITO DE X», «JUNTA MUNICIPAL DE X», «JMD X») o por un nombre inequívoco."""
    found = set()
    for m in re.finditer(r'(?:DISTRITOS? (?:MUNICIPAL )?(?:DE |DEL )?|JUNTA MUNICIPAL (?:DEL DISTRITO )?(?:DE )?|J\.?M\.?D\.? (?:DE )?)([A-Z][A-Z\- ]{3,30})', txt):
        t = m.group(1)
        for v, c in sorted(_DN.items(), key=lambda x: -len(x[0])):
            if t.startswith(v): found.add(c); break
    if not found:
        for v, c in _DRX:
            if re.search(r'(?<![A-Z])' + re.escape(v) + r'(?![A-Z])', txt):
                if v == 'VALLECAS' or (c == 13 and re.search(r'VILLA DE VALLECAS|VALLECAS VILLA|ENSANCHE DE VALLECAS|PAU DE VALLECAS', txt)): continue
                found.add(c)
    return found.pop() if len(found) == 1 else None
BARRIOS = {nrm(n) for (n,) in con.execute('select nombre from barrios')}

rows = con.execute("""select c.id,c.nombre,c.tipo_edificio,c.subtipo,c.direccion,c.lat,c.lng,b.cod_distrito from centros c
  join barrios b on b.cod=c.cod_barrio
  where coalesce(c.excluido,'')='' and c.lat is not null and c.lng is not null""").fetchall()
B = {}
for cid, n, t, st, d, lat, lng, cd in rows:
    k = (round(lat, 5), round(lng, 5))
    b = B.setdefault(k, {'key': f'{k[0]:.5f},{k[1]:.5f}', 'cents': [], 'tipos': set(), 'addr': d, 'cd': int(cd), 'dist': DIST[int(cd)]})
    b['cents'].append(n); b['tipos'].add(t or '')

GEN = r'^(INSTALACION DEPORTIVA MUNICIPAL BASICA|INSTALACION DEPORTIVA BASICA|DEPORTIVO BASICO|CENTRO DE MAYORES Y CENTRO DE DIA|JUNTA MUNICIPAL( DEL DISTRITO)?|COLEGIO PUBLICO|COLEGIO DE EDUCACION INFANTIL Y PRIMARIA|CEIP|C\.?P\.?|COLEGIO|INSTITUTO DE EDUCACION SECUNDARIA|IES\)?|CENTRO CULTURAL|CENTRO SOCIOCULTURAL|CENTRO DEPORTIVO MUNICIPAL|INSTALACION DEPORTIVA (MUNICIPAL )?(BASICA )?|POLIDEPORTIVO|BIBLIOTECA PUBLICA( MUNICIPAL)?|BIBLIOTECA|ESCUELA INFANTIL|CASA DE NIÑOS|CENTRO MUNICIPAL DE MAYORES|CENTRO DE MAYORES|CENTRO DE DIA( MUNICIPAL)?|CENTRO DE SERVICIOS SOCIALES|PARROQUIA|PARQUE|MERCADO|CENTRO DE SALUD|ESPACIO DE IGUALDAD|CENTRO JUVENIL|SALA DE ESTUDIO|CENTRO)\s+(DE |DEL |DE LA |DE LOS )?'
GENERIC = {'MADRID', 'VALLECAS', 'ENTREVIAS', 'PALOMERAS', 'SAN DIEGO', 'EL POZO', 'ARAGON', 'ASTURIAS', 'LA RIOJA', 'MADRID SUR', 'SAN PABLO', 'SANTO DOMINGO', 'LA ALBUFERA', 'RONDA SUR', 'MIGUEL HERNANDEZ', 'LOPE DE VEGA', 'PALOMERAS BAJAS', 'BUENOS AIRES', 'LA MILAGROSA', 'SAN JOSE', 'LOS TILOS', 'RETAMAR', 'TAJAMAR', 'AZORIN', 'NAVACERRADA'}
GENERIC |= BARRIOS | {v for vs in DVAR.values() for v in vs}
TYPEW = {'Educativo': r'COLEGIO|C\.?E\.?I\.?P|ESCUELA|INSTITUTO|I\.?E\.?S\b|EDUCATIV|DOCENTE|CENTROS? ESCOLAR',
 'Deportivo': r'DEPORTIV|POLIDEPORTIVO|PISCINA|I\.?D\.?B|C\.?D\.?M|PABELLON|CAMPO DE FUTBOL|PISTA',
 'Cultural': r'CULTURAL|BIBLIOTECA|AUDITORIO|SALA DE ESTUDIO|TEATRO',
 'Servicios sociales': r'MAYORES|CENTRO DE DIA|SERVICIOS SOCIALES|ESPACIO DE IGUALDAD|CENTRO JUVENIL|FAMILIA|INFANCIA',
 'Administración y servicios públicos': r'JUNTA MUNICIPAL|SEDE|OFICINA|EDIFICIO',
 'Zona verde': r'PARQUE|JARDIN|ZONA VERDE', 'Sanitario': r'CENTROS? DE SALUD|AMBULATORIO|SANITARI|HOSPITAL|(?<![A-Z.])C\.?S\.?(?![A-Z.])', 'Seguridad y emergencias': r'BOMBEROS|POLICIA|SAMUR|COMISARIA', 'Comercio': r'MERCADO|MERCADILLO'}

def _strip_dist(core, cd):
    for v in sorted(DVAR[cd] | {'VALLECAS'} if cd == 13 else DVAR[cd], key=len, reverse=True):
        core = re.sub(r'\b(DE |DEL |DISTRITO (DE )?)?' + re.escape(v) + r'\b', '', core)
    return re.sub(r'\s+', ' ', core).strip(' .,-')

def keys_for(n, cd):
    """Claves de nombre de un centro y, si su nombre es «tipo + distrito», una clave tipada del distrito."""
    k = nrm(n); k = re.sub(r'\(.*?\)?$', '', k).strip(); k = re.sub(r'\(.*?\)', '', k).strip()
    m = re.match(GEN, k); pref = m.group(1) if m else None
    core = re.sub(GEN, '', k).strip(' .,"\'«»-')
    c0 = core; core = _strip_dist(core, cd); quitado = core != c0
    core = re.sub(r'^(MUNICIPAL|PUBLICO|PUBLICA)( DE| DEL)?\s+', '', core).strip()
    core = re.sub(r'^(DE|DEL|DE LA|DE LOS)\s+', '', core).strip()
    core = re.sub(r'\s+(DE|DEL|DE LA|DEL DISTRITO|DISTRITO|DE DISTRITO)$', '', core).strip()
    out, typed = set(), set()
    if quitado and (core or pref):
        # el nombre es «tipo + distrito» («Centro Deportivo Municipal Puente de Vallecas», «Comisaría Integral del Distrito Usera»):
        # solo vale si el texto dice el tipo seguido del nombre del distrito
        tn = re.sub(r' (DEL DISTRITO|DISTRITO|DEL|DE)$', '', ' '.join(x for x in (pref, core) if x)); typed.add(re.escape(tn).replace('\\ ', r'\s+'))
    elif len(core) >= 5 and core not in ('MADRID',) and not core.startswith(('MUNICIPAL', 'AL AIRE LIBRE')): out.add(core)
    out = {x for x in out if not re.match(r'^(Y|DE|DEL|E|O)\b', x) and '  ' not in x}
    out = {x for x in out if x not in ('VERANO', 'MENTAL', 'ESTADIO', 'CENTRO', 'MUNICIPAL')}
    return out, typed

import json as _j
_c = open(BASE / 'app' / 'calles.js', encoding='utf-8').read(); _c = _j.loads(_c[_c.index('{'):_c.rindex('}') + 1])
STREET_RE = r'^(CALLE|AVENIDA|PASEO|PLAZA|RONDA|CAMINO|GLORIETA|TRAVESIA|CARRETERA|BULEVAR|COSTANILLA|PASAJE|CALLEJON|CUESTA|PARQUE|JARDIN)\s+(DE LA |DE LOS |DE LAS |DEL |DE )?'
STREET = r'^(CALLE|AVENIDA|PASEO|PLAZA|RONDA|CAMINO|GLORIETA|TRAVESIA|CARRETERA|BULEVAR|COSTANILLA|PASAJE)\s+(DE LA |DE LOS |DE LAS |DEL |DE )?'
def addr_key(a):
    a = nrm(a).split(',')[0]; m = re.match(STREET + r'(.+?)\s+(\d+)\b', a)
    return (m.group(3).strip(), m.group(4)) if m else None
STREETNAMES = set(re.sub(STREET_RE, '', nrm(x)).strip() for x in _c['names'] if x)

W = lambda s: set(re.findall(r'[A-ZÑ0-9]+', s))
IDX = collections.defaultdict(list)  # palabra más rara de la clave -> [(edificio, tipo, clave, palabras)]
_freq = collections.Counter()
for b in B.values():
    ks, ts = set(), set()
    for n in b['cents']:
        a, t = keys_for(n, b['cd']); ks |= a; ts |= t
    b['keys'] = ks; b['tkeys'] = ts; b['ak'] = addr_key(b['addr'])
    for k in ks: _freq.update(W(k))
    if b['ak']: _freq.update(W(b['ak'][0]))
def _add(b, kind, k, words):
    if not words: return
    IDX[min(words, key=lambda w: (_freq[w], -len(w)))].append((b, kind, k, words))
for b in B.values():
    for k in b['keys']: _add(b, 'n', k, W(k))
    if b['ak']: _add(b, 'a', b['ak'], W(b['ak'][0]) | {b['ak'][1]})
    for p in b['tkeys']:
        for v in DVAR[b['cd']]: _add(b, 't', (p, v), W(v))

NOEDIF = r'VIVIENDA|URBANIZACI|CALZADA|ACERAS?\b|VIA PUBLICA|VIAS PUBLICAS|VIALES|PASO DE VEHICULOS|ALUMBRADO PUBLICO|SEÑALIZACI|ARBOLADO|ENTORNO ESCOLAR|CAMINO ESCOLAR'

def _match(txt, cd):
    if cd is None: cd = distrito_de(txt)
    noedif = bool(re.search(NOEDIF, txt))
    toks = W(txt); hits = {}
    for w in toks:
        for b, kind, k, words in IDX.get(w, ()):
            if (b['key'] in hits and not hits[b['key']].startswith('dirección')) or not words <= toks: continue
            local = cd is True or cd == b['cd']
            if cd not in (None, True) and not local: continue  # texto de otro distrito
            why = None
            if kind == 'n':
                if not re.search(r'(?<![A-Z])' + re.escape(k) + r'(?![A-Z])', txt): continue
                tw = [TYPEW[t] for t in b['tipos'] if t in TYPEW]
                typed = any(re.search(x, txt) for x in tw) or any(re.search(x, k) for x in tw)
                strong = len(k.split()) >= 3 or len(k) >= 16
                if k in STREETNAMES or k in GENERIC or len(k) < 7:
                    one = len(k.split()) == 1
                    if (local or not one) and any(re.search(r'(' + x + r')[^|]{0,22}?(?<![A-Z])' + re.escape(k) + r'(?![A-Z])', txt) for x in tw): why = 'nombre: ' + k
                elif not noedif and ((local and (typed or strong)) or (typed and (strong or len(k.split()) >= 2))):
                    why = 'nombre: ' + k
            elif kind == 'a':
                st, nu = k
                mm = re.search(r'(?<![A-Z])' + re.escape(st) + r'(?![A-Z])\s*,?\s*(?:N[º°O]\.?|NUM(?:ERO)?\.?)?\s*(\d+)\b', txt)
                if mm and mm.group(1) == nu and not re.search(r'VIVIENDA|URBANIZACI|PASO DE VEHICULOS|CALZADA', txt): why = f'dirección: {st} {nu}'
            else:
                p, v = k
                if not noedif and re.search(r'(?<![A-Z])' + p + r'\s+(MUNICIPAL\s+)?(DEL\s+DISTRITO\s+|DISTRITO\s+)?(DE\s+|DEL\s+)?' + re.escape(v) + r'(?![A-Z])', txt):
                    why = f'nombre: {p} {v}'
            if why and not (b['key'] in hits and why.startswith('dirección')): hits[b['key']] = why
    return list(hits.items())

# Edificios de Puente de Vallecas que se citan con nombres distintos de los del callejero de centros
ALIAS = [(r'POLIDEPORTIVO (MUNICIPAL )?(DE )?PUENTE DE VALLECAS|(CENTRO DEPORTIVO MUNICIPAL|C\.?D\.?M\.?) PUENTE DE VALLECAS|PAYASO FOFO', '40.39146,-3.65986'),
 (r'BIBLIOTECA (PUBLICA )?(MUNICIPAL )?(DE )?(PUENTE DE )?VALLECAS\b(?! VILLA)|BIBLIOTECA .{0,20}SIERRA CAMEROS', '40.39502,-3.66555'),
 (r'NUEVA (SEDE DE LA )?(JUNTA MUNICIPAL|JMD)|(JUNTA MUNICIPAL|JMD).{0,40}BUENOS AIRES', '40.38920,-3.65180'),
 (r'MONTE OLIVETT?I,? 14', '40.39787,-3.66706'),
 (r'CENTRO (MUNICIPAL )?DE MAYORES (Y CENTRO DE DIA )?(DE )?PUENTE DE VALLECAS', '40.39042,-3.65812'),
 (r'BOMBEROS (N[º°O]\.? ?|NUM(ERO)?\.? ?)?0?8\b', '40.39462,-3.65313'),
 (r'(UNIDAD INTEGRAL|COMISARIA INTEGRAL|U\.?I\.?D\.?)( DE)?( LA)? POLICIA MUNICIPAL( DEL? DISTRITO)?( DE)? PUENTE( DE)? VALLECAS|POLICIA MUNICIPAL( DEL? DISTRITO)?( DE)? PUENTE( DE)? VALLECAS', '40.38924,-3.65238'),
 (r'(EDIFICIO )?SEDE (DE LA JUNTA MUNICIPAL )?DEL DISTRITO( DE)? PUENTE( DE)? VALLECAS|JUNTA MUNICIPAL( DEL? DISTRITO)?( DE)? PUENTE( DE)? VALLECAS', '40.38920,-3.65180'),
 (r'MERCADO (MUNICIPAL )?(DE )?PUENTE DE VALLECAS', '40.39525,-3.66775')]
_ALIAS_PV_SOLO = {2}  # índices de alias que solo valen para textos del propio distrito

def match(txt, cd=None):
    if cd is not None and cd is not True and not isinstance(cd, int): cd = True if cd else None  # compatibilidad: match(txt, pv)
    h = _match(txt, cd)
    if not h:
        cdx = distrito_de(txt) if cd is None else cd
        for i, (rx, k) in enumerate(ALIAS):
            if i in _ALIAS_PV_SOLO and cdx not in (13, True): continue
            if cdx not in (None, 13, True): continue
            if re.search(rx, txt) and not re.search(NOEDIF, txt): h = [(k, 'alias: ' + rx[:30])]; break
    if len(h) > 1:
        names = [(k, w) for k, w in h if w.startswith(('nombre', 'alias'))]
        if names: h = names
        ks = [w.split(': ', 1)[1] for k, w in h]
        h = [(k, w) for (k, w), kk in zip(h, ks) if not any(kk != o and kk in o for o in ks)]
    return h
