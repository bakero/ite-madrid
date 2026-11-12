"""Comparativa con otras grandes ciudades: liquidaciones de presupuestos de Hacienda (CONPREL).

Descarga el fichero Access anual de liquidaciones de todas las entidades locales, extrae las tablas de inventario
y clasificación económica consolidada (mdb-export, paquete mdbtools) y guarda, para cada ciudad y año, los
importes por capítulo (gastos: obligaciones reconocidas; ingresos: derechos reconocidos) en cm_ciudad_comparada.
Comprobado: Madrid 2023, capítulos 1–7 = 5.326 M€, la misma cifra que la capa propia (cm_ciudad_anio).

Uso: python3 scripts/datos/conprel.py 2016 2024   (rango de años)
"""
import csv, io, pathlib, subprocess, sys, zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P

URL = 'https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL/Consulta/DescargaFichero?CCAA=&TipoDato=Liquidaciones&Ejercicio={a}&TipoPublicacion=Access'
FICHA = 'https://serviciostelematicosext.hacienda.gob.es/SGFAL/CONPREL'
CIUDADES = {'28079AA000': 'Madrid', '08019AA000': 'Barcelona', '46250AA000': 'Valencia', '41091AA000': 'Sevilla',
            '50297AA000': 'Zaragoza', '29067AA000': 'Málaga', '30030AA000': 'Murcia', '07040AA000': 'Palma',
            '35016AA000': 'Las Palmas de Gran Canaria', '48020AA000': 'Bilbao'}


def exportar(accdb, tabla):
    return list(csv.DictReader(io.StringIO(subprocess.check_output(['mdb-export', str(accdb), tabla]).decode('utf-8', 'replace'))))


def main():
    a0, a1 = (int(x) for x in sys.argv[1:3]) if len(sys.argv) > 2 else (2016, 2024)
    con = P.abrir()
    con.execute('CREATE TABLE IF NOT EXISTS cm_ciudad_comparada(anio INTEGER, codigo TEXT, ciudad TEXT, poblacion INTEGER, tipo TEXT, '
                'capitulo TEXT, importe REAL, _descarga_id INTEGER, PRIMARY KEY(anio, codigo, tipo, capitulo))')
    fid = P.fuente(con, 'hacienda:conprel-liquidaciones', 'Hacienda (CONPREL): liquidaciones de presupuestos de las entidades locales',
                   organismo='Ministerio de Hacienda', portal='serviciostelematicosext.hacienda.gob.es', url_ficha=FICHA,
                   licencia='Reutilización con cita de la fuente (Ministerio de Hacienda)', acceso='descarga', seccion='Ciudadano',
                   prioridad='P2', notas='Datos consolidados de cada ayuntamiento con sus organismos (tablas tb_economica_cons)')
    for a in range(a0, a1 + 1):
        url = URL.format(a=a)
        if con.execute('SELECT 1 FROM descarga WHERE url=?', (url,)).fetchone():
            print(a, 'ya cargado'); continue
        try:
            did, ruta = P.descargar(con, fid, url, recurso=f'Liquidaciones{a}.zip', formato='ZIP (Access)', subcarpeta='conprel',
                                    script=__file__, archivar_copia=False,
                                    pasos=f'1) En {FICHA}, «Liquidaciones», ejercicio {a}, descarga del fichero Access completo ({url}). '
                                          '2) Del .accdb: tabla tb_inventario (ciudad y población) y tb_economica_cons (importes consolidados; '
                                          'importer = obligaciones/derechos reconocidos), códigos de 1 cifra = capítulo. 3) Guardado en cm_ciudad_comparada.')
        except Exception as e:
            print(a, 'no disponible:', e); continue
        z = zipfile.ZipFile(ruta)
        nombre = [n for n in z.namelist() if n.lower().endswith(('.accdb', '.mdb'))][0]
        accdb = ruta.parent / nombre
        z.extract(nombre, ruta.parent)
        inv = exportar(accdb, 'tb_inventario')
        ids = {r['id']: (r['codbdgel'], CIUDADES[r['codbdgel']], int(float(r['poblacion'] or 0)))
               for r in inv if r['codbdgel'] in CIUDADES and r['idente'] == r['id']}
        n = 0
        for r in exportar(accdb, 'tb_economica_cons'):
            c = r['cdcta'].strip()
            if r['id'] in ids and len(c) == 1:
                cod, ciu, pob = ids[r['id']]
                con.execute('INSERT OR REPLACE INTO cm_ciudad_comparada VALUES (?,?,?,?,?,?,?,?)',
                            (a, cod, ciu, pob, 'gasto' if r['tipreig'] == 'G' else 'ingreso', c, float(r['importer'] or 0), did))
                n += 1
        P.cerrar_descarga(con, did, 'cm_ciudad_comparada', n)
        con.commit()
        accdb.unlink()
        print(a, n, 'filas', sorted({v[1] for v in ids.values()}))


if __name__ == '__main__':
    main()
