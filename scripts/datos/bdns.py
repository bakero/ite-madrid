"""Concesiones de la Base de Datos Nacional de Subvenciones (BDNS) cuyo beneficiario es el Ayuntamiento de Madrid.

Sirve para contrastar y completar el conjunto «Subvenciones y ayudas al Ayuntamiento» de datos.madrid.es, que llega hasta 2023.
Una descarga = la consulta completa a la API pública (JSON), guardada en crudos/bdns/.
Las filas van a ds_bdns_concesiones tal cual; capa_limpia.py las añade a cm_ayuda_recibida si no estaban ya.

Uso: python3 scripts/datos/bdns.py [NIF ...]      (por defecto P2807900B, Ayuntamiento de Madrid)
"""
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P
from ckan_madrid import volcar

API = 'https://www.infosubvenciones.es/bdnstrans/api/concesiones/busqueda'
FICHA = 'https://www.infosubvenciones.es/bdnstrans/GE/es/concesiones'
CAMPOS = ['codConcesion', 'fechaConcesion', 'beneficiario', 'instrumento', 'importe', 'ayudaEquivalente', 'urlBR',
          'numeroConvocatoria', 'idConvocatoria', 'convocatoria', 'nivel1', 'nivel2', 'nivel3', 'fechaAlta']


def main(nifs):
    con = P.abrir()
    fid = P.fuente(con, 'bdns:concesiones', 'BDNS · Concesiones de subvenciones y ayudas (beneficiario: Ayuntamiento de Madrid)',
                   organismo='Intervención General de la Administración del Estado (IGAE)', portal='infosubvenciones.es',
                   url_ficha=FICHA, url_api=API, licencia='Reutilización sujeta al aviso legal de infosubvenciones.es', acceso='api',
                   seccion='Ayudas', prioridad='P2', frecuencia='diaria', cobertura='España, todas las administraciones',
                   notas='Datos dinámicos: la IGAE avisa de que pueden corregirse después de la extracción.')
    con.execute('DROP TABLE IF EXISTS ds_bdns_concesiones')
    total = 0
    for nif in nifs:
        url = f'{API}?page=0&pageSize=1000&nifCif={nif}'
        did, ruta = P.descargar(con, fid, url, recurso=f'concesiones_{nif}.json', formato='JSON', subcarpeta='bdns',
                                script=__file__, archivar_copia=False,
                                pasos=f'1) Consulta a la API pública de la BDNS: {url} (equivale a buscar en {FICHA} por NIF del beneficiario {nif}). '
                                      '2) Se guardan todas las concesiones devueltas (campo content), una fila por concesión. '
                                      '3) capa_limpia.py las une a cm_ayuda_recibida sin duplicar las que ya publica datos.madrid.es '
                                      '(misma convocatoria, fecha e importe).')
        d = json.loads(pathlib.Path(ruta).read_text(encoding='utf-8'))
        filas = [[('' if r.get(k) is None else str(r.get(k))) for k in CAMPOS] for r in d.get('content', [])]
        volcar(con, 'ds_bdns_concesiones', CAMPOS, filas, did, f'concesiones_{nif}.json', None)
        P.cerrar_descarga(con, did, 'ds_bdns_concesiones', len(filas))
        con.commit()
        total += len(filas)
        print(nif, len(filas), 'concesiones', '(de', d.get('totalElements'), ')')
    print('total', total)


if __name__ == '__main__':
    main(sys.argv[1:] or ['P2807900B'])
