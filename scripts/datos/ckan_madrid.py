"""Carga conjuntos de datos.madrid.es (API CKAN) en ciudadano_madrid.sqlite con trazabilidad completa.

Para cada conjunto del catálogo `catalogo.py`:
  1. Lee su ficha con package_show y la registra en `fuente` (URL de la ficha, licencia, frecuencia, cobertura).
  2. Agrupa sus ficheros por familia (p. ej. «Gastos», «Ingresos», «Contratos menores») y periodo, y descarga
     uno por familia y periodo: CSV si existe; si no, XLSX, XLS o el formato geográfico (ZIP/KMZ).
     Descarga también los PDF de «Contenido y estructura del fichero» (documentación del organismo).
  3. Vuelca cada CSV/XLSX/XLS tal cual (todas las columnas como texto) en la tabla ds_<id>_<familia>,
     con las columnas añadidas _descarga_id (fila -> descarga) y _recurso (nombre del fichero en el portal).

Uso:
    python3 scripts/datos/ckan_madrid.py              # todos los conjuntos del catálogo con carga=True
    python3 scripts/datos/ckan_madrid.py 300375 300533 # solo esos
Variables: CM_DB (ruta de la BD), CM_CRUDOS (carpeta de ficheros), CM_ARCHIVAR=1 (pedir copia a Internet Archive).
"""
import csv, io, json, re, sys, unicodedata, urllib.request, zipfile, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P
from catalogo import CATALOGO

API = 'https://datos.madrid.es/api/3/action/package_show?id='
FICHA = 'https://datos.madrid.es/dataset/'
csv.field_size_limit(1 << 30)
MESES = r'enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre'
PREF = ['CSV', 'XLSX', 'XLS', 'ZIP', 'KMZ', 'JSON', 'XML']


def slug(s, n=40):
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')[:n].strip('_')


def familia_periodo(titulo):
    t = re.sub(r'^\d{3}\s+[^.]+\.\s*', '', titulo.strip())             # «001 Ayuntamiento de Madrid. Gastos 2016»
    periodo = ' '.join(re.findall(r'(?:19|20)\d{2}(?:\s*-\s*(?:19|20)?\d{2,4})?', t)) or None
    mes = re.search(rf'(?<!\()\b({MESES})\b(?!\))', t, re.I)       # «Gastos. abril 2026» (ejecución mensual)
    if mes and not re.search(rf'(?:desde|hasta)\s+{mes.group(1)}', t, re.I):
        periodo = f'{mes.group(1).lower()} {periodo or ""}'.strip()
    m = re.search(rf'\((?:desde|hasta)\s+({MESES})\)', t, re.I)
    if m:
        periodo = (periodo or '') + ' ' + m.group(0)
    fam = re.sub(rf'\((?:[^)]*?(?:19|20)\d{{2}}[^)]*?|(?:desde|hasta)\s+(?:{MESES}))\)', ' ', t, flags=re.I)
    fam = re.sub(rf'\b(?:{MESES})\b', ' ', fam, flags=re.I)
    fam = re.sub(r'(?:19|20)\d{2}(?:\s*-\s*(?:19|20)?\d{2,4})?', ' ', fam)
    fam = re.sub(r'\b(?:año|campaña|ejercicio|formalizados en|a partir de)\b', ' ', fam, flags=re.I)
    fam = re.sub(r'[\s.,:;()-]+$', '', re.sub(r'\s+', ' ', fam)).strip(' .')
    fam = re.sub(r'(?:\s+(?:de|del|en|desde|hasta|a))+$', '', fam, flags=re.I)
    return fam or titulo, (periodo or '').strip() or None


def nombre_tabla(sub, fam):
    return f"ds_{sub}_{slug(fam, 55)}"


def es_documentacion(titulo):
    return bool(re.search(r'contenido y estructura|glosario', titulo, re.I))


ES = set('áéíóúñÁÉÍÓÚÑüÜ')
RARO = set('µ¢¥¤¦§¨©®±²³¶·¸¹º¼½¾¿×÷ÃÂ¡')


def decodificar(b):
    """UTF-8 si es válido; si no, entre cp1252 y cp850 (algunos CSV del portal vienen en codificación DOS) el que dé
    más letras españolas y menos símbolos raros («µREA» = «ÁREA», «Tramitaci¢n» = «Tramitación»)."""
    try:
        return b.decode('utf-8-sig')
    except UnicodeDecodeError:
        pass
    mejor, nota = None, None
    for enc in ('cp1252', 'cp850', 'latin-1'):
        try:
            t = b.decode(enc)
        except UnicodeDecodeError:
            continue
        m = t[:200000]
        n = sum(ch in ES for ch in m) - 3 * sum(ch in RARO for ch in m)
        if mejor is None or n > nota:
            mejor, nota = t, n
    return mejor


def separador(texto):
    """El separador con el que más líneas de las primeras 40 tienen el mismo número de campos (>= 3)."""
    lineas = texto.splitlines()[:40]
    mejor, pmejor = ';', -1
    for d in (';', ',', '\t', '|'):
        cuentas = [len(f) for f in csv.reader(lineas, delimiter=d)]
        cuentas = [c for c in cuentas if c >= 3]
        if not cuentas:
            continue
        moda = max(set(cuentas), key=cuentas.count)
        p = cuentas.count(moda) * 1000 + moda
        if p > pmejor:
            mejor, pmejor = d, p
    return mejor


def filas_csv(ruta):
    texto = decodificar(ruta.read_bytes())
    delim = separador(texto)
    r = csv.reader(io.StringIO(texto), delimiter=delim)
    for cab in r:                         # salta títulos encima de la cabecera («Contratos … a 31 de diciembre de 2023»)
        if sum(1 for v in cab if v.strip()) >= 3:
            return cab, r
    return None, r


def filas_xlsx(ruta):
    """Primera hoja que tenga una fila de cabecera (>= 3 celdas no vacías); las portadas e índices se saltan."""
    import openpyxl
    wb = openpyxl.load_workbook(open(ruta, 'rb'), read_only=True, data_only=True)
    for ws in wb.worksheets:
        it = ws.iter_rows(values_only=True)
        for fila in it:
            if sum(1 for v in fila if v not in (None, '')) >= 3:
                cab = [str(v) if v is not None else '' for v in fila]
                return cab, ([('' if v is None else str(v)) for v in f] for f in it)
    return None, iter(())


def filas_xls(ruta):
    import xlrd
    for sh in xlrd.open_workbook(ruta).sheets():
        inicio = next((i for i in range(sh.nrows) if sum(1 for v in sh.row_values(i) if v not in ('', None)) >= 3), None)
        if inicio is not None:
            cab = [str(v) for v in sh.row_values(inicio)]
            return cab, ([str(v) for v in sh.row_values(i)] for i in range(inicio + 1, sh.nrows))
    return None, iter(())


def columnas_limpias(cab):
    out, vistos = [], {}
    for i, c in enumerate(cab):
        s = slug(str(c or ''), 60) or f'col{i + 1}'
        if s in vistos:
            vistos[s] += 1
            s = f'{s}_{vistos[s]}'
        else:
            vistos[s] = 1
        out.append(s)
    return out


def volcar(con, tabla, cab, filas, descarga_id, recurso, periodo):
    cab = list(cab)
    while cab and not str(cab[-1] or '').strip():      # Excel suele declarar cientos de columnas vacías al final
        cab.pop()
    if not cab:
        return 0
    cols = columnas_limpias(cab)
    con.execute(f'CREATE TABLE IF NOT EXISTS "{tabla}"(_descarga_id INTEGER REFERENCES descarga(id), _recurso TEXT, _periodo TEXT)')
    existentes = {r[1] for r in con.execute(f'PRAGMA table_info("{tabla}")')}
    for c in cols:
        if c not in existentes:
            con.execute(f'ALTER TABLE "{tabla}" ADD COLUMN "{c}" TEXT')
    sql = f'INSERT INTO "{tabla}"(_descarga_id,_recurso,_periodo,{",".join(chr(34) + c + chr(34) for c in cols)}) VALUES ({",".join("?" * (len(cols) + 3))})'
    n, lote = 0, []
    for f in filas:
        if not any(str(v).strip() for v in f):
            continue
        f = list(f)[:len(cols)] + [None] * max(0, len(cols) - len(f))
        lote.append([descarga_id, recurso, periodo, *[(v.strip() if isinstance(v, str) else v) for v in f]])
        if len(lote) >= 5000:
            con.executemany(sql, lote); n += len(lote); lote = []
    if lote:
        con.executemany(sql, lote); n += len(lote)
    return n


def elegir(recursos):
    """Un recurso por (familia, periodo), por orden de preferencia de formato; más la documentación PDF."""
    grupos, docs = {}, []
    for x in recursos:
        titulo = x.get('description') or x.get('name') or ''
        fmt = (x.get('format') or '').upper()
        if fmt == 'PDF':
            if es_documentacion(titulo):
                docs.append((titulo, x))
            continue
        if fmt not in PREF:
            continue
        fam, per = familia_periodo(titulo)
        org = re.match(r'^(\d{3})\s', titulo.strip())       # 2011–2016: un fichero por organismo (001 Ayuntamiento, 508 Madrid Salud…)
        k = (org.group(1) if org else '', fam.lower(), per)
        if k not in grupos or PREF.index(fmt) < PREF.index(grupos[k][2]):
            grupos[k] = (fam, per, fmt, titulo, x)
    return list(grupos.values()), docs


LECTORES = {'CSV': filas_csv, 'XLSX': filas_xlsx, 'XLS': filas_xls}


def procesar(con, did, ruta, fmt, tabla, titulo, per):
    """Vuelca un fichero ya descargado. Si el formato declarado falla, prueba los otros (el portal a veces lo etiqueta mal)."""
    if fmt not in LECTORES:
        P.cerrar_descarga(con, did, None, 0)
        return 0
    errores = []
    for f in [fmt] + [x for x in LECTORES if x != fmt]:
        try:
            cab, filas = LECTORES[f](ruta)
            if not cab or not any(str(c or '').strip() for c in cab):
                errores.append(f'{f}: sin cabecera')
                continue
            con.execute('SAVEPOINT v')
            n = volcar(con, tabla, cab, filas, did, titulo, per)
            con.execute('RELEASE v')
            nota = '' if f == fmt else f' (el portal lo declara {fmt}; se ha leído como {f})'
            con.execute("UPDATE descarga SET tabla=?, filas=?, pasos=replace(pasos,' ERROR al cargar','')||? WHERE id=?",
                        (tabla if n else None, n, nota, did))
            return n
        except Exception as e:
            try:
                con.execute('ROLLBACK TO v'); con.execute('RELEASE v')
            except Exception:
                pass
            errores.append(f'{f}: {type(e).__name__}: {str(e)[:80]}')
    con.execute('UPDATE descarga SET pasos=pasos||? WHERE id=?', (' ERROR al cargar: ' + ' | '.join(errores), did))
    print('   !', titulo, errores[0])
    return 0


def recargar_errores(con):
    """Vuelve a volcar las descargas que fallaron, desde el fichero ya guardado en crudos/."""
    q = con.execute("SELECT id, fichero_local, formato, recurso, pasos FROM descarga WHERE pasos LIKE '%ERROR al cargar%'").fetchall()
    for did, local, fmt, recurso, pasos in q:
        tabla = re.search(r'en la tabla (\S+);', pasos)
        if not tabla:
            continue
        m = re.search(r'recurso «(.+?)»', pasos)
        titulo = m.group(1) if m else recurso
        con.execute("UPDATE descarga SET pasos=substr(pasos,1,instr(pasos,' ERROR al cargar')-1) WHERE id=?", (did,))
        n = procesar(con, did, P.CRUDOS / local, fmt, tabla.group(1), titulo, familia_periodo(titulo)[1])
        con.commit()
        print(f'   recargado {did} {fmt} {n} filas {recurso}')


def revolcar_todo(con):
    """Rehace todas las tablas ds_* desde los ficheros de crudos/ (sin volver a descargar)."""
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ds\\_%' ESCAPE '\\'").fetchall():
        con.execute(f'DROP TABLE "{t}"')
    q = con.execute("SELECT id, fichero_local, formato, recurso, pasos, url FROM descarga WHERE pasos LIKE '%Cargado sin transformar%'").fetchall()
    for did, local, fmt, recurso, pasos, url in q:
        titulo = re.search(r'recurso «(.+?)»', pasos).group(1)
        sub = local.split('/', 1)[0]
        fam, per = familia_periodo(titulo)
        tabla = nombre_tabla(sub, fam)
        pasos = re.sub(r' ERROR al cargar.*$', '', pasos)
        pasos = re.sub(r'en la tabla \S+;', f'en la tabla {tabla};', pasos)
        pasos = re.sub(r' \(el portal lo declara.*?\)', '', pasos)
        con.execute('UPDATE descarga SET pasos=?, tabla=NULL, filas=NULL WHERE id=?', (pasos, did))
        n = procesar(con, did, P.CRUDOS / local, fmt, tabla, titulo, per)
        con.commit()
    print('revolcadas', len(q))


def cargar(con, item):
    pid = item['id']
    pkg = json.load(urllib.request.urlopen(urllib.request.Request(API + pid, headers={'User-Agent': P.UA}), timeout=120))['result']
    tc = pkg.get('temporal_coverage') or []
    cobertura = ', '.join(f"{c.get('start', '')[:10]}–{c.get('end', '')[:10]}" for c in tc) or None
    fid = P.fuente(con, f"dm:{pid.split('-')[0]}", pkg['title'], organismo=(pkg.get('organization') or {}).get('title') or 'Ayuntamiento de Madrid',
                   portal='datos.madrid.es', url_ficha=FICHA + pkg['name'], url_api=API + pkg['name'],
                   licencia=pkg.get('license_title'), acceso='api', seccion=item['seccion'], prioridad=item.get('prioridad', 'P1'),
                   frecuencia=(pkg.get('frequency') or '').rsplit('/', 1)[-1] or None, cobertura=cobertura, notas=item.get('notas'))
    hechos = {r[0] for r in con.execute('SELECT url FROM descarga WHERE fuente_id=?', (fid,))}
    grupos, docs = elegir(pkg['resources'])
    if item.get('filtro'):
        grupos = [g for g in grupos if re.search(item['filtro'], g[3], re.I)]
    sub = pkg['name'].split('-')[0]
    pasos_base = (f"1) Abrir {FICHA + pkg['name']} (o la API {API + pkg['name']}). "
                  "2) Descargar el recurso «{t}» en formato {f}. ")
    for titulo, x in docs:
        if x['url'] in hechos:
            continue
        P.descargar(con, fid, x['url'], formato='PDF', subcarpeta=sub, script=__file__,
                    pasos=pasos_base.format(t=titulo, f='PDF') + 'Documento del organismo que describe los campos.')
    total = 0
    for fam, per, fmt, titulo, x in sorted(grupos, key=lambda g: (g[0], g[1] or '')):
        if x['url'] in hechos:
            continue
        tabla = nombre_tabla(sub, fam)
        did, ruta = P.descargar(con, fid, x['url'], formato=fmt, subcarpeta=sub, script=__file__,
                                pasos=pasos_base.format(t=titulo, f=fmt) +
                                f"3) Cargado sin transformar en la tabla {tabla}; cada fila lleva _descarga_id={{id}}.")
        con.execute('UPDATE descarga SET pasos=replace(pasos,"{id}",?) WHERE id=?', (str(did), did))
        n = procesar(con, did, ruta, fmt, tabla, titulo, per)
        con.commit()
        total += n
        print(f'   {fmt:5} {n:>8} filas  {titulo[:70]}')
    return total


def main():
    ids = set(sys.argv[1:])
    con = P.abrir()
    if '--revolcar' in ids:
        revolcar_todo(con)
        return
    if '--errores' in ids:
        recargar_errores(con)
        return
    for item in CATALOGO:
        if ids and item['id'].split('-')[0] not in ids:
            continue
        if not ids and not item.get('carga', True):
            continue
        print('==', item['id'])
        try:
            print('   total', cargar(con, item))
        except Exception as e:
            print('   ! fallo', type(e).__name__, e)
        con.commit()


if __name__ == '__main__':
    main()
