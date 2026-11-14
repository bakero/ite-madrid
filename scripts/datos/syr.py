"""Sugerencias, reclamaciones y felicitaciones al Ayuntamiento (datos.madrid.es 300044, generales y tributarias, recibidas).

Cada fichero anual se descarga con su huella (tabla descarga) y se recorre; se guarda el recuento por año, distrito, barrio,
tipo (sugerencia, reclamación, felicitación) y materia en cm_syr. No se copian datos personales (sexo, edad) ni direcciones.

Uso: python3 scripts/datos/syr.py
"""
import collections, csv, io, json, pathlib, re, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P
from avisos import plano

ID = '300044-0-syrg-syrt'
API = 'https://datos.madrid.es/api/3/action/package_show?id=' + ID
FICHA = 'https://datos.madrid.es/dataset/' + ID


def col(f, *pat):
    for k in f:
        ku = (k or '').upper().strip('﻿" ')
        if any(re.fullmatch(p, ku) for p in pat):
            return f[k]
    return None


def entero(x):
    try:
        return int(float(str(x).strip()))
    except (TypeError, ValueError):
        return None


def main():
    con = P.abrir()
    pkg = json.load(urllib.request.urlopen(urllib.request.Request(API, headers={'User-Agent': P.UA}), timeout=120))['result']
    fid = P.fuente(con, 'dm:300044', pkg['title'], organismo='Ayuntamiento de Madrid', portal='datos.madrid.es', url_ficha=FICHA, url_api=API,
                   licencia=(pkg.get('license_title') or 'CC BY 4.0'), acceso='descarga', seccion='Servicios', prioridad='P2', frecuencia='anual',
                   cobertura='ciudad de Madrid, desde 2016')
    con.execute('''CREATE TABLE IF NOT EXISTS cm_syr(anio INTEGER, cod_distrito INTEGER, cod_barrio INTEGER, ambito TEXT, tipo TEXT, materia TEXT,
                   solicitudes INTEGER, _descarga_id INTEGER)''')
    for r in pkg['resources']:
        nom = (r.get('description') or r.get('name') or '').strip()
        m = re.match(r'Sugerencias y reclamaciones (generales|tributarias)\. Recibidas (?:desde )?(\d{4})', nom)
        if r.get('format') != 'CSV' or not m:
            continue
        amb = m.group(1)
        did, ruta = P.descargar(con, fid, r['url'], recurso=nom, formato='CSV', subcarpeta='300044', script=__file__, archivar_copia=False,
                                pasos=f'1) Abrir {FICHA}, recurso «{nom}» ({r["url"]}). 2) Se recorre el CSV y se cuenta cada solicitud por año de '
                                      'presentación, distrito, barrio, tipo de solicitud y materia. No se usan sexo, edad ni dirección. 3) Resultado en cm_syr.')
        raw = pathlib.Path(ruta).read_bytes()
        try:
            txt = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            txt = raw.decode('cp1252', errors='replace')
        sep = ';' if txt[:2000].count(';') >= txt[:2000].count(',') else ','
        cnt = collections.Counter()
        for f in csv.DictReader(io.StringIO(txt), delimiter=sep):
            fe = re.sub(r'\D', '', str(col(f, r'FECHA_PRES.*', r'FECHA.*PRESENTACI.*', r'FECHA') or ''))
            y = int(fe[:4]) if len(fe) >= 8 and fe[:2] in ('19', '20') else (int(fe[-4:]) if len(fe) >= 8 else None)
            d = entero(col(f, r'ID_DISTRITO', r'DISTRITO_ID', r'COD.*DISTRITO'))
            b = entero(col(f, r'ID_BARRIO', r'BARRIO_ID', r'COD.*BARRIO'))
            d = d if d and 1 <= d <= 21 else None
            cb = None
            if d and b:
                cb = b if b // 10 == d and b > 21 else d * 10 + (b % 100 if b < 100 else b % 10)
            tipo = plano(col(f, r'DESC_TIPOSOLICITUD', r'TIPO.*SOLICITUD') or 'SIN TIPO')
            mat = plano(col(f, r'DESC_MATERIA_COMPLETO', r'DESC_MATERIA', r'MATERIA') or 'SIN MATERIA')
            cnt[(y, d, cb, tipo, mat)] += 1
        del txt, raw
        con.execute('DELETE FROM cm_syr WHERE _descarga_id IN (SELECT id FROM descarga WHERE fuente_id = ? AND recurso = ?)', (fid, nom))
        con.executemany('INSERT INTO cm_syr VALUES (?,?,?,?,?,?,?,?)', [(y, d, b, amb, t, mt, n, did) for (y, d, b, t, mt), n in cnt.items()])
        P.cerrar_descarga(con, did, 'cm_syr', sum(cnt.values()))
        con.commit()
        print(nom, sum(cnt.values()), flush=True)
    con.execute('INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES (?,?,?,?)',
                ('cm_syr', 'Sugerencias, reclamaciones y felicitaciones recibidas por año, distrito, barrio, tipo y materia',
                 con.execute('SELECT count(*) FROM cm_syr').fetchone()[0], 'syr.py'))
    con.commit()


if __name__ == '__main__':
    main()
