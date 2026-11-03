"""Carga en la BD los resultados de la consulta ITE (JSON exportados por el navegador)
y regenera app/data.js y centros_ite_madrid.xlsx.
Uso:
  ITE_DB=/tmp/ite_madrid.sqlite python3 scripts/ingest_export.py [resultados.json ...]
Sin argumentos, solo regenera las salidas a partir de la BD.
"""
import datetime, json, os, re, sqlite3, sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get('ITE_DB', os.path.join(ROOT, 'ite_madrid.sqlite'))
HOY = datetime.date.today().isoformat()

def estado(r):
    s = r[0] or ''
    if s == 'OK':
        n, dic, subs, prox = r[7], (r[11] or '').upper(), (r[22] or '').upper(), r[5]
        if not n or not dic or dic == '-':
            return f'Sin ITE/IEE presentada (próxima ITE {prox})' if prox and prox != '-' else 'Sin ITE/IEE presentada'
        if 'I.E.E.' in dic: return 'IEE complementario de ITE'
        if dic.startswith('FAVORABLE'): return 'Favorable'
        if 'SUBSANADAS' in dic or subs.startswith('SI'): return 'Desfavorable – deficiencias subsanadas'
        if dic.startswith('DESFAVORABLE'): return 'Desfavorable – pendiente de subsanar'
        return 'Otro: ' + r[11]
    m = {'Sin número de portal consultable': 'No consultado: sin número de portal consultable',
         'Número no encontrado en el vial': 'No consultado: número no encontrado en el vial',
         'Vial ambiguo': 'No consultado: vial ambiguo', 'Vial no encontrado': 'No consultado: vial no encontrado',
         'Sin dirección': 'No consultado: sin dirección'}
    if s in m: return m[s]
    if 'BDC' in s: return 'Error del Registro (BDC)'
    if 'Timeout' in s: return 'Registro sin respuesta'
    return 'No consultado: ' + s.replace('Error: ', '')

def ingest(con, path):
    res = json.load(open(path, encoding='utf-8'))
    n = 0
    for addr, r in res.items():
        if not isinstance(r, list) or len(r) < 26 or r[0] == 'pending':
            continue
        if not con.execute('SELECT 1 FROM direcciones WHERE direccion=?', (addr,)).fetchone():
            continue
        est = estado(r)
        origen = 'error' if r[0].startswith('Error') else 'consulta_' + HOY
        con.execute('INSERT OR REPLACE INTO ite VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (addr, est, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13],
                     r[14], r[15], r[16], r[17], r[18], r[19], r[20], r[21], r[22], r[23], r[24], r[25], HOY, origen))
        n += 1
    con.commit()
    print('ingeridos', n, 'de', path)

COLS = ['Distrito', 'Centro', 'Dirección', 'Teléfono', 'Tipo de edificio', 'Subtipo', 'Categoría datos.madrid.es', 'Fuente', 'Otras fuentes', 'Empresa gestora',
        'Estado de la inspección', 'Año de construcción', 'Tipo expediente', 'Dictamen', 'Parcial/Total',
        'Causa dictamen desfavorable', 'Situación administrativa', 'Dependencia actual', 'Nº expediente',
        'Fecha presentación', 'Estado orden de ejecución', 'Fecha resolución', 'Resolución', 'Deficiencias subsanadas',
        'Año próxima ITE', 'Fecha máx. IEE', 'ITE/IEE anteriores', 'Denominación en el Registro', 'Dirección en el Registro',
        'Resultado consulta Registro', 'Fecha consulta', 'Latitud', 'Longitud', 'Ficha madrid.es']
SQL = """SELECT distrito, nombre, direccion, telefono, tipo_edificio, subtipo, categoria_origen, fuente, otras_fuentes, empresa_gestora,
  COALESCE(estado_inspeccion,'Pendiente de consulta'), anio_construccion, tipo_expediente, dictamen, parcial_total,
  causa_desfavorable, situacion_administrativa, dependencia_actual, n_expediente, fecha_presentacion, estado_orden,
  fecha_resolucion, resolucion, deficiencias_subsanadas, anio_proxima_ite, fecha_max_iee, ite_anteriores, denominacion,
  vial_registro, resultado_consulta, fecha_consulta, lat, lng, url_ficha FROM v_centros_ite WHERE COALESCE(excluido,'')='' ORDER BY distrito, nombre"""

def fix_distritos(con):
    """Asigna distrito por coordenadas a los centros sin distrito válido (algunos de datos.madrid.es)."""
    polys = [(n, json.loads(l)) for n, l in con.execute('SELECT nombre, contorno_json FROM distritos')]
    def inside(x, y, rings):
        c = False
        for ring in rings:
            for i in range(len(ring)):
                (x1, y1), (x2, y2) = ring[i - 1], ring[i]
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    c = not c
        return c
    names = [nm for nm, _ in polys]
    n = 0
    q = "SELECT id, lat, lng FROM centros WHERE (distrito IS NULL OR distrito NOT IN (%s)) AND lat IS NOT NULL" % ','.join('?' * len(names))
    for cid, lat, lng in con.execute(q, names).fetchall():
        d = next((nm for nm, rings in polys if inside(lng, lat, rings)), None)
        if d:
            con.execute('UPDATE centros SET distrito=? WHERE id=?', (d, cid)); n += 1
    con.commit()
    if n: print('distrito asignado por coordenadas a', n, 'centros')

def unificar_educativo(con):
    """Los centros de datos.madrid.es entran con tipo 'Educación' y la categoría del Ayuntamiento como subtipo.
    Se pasan al esquema de madrid.es (tipo 'Educativo' + sus subtipos). La categoría original queda en categoria_origen."""
    cols = [r[1] for r in con.execute('PRAGMA table_info(centros)')]
    if 'categoria_origen' not in cols:
        con.execute('ALTER TABLE centros ADD COLUMN categoria_origen TEXT')
    def sub(cat):
        c = (cat or '').upper()
        if 'ESCUELAS INFANTILES' in c: return 'Escuela infantil'
        if 'COLEGIOS PUBLICOS' in c or 'CENTROS PUBLICOS EDUCACION ESPECIAL' in c: return 'Colegio público (CEIP / CPEE)'
        if 'COLEGIOS PRIVADOS CONCERTADOS' in c or 'CENTROS PRIVADOS CONCERTADOS EDUCACION ESPECIAL' in c: return 'Colegio (no público)'
        if 'INSTITUTOS' in c: return 'Instituto (IES)'
        return 'Otros centros formativos'
    rows = con.execute("SELECT id, subtipo FROM centros WHERE tipo_edificio='Educación'").fetchall()
    for cid, st in rows:
        con.execute("UPDATE centros SET tipo_edificio='Educativo', categoria_origen=COALESCE(categoria_origen, ?), subtipo=? WHERE id=?", (st, sub(st), cid))
    con.commit()
    if rows: print('unificados en Educativo:', len(rows), 'centros')

def completar_coordenadas(con):
    """Centros sin coordenadas: se toman de otro centro con la misma dirección o de la tabla
    coordenadas_manual (geocodificación de CartoCiudad revisada a mano)."""
    con.execute('CREATE TABLE IF NOT EXISTS coordenadas_manual(direccion TEXT PRIMARY KEY, lat REAL, lng REAL, fuente TEXT, nota TEXT)')
    n = con.execute("""UPDATE centros SET
        lat = COALESCE((SELECT lat FROM direcciones d WHERE d.direccion=centros.direccion AND d.lat IS NOT NULL),
                       (SELECT lat FROM coordenadas_manual m WHERE m.direccion=centros.direccion)),
        lng = COALESCE((SELECT lng FROM direcciones d WHERE d.direccion=centros.direccion AND d.lat IS NOT NULL),
                       (SELECT lng FROM coordenadas_manual m WHERE m.direccion=centros.direccion))
        WHERE lat IS NULL""").rowcount
    con.execute('UPDATE direcciones SET lat=(SELECT lat FROM coordenadas_manual m WHERE m.direccion=direcciones.direccion), lng=(SELECT lng FROM coordenadas_manual m WHERE m.direccion=direcciones.direccion) WHERE lat IS NULL AND direccion IN (SELECT direccion FROM coordenadas_manual)')
    con.commit()
    left = con.execute('SELECT count(*) FROM centros WHERE lat IS NULL').fetchone()[0]
    print('centros sin coordenadas:', left)

def excluir_no_edificios(con):
    """Registros que no son un edificio (servicios itinerantes o sin ubicación: puntos limpios móviles y de
    proximidad, instalaciones deportivas básicas sin dirección...). Se marcan en la BD y no se exportan."""
    cols = [r[1] for r in con.execute('PRAGMA table_info(centros)')]
    if 'excluido' not in cols:
        con.execute('ALTER TABLE centros ADD COLUMN excluido TEXT')
    con.execute("UPDATE centros SET excluido='No es un edificio: sin dirección ni coordenadas' WHERE COALESCE(TRIM(direccion),'')='' AND lat IS NULL")
    con.commit()
    print('excluidos (no son edificios):', con.execute("SELECT count(*) FROM centros WHERE COALESCE(excluido,'')<>''").fetchone()[0])

def export(con):
    completar_coordenadas(con)
    excluir_no_edificios(con)
    fix_distritos(con)
    unificar_educativo(con)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import reclasificacion
    reclasificacion.aplicar(con)
    rows =[['' if v is None else v for v in r] for r in con.execute(SQL)]
    dist = [{'cod': c, 'nom': n, 'lines': json.loads(l)} for c, n, l in con.execute('SELECT cod,nombre,contorno_json FROM distritos')]
    os.makedirs(os.path.join(ROOT, 'app'), exist_ok=True)
    with open(os.path.join(ROOT, 'app', 'data.js'), 'w', encoding='utf-8') as f:
        f.write('window.ITE_GENERADO=' + json.dumps(HOY) + ';\n')
        f.write('window.ITE_COLS=' + json.dumps(COLS, ensure_ascii=False) + ';\n')
        f.write('window.ITE_ROWS=' + json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + ';\n')
        f.write('window.DISTRITOS=' + json.dumps(dist, ensure_ascii=False, separators=(',', ':')) + ';\n')
    # Excel
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Centros + ITE'
    ws.append(COLS)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F5FA8'); c.alignment = Alignment(wrap_text=True)
    fills = {'Favorable': 'D9F2E3', 'Desfavorable – pendiente': 'F8D7D7', 'Desfavorable – deficiencias': 'FCE6CC', 'IEE': 'E6E0F8'}
    ei = COLS.index('Estado de la inspección') + 1
    for r in rows:
        ws.append(r)
        v = str(r[ei - 1])
        for k, col in fills.items():
            if v.startswith(k):
                ws.cell(ws.max_row, ei).fill = PatternFill('solid', fgColor=col)
    ws.freeze_panes = 'C2'; ws.auto_filter.ref = ws.dimensions
    for i, w in enumerate([18, 45, 38, 14, 22, 22, 16, 30, 28, 36] + [16] * (len(COLS) - 10), 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    rs = wb.create_sheet('Resumen por distrito')
    cats = [('Favorable', lambda v: v == 'Favorable'), ('Desfavorable pendiente', lambda v: 'pendiente de subsanar' in v),
            ('Desfavorable subsanada', lambda v: 'subsanadas' in v), ('IEE complementario', lambda v: v.startswith('IEE')),
            ('Sin ITE presentada', lambda v: v.startswith('Sin ITE')),
            ('No consultable / error', lambda v: v.startswith(('No consultado', 'Error', 'Registro sin', 'Sin datos'))),
            ('Pendiente de consulta', lambda v: v.startswith('Pendiente'))]
    rs.append(['Distrito', 'Centros', 'Direcciones'] + [c for c, _ in cats])
    by = {}
    for r in rows:
        by.setdefault(r[0], []).append(r)
    tot = [0] * (2 + len(cats))
    for d in sorted(by):
        rr = by[d]; dirs = {}
        for r in rr: dirs[r[2]] = str(r[ei - 1])
        vals = [len(rr), len(dirs)] + [sum(1 for v in dirs.values() if f(v)) for _, f in cats]
        rs.append([d] + vals); tot = [a + b for a, b in zip(tot, vals)]
    alld = {r[2]: str(r[ei - 1]) for r in rows}  # una dirección puede estar en varios distritos: el total cuenta direcciones únicas
    rs.append(['TOTAL (direcciones únicas)', len(rows), len(alld)] + [sum(1 for v in alld.values() if f(v)) for _, f in cats])
    for c in rs[1]: c.font = Font(bold=True)
    fs = wb.create_sheet('Fuentes')
    fs.append(['Fuente', 'URL', 'Fichero', 'Fecha de carga', 'Registros'])
    for r in con.execute('SELECT nombre,url,fichero,fecha_carga,n_registros FROM fuentes'):
        fs.append(list(r))
    fs.append([]); fs.append(['Notas'])
    for t in ['Estado de la inspección: resumen calculado a partir de Dictamen y Deficiencias subsanadas de la ITE/IEE más reciente del Registro de Edificios y Construcciones (servpub.madrid.es). Los recuentos del resumen son por dirección (edificio).',
              'La información del Registro no tiene carácter de certificado. Comprobar "Denominación en el Registro" para confirmar que la ficha corresponde al edificio del centro.',
              'Los centros de datos.madrid.es se añaden solo si no estaban ya en el listado de madrid.es (misma dirección y nombre parecido); en ese caso la fuente aparece en "Otras fuentes".']:
        fs.append([t])
    out = os.path.join(ROOT, 'centros_ite_madrid.xlsx')
    tmp = '/tmp/centros_ite_madrid.xlsx'
    wb.save(tmp)
    with open(tmp, 'rb') as a, open(out, 'wb') as b:
        b.write(a.read())
    c = {}
    for v in {r[2]: str(r[ei - 1]) for r in rows}.values():
        k = next((n for n, f in cats if f(v)), 'Otro'); c[k] = c.get(k, 0) + 1
    print(json.dumps({'centros': len(rows), 'direcciones_por_estado': c}, ensure_ascii=False))

if __name__ == '__main__':
    con = sqlite3.connect(DB)
    for p in sys.argv[1:]:
        ingest(con, p)
    export(con)
    con.close()
