"""Pasa los datos del Mapa ITE (ite_madrid.sqlite y datos/*.json) a ciudadano_madrid.sqlite con su procedencia.

- Copia las tablas existentes y añade _descarga_id a cada fila.
- Registra cada fuente y cada fichero usado (con su SHA-256 si el fichero está en datos/).
- Carga los anuncios del BOE y los enlaces de la Plataforma de Contratación con su URL por fila.
Los datos de una carga anterior se marcan con archivo_estado «pendiente: carga anterior al esquema».
Idempotente: si la tabla ya existe en la BD nueva, no la vuelve a copiar.
"""
import json, pathlib, sqlite3, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P

ROOT = P.ROOT
D = ROOT / 'datos'
VIEJA = ROOT / 'ite_madrid.sqlite'
DM = 'https://datos.madrid.es/dataset/'
REGISTRO = 'https://servpub.madrid.es/GITEP_WBFICHA/SGiteCons'
PLACSP = 'https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl='
SCRIPT = 'scripts/datos/migrar_existente.py'

ABIERTOS = {  # fichero -> (id del conjunto, nombre exacto usado en centros.otras_fuentes)
    '212790-4-centros-educacion-json.json': ('212790-0-centros-educacion', 'Centros de educación (sedes)'),
    '300614-5-centros-educativos-json.json': ('300614-0-centros-educativos', 'Centros educativos en Madrid'),
    '202311-0-colegios-publicos-json.json': ('202311-0-colegios-publicos', 'Colegios públicos'),
    '202318-2-escuelas-infantiles-json.json': ('202318-0-escuelas-infantiles', 'Escuelas infantiles municipales'),
    '212904-2-centros-ensenanza-json.json': ('212904-0-centros-ensenanza', 'Centros de enseñanza (sedes)'),
    '207037-0-idiomas-oficial-json.json': ('207037-0-idiomas-oficial', 'Escuelas Oficiales de Idiomas'),
    '300307-1-escuelas-infantiles-empresas-csv.csv': ('300307-0-escuelas-infantiles-empresas', 'Empresas gestoras de escuelas infantiles'),
}


def copiar_tablas(con):
    con.execute('ATTACH DATABASE ? AS vieja', (str(VIEJA),))
    tablas = [r[0] for r in con.execute("SELECT name FROM vieja.sqlite_master WHERE type='table'")]
    for t in tablas:
        destino = 'fuentes_mapa_ite' if t == 'fuentes' else t
        if con.execute("SELECT 1 FROM main.sqlite_master WHERE name=?", (destino,)).fetchone():
            continue
        sql = con.execute("SELECT sql FROM vieja.sqlite_master WHERE name=?", (t,)).fetchone()[0]
        sql = sql.replace(f'CREATE TABLE {t}', f'CREATE TABLE "{destino}"', 1).replace(f'CREATE TABLE "{t}"', f'CREATE TABLE "{destino}"', 1)
        con.execute(sql)
        con.execute(f'INSERT INTO main."{destino}" SELECT * FROM vieja."{t}"')
        if destino != 'fuentes_mapa_ite':
            con.execute(f'ALTER TABLE main."{destino}" ADD COLUMN _descarga_id INTEGER REFERENCES descarga(id)')
    for (sql,) in con.execute("SELECT sql FROM vieja.sqlite_master WHERE type='view'").fetchall():
        con.execute(sql.replace('CREATE VIEW', 'CREATE VIEW IF NOT EXISTS', 1))
    con.commit()
    con.execute('DETACH DATABASE vieja')


def ya(con, clave):
    return con.execute('SELECT 1 FROM descarga d JOIN fuente f ON f.id=d.fuente_id WHERE f.clave=?', (clave,)).fetchone()


def main():
    con = P.abrir()
    copiar_tablas(con)

    # 1. Listados de madrid.es (21 distritos): extracción con el script del navegador
    k = 'madrid.es:distritos-listados'
    if not ya(con, k):
        fid = P.fuente(con, k, 'madrid.es: «Direcciones y teléfonos» y «Recursos educativos públicos» de los 21 distritos',
                       organismo='Ayuntamiento de Madrid', portal='madrid.es',
                       url_ficha='https://www.madrid.es/portales/munimadrid/es/Inicio/El-Ayuntamiento/Distritos/',
                       acceso='extraccion', seccion='Edificios', prioridad='P1', cobertura='2026-11-02')
        did = P.registrar_existente(con, fid, 'https://www.madrid.es/portales/munimadrid/es/Inicio/El-Ayuntamiento/Distritos/',
                                    ruta=D / 'centros_madrid_21_distritos_ITE.xlsx', recurso='centros_madrid_21_distritos_ITE.xlsx',
                                    fecha='2026-11-02', formato='XLSX', script='scripts/navegador/01_listados_madrid_es.js',
                                    pasos='Para cada distrito, abrir «Direcciones y teléfonos» y «Recursos educativos públicos» en madrid.es '
                                          'y recorrer los listados con scripts/navegador/01_listados_madrid_es.js. La URL de la ficha de cada '
                                          'centro está en centros.url_ficha.', tabla='centros')
        n = con.execute("UPDATE centros SET _descarga_id=? WHERE fuente='madrid.es'", (did,)).rowcount
        P.cerrar_descarga(con, did, 'centros', n)

    # 2. Conjuntos de datos.madrid.es ya usados (fichero local = el descargado entonces)
    ids_por_nombre = {}
    for fichero, (pid, nombre) in ABIERTOS.items():
        k = 'dm:' + pid.split('-')[0]
        fid = P.fuente(con, k, nombre, organismo='Ayuntamiento de Madrid', portal='datos.madrid.es', url_ficha=DM + pid,
                       licencia='Creative Commons Attribution 4.0 International (CC BY 4.0)', acceso='api', seccion='Edificios', prioridad='P1')
        fila = con.execute('SELECT id FROM descarga WHERE fuente_id=? AND recurso=?', (fid, fichero)).fetchone()
        did = fila[0] if fila else P.registrar_existente(
            con, fid, f'{DM}{pid}', ruta=D / fichero, recurso=fichero, fecha='2026-11-02', formato=fichero.rsplit('.', 1)[-1].upper(),
            script='scripts/build_db.py', pasos=f'Abrir {DM}{pid} y descargar «{fichero}». Cargado por scripts/build_db.py.')
        ids_por_nombre[nombre] = did
    for cid, otras in con.execute("SELECT id, otras_fuentes FROM centros WHERE fuente='datos.madrid.es' AND _descarga_id IS NULL").fetchall():
        primera = (otras or '').split(';')[0].strip()
        if primera in ids_por_nombre:
            con.execute('UPDATE centros SET _descarga_id=? WHERE id=?', (ids_por_nombre[primera], cid))
    for nombre, did in ids_por_nombre.items():
        n = con.execute('SELECT count(*) FROM centros WHERE _descarga_id=?', (did,)).fetchone()[0]
        P.cerrar_descarga(con, did, 'centros' if n else None, n)

    # 3. ITE: Registro de Edificios y Construcciones (consulta por dirección)
    k = 'madrid:registro-edificios'
    if not ya(con, k):
        fid = P.fuente(con, k, 'Registro de Edificios y Construcciones (ITE/IEE)', organismo='Ayuntamiento de Madrid',
                       portal='servpub.madrid.es', url_ficha=REGISTRO, acceso='extraccion', seccion='Edificios', prioridad='P1',
                       notas='No se republica copia: requiere permiso de reutilización. Solo URL, fecha y pasos.')
        for origen, fecha, ruta in [('consulta_2026-11-03', '2026-11-03', D / 'ite_resultados_20261103_0522.json'),
                                    ('excel_02-11-2026', '2026-11-02', D / 'centros_madrid_21_distritos_ITE.xlsx'),
                                    ('error', '2026-11-03', D / 'ite_resultados_20261103_0522.json')]:
            did = P.registrar_existente(con, fid, REGISTRO, ruta=ruta, recurso=f'consultas {origen}', fecha=fecha, formato='JSON',
                                        script='scripts/navegador/02_consulta_ite_registro.js',
                                        pasos=f'En {REGISTRO}, buscar cada dirección por vía y número (campo ite.vial_registro) y leer la '
                                              'última ITE/IEE. Hecho con scripts/navegador/02_consulta_ite_registro.js; '
                                              f'origen «{origen}». El Registro no tiene carácter de certificado.', tabla='ite')
            n = con.execute('UPDATE ite SET _descarga_id=? WHERE origen=?', (did, origen)).rowcount
            P.cerrar_descarga(con, did, 'ite', n)

    # 4. Ámbitos e indicadores
    for k, pid, nombre, fichero, tablas, cuando in [
        ('dm:300497', '300497-0-distritos-municipales-madrid', 'Distritos municipales de Madrid', 'distritos_madrid_simpl.json', ['distritos'], '2026-11-02'),
        ('dm:900012', '900012-0-limites-administrativos-mapas', 'Límites administrativos actuales (barrios)', 'vulnerabilidad/barrios_shp.zip', ['barrios'], '2026-11-06'),
        ('dm:300577', '300577-0-iguala-vulnerabilidad', 'IGUALA. Índice de vulnerabilidad territorial agregado', 'vulnerabilidad/iguala_ivta_global.xlsx',
         ['barrios_indicadores', 'distritos_vulnerabilidad'], '2026-11-06')]:
        if ya(con, k):
            continue
        fid = P.fuente(con, k, nombre, organismo='Ayuntamiento de Madrid', portal='datos.madrid.es', url_ficha=DM + pid,
                       licencia='Creative Commons Attribution 4.0 International (CC BY 4.0)', acceso='api', seccion='Transversal', prioridad='P1')
        did = P.registrar_existente(con, fid, DM + pid, ruta=D / fichero, recurso=fichero, fecha=cuando,
                                    formato=fichero.rsplit('.', 1)[-1].upper(), script='scripts/vulnerabilidad.py',
                                    pasos=f'Abrir {DM + pid} y descargar «{fichero.rsplit("/", 1)[-1]}».', tabla=tablas[0])
        for t in tablas:
            n = con.execute(f'UPDATE "{t}" SET _descarga_id=?', (did,)).rowcount
        P.cerrar_descarga(con, did, ','.join(tablas), n)

    # 5. Coordenadas a mano (CartoCiudad)
    k = 'ign:cartociudad'
    if not ya(con, k):
        fid = P.fuente(con, k, 'CartoCiudad: geocodificación de direcciones', organismo='Instituto Geográfico Nacional',
                       portal='cartociudad.es', url_ficha='https://www.cartociudad.es/web/portal/herramientas-calculos/geocodificador',
                       licencia='CC BY 4.0 (atribución IGN)', acceso='api', seccion='Transversal', prioridad='P1')
        did = P.registrar_existente(con, fid, 'https://www.cartociudad.es/geocoder/api/geocoder/find?q=<dirección>',
                                    recurso='coordenadas_manual', fecha='2026-11-03', script='scripts/coordenadas_manual.py',
                                    pasos='Para cada dirección de coordenadas_manual, consultar el geocodificador de CartoCiudad con la dirección '
                                          'completa y tomar lat/lng del primer resultado.', tabla='coordenadas_manual')
        n = con.execute('UPDATE coordenadas_manual SET _descarga_id=?', (did,)).rowcount
        P.cerrar_descarga(con, did, 'coordenadas_manual', n)

    # 6. BOE 1995–2014 (Puente de Vallecas): una URL por anuncio
    k = 'boe:anuncios'
    if not ya(con, k):
        fid = P.fuente(con, k, 'BOE: anuncios de contratación del Ayuntamiento de Madrid (Puente de Vallecas, 1995–2014)',
                       organismo='Agencia Estatal Boletín Oficial del Estado', portal='boe.es', url_ficha='https://www.boe.es/buscar/anboe.php',
                       licencia='Reutilización libre con cita de la fuente (aviso legal del BOE)', acceso='api', seccion='Servicios',
                       prioridad='P2', cobertura='1995–2014')
        did = P.registrar_existente(con, fid, 'https://www.boe.es/diario_boe/txt.php?id=<id del anuncio>',
                                    ruta=D / 'inversiones/boe_vallecas_1995_2014.json', recurso='boe_vallecas_1995_2014.json', formato='JSON',
                                    fecha='2026-11-10', script='scripts/inversiones/boe_parse.py',
                                    pasos='Búsqueda en el BOE (sección V-A, Administración Local) por los términos de la columna consulta; '
                                          'cada anuncio se abre en la URL de la columna url.', tabla='boe_anuncios')
        con.execute('CREATE TABLE IF NOT EXISTS boe_anuncios(id TEXT PRIMARY KEY, fecha TEXT, departamento TEXT, titulo TEXT, texto TEXT, '
                    'consulta TEXT, url TEXT, _descarga_id INTEGER REFERENCES descarga(id))')
        filas = json.load(open(D / 'inversiones/boe_vallecas_1995_2014.json', encoding='utf-8'))
        con.executemany('INSERT OR IGNORE INTO boe_anuncios VALUES (?,?,?,?,?,?,?,?)',
                        [(a['id'], a.get('fecha'), a.get('dep'), a.get('titulo'), a.get('texto'), json.dumps(a.get('q'), ensure_ascii=False),
                          f"https://www.boe.es/diario_boe/txt.php?id={a['id']}", did) for a in filas])
        P.cerrar_descarga(con, did, 'boe_anuncios', len(filas))

    # 7. Enlaces a la Plataforma de Contratación por expediente (pliegos de servicios)
    k = 'placsp:expedientes-juntas'
    if not ya(con, k):
        fid = P.fuente(con, k, 'Plataforma de Contratación del Sector Público: expedientes de las Juntas de distrito',
                       organismo='Ministerio de Hacienda', portal='contrataciondelestado.es',
                       url_ficha='https://contrataciondelestado.es/wps/portal/plataforma/buscadores/busqueda',
                       acceso='extraccion', seccion='Servicios', prioridad='P1')
        did = P.registrar_existente(con, fid, PLACSP + '<idEvl>', ruta=D / 'servicios/enlaces.json', recurso='enlaces.json', formato='JSON',
                                    fecha='2026-11-11', script='scripts/servicios/enlaces_plataforma.py',
                                    pasos='Buscar cada expediente en el buscador de licitaciones de la Plataforma; la ficha está en la URL de '
                                          'la columna url; de ahí se descargan el pliego (PPT) y el anexo económico.', tabla='placsp_expedientes')
        con.execute('CREATE TABLE IF NOT EXISTS placsp_expedientes(expediente TEXT, id_evl TEXT, resumen TEXT, url TEXT, '
                    '_descarga_id INTEGER REFERENCES descarga(id), PRIMARY KEY(expediente, id_evl))')
        enl = json.load(open(D / 'servicios/enlaces.json', encoding='utf-8'))
        filas = [(exp, e[0], e[1] if len(e) > 1 else None, PLACSP + e[0], did) for exp, lst in enl.items() for e in lst]
        con.executemany('INSERT OR IGNORE INTO placsp_expedientes VALUES (?,?,?,?,?)', filas)
        P.cerrar_descarga(con, did, 'placsp_expedientes', len(filas))

    # 8. Ficheros intermedios que aún no están en tablas (se rehacen desde las tablas ds_* cargadas por ckan_madrid.py)
    for fichero, clave, url, script in [
        ('inversiones/inversiones_2014_2025.json', 'dm:211496', DM + '211496-0-ejecucion-presupuestaria-histori', 'scripts/inversiones/descarga_inversiones.py'),
        ('inversiones/contratos_obras.json', 'dm:216876', DM + '216876-0-contratos-actividad', 'scripts/inversiones/contratos_obras.py'),
        ('servicios/servicios_pv.json', 'dm:216876', DM + '216876-0-contratos-actividad', 'scripts/servicios/servicios.py'),
        ('servicios/reparto_pliegos.json', 'placsp:expedientes-juntas', PLACSP + '<idEvl>', 'scripts/servicios/reparto_pliegos.py'),
        ('servicios/empresas_distritos.json', 'dm:216876', DM + '216876-0-contratos-actividad', 'scripts/servicios/empresas_distritos.py'),
    ]:
        fid = con.execute('SELECT id FROM fuente WHERE clave=?', (clave,)).fetchone()
        if not fid:
            fid = (P.fuente(con, clave, clave, portal='datos.madrid.es', url_ficha=url, acceso='api', seccion='Servicios'),)
        if not con.execute('SELECT 1 FROM descarga WHERE fichero_local=?', ('datos/' + fichero,)).fetchone():
            P.registrar_existente(con, fid[0], url, ruta=D / fichero, recurso=fichero, formato='JSON', script=script,
                                  pasos=f'Fichero intermedio generado por {script} a partir de {url}. Pendiente de rehacer desde las tablas ds_*.')
    con.commit()
    sin = {t: con.execute(f'SELECT count(*) FROM "{t}" WHERE _descarga_id IS NULL').fetchone()[0]
           for t in ['centros', 'ite', 'distritos', 'barrios', 'barrios_indicadores', 'distritos_vulnerabilidad', 'coordenadas_manual']}
    print('Filas sin procedencia por tabla:', sin)


if __name__ == '__main__':
    main()
