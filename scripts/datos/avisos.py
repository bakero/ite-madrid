"""Avisos ciudadanos (datos.madrid.es 212411): quejas e incidencias de la vía pública que los vecinos comunican al Ayuntamiento.

Ficheros «Avisos ciudadanos recibidos» de cada año (sistema AVISA hasta 2018 y SIC desde 2018), de 70 a 160 MB cada uno.
Cada fichero se descarga con su huella (tabla descarga) y se recorre línea a línea; se guarda solo el recuento por
año, distrito, barrio y categoría en cm_aviso (no se copian los millones de filas a la base de datos).

Uso: python3 scripts/datos/avisos.py            # todos los años
     python3 scripts/datos/avisos.py 2025 2026  # solo esos años
"""
import collections, csv, io, json, pathlib, re, sys, unicodedata, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P

ID = '212411-0-madrid-avisa'
API = 'https://datos.madrid.es/api/3/action/package_show?id=' + ID
FICHA = 'https://datos.madrid.es/dataset/' + ID


def plano(s):
    s = unicodedata.normalize('NFD', (s or '').strip()).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).upper()


def main(anios):
    con = P.abrir()
    pkg = json.load(urllib.request.urlopen(urllib.request.Request(API, headers={'User-Agent': P.UA}), timeout=120))['result']
    fid = P.fuente(con, 'dm:212411', pkg['title'], organismo='Ayuntamiento de Madrid', portal='datos.madrid.es', url_ficha=FICHA, url_api=API,
                   licencia=(pkg.get('license_title') or 'CC BY 4.0'), acceso='descarga', seccion='Seguridad', prioridad='P2', frecuencia='mensual',
                   cobertura='ciudad de Madrid, por distrito y barrio, desde 2014')
    con.execute('''CREATE TABLE IF NOT EXISTS cm_aviso(anio INTEGER, cod_distrito INTEGER, cod_barrio INTEGER, categoria TEXT, sistema TEXT,
                   avisos INTEGER, _descarga_id INTEGER)''')
    for r in pkg['resources']:
        nom = (r.get('description') or r.get('name') or '').strip()
        m = re.search(r'recibidos \((AVISA|SIC)\)\. (\d{4})', nom)
        if r.get('format') != 'CSV' or not m:
            continue
        sis, anio = m.group(1), int(m.group(2))
        if anios and anio not in anios:
            continue
        did, ruta = P.descargar(con, fid, r['url'], recurso=nom, formato='CSV', subcarpeta='212411', script=__file__, archivar_copia=False,
                                pasos=f'1) Abrir {FICHA}, recurso «{nom}» ({r["url"]}). 2) Se recorre el CSV (separador «;») y se cuenta cada aviso '
                                      'por año de recepción, DISTRITO_ID, BARRIO_ID y categoría (CATEGORIA_NIVEL1 en SIC, SECCION en AVISA). '
                                      '3) Código de barrio = distrito × 10 + barrio. 4) Resultado en cm_aviso.')
        raw = pathlib.Path(ruta).read_bytes()
        try:
            txt = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            txt = raw.decode('cp1252', errors='replace')
        del raw
        cnt = collections.Counter()
        rd = csv.DictReader(io.StringIO(txt), delimiter=';')
        for f in rd:
            try:
                d = int(float(str(f.get('DISTRITO_ID') or '').strip() or 0))
            except ValueError:
                d = 0
            b = str(f.get('BARRIO_ID') or '').strip()
            try:
                bi = int(float(b)) % 100 if b else 0
            except ValueError:
                bi = 0
            fe = str(f.get('FECHA_DE_RECEPCION') or '')
            y = int(fe[-4:]) if re.match(r'.*\d{4}$', fe) else anio
            cat = plano(f.get('CATEGORIA_NIVEL1') or f.get('SECCION') or 'SIN CATEGORIA')
            cnt[(y, d if 1 <= d <= 21 else None, d * 10 + bi if 1 <= d <= 21 and bi else None, cat)] += 1
        del txt
        con.execute('DELETE FROM cm_aviso WHERE _descarga_id IN (SELECT id FROM descarga WHERE fuente_id = ? AND recurso = ?)', (fid, nom))
        con.executemany('INSERT INTO cm_aviso VALUES (?,?,?,?,?,?,?)', [(y, d, b, c, sis, n, did) for (y, d, b, c), n in cnt.items()])
        P.cerrar_descarga(con, did, 'cm_aviso', sum(cnt.values()))
        con.commit()
        print(anio, sis, sum(cnt.values()), 'avisos', len(cnt), 'grupos', flush=True)
    con.execute('INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES (?,?,?,?)',
                ('cm_aviso', 'Avisos ciudadanos recibidos por año, distrito, barrio y categoría (recuento)',
                 con.execute('SELECT count(*) FROM cm_aviso').fetchone()[0], 'avisos.py'))
    con.commit()


if __name__ == '__main__':
    main({int(a) for a in sys.argv[1:]})
