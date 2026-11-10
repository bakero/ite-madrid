"""Indicadores socioeconómicos por distrito del «Panel de indicadores de distritos y barrios» del Ayuntamiento
(datos.madrid.es, conjunto 300087, fichero acumulado). Toma el valor más reciente de cada indicador para cada distrito
y para la ciudad y genera app/socio.js.

Uso: python indicadores.py [acumulado.csv]   (sin argumento lo descarga)
"""
import csv, io, json, pathlib, sys, urllib.request, datetime, re

BASE = pathlib.Path(__file__).resolve().parents[2]
URL = 'https://datos.madrid.es/dataset/300087-0-indicadores-distritos/resource/300087-0-indicadores-distritos-csv/download/acumulado.csv'
# clave corta, indicador completo en el panel, etiqueta para la app, unidad, decimales
IND = [
    ('hab', 'Número habitantes', 'Habitantes', 'hab.', 0),
    ('sup', 'Superficie (ha.)', 'Superficie', 'ha', 0),
    ('dens', 'Población densidad (hab./ha.)', 'Densidad', 'hab./ha', 0),
    ('renta', 'Renta neta media anual de los hogares (Urban Audit)', 'Renta neta media por hogar', '€', 0),
    ('rentap', 'Renta media disponible por persona', 'Renta disponible por persona', '€', 0),
    ('paro', 'Tasa absoluta de paro registrado (febrero)', 'Paro registrado', '%', 1),
    ('edad', 'Edad media de la población', 'Edad media', 'años', 1),
    ('env', 'Porcentaje de envejecimiento (población mayor de 65 años/población total)', 'Mayores de 65 años', '%', 1),
    ('menores', 'Población en etapa educativa (población de 0 a 16 años -16 no incluidos)', 'Menores de 16 años', 'hab.', 0),
    ('migr', 'Proporción de personas migrantes (personas extranjeras menos UE y resto países de OCDE / población total)', 'Población migrante (fuera de UE y OCDE)', '%', 1),
    ('ivta', 'Indice de Vulnerabilidad Territorial Agregado', 'Índice de vulnerabilidad territorial (IVTA)', '', 2),
    ('anioviv', 'Año medio de construcción de inmuebles de uso residencial', 'Año medio de construcción de las viviendas', '', 0),
    ('vcat', 'Valor catastral medio por inmueble de uso residencial', 'Valor catastral medio de la vivienda', '€', 0),
    ('verde', 'Superficie de zonas verdes y parques de distrito (ha.) entre número de habitantes *10.000', 'Zonas verdes por 10.000 hab.', 'ha', 1),
    ('colegios', 'Colegios públicos infantil y primaria', 'Colegios públicos', '', 0),
    ('cdm', 'Centros deportivos municipales', 'Centros deportivos municipales', '', 0),
    ('mayores', 'Centros municipales de mayores', 'Centros municipales de mayores', '', 0),
    ('cultura', 'Centros y espacios culturales', 'Centros y espacios culturales', '', 0),
]


def num(s):
    s = (s or '').strip().replace('.', '').replace(',', '.') if re.search(r'\d,\d', s or '') else (s or '').strip()
    try:
        return float(s)
    except ValueError:
        return None


def main():
    b = open(sys.argv[1], 'rb').read() if len(sys.argv) > 1 else urllib.request.urlopen(URL, timeout=300).read()
    r = csv.DictReader(io.StringIO(b.decode('utf-8-sig')), delimiter=';')
    want = {x[1]: x for x in IND}
    best = {}  # (ambito, clave) -> (periodo, año, valor, fecha, fuente)
    for x in r:
        if x['cod_barrio'].strip() or x['indicador_completo'] not in want:
            continue
        k = want[x['indicador_completo']][0]
        amb = x['cod_distrito'].strip() or 'madrid'
        v = num(x['valor_indicador'])
        if v is None:
            continue
        key = (x['Periodo panel'], x['año'])
        if (amb, k) not in best or key > best[(amb, k)][0]:
            best[(amb, k)] = (key, v, x['fecha_indicador'], x['fuente_indicador'])
    dist = {}
    for (amb, k), (key, v, f, fu) in best.items():
        if k == 'migr' and v < 1:  # el panel lo da como proporción
            v = round(v * 100, 2)
        dist.setdefault(amb, {})[k] = v
    meta = []
    for k, full, l, u, d in IND:
        fechas = {best[(a, kk)][2] for (a, kk) in best if kk == k}
        fuentes = {best[(a, kk)][3] for (a, kk) in best if kk == k}
        tot = k in ('hab', 'sup', 'menores', 'colegios', 'cdm', 'mayores', 'cultura')  # recuentos: se comparan con la media por distrito
        dif = 'abs' if k in ('edad', 'anioviv') else ('pp' if u == '%' else 'rel')
        meta.append({'k': k, 'l': l, 'u': u, 'd': d, 'tot': tot, 'dif': dif, 'fecha': sorted(fechas)[-1] if fechas else '', 'fuente': '; '.join(sorted(fuentes))})
    madrid = dist.pop('madrid', {})
    out = {'generado': datetime.date.today().isoformat(), 'fuente': URL, 'ind': meta, 'dist': {str(int(c)): v for c, v in dist.items()}, 'madrid': madrid}
    open(BASE / 'app' / 'socio.js', 'w', encoding='utf-8').write('window.SOCIO=' + json.dumps(out, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(len(out['dist']), 'distritos ·', 'Madrid:', {k: madrid.get(k) for k in ('hab', 'renta', 'paro', 'ivta')})
    for m in meta:
        print(m['k'], m['fecha'], sum(1 for d in out['dist'].values() if m['k'] in d), '| Madrid', madrid.get(m['k']))


if __name__ == '__main__':
    main()
