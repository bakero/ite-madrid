"""Capa de barrios: los 131 barrios oficiales y los datos que se pueden llevar a barrio.

- cm_barrio: código (distrito × 10 + barrio), nombre, distrito y población del último padrón.
- cm_barrio_panel: indicadores del «Panel de indicadores de distritos y barrios» (datos.madrid.es 300087), último valor de cada uno.
- cm_barrio_dato: datos propios llevados a barrio
    · por el código de barrio que trae el fichero (farolas, señales, avisos ciudadanos),
    · o por el punto en que caen sus coordenadas dentro del contorno oficial del barrio (accidentes desde 2019, asfaltado,
      inversiones principales). Contornos: «Límites administrativos» de datos.madrid.es (900012), los mismos del mapa.

Uso: python3 scripts/datos/barrios.py
"""
import json, pathlib, re, sqlite3, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree
from pyproj import Transformer

ROOT = P.ROOT
PANEL = {  # clave: (texto exacto del indicador en el panel, unidad corta)
    'superficie_ha': 'Superficie (ha.)', 'densidad': 'Población densidad (hab./ha.)', 'habitantes': 'Número habitantes',
    'edad_media': 'Edad media de la población', 'envejecimiento': 'Porcentaje de envejecimiento (población mayor de 65 años/población total)',
    'mayores_65': 'Población de 65 años y más', 'mayores_80': 'Población de 80 años y más', 'menores_15': 'Población de 0 a 14 años',
    'extranjeros': 'Personas con nacionalidad extranjera', 'hogares': 'Total hogares', 'tam_hogar': 'Tamaño medio del hogar',
    'hogar_mujer_sola_65': 'Hogares con una mujer sola mayor de 65 años', 'hogar_hombre_solo_65': 'Hogares con un hombre solo mayor de 65 años',
    'monoparental_mujer': 'Hogares monoparentales: una mujer adulta con uno o más menores',
    'renta_persona': 'Renta media disponible por persona', 'renta_hogar': 'Renta neta media anual de los hogares (Urban Audit)',
    'pension_h': 'Pensión media mensual hombres', 'pension_m': 'Pensión media mensual mujeres',
    'paro': 'Paro registrado (número de personas registradas en SEPE en febrero)', 'tasa_paro': 'Tasa absoluta de paro registrado (febrero)',
    'estudios_sup': 'Población mayor/igual de 25 años con estudios superiores, licenciatura, arquitectura, ingeniería sup., estudios sup. no universitarios, doctorado, postgraduado',
    'pob_25': 'Nivel de estudios de la población mayor/igual de 25 años',
    'locales_abiertos': 'Número de locales dados de alta abiertos', 'locales_cerrados': 'Número de locales dados de alta cerrados',
    'locales_total': 'Número de locales dados de alta totales', 'anio_construccion': 'Año medio de construcción de inmuebles de uso residencial',
    'asociaciones': 'Asociaciones (sección 1ª)', 'asoc_vecinales': 'Asociaciones vecinales',
    'c_mayores': 'Centros municipales de mayores', 'c_ss': 'Centros de servicios sociales', 'residencias': 'Residencias para personas mayores',
    'c_dia': 'Centros de día de alzheimer y físicos', 'apart_mayores': 'Apartamentos municipales para mayores',
    'c_deportivos': 'Centros deportivos municipales', 'inst_deportivas': 'Instalaciones deportivas básicas', 'piscinas': 'Piscinas cubiertas',
    'c_culturales': 'Centros y espacios culturales', 'bibliotecas': 'Bibliotecas municipales', 'esc_infantiles': 'Escuelas infantiles municipales',
    'colegios_pub': 'Colegios públicos infantil y primaria', 'c_salud': 'Centros municipales de salud comunitaria (CMSC)',
    'sin_hogar': 'Centros para personas sin hogar', 'mercados': 'Mercados municipales', 'natalidad': 'Tasa bruta de natalidad (‰)',
    'crecimiento': 'Tasa de crecimiento demográfico (porcentaje)',
}


def geometria():
    """Contornos de barrio en longitud/latitud, tal como los usa el mapa (app/data.js ← barrios_shp.zip de 900012)."""
    s = (ROOT / 'app' / 'data.js').read_text(encoding='utf-8')
    i = s.index('window.VULNERABILIDAD'); j = s.index('=', i) + 1
    d, _ = json.JSONDecoder().raw_decode(s[j:].lstrip())
    pol = {}
    for b in d['barrios']:
        rings = [Polygon(l) for l in b['lines'] if len(l) >= 3]
        pol[int(b['cod'])] = (b['nom'], int(b['cd']), rings)
    return pol


def main():
    con = P.abrir()
    con.execute('CREATE TABLE IF NOT EXISTS cm_tablas(tabla TEXT PRIMARY KEY, descripcion TEXT, filas INTEGER, origen TEXT)')
    did_lim = con.execute("SELECT d.id FROM descarga d JOIN fuente f ON f.id=d.fuente_id WHERE f.clave='dm:900012' ORDER BY d.id DESC").fetchone()[0]
    pol = geometria()
    geoms, codes = [], []
    for c, (_, _, rings) in pol.items():
        for r in rings:
            geoms.append(r.buffer(0)); codes.append(c)
    tree = STRtree(geoms)

    def barrio_de(lng, lat):
        if lng is None or lat is None:
            return None
        p = Point(lng, lat)
        for k in tree.query(p):
            if geoms[k].contains(p):
                return codes[k]
        return None

    # ---- cm_barrio ----
    yP = con.execute('SELECT max(anio) FROM cm_poblacion').fetchone()[0]
    hab = dict(con.execute('SELECT cod_barrio, sum(personas) FROM cm_poblacion WHERE anio=? GROUP BY 1', (yP,)).fetchall())
    did_pob = con.execute('SELECT max(_descarga_id) FROM cm_poblacion WHERE anio=?', (yP,)).fetchone()[0]
    con.execute('DROP TABLE IF EXISTS cm_barrio')
    con.execute('CREATE TABLE cm_barrio(cod_barrio INTEGER PRIMARY KEY, barrio TEXT, cod_distrito INTEGER, habitantes INTEGER, anio_padron INTEGER, _descarga_id INTEGER)')
    con.executemany('INSERT INTO cm_barrio VALUES (?,?,?,?,?,?)', [(c, n, d, hab.get(c), yP, did_lim) for c, (n, d, _) in pol.items()])

    # ---- cm_barrio_panel ----
    T = 'ds_300087_acumulado'
    con.execute('DROP TABLE IF EXISTS cm_barrio_panel')
    con.execute('CREATE TABLE cm_barrio_panel(cod_barrio INTEGER, cod_distrito INTEGER, indicador TEXT, nombre TEXT, unidad TEXT, anio INTEGER, valor REAL, _descarga_id INTEGER)')
    inv = {v: k for k, v in PANEL.items()}
    filas = {}
    for cb, cd, ind, uni, ano, per, val, did in con.execute(f'''SELECT cod_barrio, cod_distrito, indicador_completo, unidad_indicador, ano, periodo_panel, valor_indicador, _descarga_id
                                                             FROM "{T}" WHERE indicador_completo IN ({','.join('?' * len(inv))})''', list(inv)):
        k = inv[ind]
        try:
            v = float(str(val).replace('.', '').replace(',', '.')) if re.match(r'^-?\d{1,3}(\.\d{3})+(,\d+)?$', str(val).strip()) else float(str(val).replace(',', '.'))
        except ValueError:
            continue
        b = int(cb) if str(cb).strip() else 0
        d = int(cd) if str(cd).strip().isdigit() else 0
        key = (b, d, k)
        cand = (int(per) if str(per).isdigit() else 0, int(ano) if str(ano).isdigit() else 0)
        if key not in filas or cand > filas[key][0]:
            filas[key] = (cand, ind, uni, v, did)
    con.executemany('INSERT INTO cm_barrio_panel VALUES (?,?,?,?,?,?,?,?)',
                    [(b, d, k, ind, uni, an, v, did) for (b, d, k), ((_, an), ind, uni, v, did) in filas.items()])

    # ---- cm_barrio_dato ----
    con.execute('DROP TABLE IF EXISTS cm_barrio_dato')
    con.execute('CREATE TABLE cm_barrio_dato(anio INTEGER, cod_barrio INTEGER, indicador TEXT, valor REAL, metodo TEXT, _descarga_id INTEGER)')
    ins = lambda rows: con.executemany('INSERT INTO cm_barrio_dato VALUES (?,?,?,?,?,?)', rows)
    utm = Transformer.from_crs('EPSG:25830', 'EPSG:4326', always_xy=True)
    # accidentes (desde 2019, coordenadas UTM ETRS89 huso 30)
    agg = {}
    for anio, acc, grav, tipo, x, y, did in con.execute('''SELECT anio, accidente, gravedad, tipo_accidente, max(x_utm), max(y_utm), min(_descarga_id)
                                                          FROM cm_accidente WHERE anio >= 2019 GROUP BY anio, accidente'''):
        if not x or not y or x < 400000:
            continue
        lng, lat = utm.transform(x, y)
        b = barrio_de(lng, lat)
        if b is None:
            continue
        a = agg.setdefault((anio, b), [0, 0, did])
        a[0] += 1
        if (tipo or '').startswith('Atropello'):
            a[1] += 1
    ins([(an, b, 'accidentes', v[0], 'coordenadas', v[2]) for (an, b), v in agg.items()] + [(an, b, 'atropellos', v[1], 'coordenadas', v[2]) for (an, b), v in agg.items()])
    gv = {}
    for anio, x, y, n, did in con.execute('''SELECT anio, max(x_utm), max(y_utm), sum(gravedad IN ('grave','fallecido')), min(_descarga_id) FROM cm_accidente
                                             WHERE anio >= 2019 GROUP BY anio, accidente HAVING sum(gravedad IN ('grave','fallecido')) > 0'''):
        if not x or x < 400000:
            continue
        b = barrio_de(*utm.transform(x, y))
        if b is not None:
            g = gv.setdefault((anio, b), [0, did]); g[0] += n
    ins([(an, b, 'graves_fallecidos', v[0], 'coordenadas', v[1]) for (an, b), v in gv.items()])
    # asfaltado
    ag = {}
    for anio, lat, lng, pr, did in con.execute('SELECT anio, lat, lng, precio_aprox, _descarga_id FROM cm_asfalto'):
        b = barrio_de(lng, lat)
        if b is not None:
            a = ag.setdefault((anio, b), [0, 0, did]); a[0] += 1; a[1] += pr or 0
    ins([(an, b, 'tramos_asfaltados', v[0], 'coordenadas', v[2]) for (an, b), v in ag.items()])
    # inversiones principales (último listado)
    yI = con.execute('SELECT max(anio_datos) FROM cm_inversion_principal').fetchone()[0]
    ai = {}
    for lat, lng, pres, did in con.execute('SELECT lat, lng, presupuesto_total, _descarga_id FROM cm_inversion_principal WHERE anio_datos=?', (yI,)):
        b = barrio_de(lng, lat)
        if b is not None:
            a = ai.setdefault(b, [0, 0, did]); a[0] += 1; a[1] += pres or 0
    ins([(yI, b, 'inversiones_n', v[0], 'coordenadas', v[2]) for b, v in ai.items()] + [(yI, b, 'inversiones_eur', v[1], 'coordenadas', v[2]) for b, v in ai.items()])
    # farolas y señales (código de barrio del fichero)
    F = 'ds_300573_unidades_luminosas_farolas'
    ins([(2022, int(d) * 10 + int(b), 'farolas', n, 'codigo', did) for d, b, n, did in con.execute(
        f'SELECT distrito_n_10_0, barrio_n_10_0, count(*), min(_descarga_id) FROM "{F}" GROUP BY 1, 2') if str(d).isdigit() and str(b).isdigit() and int(b) > 0])
    S = 'ds_300273_senales_verticales'
    rows = []
    for d, b, n, did in con.execute(f'''SELECT distrito, barrio, count(*), min(_descarga_id) FROM "{S}"
                                       WHERE substr(fecha_de_baja,7,2) IN ('99','') OR fecha_de_baja IS NULL GROUP BY 1, 2'''):
        md, mb = re.match(r'\s*(\d+)', d or ''), re.match(r'\s*(\d+)', b or '')
        if md and mb:
            cb = int(mb.group(1)); cb = cb if cb > 21 else int(md.group(1)) * 10 + cb
            rows.append((None, cb, 'senales', n, 'codigo', did))
    ins(rows)
    # avisos ciudadanos
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='cm_aviso'").fetchone():
        ins([(a, b, 'avisos', n, 'codigo', did) for a, b, n, did in con.execute(
            'SELECT anio, cod_barrio, sum(avisos), min(_descarga_id) FROM cm_aviso WHERE cod_barrio IS NOT NULL GROUP BY 1, 2')])
    for t, dsc in [('cm_barrio', 'Los 131 barrios: código, nombre, distrito y habitantes del último padrón'),
                   ('cm_barrio_panel', 'Indicadores por barrio del Panel de indicadores de distritos y barrios (último valor)'),
                   ('cm_barrio_dato', 'Datos propios llevados a barrio por código o por coordenadas')]:
        con.execute('INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES (?,?,?,?)',
                    (t, dsc, con.execute(f'SELECT count(*) FROM {t}').fetchone()[0], 'barrios.py'))
    con.commit()
    for t in ('cm_barrio', 'cm_barrio_panel', 'cm_barrio_dato'):
        print(t, con.execute(f'SELECT count(*) FROM {t}').fetchone()[0])
    print(con.execute('SELECT indicador, count(DISTINCT cod_barrio), min(anio), max(anio), sum(valor) FROM cm_barrio_dato GROUP BY 1').fetchall())


if __name__ == '__main__':
    main()
