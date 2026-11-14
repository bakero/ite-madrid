"""Proyectos europeos de investigación (CORDIS) en los que participa el Ayuntamiento de Madrid (NIF P2807900B).

1) Búsqueda en la API de CORDIS de proyectos que mencionan «Ayuntamiento de Madrid».
2) Por cada proyecto, su ficha JSON (cordis.europa.eu/project/id/<id>?format=json); una descarga por ficha.
3) Se guarda solo si entre los socios está la organización con NIF ESP2807900B, con la aportación de la UE a ese socio.
Tablas: ds_cordis_participacion (tal cual) y cm_proyecto_ue.

Uso: python3 scripts/datos/cordis.py
"""
import json, pathlib, sys, urllib.parse, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P
from ckan_madrid import volcar

NIF = 'ESP2807900B'
BUSCA = 'https://cordis.europa.eu/api/search/results?' + urllib.parse.urlencode(
    {'q': "(contenttype='project' AND 'Ayuntamiento de Madrid')", 'num': 10, 'format': 'json'})
FICHA = 'https://cordis.europa.eu/project/id/{}'


def main():
    con = P.abrir()
    fid = P.fuente(con, 'cordis:ayto-madrid', 'CORDIS · Proyectos de investigación de la UE con participación del Ayuntamiento de Madrid',
                   organismo='Comisión Europea (CORDIS)', portal='cordis.europa.eu', url_ficha='https://cordis.europa.eu/search?q=%27Ayuntamiento%20de%20Madrid%27',
                   url_api='https://cordis.europa.eu/api/search/results', licencia='CC BY 4.0 (aviso legal de la Comisión Europea)', acceso='api',
                   seccion='Ayudas', prioridad='P2', frecuencia='continua', cobertura='FP7, Horizonte 2020, Horizonte Europa',
                   notas='Solo proyectos en los que el NIF del socio es ESP2807900B; no incluye empresas ni organismos municipales con NIF propio.')
    ids, pag = [], 1
    while True:
        u = f'{BUSCA}&p={pag}'
        did0, ruta = P.descargar(con, fid, u, recurso=f'busqueda_p{pag}.json', formato='JSON', subcarpeta='cordis', script=__file__, archivar_copia=False,
                                 pasos=f'1) Búsqueda en la API de CORDIS, página {pag} de 10 resultados: {u}. 2) Se abre la ficha de cada proyecto encontrado.')
        res = json.loads(pathlib.Path(ruta).read_text(encoding='utf-8'))['payload']
        nuevos = [h['id'] for h in res.get('results', [])]
        P.cerrar_descarga(con, did0, None, len(nuevos))
        ids += nuevos
        if not nuevos or len(ids) >= int(res.get('total') or 0) or pag >= 20:
            break
        pag += 1
    cab = ['proyecto', 'acronimo', 'titulo', 'programa', 'inicio', 'fin', 'coste_total', 'aportacion_ue_total', 'socio', 'nif', 'rol',
           'aportacion_ue_socio', 'coste_socio', 'url']
    con.execute('DROP TABLE IF EXISTS ds_cordis_participacion')
    n = 0
    for pid in ids:
        url = FICHA.format(pid) + '?format=json'
        did, ruta = P.descargar(con, fid, url, recurso=f'proyecto_{pid}.json', formato='JSON', subcarpeta='cordis', script=__file__,
                                archivar_copia=False,
                                pasos=f'1) Ficha del proyecto {FICHA.format(pid)} (JSON: {url}). 2) En relations/associations se busca el socio con '
                                      f'vatNumber {NIF} (Ayuntamiento de Madrid) y su attributes/ecContribution (aportación de la UE a ese socio).')
        d = json.loads(pathlib.Path(ruta).read_text(encoding='utf-8'))
        prog = ', '.join(sorted({p.get('code', '') for p in (d.get('relations', {}).get('programmes') or []) if isinstance(p, dict)} - {''}))
        filas = []
        for a in d.get('relations', {}).get('associations', []) or []:
            if isinstance(a, dict) and a.get('vatNumber') == NIF:
                at = a.get('attributes', {})
                filas.append([pid, d.get('acronym'), d.get('title'), prog, d.get('startDate'), d.get('endDate'), d.get('totalCost'),
                              d.get('ecMaxContribution'), a.get('legalName'), a.get('vatNumber'), at.get('type'), at.get('ecContribution'),
                              at.get('totalCost'), FICHA.format(pid)])
        filas = [[('' if v is None else str(v)) for v in f] for f in filas]
        if filas:
            volcar(con, 'ds_cordis_participacion', cab, filas, did, f'proyecto_{pid}.json', None)
        P.cerrar_descarga(con, did, 'ds_cordis_participacion' if filas else None, len(filas))
        n += len(filas)
    con.execute('DROP TABLE IF EXISTS cm_proyecto_ue')
    con.execute('''CREATE TABLE cm_proyecto_ue AS SELECT proyecto, acronimo, titulo, programa, inicio, fin, CAST(substr(inicio,1,4) AS INTEGER) AS anio,
                   CAST(nullif(aportacion_ue_socio,'') AS REAL) AS aportacion_ue_ayto, CAST(nullif(coste_total,'') AS REAL) AS coste_total_proyecto,
                   rol, url, _descarga_id FROM ds_cordis_participacion''')
    con.execute('INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES (?,?,?,?)',
                ('cm_proyecto_ue', 'Proyectos de investigación de la UE (CORDIS) con el Ayuntamiento de Madrid como socio', n, 'cordis.py'))
    con.commit()
    print(len(ids), 'proyectos encontrados;', n, 'con el Ayuntamiento como socio;',
          con.execute('SELECT round(sum(aportacion_ue_ayto)) FROM cm_proyecto_ue').fetchone()[0], '€ de aportación UE')


if __name__ == '__main__':
    main()
