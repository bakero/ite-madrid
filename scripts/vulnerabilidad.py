"""
Barrios y vulnerabilidad: carga en la BD los contornos de los 131 barrios y los
indicadores de IGUALA (Ayuntamiento de Madrid), y asigna a cada centro su barrio
por coordenadas.

Fuentes (datos.madrid.es):
  - Límites administrativos actuales, Barrios municipales (SHP, ETRS89 UTM 30N)
    https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas
  - IGUALA. Índice de vulnerabilidad territorial agregado, «Datos globales y por
    esferas para distritos» (hojas «Vul. esferas distritos» y «Descriptivos barrios»)
    https://datos.madrid.es/dataset/300577-0-iguala-vulnerabilidad

Uso:
  ITE_DB=/tmp/ite_madrid.sqlite python3 scripts/vulnerabilidad.py \
      datos/vulnerabilidad/barrios_shp.zip datos/vulnerabilidad/iguala_ivta_global.xlsx
Después: python3 scripts/ingest_export.py   (regenera app/data.js con barrio y renta)

Requiere: pyshp, pyproj, openpyxl.
Nota: IGUALA publica el índice agregado (IVTA) solo por distrito; por barrio se
usa la renta neta media por hogar de la hoja «Descriptivos barrios».
"""
import datetime, io, json, os, sqlite3, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get('ITE_DB', os.path.join(ROOT, 'ite_madrid.sqlite'))
HOY = datetime.date.today().isoformat()
URL_BARRIOS = 'https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas'
URL_IGUALA = 'https://datos.madrid.es/dataset/300577-0-iguala-vulnerabilidad'


def _dp(pts, tol):
    """Douglas-Peucker sobre [[x,y],...]."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop(); (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay; L = (dx * dx + dy * dy) ** .5 or 1e-12
        md, mi = 0, -1
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + bx * ay - by * ax) / L
            if d > md: md, mi = d, i
        if md > tol:
            keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]


def cargar(con, shp_zip, xlsx):
    import shapefile, openpyxl
    from pyproj import Transformer
    tr = Transformer.from_crs('EPSG:25830', 'EPSG:4326', always_xy=True)
    z = zipfile.ZipFile(shp_zip)
    nm = lambda ext: next(n for n in z.namelist() if n.upper().endswith('BARRIOS.' + ext))
    r = shapefile.Reader(shp=io.BytesIO(z.read(nm('SHP'))), dbf=io.BytesIO(z.read(nm('DBF'))), shx=io.BytesIO(z.read(nm('SHX'))), encoding='utf-8')
    fields = [f[0] for f in r.fields[1:]]
    con.executescript('''
      CREATE TABLE IF NOT EXISTS barrios(cod INTEGER PRIMARY KEY, nombre TEXT, cod_distrito INTEGER, distrito TEXT, contorno_json TEXT);
      CREATE TABLE IF NOT EXISTS barrios_indicadores(cod INTEGER, anio INTEGER, renta_hogar REAL, valor_catastral REAL,
        tasa_extranjera REAL, tasa_abstencion REAL, pct_mujeres REAL, pct_dependiente REAL, PRIMARY KEY(cod, anio));
      CREATE TABLE IF NOT EXISTS distritos_vulnerabilidad(cod_distrito INTEGER, anio INTEGER, ivta REAL, ivta_media REAL,
        bienestar REAL, medio_ambiente REAL, educacion REAL, economia REAL, salud REAL, PRIMARY KEY(cod_distrito, anio));''')
    con.execute('DELETE FROM barrios')
    for sr in r.iterShapeRecords():
        a = dict(zip(fields, sr.record))
        cod = int(a.get('COD_BAR') or a.get('CODBAR') or a.get('COD_DISBAR'))
        pts, parts = sr.shape.points, list(sr.shape.parts) + [len(sr.shape.points)]
        rings = []
        for i in range(len(parts) - 1):
            ring = [list(tr.transform(x, y)) for x, y in pts[parts[i]:parts[i + 1]]]
            # anillo cerrado: se parte por el punto más lejano al inicial para que Douglas-Peucker no lo colapse
            k = max(range(len(ring)), key=lambda i: (ring[i][0] - ring[0][0]) ** 2 + (ring[i][1] - ring[0][1]) ** 2)
            simp = _dp(ring[:k + 1], 0.00005) + _dp(ring[k:], 0.00005)[1:]
            rings.append([[round(x, 5), round(y, 5)] for x, y in simp])
        con.execute('INSERT INTO barrios VALUES(?,?,?,?,?)', (cod, a.get('NOMBRE'), int(a.get('CODDIS') or a.get('COD_DIS_TX')), a.get('NOMDIS'), json.dumps(rings)))
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    con.execute('DELETE FROM barrios_indicadores'); con.execute('DELETE FROM distritos_vulnerabilidad')
    for row in list(wb['Descriptivos barrios'].iter_rows(values_only=True))[1:]:
        if row[0] is None: continue
        con.execute('INSERT INTO barrios_indicadores VALUES(?,?,?,?,?,?,?,?)', (int(row[0]), int(row[4]), row[6], row[5], row[7], row[8], row[9], row[10]))
    for row in list(wb['Vul. esferas distritos'].iter_rows(values_only=True))[1:]:
        if row[0] is None: continue
        con.execute('INSERT INTO distritos_vulnerabilidad VALUES(?,?,?,?,?,?,?,?,?)', (int(row[0]), int(row[2]), row[3], row[4], row[5], row[7], row[9], row[11], row[13]))
    for nombre, url, fich, n in [('Barrios municipales (SHP, Límites administrativos actuales)', URL_BARRIOS, os.path.basename(shp_zip), con.execute('SELECT count(*) FROM barrios').fetchone()[0]),
                                 ('IGUALA: renta por barrio e IVTA por distrito (datos globales y por esferas)', URL_IGUALA, os.path.basename(xlsx), con.execute('SELECT count(*) FROM barrios_indicadores').fetchone()[0])]:
        con.execute('INSERT INTO fuentes(nombre,url,fichero,fecha_carga,n_registros) VALUES(?,?,?,?,?) ON CONFLICT(nombre) DO UPDATE SET url=excluded.url,fichero=excluded.fichero,fecha_carga=excluded.fecha_carga,n_registros=excluded.n_registros',
                    (nombre, url, fich, HOY, n))
    con.commit()
    print('barrios:', con.execute('SELECT count(*) FROM barrios').fetchone()[0],
          '· indicadores barrio:', con.execute('SELECT count(*), min(anio), max(anio) FROM barrios_indicadores').fetchone(),
          '· IVTA distrito:', con.execute('SELECT count(*), min(anio), max(anio) FROM distritos_vulnerabilidad').fetchone())


def _inside(x, y, rings):
    c = False
    for ring in rings:
        for i in range(len(ring)):
            (x1, y1), (x2, y2) = ring[i - 1], ring[i]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
    return c


def asignar(con):
    """centros.cod_barrio por punto en polígono (si la tabla barrios existe)."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='barrios'").fetchone():
        return
    if 'cod_barrio' not in [r[1] for r in con.execute('PRAGMA table_info(centros)')]:
        con.execute('ALTER TABLE centros ADD COLUMN cod_barrio INTEGER')
    polys = []
    for cod, rj in con.execute('SELECT cod, contorno_json FROM barrios'):
        rings = json.loads(rj); xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
        polys.append((cod, rings, (min(xs), min(ys), max(xs), max(ys))))
    n = sin = 0
    for cid, lat, lng in con.execute('SELECT id, lat, lng FROM centros WHERE lat IS NOT NULL AND lng IS NOT NULL').fetchall():
        hit = next((c for c, rings, (x0, y0, x1, y1) in polys if x0 <= lng <= x1 and y0 <= lat <= y1 and _inside(lng, lat, rings)), None)
        if hit is None:  # punto justo en el borde o fuera por la simplificación: barrio más cercano
            hit = min(polys, key=lambda p: min((lng - x) ** 2 + (lat - y) ** 2 for r in p[1] for x, y in r))[0]; sin += 1
        con.execute('UPDATE centros SET cod_barrio=? WHERE id=?', (hit, cid)); n += 1
    con.commit()
    print('centros con barrio:', n, '(por cercanía:', sin, ')')


def export_js(con):
    """Datos de barrios para app/data.js (None si no hay tabla)."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='barrios'").fetchone():
        return None
    out = []
    for cod, nom, cd, dist, rj in con.execute('SELECT cod,nombre,cod_distrito,distrito,contorno_json FROM barrios ORDER BY cod'):
        ind = {a: r for a, r in con.execute('SELECT anio, renta_hogar FROM barrios_indicadores WHERE cod=?', (cod,))}
        out.append({'cod': cod, 'nom': nom, 'cd': cd, 'dist': dist, 'renta': ind, 'lines': json.loads(rj)})
    ivta = {}
    for cd, a, v, m in con.execute('SELECT cod_distrito, anio, ivta, ivta_media FROM distritos_vulnerabilidad'):
        ivta.setdefault(cd, {})[a] = [round(v, 3), round(m, 3)]
    return {'barrios': out, 'ivta': ivta}


if __name__ == '__main__':
    con = sqlite3.connect(DB)
    if len(sys.argv) >= 3:
        cargar(con, sys.argv[1], sys.argv[2])
    asignar(con)
