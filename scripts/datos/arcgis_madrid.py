"""Carga capas del servidor de mapas del Ayuntamiento (sigma.madrid.es, ArcGIS REST) con trazabilidad.

Por cada capa: una descarga = la consulta GeoJSON completa (todas las páginas), guardada en crudos/sigma/.
Las filas van a ds_sigma_<capa> con sus atributos tal cual, más _anio, la geometría (GeoJSON) y su punto central.

Uso: python3 scripts/datos/arcgis_madrid.py            # todas las capas de CAPAS
     python3 scripts/datos/arcgis_madrid.py asfalto    # las que contienen «asfalto»
"""
import json, pathlib, sys, urllib.parse, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P
from ckan_madrid import volcar

BASE = 'https://sigma.madrid.es/hosted/rest/services'
VISOR = 'https://geoportal.madrid.es/IDEAM_WBGEOPORTAL/visor_ayto.iam'
CAPAS = [(f'OBRAS/OPERACION_ASFALTO_{a}', 0, 'operacion_asfalto', a, 'Via publica') for a in range(2020, 2027)]


def leer(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': P.UA}), timeout=300))


def capa_real(servicio, capa):
    """Algunos servicios no numeran su capa como 0: se toma la primera capa con datos."""
    d = leer(f'{BASE}/{servicio}/MapServer?f=json')
    ids = [l['id'] for l in d.get('layers', []) if not l.get('subLayerIds')]
    return capa if capa in ids else (ids[0] if ids else capa)


def consulta(servicio, capa, offset):
    q = urllib.parse.urlencode(dict(where='1=1', outFields='*', returnGeometry='true', outSR=4326, f='geojson',
                                    resultOffset=offset, resultRecordCount=1000))
    return f'{BASE}/{servicio}/MapServer/{capa}/query?{q}'


def centro(geom):
    pts = []
    def rec(c):
        if c and isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c or []:
                rec(x)
    rec((geom or {}).get('coordinates'))
    if not pts:
        return None, None
    return sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)


def cargar(con, servicio, capa, nombre, anio, seccion):
    fid = P.fuente(con, f'sigma:{nombre}', 'Geoportal del Ayuntamiento: ' + nombre.replace('_', ' ').capitalize(),
                   organismo='Ayuntamiento de Madrid', portal='sigma.madrid.es (ArcGIS REST del Geoportal)',
                   url_ficha=f'{BASE}/{servicio.rsplit("/", 1)[0]}', acceso='api', seccion=seccion, prioridad='P1',
                   licencia='Información pública reutilizable del Ayuntamiento de Madrid (atribución)')
    capa = capa_real(servicio, capa)
    url0 = consulta(servicio, capa, 0)
    if con.execute('SELECT 1 FROM descarga WHERE url=?', (url0,)).fetchone():
        print('   ya cargada', servicio)
        return 0
    feats, off = [], 0
    while True:
        u = consulta(servicio, capa, off)
        d = leer(u)
        if 'error' in d:
            raise RuntimeError(f"{servicio}: {d['error'].get('message')}")
        fs = d.get('features') or []
        feats += fs
        if len(fs) < 1000:
            break
        off += 1000
    sub = P.CRUDOS / 'sigma'
    sub.mkdir(parents=True, exist_ok=True)
    ruta = sub / f'{servicio.replace("/", "_")}_{capa}.geojson'
    ruta.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}, ensure_ascii=False), encoding='utf-8')
    tabla = f'ds_sigma_{nombre}'
    did = con.execute(
        'INSERT INTO descarga(fuente_id,recurso,url,fecha,sha256,bytes,formato,fichero_local,archivo_estado,script,commit_git,pasos) '
        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
        (fid, f'{servicio} capa {capa}', url0, P.ahora(), P.sha256_fichero(ruta), ruta.stat().st_size, 'GeoJSON',
         str(ruta.relative_to(P.CRUDOS)), 'pendiente: copia en Internet Archive no solicitada (consulta de API)',
         'scripts/datos/arcgis_madrid.py', P.commit_actual(),
         f'1) Consultar {url0} (si hay más de 1.000 elementos, repetir con resultOffset=1000, 2000…). '
         f'2) También visible en el visor del Geoportal ({VISOR}), capa «{servicio}». '
         f'3) Cargado en {tabla}; cada fila lleva _descarga_id.')).lastrowid
    claves = sorted({k for f in feats for k in (f.get('properties') or {})})
    filas = []
    for f in feats:
        p = f.get('properties') or {}
        lat, lng = centro(f.get('geometry'))
        filas.append([str(anio), str(lat or ''), str(lng or ''), json.dumps(f.get('geometry'), separators=(',', ':'))] +
                     ['' if p.get(k) is None else str(p.get(k)) for k in claves])
    n = volcar(con, tabla, ['anio', 'lat', 'lng', 'geometria'] + claves, filas, did, f'{servicio} capa {capa}', str(anio))
    P.cerrar_descarga(con, did, tabla, n)
    con.commit()
    print(f'   {servicio}: {n} elementos')
    return n


def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ''
    con = P.abrir()
    for c in CAPAS:
        if filtro in c[0].lower():
            cargar(con, *c)


if __name__ == '__main__':
    main()
