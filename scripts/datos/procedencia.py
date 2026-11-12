"""Trazabilidad de cada dato de Ciudadano Madrid.

Tres piezas:
  fuente    -> el conjunto de datos, servicio o página de origen (organismo, URL de su ficha, licencia, acceso).
  descarga  -> cada fichero o página concreta obtenida: URL exacta, fecha, SHA-256, tamaño, copia archivada,
               script y commit que la procesó, pasos para repetirla.
  descarga_id en cada fila de las tablas de datos -> apunta a la descarga de la que sale.

Uso típico:
    con = abrir()
    fid = fuente(con, clave='dm:300375', nombre='Licencias de obras en vía pública', ...)
    did, ruta = descargar(con, fid, url, script=__file__, pasos='...')
"""
import datetime, hashlib, json, os, pathlib, sqlite3, subprocess, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
DB = pathlib.Path(os.environ.get('CM_DB', ROOT / 'ciudadano_madrid.sqlite'))
CRUDOS = pathlib.Path(os.environ.get('CM_CRUDOS', ROOT / 'crudos'))
UA = 'CiudadanoMadrid/1.0 (+https://github.com/bakero/ite-madrid)'

SCHEMA = """
CREATE TABLE IF NOT EXISTS fuente(
  id INTEGER PRIMARY KEY,
  clave TEXT UNIQUE NOT NULL,          -- p. ej. dm:300375 (datos.madrid.es), aeat:irpf-cp, kohesio:Q4633470
  nombre TEXT NOT NULL,
  organismo TEXT,
  portal TEXT,                         -- datos.madrid.es, transparencia.madrid.es, hacienda.gob.es...
  url_ficha TEXT,                      -- página pública donde cualquiera encuentra el conjunto
  url_api TEXT,                        -- llamada de API usada para listar sus ficheros, si la hay
  licencia TEXT,
  acceso TEXT CHECK(acceso IN ('api','descarga','extraccion','solicitud')),
  seccion TEXT,                        -- Ciudadano, Via publica, Servicios, Ayudas, Edificios, Transversal
  prioridad TEXT,
  frecuencia TEXT,
  cobertura TEXT,                      -- años que cubre según el organismo
  notas TEXT,
  alta TEXT
);
CREATE TABLE IF NOT EXISTS descarga(
  id INTEGER PRIMARY KEY,
  fuente_id INTEGER NOT NULL REFERENCES fuente(id),
  recurso TEXT,                        -- nombre del fichero o recurso en el portal
  url TEXT NOT NULL,                   -- URL exacta descargada
  fecha TEXT NOT NULL,                 -- fecha y hora UTC de la descarga
  sha256 TEXT,
  bytes INTEGER,
  formato TEXT,
  fichero_local TEXT,                  -- ruta relativa dentro de crudos/ (no se sube al repo)
  archivo_url TEXT,                    -- copia en web.archive.org
  archivo_estado TEXT,                 -- ok / pendiente / fallo: motivo
  release_url TEXT,                    -- copia en GitHub Releases, si se sube
  script TEXT,                         -- script que la descargó y procesó
  commit_git TEXT,
  pasos TEXT,                          -- cómo repetirla a mano, en texto
  filas INTEGER,                       -- filas cargadas en la BD desde esta descarga
  tabla TEXT                           -- tabla de la BD donde están sus filas
);
CREATE INDEX IF NOT EXISTS ix_descarga_fuente ON descarga(fuente_id);
CREATE VIEW IF NOT EXISTS v_procedencia AS
  SELECT d.id AS descarga_id, f.clave, f.nombre AS fuente, f.organismo, f.url_ficha, f.licencia, f.seccion,
         d.recurso, d.url, d.fecha, d.sha256, d.bytes, d.archivo_url, d.archivo_estado, d.release_url,
         d.script, d.commit_git, d.pasos, d.tabla, d.filas
  FROM descarga d JOIN fuente f ON f.id = d.fuente_id;
"""


def ahora():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def commit_actual():
    try:
        return subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', '--short', 'HEAD'], text=True).strip()
    except Exception:
        return None


def abrir(db=DB):
    con = sqlite3.connect(db)
    con.execute('PRAGMA journal_mode=WAL')
    con.executescript(SCHEMA)
    return con


def fuente(con, clave, nombre, **kw):
    """Crea o actualiza la ficha de una fuente y devuelve su id."""
    campos = ['organismo', 'portal', 'url_ficha', 'url_api', 'licencia', 'acceso', 'seccion', 'prioridad',
              'frecuencia', 'cobertura', 'notas']
    vals = {k: kw.get(k) for k in campos}
    fila = con.execute('SELECT id FROM fuente WHERE clave=?', (clave,)).fetchone()
    if fila:
        sets = ', '.join(f'{k}=COALESCE(?,{k})' for k in campos)
        con.execute(f'UPDATE fuente SET nombre=?, {sets} WHERE id=?', [nombre, *vals.values(), fila[0]])
        return fila[0]
    cur = con.execute(f'INSERT INTO fuente(clave,nombre,{",".join(campos)},alta) VALUES (?,?,{",".join("?" * len(campos))},?)',
                      [clave, nombre, *vals.values(), ahora()])
    return cur.lastrowid


def sha256_fichero(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def archivar(url):
    """Pide una copia a Internet Archive. Devuelve (url_archivo, estado)."""
    try:
        req = urllib.request.Request('https://web.archive.org/save/' + url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            loc = r.headers.get('Content-Location') or r.geturl()
            if loc and '/web/' in loc:
                return ('https://web.archive.org' + loc if loc.startswith('/') else loc), 'ok'
            return None, 'fallo: respuesta sin enlace de captura'
    except Exception as e:
        return None, f'pendiente: {type(e).__name__}: {str(e)[:120]}'


def descargar(con, fuente_id, url, recurso=None, formato=None, subcarpeta=None, script=None, pasos=None,
              archivar_copia=True, timeout=600):
    """Descarga url a crudos/, registra la descarga y devuelve (descarga_id, ruta_local)."""
    sub = CRUDOS / (subcarpeta or str(fuente_id))
    sub.mkdir(parents=True, exist_ok=True)
    nombre = recurso or url.rstrip('/').rsplit('/', 1)[-1] or 'recurso'
    ruta = sub / nombre
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(ruta, 'wb') as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    if archivar_copia and os.environ.get('CM_ARCHIVAR') == '1':
        arch_url, arch_estado = archivar(url)
    elif archivar_copia:
        arch_url, arch_estado = None, 'pendiente: web.archive.org no accesible desde el entorno de carga'
    else:
        arch_url, arch_estado = None, 'no solicitado'
    cur = con.execute(
        'INSERT INTO descarga(fuente_id,recurso,url,fecha,sha256,bytes,formato,fichero_local,archivo_url,archivo_estado,'
        'script,commit_git,pasos) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (fuente_id, nombre, url, ahora(), sha256_fichero(ruta), ruta.stat().st_size, formato,
         str(ruta.relative_to(CRUDOS)), arch_url, arch_estado,
         os.path.relpath(script, ROOT) if script else None, commit_actual(), pasos))
    return cur.lastrowid, ruta


def registrar_existente(con, fuente_id, url, ruta=None, recurso=None, fecha=None, formato=None, script=None,
                        pasos=None, tabla=None, filas=None):
    """Registra una descarga hecha antes de existir este esquema (sin volver a descargar)."""
    sha = byt = None
    if ruta and pathlib.Path(ruta).exists():
        sha, byt = sha256_fichero(ruta), pathlib.Path(ruta).stat().st_size
    cur = con.execute(
        'INSERT INTO descarga(fuente_id,recurso,url,fecha,sha256,bytes,formato,fichero_local,archivo_estado,script,'
        'commit_git,pasos,tabla,filas) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (fuente_id, recurso, url, fecha or ahora(), sha, byt, formato,
         os.path.relpath(ruta, ROOT) if ruta else None, 'pendiente: carga anterior al esquema',
         script, commit_actual(), pasos, tabla, filas))
    return cur.lastrowid


def cerrar_descarga(con, descarga_id, tabla, filas):
    con.execute('UPDATE descarga SET tabla=?, filas=? WHERE id=?', (tabla, filas, descarga_id))


def ficha_json(con, descarga_id):
    r = con.execute('SELECT * FROM v_procedencia WHERE descarga_id=?', (descarga_id,))
    cols = [c[0] for c in r.description]
    fila = r.fetchone()
    return json.dumps(dict(zip(cols, fila)), ensure_ascii=False) if fila else None
