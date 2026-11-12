"""Capa limpia de Ciudadano Madrid: tablas cm_* listas para la web, construidas desde las tablas ds_* sin transformar.

Cada fila de una tabla cm_* conserva _descarga_id: la procedencia llega intacta hasta la web (v_procedencia).
Lo que hace esta capa, y nada más:
  - Une las variantes de columnas de cada año (el portal cambia nombres: tipo_obr / tipo_obra / tipo_de_obra…).
  - Convierte importes y cantidades a número (formatos «1.234,56», «1234.56», «14.846.541.14», «491.799,79€»).
  - Asigna código de distrito (201–221 en presupuesto; 1–21 en la web) a partir del texto del órgano o del distrito.
  - Marca las personas físicas (NIF que empieza por cifra o por X/Y/Z) para que la web no muestre su nombre.
Regla de números ambiguos: un único punto seguido de 3 cifras («23.410») se lee como separador de miles.

Uso: python3 scripts/datos/capa_limpia.py
"""
import pathlib, re, sqlite3, sys, unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P

DISTRITOS = ['CENTRO', 'ARGANZUELA', 'RETIRO', 'SALAMANCA', 'CHAMARTIN', 'TETUAN', 'CHAMBERI', 'FUENCARRAL-EL PARDO',
             'MONCLOA-ARAVACA', 'LATINA', 'CARABANCHEL', 'USERA', 'PUENTE DE VALLECAS', 'MORATALAZ', 'CIUDAD LINEAL',
             'HORTALEZA', 'VILLAVERDE', 'VILLA DE VALLECAS', 'VICALVARO', 'SAN BLAS-CANILLEJAS', 'BARAJAS']


NOMBRES = ['Centro', 'Arganzuela', 'Retiro', 'Salamanca', 'Chamartín', 'Tetuán', 'Chamberí', 'Fuencarral-El Pardo',
           'Moncloa-Aravaca', 'Latina', 'Carabanchel', 'Usera', 'Puente de Vallecas', 'Moratalaz', 'Ciudad Lineal',
           'Hortaleza', 'Villaverde', 'Villa de Vallecas', 'Vicálvaro', 'San Blas-Canillejas', 'Barajas']


def plano(s):
    s = unicodedata.normalize('NFD', str(s or '').upper())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s*-\s*', '-', re.sub(r'\s+', ' ', s)).strip()


CLAVES = sorted([(plano(d), i + 1) for i, d in enumerate(DISTRITOS)] +
                [('FUENCARRAL', 8), ('MONCLOA', 9), ('SAN BLAS', 20), ('CANILLEJAS', 20)], key=lambda x: -len(x[0]))


def num(x):
    if x is None:
        return None
    s = re.sub(r"[^0-9,.+-]", '', str(x))          # quita €, espacios, comillas y el «?» de los CSV con el € mal codificado
    if not s or s in ('-', '.', ','):
        return None
    neg = s.startswith('-')
    s = s.lstrip('+-')
    if ',' in s and '.' in s:
        dec = ',' if s.rfind(',') > s.rfind('.') else '.'
        s = s.replace('.' if dec == ',' else ',', '').replace(dec, '.')
    elif ',' in s:
        s = s.replace('.', '').replace(',', '.') if s.count(',') == 1 else s.replace(',', '')
    elif s.count('.') > 1:
        partes = s.split('.')
        s = ''.join(partes[:-1]) + ('.' + partes[-1] if len(partes[-1]) == 2 else partes[-1])
    elif '.' in s and re.fullmatch(r'\d{1,3}\.\d{3}', s):
        s = s.replace('.', '')
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def coord(x):
    """Coordenadas en grados decimales: el punto (o la coma) siempre es decimal («40.621» = 40,621)."""
    s = re.sub(r"[\s']", '', str(x or '')).replace(',', '.')
    try:
        v = float(s)
    except ValueError:
        return None
    return v if -180 <= v <= 180 else None


def cod_distrito(*textos):
    """Código 1–21 del distrito citado en el texto; acepta códigos 201–221 y 1–21."""
    for t in textos:
        if t is None:
            continue
        s = str(t).strip()
        if re.fullmatch(r'2(0[1-9]|1\d|2[01])', s):
            return int(s) - 200
        if re.fullmatch(r'0?([1-9]|1\d|2[01])', s):
            return int(s)
        p = plano(s)
        for k, c in CLAVES:
            if re.search(r'(^|[^A-Z])' + re.escape(k) + r'([^A-Z]|$)', p):
                return c
    return None


ADJ = re.compile(r'^\s*\(([A-Z0-9-]{8,12})\)\s*(.*?)(?:\s+PYME:\s*(SI|SÍ|NO))?\s*$', re.I)


def adj_nif(texto, nif):
    """El registro de 2021 en adelante trae «(A28541639) FCC MEDIO AMBIENTE, S.A. PYME: NO» en una sola columna."""
    m = ADJ.match(str(texto or ''))
    if nif and str(nif).strip():
        return re.sub(r'[^0-9A-Z]', '', str(nif).upper())
    return m.group(1).replace('-', '').upper() if m else None


def adj_nombre(texto):
    m = ADJ.match(str(texto or ''))
    return (m.group(2).strip() if m else str(texto or '').strip()) or None


TIPOS = {'CL': 'CALLE', 'C': 'CALLE', 'CALL': 'CALLE', 'AV': 'AVENIDA', 'AVDA': 'AVENIDA', 'AVD': 'AVENIDA', 'PS': 'PASEO', 'PZ': 'PLAZA',
         'PZA': 'PLAZA', 'GL': 'GLORIETA', 'CTRA': 'CARRETERA', 'CR': 'CARRETERA', 'RD': 'RONDA', 'TR': 'TRAVESIA', 'CM': 'CAMINO'}


def via_clave(via):
    """Clave para agrupar la misma calle escrita de varias formas («AVENIDA DE LA ALBUFERA» = «AVENIDA ALBUFERA»)."""
    p = plano(via).replace('.', ' ').replace('/', ' ')
    pal = p.split()
    if pal and pal[0] in TIPOS:
        pal[0] = TIPOS[pal[0]]
    pal = [w for w in pal if w not in ('DE', 'DEL', 'LA', 'LAS', 'LOS', 'EL', 'D', 'L')]
    return ' '.join(pal) or None


def es_persona_fisica(nif):
    s = re.sub(r'[^0-9A-Z]', '', str(nif or '').upper())
    return 1 if re.match(r'^([0-9]{8}[A-Z]|[XYZ][0-9]{7}[A-Z])$', s) else 0


def columnas(con, t):
    return {r[1] for r in con.execute(f'PRAGMA table_info("{t}")')}


def co(con, t, *cands):
    """COALESCE de las columnas candidatas que existan en la tabla t (vacío = nulo)."""
    hay = [c for c in cands if c in columnas(con, t)]
    if not hay:
        return 'NULL'
    return 'COALESCE(' + ','.join(f"NULLIF(TRIM(\"{c}\"),'')" for c in hay) + ')' if len(hay) > 1 else f"NULLIF(TRIM(\"{hay[0]}\"),'')"


def tabla(con, nombre, sql_select, descripcion):
    con.execute(f'DROP TABLE IF EXISTS "{nombre}"')
    con.execute(f'CREATE TABLE "{nombre}" AS {sql_select}')
    n = con.execute(f'SELECT count(*) FROM "{nombre}"').fetchone()[0]
    con.execute('INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES (?,?,?,?)', (nombre, descripcion, n, sql_select))
    print(f'{nombre:32} {n:>9}')
    return n


def deuda_pmp(con):
    """Deuda (filas = conceptos, columnas = 31/12 de cada año) a formato largo; periodo medio de pago mensual."""
    D = 'ds_300113_deuda'
    cols = [r[1] for r in con.execute(f'PRAGMA table_info("{D}")') if re.match(r'\d{4}_12_31', r[1])]
    con.execute('DROP TABLE IF EXISTS cm_deuda')
    con.execute('CREATE TABLE cm_deuda(anio INTEGER, concepto TEXT, importe REAL, _descarga_id INTEGER)')
    for concepto, did, *vals in con.execute(f'SELECT prestamos_a_largo_plazo_por_entidades_financieras, _descarga_id, {",".join(chr(34)+c+chr(34) for c in cols)} FROM "{D}"').fetchall():
        if concepto and concepto.strip().upper() in ('TOTAL DEUDA LARGO Y CORTO PLAZO', 'TOTAL DEUDA PDE', 'TOTAL DEUDA LARGO PLAZO', 'TOTAL DEUDA CORTO PLAZO', 'AMORTIZACIONES LARGO PLAZO', 'NUEVA DEUDA LARGO PLAZO CONCERTADA'):
            for c, v in zip(cols, vals):
                if num(v) is not None:
                    con.execute('INSERT INTO cm_deuda VALUES (?,?,?,?)', (int(c[:4]), concepto.strip(), num(v), did))
    con.execute('INSERT OR REPLACE INTO cm_tablas VALUES (?,?,?,?)', ('cm_deuda', 'Deuda del Ayuntamiento a 31 de diciembre (total y PDE) y nueva deuda/amortizaciones',
                con.execute('SELECT count(*) FROM cm_deuda').fetchone()[0], D))
    M = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
    con.execute('DROP TABLE IF EXISTS cm_pmp')
    con.execute('CREATE TABLE cm_pmp(anio INTEGER, mes INTEGER, dias REAL, _descarga_id INTEGER)')
    for mes, anio, dias, did in con.execute('SELECT meses, anos, pmp_global_sec_2010_dias, _descarga_id FROM ds_900045_periodo_medio_de_pago_a_proveedores'):
        if mes and anio and M.get(mes.strip().lower()):
            con.execute('INSERT INTO cm_pmp VALUES (?,?,?,?)', (int(float(anio)), M[mes.strip().lower()], num(dias), did))
    con.execute('INSERT OR REPLACE INTO cm_tablas VALUES (?,?,?,?)', ('cm_pmp', 'Periodo medio de pago a proveedores (días), mensual',
                con.execute('SELECT count(*) FROM cm_pmp').fetchone()[0], 'ds_900045_periodo_medio_de_pago_a_proveedores'))


def main():
    con = P.abrir()
    for f, k in [(num, 'num'), (cod_distrito, 'cod_distrito'), (es_persona_fisica, 'es_pf'), (coord, 'coord'), (adj_nif, 'adj_nif'), (adj_nombre, 'adj_nombre'), (via_clave, 'via_clave')]:
        con.create_function(k, -1 if k == 'cod_distrito' else (2 if k == 'adj_nif' else 1), f, deterministic=True)
    con.execute('CREATE TABLE IF NOT EXISTS cm_tablas(tabla TEXT PRIMARY KEY, descripcion TEXT, filas INTEGER, origen TEXT)')
    con.execute('DROP TABLE IF EXISTS cm_distrito')
    con.execute('CREATE TABLE cm_distrito(cod INTEGER PRIMARY KEY, nombre TEXT, seccion_presupuesto INTEGER)')
    con.executemany('INSERT INTO cm_distrito VALUES (?,?,?)', [(i + 1, NOMBRES[i], 201 + i) for i, d in enumerate(DISTRITOS)])

    # ---------- Transversal: población por distrito y año (1 de enero) ----------
    t = 'ds_300557_poblacion_por_distrito_y_barrio_a_1'
    tabla(con, 'cm_poblacion', f'''
        SELECT CAST(substr(fecha, -4) AS INTEGER) AS anio, CAST(cod_distrito AS INTEGER) AS cod_distrito,
               CAST(cod_barrio AS INTEGER) AS cod_barrio, barrio, num(num_personas) AS personas, _descarga_id
        FROM "{t}" WHERE cod_distrito <> '' ''', 'Población a 1 de enero por barrio (padrón)')

    # ---------- Ciudadano: gasto, ingresos e inversión ----------
    g = 'ds_211496_gastos'
    tabla(con, 'cm_gasto', f'''
        SELECT CAST(substr(_periodo,1,4) AS INTEGER) AS anio, printf('%03d', CAST(centro AS INTEGER)) AS centro, descripcion_centro, seccion, descripcion_seccion,
               cod_distrito(CASE WHEN descripcion_seccion LIKE 'DISTRITO%' THEN seccion END) AS cod_distrito,
               programa, descripcion_programa, substr(programa,1,1) AS area_gasto, substr(programa,1,2) AS politica_gasto,
               capitulo, descripcion_capitulo, economico, descripcion_economico,
               num(cred_inicial) AS credito_inicial, num(c_definitivo) AS credito_definitivo, num(obl_reconoc) AS obligaciones_reconocidas,
               _descarga_id
        FROM "{g}" ''', 'Ejecución anual del presupuesto de gastos (Ayuntamiento y organismos autónomos, sin consolidar)')
    i = 'ds_211496_ingresos'
    tabla(con, 'cm_ingresos', f'''
        SELECT CAST(substr(_periodo,1,4) AS INTEGER) AS anio, printf('%03d', CAST(centro AS INTEGER)) AS centro, descripcion_centro, capitulo, descripcion_capitulo,
               economico, descripcion_economico, num(prev_inicial) AS prevision_inicial, num(prev_definitiv) AS prevision_definitiva,
               num(d_recon_netos) AS derechos_reconocidos, num(recaudado) AS recaudado, _descarga_id
        FROM "{i}" ''', 'Ejecución anual del presupuesto de ingresos (impuestos, tasas, transferencias…)')
    v = 'ds_211496_inversiones'
    tabla(con, 'cm_inversion_proyecto', f'''
        SELECT CAST(substr(_periodo,1,4) AS INTEGER) AS anio, definicion_proyecto AS proyecto, titulo, seccion, programa, subconcepto,
               distrito AS distrito_presupuesto, texto_distrito, cod_distrito(distrito) AS cod_distrito,
               {co(con, v, 'descripcion_linea_de_inversion')} AS linea, {co(con, v, 'descripcion_subline_de_inversion', 'descripcion_sublinea_de_inversion')} AS sublinea,
               num(cred_inicial) AS credito_inicial, num(c_definitivo) AS credito_definitivo, num(obl_reconoc) AS obligaciones_reconocidas,
               _descarga_id
        FROM "{v}" ''', 'Proyectos de inversión con su distrito (998 = varios distritos; 999 = no territorializable)')
    tabla(con, 'cm_distrito_anio', '''
        WITH junta AS (SELECT anio, cod_distrito, sum(credito_inicial) ci, sum(credito_definitivo) cd, sum(obligaciones_reconocidas) orr
                       FROM cm_gasto WHERE cod_distrito IS NOT NULL GROUP BY 1,2),
             inv AS (SELECT anio, cod_distrito, sum(credito_definitivo) icd, sum(obligaciones_reconocidas) ior
                     FROM cm_inversion_proyecto WHERE cod_distrito BETWEEN 1 AND 21 GROUP BY 1,2),
             pob AS (SELECT anio, cod_distrito, sum(personas) personas FROM cm_poblacion GROUP BY 1,2)
        SELECT j.anio, j.cod_distrito, d.nombre AS distrito, p.personas,
               j.ci AS junta_credito_inicial, j.cd AS junta_credito_definitivo, j.orr AS junta_gastado,
               j.cd - j.orr AS junta_no_gastado, round(100.0 * j.orr / NULLIF(j.cd,0), 1) AS junta_pct_ejecucion,
               i.icd AS inversion_presupuestada, i.ior AS inversion_ejecutada,
               round(j.orr / NULLIF(p.personas,0), 2) AS junta_gastado_por_habitante,
               round(i.ior / NULLIF(p.personas,0), 2) AS inversion_por_habitante
        FROM junta j JOIN cm_distrito d ON d.cod = j.cod_distrito
        LEFT JOIN inv i ON i.anio = j.anio AND i.cod_distrito = j.cod_distrito
        LEFT JOIN pob p ON p.anio = j.anio AND p.cod_distrito = j.cod_distrito''',
          'Por distrito y año: gasto de la Junta (presupuestado, gastado, no gastado), inversión territorializada y euros por habitante. '
          'Agregado de cm_gasto, cm_inversion_proyecto y cm_poblacion (la procedencia está en esas tablas).')

    E = 'ds_211496_eliminaciones_de_gastos'
    tabla(con, 'cm_ciudad_anio', f'''
        WITH g AS (SELECT anio, sum(credito_inicial) ci, sum(credito_definitivo) cd, sum(obligaciones_reconocidas) orr
                   FROM cm_gasto WHERE CAST(capitulo AS INTEGER) BETWEEN 1 AND 7 GROUP BY 1),
             e AS (SELECT CAST(substr(_periodo,1,4) AS INTEGER) anio, sum(num(COALESCE(NULLIF(cred_inicial,''), importe))) ci,
                          sum(num(COALESCE(NULLIF(c_definitivo,''), importe))) cd, sum(num(COALESCE(NULLIF(obl_reconoc,''), importe))) orr,
                          max(NULLIF(obl_reconoc,'') IS NULL) aprox FROM "{E}" GROUP BY 1),
             i AS (SELECT anio, sum(derechos_reconocidos) dr, sum(recaudado) rec FROM cm_ingresos GROUP BY 1),
             p AS (SELECT anio, sum(personas) personas FROM cm_poblacion GROUP BY 1)
        SELECT g.anio, p.personas, g.ci - COALESCE(e.ci,0) AS gasto_no_financiero_inicial, g.cd - COALESCE(e.cd,0) AS gasto_no_financiero_definitivo,
               g.orr - COALESCE(e.orr,0) AS gasto_no_financiero_ejecutado,
               round(100.0 * (g.orr - COALESCE(e.orr,0)) / NULLIF(g.cd - COALESCE(e.cd,0),0), 1) AS pct_ejecucion,
               round((g.orr - COALESCE(e.orr,0)) / NULLIF(p.personas,0), 2) AS gasto_por_habitante,
               COALESCE(e.aprox,0) AS eliminacion_aproximada, i.dr AS ingresos_derechos_reconocidos_sin_consolidar, i.rec AS ingresos_recaudados_sin_consolidar
        FROM g LEFT JOIN e ON e.anio = g.anio LEFT JOIN i ON i.anio = g.anio LEFT JOIN p ON p.anio = g.anio''',
          'Ciudad por año: gasto no financiero (capítulos 1–7) consolidado Ayuntamiento + organismos autónomos '
          '(se restan las eliminaciones internas; hasta 2022 el portal solo da el importe presupuestado de las eliminaciones: eliminacion_aproximada=1). Comprobado: 2023 = 5.326 M€ y 2025 = 5.931 M€, como publica el Ayuntamiento.')

    # ---------- Servicios: contratos (registro + menores) ----------
    partes = []
    for t, tipo in [('ds_216876_contratos_inscritos_en_el_registro_de_contratos', 'registro'),
                    ('ds_216876_contratos_formalizados_inscritos_en_el_registro_de_cont', 'registro'),
                    ('ds_216876_contratos_basados_en_un_acuerdo_marco_inscritos_en_el_r', 'acuerdo marco'),
                    ('ds_216876_contratos_basados_en_un_acuerdo_marco_o_especificos_der', 'acuerdo marco'),
                    ('ds_216876_contratos_derivados_de_procedimientos_de_homologacion', 'homologación'),
                    ('ds_300253_contratos_menores', 'menor')]:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone():
            continue
        organo = co(con, t, 'centro_seccion', 'organismo', 'organo_de_contratacion', 'org_contratacion', 'seccion', 'descripcion_centro', 'descripcion')
        partes.append(f'''
        SELECT '{tipo}' AS tipo_registro, CAST(substr(COALESCE({co(con, t, 'ano', 'a_o')}, _periodo),1,4) AS INTEGER) AS anio,
               {organo} AS organo,
               cod_distrito({co(con, t, 'centro_seccion', 'organismo', 'seccion', 'organo_de_contratacion', 'org_contratacion', 'descripcion_centro', 'descripcion', 'centro')}) AS cod_distrito,
               {co(con, t, 'objeto_del_contrato', 'descripcion_contrato', 'objeto_derivado', 'titulo_del_expediente')} AS objeto,
               {co(con, t, 'tipo_de_contrato', 'tipo_contrato', 'tipo_de_expediente', 't_expediente')} AS tipo_contrato,
               {co(con, t, 'procedimiento_de_adjudicacion', 'procedimiento_adjudicacion')} AS procedimiento,
               adj_nombre({co(con, t, 'razon_social_adjudicatario', 'adjudicatario', 'nombre_razon_social', 'contratista', 'tercero')}) AS adjudicatario,
               adj_nif({co(con, t, 'razon_social_adjudicatario', 'adjudicatario', 'nombre_razon_social', 'contratista', 'tercero')},
                       {co(con, t, 'nif_adjudicatario', 'nif_cif_adjudicatario', 'n_i_f', 'nif', 'cif')}) AS nif,
               num({co(con, t, 'importe_adjudicacion_iva_inc', 'importe_adjudicacion_iva_incluido', 'importe_adjudicacion', 'importe')}) AS importe_iva_inc,
               {co(con, t, 'fecha_de_adjudicacion', 'fecha_adjudicacion', 'fecha_aprobacion', 'fech_apro', 'fecha_formalizacion', 'fe_contab')} AS fecha,
               {co(con, t, 'n_de_expediente', 'numero_expediente', 'n_expediente', 'n_exped_adm')} AS expediente,
               _descarga_id
        FROM "{t}"''')
    tabla(con, 'cm_contrato', ' UNION ALL '.join(partes).replace('upper(replace(replace(NULL', 'upper(replace(replace(NULL'),
          'Contratos del Registro de Contratos (2015–) y contratos menores (2015–), con órgano, distrito, adjudicatario e importe')
    con.execute("ALTER TABLE cm_contrato ADD COLUMN persona_fisica INTEGER")
    con.execute("UPDATE cm_contrato SET persona_fisica = es_pf(nif)")

    # ---------- Vía pública ----------
    L = 'ds_300375_relacion_de_licencias_de_obras_en_via_publica'
    tabla(con, 'cm_obra_licencia', f'''
        SELECT CAST(ano AS INTEGER) AS anio, upper(mes) AS mes, direccion,
               trim(CASE WHEN instr(direccion, ',') > 0 THEN substr(direccion, 1, instr(direccion, ',') - 1)
                         ELSE rtrim(direccion, '0123456789 ') END) AS via,
               via_clave(trim(CASE WHEN instr(direccion, ',') > 0 THEN substr(direccion, 1, instr(direccion, ',') - 1)
                         ELSE rtrim(direccion, '0123456789 ') END)) AS via_clave,
               cod_distrito({co(con, L, 'codigo_distrito', 'codigo_de_distrito')}, distrito) AS cod_distrito,
               CASE WHEN upper({co(con, L, 'tipo_obr', 'tipo_obra', 'tipo_de_obra')}) LIKE 'AVER%' THEN 'Avería urgente'
                    WHEN upper({co(con, L, 'tipo_obr', 'tipo_obra', 'tipo_de_obra')}) LIKE '%CANALIZ%' THEN 'Canalización'
                    WHEN upper({co(con, L, 'tipo_obr', 'tipo_obra', 'tipo_de_obra')}) LIKE '%ALCANTAR%' OR upper({co(con, L, 'tipo_obr', 'tipo_obra', 'tipo_de_obra')}) LIKE 'SANEA%' THEN 'Alcantarillado'
                    WHEN upper({co(con, L, 'tipo_obr', 'tipo_obra', 'tipo_de_obra')}) LIKE 'CALA%' THEN 'Cala programada'
                    WHEN upper({co(con, L, 'tipo_obr', 'tipo_obra', 'tipo_de_obra')}) LIKE 'OBRA%MUNICIPAL%' THEN 'Obra municipal'
                    ELSE 'Otro (' || {co(con, L, 'tipo_obr', 'tipo_obra', 'tipo_de_obra')} || ')' END AS tipo_obra,
               _descarga_id
        FROM "{L}" ''', 'Licencias de obras en vía pública finalizadas (calas, canalizaciones, alcantarillado, averías), desde abril de 2017')
    I = 'ds_300533_inversiones_principales_equipamientos_obras_e_infraestr'
    tabla(con, 'cm_inversion_principal', f'''
        SELECT CAST(substr(_periodo,1,4) AS INTEGER) AS anio_datos, codigo_pep, denominacion, descripcion_seccion AS gestor,
               cod_distrito(distrito, denominacion_distrito) AS cod_distrito, direccion,
               coord(latitud) AS lat, coord(longitud) AS lng,
               denominacion_linea_de_inversion AS linea, estado, ano_inicio, {co(con, I, 'ano_de_finalizacion', 'ano_de_finalizacion_previsto')} AS ano_fin,
               num(presupuesto_total_previsto) AS presupuesto_total, num(gasto_ejecutado) AS gasto_ejecutado, url_fotografia, _descarga_id
        FROM "{I}" ''', 'Inversiones principales (equipamientos, obras, infraestructuras) con coordenadas e importes, 2020–2026')
    O = 'ds_300538_obras_publicas_planificadas_y_en_ejecucion'
    tabla(con, 'cm_obra_publica', f'''
        SELECT * , cod_distrito({co(con, O, 'distrito_s')}) AS cod_distrito FROM "{O}" ''',
          'Obras públicas planificadas y en ejecución (columnas originales del portal + cod_distrito)')

    # ---------- Ayudas y convenios ----------
    A = 'ds_254934_subvenciones_y_ayudas_al_ayuntamiento_de_madrid'
    tabla(con, 'cm_ayuda_recibida', f'''
        SELECT tipo_administracion_concedente AS nivel, administracion_concedente, organo_concedente, codigo_bdns, convocatoria,
               url_bases_reguladoras, fecha_de_concesion AS fecha, CAST(substr(fecha_de_concesion,-4) AS INTEGER) AS anio,
               beneficiario, num(importe) AS importe, instrumento, _descarga_id
        FROM "{A}" ''', 'Subvenciones y ayudas que otras administraciones conceden al Ayuntamiento, sus organismos y empresas')
    bdns_completar(con)
    F = 'ds_369053_fondos_europeos'
    tabla(con, 'cm_fondo_europeo', f'''
        SELECT subproyecto, denominacion, fecha_solicitud, fecha_resolucion, CAST(substr(fecha_resolucion,-4) AS INTEGER) AS anio,
               num(importe_concedido) AS importe_concedido, num(importe_total_coste_real_con_iva) AS coste_real_iva,
               fecha_finalizacion, tipo_de_subvencion, territorio, cod_distrito(territorio) AS cod_distrito, nombre_beneficiario, url, _descarga_id
        FROM "{F}" ''', 'Fondos europeos obtenidos (Mecanismo de Recuperación y FEDER) por subproyecto')
    C = 'ds_300295_convenios_inscritos'
    tabla(con, 'cm_convenio', f'''
        SELECT numero_de_convenio, substr(fecha_de_suscripcion,1,10) AS fecha_suscripcion, CAST(substr(fecha_de_suscripcion,1,4) AS INTEGER) AS anio,
               area_de_gobierno_o_distrito AS organo, cod_distrito(area_de_gobierno_o_distrito) AS cod_distrito, titulo_objeto,
               substr(inicio_de_vigencia,1,10) AS inicio, substr(fin_de_vigencia,1,10) AS fin, otras_entidades_firmantes,
               num(obligaciones_economicas_ayuntamiento) AS obligacion_ayuntamiento, num(obligaciones_economicas_otras_entidades) AS obligacion_otras,
               documento_del_convenio, _descarga_id
        FROM "{C}" ''', 'Convenios inscritos desde noviembre de 2018 (con administraciones, universidades y entidades privadas)')

    # ---------- Tanda 2 (12/11/2026 tarde) ----------
    # Pagos reales a terceros (obligaciones reconocidas por perceptor). Personas físicas: sin nombre.
    partes = []
    for t, org in [('ds_300272_pagos_a_terceros_areas_y_distritos', 'Ayuntamiento'), ('ds_300272_pagos_a_terceros_organismos_autonomos', 'Organismo autónomo')]:
        partes.append(f"""SELECT CAST(substr(COALESCE(NULLIF(ejercicio,''),_periodo),1,4) AS INTEGER) AS anio, '{org}' AS tipo_centro, centro_gestor,
               seccion, cod_distrito(CASE WHEN seccion BETWEEN '201' AND '221' THEN seccion END) AS cod_distrito,
               programa, substr(programa,1,2) AS politica_gasto, subconcepto,
               upper(replace(n_ident_fis_1,' ','')) AS nif, nombre_del_tercero AS tercero,
               CASE WHEN significado LIKE '%sica%' AND significado NOT LIKE '%Jur%' THEN 1 ELSE es_pf(n_ident_fis_1) END AS persona_fisica,
               significado AS tipo_tercero, num(importe_mon_encp) AS importe, texto AS concepto,
               COALESCE(NULLIF(expediente_administrativo,''), numero_del_expediente) AS expediente, _descarga_id FROM "{t}" """)
    tabla(con, 'cm_pago', ' UNION ALL '.join(partes), 'Pagos a terceros: lo que el Ayuntamiento ha reconocido pagar a cada proveedor o perceptor (2011–2025)')

    # Presupuesto aprobado del año en curso y proyecto del siguiente, por sección y programa
    partes = []
    for t, col, anio, est in [('ds_300666_gastos', 'presupuesto_2026', 2026, 'aprobado'),
                              ('ds_128004_proyecto_de_presupuesto_general_gastos', 'sumadeimporte', 2027, 'proyecto')]:
        partes.append(f"""SELECT {anio} AS anio, '{est}' AS estado, printf('%03d', CAST(centro AS INTEGER)) AS centro, seccion, descripcion_seccion,
               cod_distrito(CASE WHEN descripcion_seccion LIKE 'DISTRITO%' THEN seccion END) AS cod_distrito,
               programa, descripcion_programa, substr(programa,1,2) AS politica_gasto, capitulo, num({col}) AS importe, _descarga_id FROM "{t}" """)
    tabla(con, 'cm_presupuesto_futuro', ' UNION ALL '.join(partes), 'Presupuesto aprobado 2026 y proyecto de presupuesto 2027 (gastos) por sección y programa')

    # Ayudas sociales a vecinos (sin datos de beneficiarios)
    S = 'ds_300350_ayudas_sociales'
    tabla(con, 'cm_ayuda_social', f"""
        SELECT CAST(substr(_periodo,1,4) AS INTEGER) AS anio,
               cod_distrito({co(con, S, 'descripcion_organo_gestor', 'area_title')}) AS cod_distrito,
               {co(con, S, 'descripcion_organo_gestor', 'area_title')} AS organo,
               {co(con, S, 'objeto_ayuda', 'title', 'linea_financiacion_title')} AS objeto,
               num({co(con, S, 'importe_concedido', 'importe')}) AS importe, _descarga_id FROM "{S}" """,
          'Ayudas sociales concedidas por el Ayuntamiento y las Juntas (sin datos personales de beneficiarios)')

    # Listas de espera de servicios a mayores: solo campos no identificativos
    partes = []
    for t, srv in [('ds_300619_lista_de_espera_de_apartamentos_municipales_para_person', 'Apartamentos municipales para mayores'),
                   ('ds_300620_lista_de_espera_de_residencia_municipal_para_personas_m', 'Residencia municipal (Alzheimer y otras demencias)'),
                   ('ds_300621_lista_de_espera_de_residencia_municipal_para_personas_m', 'Residencia municipal (deterioro físico)'),
                   ('ds_300622_listas_de_espera_de_centros_de_dia_para_personas_mayore', 'Centro de día (Alzheimer)'),
                   ('ds_300623_lista_de_espera_de_centros_de_dia_para_personas_mayores', 'Centro de día (deterioro físico)')]:
        if con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone():
            partes.append(f"""SELECT '{srv}' AS servicio, CAST(distrito_cod AS INTEGER) AS cod_distrito, tramo_edad, sexo,
                   substr(fecha_de_entrada,1,10) AS fecha_entrada, fx_carga AS fecha_datos,
                   CAST(julianday(fx_carga) - julianday(substr(fecha_de_entrada,1,10)) AS INTEGER) AS dias_espera, _descarga_id FROM "{t}" """)
    tabla(con, 'cm_lista_espera', ' UNION ALL '.join(partes), 'Listas de espera de servicios municipales para mayores (sin DNI ni iniciales)')

    # Operación Asfalto (Geoportal)
    A2 = 'ds_sigma_operacion_asfalto'
    if con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (A2,)).fetchone():
        dist = co(con, A2, 'distrito_txt', 'distrito_t', 'distrito_nombre', 'distrito')
        tabla(con, 'cm_asfalto', f"""
            SELECT CAST(anio AS INTEGER) AS anio, {co(con, A2, 'calleactuacion', 'calleactua', 'calle')} AS calle,
                   {co(con, A2, 'tramocalle', 'areaactuacion')} AS tramo,
                   cod_distrito(substr(replace(replace({dist},'.',' '),'  ',' '),4), {dist}) AS cod_distrito,
                   {co(con, A2, 'estado')} AS estado, {co(con, A2, 'fecha_ini', 'fecha_ini_eje', 'f_inicio', 'fecha_inicio')} AS inicio,
                   {co(con, A2, 'fecha_fin', 'fecha_fin_eje', 'f_fin', 'fecha_final')} AS fin, num({co(con, A2, 'sup_m2')}) AS superficie_m2,
                   num({co(con, A2, 'precio_aprox')}) AS precio_aprox, num({co(con, A2, 'ton')}) AS toneladas,
                   coord(lat) AS lat, coord(lng) AS lng, _descarga_id FROM "{A2}" """,
              'Operación Asfalto 2020–2026: tramos asfaltados (Geoportal); 2025 con precio aproximado')
    deuda_pmp(con)
    contexto_comunidad(con)
    con.commit()


def bdns_completar(con):
    """Añade a cm_ayuda_recibida las concesiones de la BDNS que no estén ya (misma convocatoria, fecha e importe)."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name='ds_bdns_concesiones'").fetchone():
        return
    n0 = con.execute('SELECT count(*) FROM cm_ayuda_recibida').fetchone()[0]
    con.execute('''INSERT INTO cm_ayuda_recibida
        SELECT CASE nivel1 WHEN 'AUTONOMICA' THEN 'Autonómica' WHEN 'ESTADO' THEN 'Estatal' WHEN 'LOCAL' THEN 'Local' ELSE nivel1 END,
               nivel2, nivel3, numeroconvocatoria, convocatoria, urlbr,
               substr(fechaconcesion,9,2)||'/'||substr(fechaconcesion,6,2)||'/'||substr(fechaconcesion,1,4), CAST(substr(fechaconcesion,1,4) AS INTEGER),
               trim(substr(beneficiario, instr(beneficiario,' ')+1)), num(importe), trim(instrumento), b._descarga_id
        FROM ds_bdns_concesiones b
        WHERE NOT EXISTS (SELECT 1 FROM cm_ayuda_recibida a WHERE a.codigo_bdns = b.numeroconvocatoria
                          AND a.fecha = substr(fechaconcesion,9,2)||'/'||substr(fechaconcesion,6,2)||'/'||substr(fechaconcesion,1,4)
                          AND abs(coalesce(a.importe,0) - num(b.importe)) < 1)''')
    print('   BDNS añade', con.execute('SELECT count(*) FROM cm_ayuda_recibida').fetchone()[0] - n0, 'concesiones nuevas')


def contexto_comunidad(con):
    """Indicadores por distrito publicados por la Comunidad de Madrid (el distrito va dentro del texto «concepto»)."""
    T = {'P': 'ds_cm_pensiones_pensiones_contributivas_pensionistas_por_distritos_y_se',
         'E': 'ds_cm_empresas_colectivo_empresarial_base_unidades_productivas_y_ocupa',
         'K': 'ds_cm_catastro_catastro_inmobiliario_inmuebles_por_distrito_y_uso_csv'}
    if not all(con.execute('SELECT 1 FROM sqlite_master WHERE name=?', (t,)).fetchone() for t in T.values()):
        return
    tabla(con, 'cm_distrito_contexto', f'''
        SELECT CAST(ano AS INTEGER) AS anio, cod_distrito(replace(concepto, ' del municipio de Madrid', '')) AS cod_distrito,
               'pensionistas' AS indicador, sexo AS detalle, num(valor) AS valor, _descarga_id FROM "{T['P']}"
         WHERE concepto LIKE '%distrito de %' AND concepto NOT LIKE '%no consta%'
        UNION ALL
        SELECT CAST(ano AS INTEGER), cod_distrito(replace(concepto, ' del municipio de Madrid', '')),
               CASE medida WHEN 'Ocupados' THEN 'ocupados' ELSE 'unidades_productivas' END, estrato_empleo, num(valor), _descarga_id FROM "{T['E']}"
        UNION ALL
        SELECT CAST(ano AS INTEGER), cod_distrito(replace(concepto, ' del municipio de Madrid', '')), 'inmuebles', uso, num(valor), _descarga_id FROM "{T['K']}"''',
          'Contexto por distrito (Comunidad de Madrid): pensionistas, empresas y empleo, inmuebles por uso')
    malos = con.execute('SELECT count(*) FROM cm_distrito_contexto WHERE cod_distrito IS NULL').fetchone()[0]
    print('   sin distrito:', malos)


if __name__ == '__main__':
    main()
