"""Renta de los hogares por distrito de Madrid: Atlas de Distribución de Renta de los Hogares (ADRH) del INE.

Una descarga = la tabla 31097 «Indicadores de renta media y mediana» (provincia de Madrid) completa en JSON, desde la API Tempus del INE.
De ella se guardan las series «Madrid distrito NN» y «Madrid» (municipio), dato base, en ds_ine_adrh_renta, y la capa limpia cm_renta.

Uso: python3 scripts/datos/ine_renta.py
"""
import json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P
from ckan_madrid import volcar

TABLA = 31097
API = f'https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{TABLA}?nult=20'
FICHA = f'https://www.ine.es/jaxiT3/Tabla.htm?t={TABLA}'
SERIE = re.compile(r'^Madrid(?: distrito (\d{2}))?\. Dato base\. (.+?)\.\s*$')


def main():
    con = P.abrir()
    fid = P.fuente(con, 'ine:adrh-31097', 'INE · Atlas de Distribución de Renta de los Hogares · Indicadores de renta media y mediana (provincia de Madrid)',
                   organismo='Instituto Nacional de Estadística (INE)', portal='ine.es', url_ficha=FICHA,
                   url_api='https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/353', licencia='Reutilización libre citando la fuente (aviso legal del INE)',
                   acceso='api', seccion='Ciudadano', prioridad='P2', frecuencia='anual', cobertura='secciones censales, distritos y municipios desde 2015',
                   notas='Renta del año de referencia; el INE la publica con unos dos años de retraso.')
    did, ruta = P.descargar(con, fid, API, recurso=f'DATOS_TABLA_{TABLA}.json', formato='JSON', subcarpeta='ine', script=__file__,
                            archivar_copia=False,
                            pasos=f'1) Tabla {FICHA} (operación ADRH, provincia de Madrid). 2) Descarga por la API Tempus: {API}. '
                                  '3) Se guardan las series «Madrid distrito NN. Dato base. …» y «Madrid. Dato base. …» (renta neta media por persona, '
                                  'por hogar, media y mediana por unidad de consumo), un valor por año. 4) cm_renta: una fila por año, distrito e indicador.')
    d = json.loads(pathlib.Path(ruta).read_text(encoding='utf-8'))
    filas = []
    for s in d:
        m = SERIE.match(s['Nombre'])
        if not m:
            continue
        for x in s.get('Data', []):
            if x.get('Valor') is not None:
                filas.append([s['COD'], s['Nombre'].strip(), m.group(1) or '', m.group(2), str(x.get('Anyo') or x.get('NombrePeriodo')), str(x['Valor'])])
    con.execute('DROP TABLE IF EXISTS ds_ine_adrh_renta')
    volcar(con, 'ds_ine_adrh_renta', ['cod_serie', 'nombre', 'distrito', 'indicador', 'anio', 'valor'], filas, did, f'DATOS_TABLA_{TABLA}.json', None)
    P.cerrar_descarga(con, did, 'ds_ine_adrh_renta', len(filas))
    con.execute('DROP TABLE IF EXISTS cm_renta')
    con.execute('''CREATE TABLE cm_renta AS SELECT CAST(anio AS INTEGER) AS anio, CASE WHEN distrito = '' THEN 0 ELSE CAST(distrito AS INTEGER) END AS cod_distrito,
                   indicador, CAST(valor AS REAL) AS euros, _descarga_id FROM ds_ine_adrh_renta''')
    con.execute('INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES (?,?,?,?)',
                ('cm_renta', 'Renta de los hogares por distrito (INE, ADRH); cod_distrito 0 = municipio de Madrid',
                 con.execute('SELECT count(*) FROM cm_renta').fetchone()[0], 'ine_renta.py'))
    con.commit()
    print(len(filas), 'valores;', con.execute('SELECT min(anio), max(anio), count(DISTINCT cod_distrito) FROM cm_renta').fetchone())


if __name__ == '__main__':
    main()
