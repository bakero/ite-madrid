"""Crea/actualiza ite_madrid.sqlite a partir de:
  - datos/centros_madrid_21_distritos_ITE.xlsx  (listados de madrid.es + ITE ya consultada)
  - datos/*.json de datos.madrid.es (centros educativos y de enseñanza)
  - datos/300307-...-escuelas-infantiles-empresas-csv.csv (empresa gestora de EI municipales)
  - datos/distritos_madrid_simpl.json (contornos)
y genera datos/pendientes_ite.json con las direcciones que faltan por consultar.
Es idempotente: se puede relanzar; no borra resultados ITE ya guardados.
Uso: python3 scripts/build_db.py   (desde la carpeta mapa_ite_madrid)
"""
import csv, datetime, json, os, re, sqlite3, unicodedata
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, 'datos', *p)
# SQLite no puede bloquear ficheros en algunas carpetas montadas: ITE_DB permite trabajar en otra ruta y copiar después
DB = os.environ.get('ITE_DB', os.path.join(ROOT, 'ite_madrid.sqlite'))
HOY = datetime.date.today().isoformat()

OPEN_SOURCES = [  # (fichero, nombre, url)
    ('212790-4-centros-educacion-json.json', 'Centros de educación (sedes)', 'https://datos.madrid.es/dataset/212790-0-centros-educacion'),
    ('300614-5-centros-educativos-json.json', 'Centros educativos en Madrid', 'https://datos.madrid.es/dataset/300614-0-centros-educativos'),
    ('202311-0-colegios-publicos-json.json', 'Colegios públicos', 'https://datos.madrid.es/dataset/202311-0-colegios-publicos'),
    ('202318-2-escuelas-infantiles-json.json', 'Escuelas infantiles municipales', 'https://datos.madrid.es/dataset/202318-0-escuelas-infantiles'),
    ('212904-2-centros-ensenanza-json.json', 'Centros de enseñanza (sedes)', 'https://datos.madrid.es/dataset/212904-0-centros-ensenanza'),
    ('207037-0-idiomas-oficial-json.json', 'Escuelas Oficiales de Idiomas', 'https://datos.madrid.es/dataset/207037-0-idiomas-oficial'),
]
EI_EMPRESAS = ('300307-1-escuelas-infantiles-empresas-csv.csv', 'Empresas gestoras de escuelas infantiles', 'https://datos.madrid.es/dataset/300307-0-escuelas-infantiles-empresas')

SCHEMA = """
CREATE TABLE IF NOT EXISTS fuentes(id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, url TEXT, fichero TEXT, fecha_carga TEXT, n_registros INTEGER);
CREATE TABLE IF NOT EXISTS distritos(cod TEXT PRIMARY KEY, nombre TEXT, contorno_json TEXT);
CREATE TABLE IF NOT EXISTS direcciones(direccion TEXT PRIMARY KEY, tipo_via TEXT, nombre_via TEXT, numero TEXT, cp TEXT, lat REAL, lng REAL);
CREATE TABLE IF NOT EXISTS centros(
  id INTEGER PRIMARY KEY, fuente TEXT, id_origen TEXT, nombre TEXT, distrito TEXT, barrio TEXT,
  direccion TEXT REFERENCES direcciones(direccion), direccion_original TEXT, telefono TEXT,
  tipo_edificio TEXT, subtipo TEXT, en_dir_telefonos TEXT, en_recursos_educativos TEXT,
  empresa_gestora TEXT, url_ficha TEXT, lat REAL, lng REAL, otras_fuentes TEXT,
  UNIQUE(fuente, id_origen));
CREATE TABLE IF NOT EXISTS ite(
  direccion TEXT PRIMARY KEY REFERENCES direcciones(direccion), estado_inspeccion TEXT, resultado_consulta TEXT,
  vial_registro TEXT, denominacion TEXT, anio_construccion TEXT, anio_1a_obligacion TEXT, anio_proxima_ite TEXT,
  fecha_max_iee TEXT, n_ite_iee INTEGER, n_expediente TEXT, fecha_presentacion TEXT, tipo_expediente TEXT,
  dictamen TEXT, parcial_total TEXT, causa_desfavorable TEXT, situacion_administrativa TEXT, dependencia_actual TEXT,
  exp_orden_ejecucion TEXT, n_ordenes INTEGER, estado_orden TEXT, dependencia_orden TEXT, fecha_resolucion TEXT,
  resolucion TEXT, deficiencias_subsanadas TEXT, ite_anteriores TEXT, cp_registro TEXT, distrito_registro TEXT,
  fecha_consulta TEXT, origen TEXT);
CREATE VIEW IF NOT EXISTS v_centros_ite AS
  SELECT c.*, i.estado_inspeccion, i.resultado_consulta, i.denominacion, i.vial_registro, i.anio_construccion,
         i.tipo_expediente, i.dictamen, i.parcial_total, i.causa_desfavorable, i.situacion_administrativa,
         i.dependencia_actual, i.n_expediente, i.fecha_presentacion, i.exp_orden_ejecucion, i.estado_orden,
         i.dependencia_orden, i.fecha_resolucion, i.resolucion, i.deficiencias_subsanadas, i.anio_proxima_ite,
         i.fecha_max_iee, i.n_ite_iee, i.ite_anteriores, i.fecha_consulta
  FROM centros c LEFT JOIN ite i ON i.direccion = c.direccion;
"""

def nrm(s):
    s = unicodedata.normalize('NFD', str(s or '').upper())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s.replace('\xa0', ' ')).strip()

def key_dist(s):
    return re.sub(r'[^a-z]', '', nrm(s).lower())

def norm_open_addr(street, cp):
    """'CALLE ALMAGRO 5 I.F.E. ...' -> ('CALLE ALMAGRO 5, 28010 MADRID', tipo, nombre, num)"""
    s = nrm(street).replace('C/', 'CALLE ')
    m = re.match(r'^(\S+)\s+(.*?)\s+(\d+)\b', s)
    if not m:
        m2 = re.match(r'^(\S+)\s+(.*)$', s)
        if not m2:
            return None, None, None, None
        return f'{m2.group(1)} {m2.group(2)} 0, {cp} MADRID', m2.group(1), m2.group(2), None
    tipo, nombre, num = m.group(1), m.group(2), str(int(m.group(3)))
    return f'{tipo} {nombre} {num}, {cp} MADRID', tipo, nombre, num

def parse_excel_addr(a):
    m = re.match(r'^\s*(\S+)\s+(.*?)(?:\s+(\d+|S/N))?\s*,\s*(\d{5})?', a or '')
    if not m:
        return None, None, None, None
    return m.group(1), m.group(2), m.group(3), m.group(4)

def estado_from(res, dictamen, subs, n_ites, prox):
    if res != 'OK':
        return None
    d = nrm(dictamen)
    if not n_ites or not d or d == '-':
        return f'Sin ITE/IEE presentada (próxima ITE {prox})' if prox and prox != '-' else 'Sin ITE/IEE presentada'
    if 'I.E.E.' in d:
        return 'IEE complementario de ITE'
    if d.startswith('FAVORABLE'):
        return 'Favorable'
    if 'SUBSANADAS' in d or nrm(subs).startswith('SI'):
        return 'Desfavorable – deficiencias subsanadas'
    if d.startswith('DESFAVORABLE'):
        return 'Desfavorable – pendiente de subsanar'
    return 'Otro: ' + dictamen

REQUEUE = ('Pendiente de consulta', 'Error del Registro', 'Registro sin respuesta', 'No consultado: respuesta inválida')

def main():
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    cur = con.cursor()

    def fuente(nombre, url, fichero, n):
        cur.execute('INSERT INTO fuentes(nombre,url,fichero,fecha_carga,n_registros) VALUES(?,?,?,?,?) '
                    'ON CONFLICT(nombre) DO UPDATE SET url=excluded.url,fichero=excluded.fichero,fecha_carga=excluded.fecha_carga,n_registros=excluded.n_registros',
                    (nombre, url, fichero, HOY, n))

    def add_dir(addr, tipo, nombre, num, cp, lat, lng):
        cur.execute('INSERT INTO direcciones VALUES(?,?,?,?,?,?,?) ON CONFLICT(direccion) DO UPDATE SET '
                    'lat=COALESCE(direcciones.lat,excluded.lat), lng=COALESCE(direcciones.lng,excluded.lng)',
                    (addr, tipo, nombre, num, cp, lat, lng))

    # --- distritos
    dist = json.load(open(D('distritos_madrid_simpl.json'), encoding='utf-8'))
    for d in dist:
        try:
            d['nom'] = d['nom'].encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        cur.execute('INSERT OR REPLACE INTO distritos VALUES(?,?,?)', (d['cod'], d['nom'], json.dumps(d['lines'])))
    distmap = {key_dist(d['nom']): d['nom'] for d in dist}
    fuente('Distritos municipales de Madrid (KML, Geoportal)', 'https://datos.madrid.es/dataset/300497-0-distritos-municipales-madrid', 'distritos_madrid_simpl.json', len(dist))

    # --- Excel madrid.es + ITE ya consultada
    ws = openpyxl.load_workbook(D('centros_madrid_21_distritos_ITE.xlsx'), read_only=True, data_only=True)['Centros + ITE']
    it = ws.iter_rows(values_only=True)
    H = list(next(it)); g = lambda r, k: r[H.index(k)]
    n = 0
    for i, r in enumerate(it):
        if not any(r):
            continue
        n += 1
        addr = ' '.join(str(g(r, 'Dirección') or '').split())
        tipo, nombre, num, cp = parse_excel_addr(addr)
        lat, lng = g(r, 'Latitud'), g(r, 'Longitud')
        add_dir(addr, tipo, nombre, num, cp, lat, lng)
        cur.execute('INSERT OR IGNORE INTO centros(fuente,id_origen,nombre,distrito,direccion,direccion_original,telefono,tipo_edificio,subtipo,'
                    'en_dir_telefonos,en_recursos_educativos,url_ficha,lat,lng) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    ('madrid.es', f'{g(r,"Distrito")}|{i}', g(r, 'Centro'), g(r, 'Distrito'), addr, addr,
                     ' '.join(str(g(r, 'Teléfono') or '').split()), g(r, 'Tipo de edificio'), g(r, 'Subtipo'),
                     g(r, 'En "Direcciones y teléfonos"'), g(r, 'En "Recursos educativos públicos"'), g(r, 'Ficha madrid.es'), lat, lng))
        est = g(r, 'Estado de la inspección') or ''
        if est.startswith(REQUEUE):
            continue
        exists = cur.execute('SELECT origen FROM ite WHERE direccion=?', (addr,)).fetchone()
        if exists and exists[0] != 'excel_02-11-2026':
            continue  # no pisar consultas más recientes
        cur.execute('INSERT OR REPLACE INTO ite(direccion,estado_inspeccion,resultado_consulta,vial_registro,denominacion,anio_construccion,'
                    'anio_proxima_ite,fecha_max_iee,n_ite_iee,n_expediente,fecha_presentacion,tipo_expediente,dictamen,parcial_total,'
                    'causa_desfavorable,situacion_administrativa,dependencia_actual,exp_orden_ejecucion,estado_orden,dependencia_orden,'
                    'fecha_resolucion,resolucion,deficiencias_subsanadas,ite_anteriores,fecha_consulta,origen) '
                    'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (addr, est, g(r, 'Resultado consulta Registro'), g(r, 'Dirección en el Registro'), g(r, 'Denominación en el Registro'),
                     g(r, 'Año de construcción'), g(r, 'Año próxima ITE'), g(r, 'Fecha máx. IEE'), g(r, 'Nº ITE/IEE presentadas'),
                     g(r, 'Nº expediente'), g(r, 'Fecha presentación'), g(r, 'Tipo expediente'), g(r, 'Dictamen'), g(r, 'Parcial/Total'),
                     g(r, 'Causa dictamen desfavorable'), g(r, 'Situación administrativa'), g(r, 'Dependencia actual'),
                     g(r, 'Expediente (orden de ejecución)'), g(r, 'Estado orden de ejecución'), g(r, 'Dependencia orden de ejecución'),
                     g(r, 'Fecha resolución'), g(r, 'Resolución'), g(r, 'Deficiencias subsanadas'), g(r, 'ITE/IEE anteriores'),
                     '2026-11-02', 'excel_02-11-2026'))
    fuente('madrid.es – Direcciones y teléfonos + Recursos educativos (21 distritos)', 'https://www.madrid.es', 'centros_madrid_21_distritos_ITE.xlsx', n)

    # --- datos abiertos (JSON-LD)
    by_addr = {}
    for (direccion, nombre) in cur.execute("SELECT direccion, nombre FROM centros WHERE fuente='madrid.es'").fetchall():
        by_addr.setdefault(direccion, []).append(nombre)
    seen_ids = {}
    stats = {}
    for fich, nom, url in OPEN_SOURCES:
        p = D(fich)
        if not os.path.exists(p):
            print('FALTA', fich); continue
        g_ = json.load(open(p, encoding='utf-8'))['@graph']
        fuente(nom, url, fich, len(g_))
        st = stats.setdefault(nom, {'total': len(g_), 'ya_en_madrid_es': 0, 'duplicado_otra_fuente': 0, 'nuevos': 0})
        for x in g_:
            oid = str(x.get('id'))
            if oid in seen_ids:
                st['duplicado_otra_fuente'] += 1
                cur.execute("UPDATE centros SET otras_fuentes=COALESCE(otras_fuentes||'; ','')||? WHERE fuente=? AND id_origen=?", (nom, seen_ids[oid], oid))
                continue
            seen_ids[oid] = 'datos.madrid.es'
            a = x.get('address', {}) or {}
            loc = x.get('location', {}) or {}
            cp = a.get('postal-code', '')
            addr, tipo, nombre_via, num = norm_open_addr(a.get('street-address', ''), cp)
            if not addr:
                continue
            dkey = (a.get('district', {}) or {}).get('@id', '').rsplit('/', 1)[-1]
            distrito = distmap.get(key_dist(dkey), dkey)
            barrio = (a.get('area', {}) or {}).get('@id', '').rsplit('/', 1)[-1]
            title = x.get('title', '')
            subt = re.sub(r'(?<!^)(?=[A-Z])', ' ', x.get('@type', '').rsplit('/', 1)[-1]).replace('Enseñanza', 'Enseñanza')
            # ¿ya está en el listado de madrid.es? misma dirección y nombre parecido
            tt = set(w for w in re.findall(r'[A-Z]{4,}', nrm(title)))
            dup = False
            for other in by_addr.get(addr, []):
                to = set(re.findall(r'[A-Z]{4,}', nrm(other)))
                if tt and to and len(tt & to) / min(len(tt), len(to)) >= 0.5:
                    dup = True; break
            add_dir(addr, tipo, nombre_via, num, cp, loc.get('latitude'), loc.get('longitude'))
            if dup:
                st['ya_en_madrid_es'] += 1
                cur.execute("UPDATE centros SET otras_fuentes=COALESCE(otras_fuentes||'; ','')||? WHERE fuente='madrid.es' AND direccion=? AND (otras_fuentes IS NULL OR otras_fuentes NOT LIKE ?)",
                            (nom, addr, '%' + nom + '%'))
                continue
            st['nuevos'] += 1
            cur.execute('INSERT OR IGNORE INTO centros(fuente,id_origen,nombre,distrito,barrio,direccion,direccion_original,tipo_edificio,subtipo,url_ficha,lat,lng,otras_fuentes) '
                        'VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        ('datos.madrid.es', oid, title, distrito, barrio, addr, a.get('street-address', ''), 'Educación',
                         subt, x.get('relation', ''), loc.get('latitude'), loc.get('longitude'), nom))

    # --- empresa gestora de escuelas infantiles municipales
    p = D(EI_EMPRESAS[0])
    if os.path.exists(p):
        raw = open(p, 'rb').read()
        try:
            txt = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            txt = raw.decode('latin-1')
        rows = list(csv.reader(txt.splitlines(), delimiter=';'))
        hdr = [h.strip() for h in rows[0]]
        ok = 0; tot = 0
        for r in rows[1:]:
            if len(r) < 6 or not r[2].strip():
                continue
            tot += 1
            ei, emp = nrm(r[2]), ' '.join(r[5].split())
            cands = cur.execute("SELECT id, nombre FROM centros WHERE (subtipo LIKE '%Infantil%' OR nombre LIKE '%nfantil%')").fetchall()
            hit = [c for c in cands if ei and ei in nrm(c[1])]
            for c in hit:
                cur.execute('UPDATE centros SET empresa_gestora=? WHERE id=?', (emp, c[0]))
            ok += bool(hit)
        fuente(EI_EMPRESAS[1], EI_EMPRESAS[2], EI_EMPRESAS[0], tot)
        stats[EI_EMPRESAS[1]] = {'total': tot, 'asociadas_a_un_centro': ok}

    con.commit()
    # --- pendientes de consultar
    pend = cur.execute("""SELECT d.direccion FROM direcciones d LEFT JOIN ite i ON i.direccion=d.direccion
                          WHERE (i.direccion IS NULL OR i.origen IN ('pendiente','error'))
                          AND d.direccion IN (SELECT direccion FROM centros)""").fetchall()
    # Errores BDC al final
    pend = [p[0] for p in pend]
    json.dump(pend, open(D('pendientes_ite.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(json.dumps({'centros': cur.execute('SELECT fuente,count(*) FROM centros GROUP BY fuente').fetchall(),
                      'direcciones': cur.execute('SELECT count(*) FROM direcciones WHERE direccion IN (SELECT direccion FROM centros)').fetchone()[0],
                      'con_ite_resuelta': cur.execute('SELECT count(*) FROM ite').fetchone()[0],
                      'pendientes': len(pend), 'fuentes': stats}, ensure_ascii=False, indent=1))
    con.close()

if __name__ == '__main__':
    main()
