"""Genera los JSON que lee la web (app/sec/*.json) desde las tablas cm_* de ciudadano_madrid.sqlite.

Cada bloque lleva `src`: la lista de descargas de las que sale; app/sec/fuentes.json da, para cada una,
la URL oficial, la fecha, el SHA-256 y los pasos (enlace «De dónde sale» de la web).
Los nombres de personas físicas no se exportan («Persona física»).

Uso: python3 scripts/datos/exporta_web.py
"""
import json, pathlib, sqlite3, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P

OUT = P.ROOT / 'app' / 'sec'
POLITICAS = {'01': 'Deuda pública', '11': 'Justicia', '13': 'Seguridad y movilidad', '15': 'Vivienda y urbanismo',
             '16': 'Bienestar comunitario (limpieza, residuos, alumbrado, cementerios)', '17': 'Medio ambiente y zonas verdes',
             '22': 'Prestaciones a empleados', '23': 'Servicios sociales', '24': 'Fomento del empleo', '31': 'Sanidad',
             '32': 'Educación', '33': 'Cultura', '34': 'Deporte', '43': 'Comercio, turismo y pymes', '44': 'Transporte público',
             '46': 'Investigación e innovación', '49': 'Otras actuaciones económicas', '91': 'Órganos de gobierno',
             '92': 'Servicios generales', '93': 'Administración financiera y tributaria'}
VIA = [('153', 'Vías públicas (calzadas, aceras, infraestructuras)'), ('171', 'Parques y zonas verdes'),
       ('165', 'Alumbrado y equipamientos urbanos'), ('133', 'Tráfico y señalización'), ('163', 'Limpieza viaria')]


def filas(con, sql, *a):
    cur = con.execute(sql, a)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def srcs(con, tabla, where='1'):
    return [r[0] for r in con.execute(f'SELECT DISTINCT _descarga_id FROM {tabla} WHERE {where} AND _descarga_id IS NOT NULL ORDER BY 1')]


def r0(v, n=0):
    return None if v is None else round(v, n) if n else int(round(v))


def ciudadano(con, usados):
    s_g, s_i, s_p = srcs(con, 'cm_gasto'), srcs(con, 'cm_ingresos'), srcs(con, 'cm_poblacion')
    s_e = srcs(con, 'ds_211496_eliminaciones_de_gastos')
    s_v = srcs(con, 'cm_inversion_proyecto')
    usados.update(s_g + s_i + s_p + s_e + s_v)
    ciudad = [dict(anio=r['anio'], hab=r0(r['personas']), gasto=r0(r['gasto_no_financiero_ejecutado']),
                   presup=r0(r['gasto_no_financiero_definitivo']), pct=r['pct_ejecucion'], hab_gasto=r0(r['gasto_por_habitante']),
                   aprox=r['eliminacion_aproximada'])
              for r in filas(con, 'SELECT * FROM cm_ciudad_anio ORDER BY anio')]
    ingresos = {}
    for r in filas(con, "SELECT anio, capitulo, descripcion_capitulo d, sum(derechos_reconocidos) v FROM cm_ingresos "
                        "WHERE centro='001' GROUP BY 1,2 ORDER BY 1,2"):
        ingresos.setdefault(r['anio'], {})[r['capitulo']] = r0(r['v'])
    cap_ing = {r['capitulo']: r['d'].capitalize() for r in filas(con, "SELECT capitulo, max(descripcion_capitulo) d FROM cm_ingresos GROUP BY 1")}
    impuestos = {}
    for r in filas(con, "SELECT anio, economico, max(descripcion_economico) d, sum(derechos_reconocidos) v FROM cm_ingresos "
                        "WHERE centro='001' AND capitulo IN ('1','2') GROUP BY 1,2"):
        impuestos.setdefault(r['anio'], []).append([r['economico'], r['d'], r0(r['v'])])
    politicas = {}
    for r in filas(con, "SELECT anio, politica_gasto p, sum(obligaciones_reconocidas) v FROM cm_gasto "
                        "WHERE CAST(capitulo AS INTEGER) BETWEEN 1 AND 7 GROUP BY 1,2"):
        politicas.setdefault(r['anio'], {})[r['p']] = r0(r['v'])
    distritos = [dict(anio=r['anio'], cd=r['cod_distrito'], hab=r0(r['personas']), ci=r0(r['junta_credito_inicial']),
                      cdf=r0(r['junta_credito_definitivo']), pag=r0(r['junta_gastado']), nog=r0(r['junta_no_gastado']),
                      pct=r['junta_pct_ejecucion'], inv=r0(r['inversion_presupuestada']), invp=r0(r['inversion_ejecutada']),
                      pag_hab=r0(r['junta_gastado_por_habitante'], 1), inv_hab=r0(r['inversion_por_habitante'], 1))
                 for r in filas(con, 'SELECT * FROM cm_distrito_anio ORDER BY anio, cod_distrito')]
    s_d, s_m, s_f, s_a = srcs(con, 'cm_deuda'), srcs(con, 'cm_pmp'), srcs(con, 'cm_presupuesto_futuro'), srcs(con, 'cm_ayuda_social')
    usados.update(s_d + s_m + s_f + s_a)
    deuda = [[r['anio'], r['concepto'], r0(r['importe'])] for r in filas(con, "SELECT * FROM cm_deuda WHERE concepto IN ('TOTAL DEUDA LARGO Y CORTO PLAZO','TOTAL DEUDA PDE') ORDER BY anio")]
    pmp = [[r['anio'], r['mes'], r['dias']] for r in filas(con, 'SELECT * FROM cm_pmp ORDER BY anio, mes')]
    futuro = [[r['anio'], r['estado'], r['cd'], r0(r['v'])] for r in filas(con, 'SELECT anio, estado, cod_distrito cd, sum(importe) v FROM cm_presupuesto_futuro GROUP BY 1,2,3')]
    futuro_pol = [[r['anio'], r['p'], r0(r['v'])] for r in filas(con, "SELECT anio, politica_gasto p, sum(importe) v FROM cm_presupuesto_futuro WHERE CAST(capitulo AS INTEGER) BETWEEN 1 AND 7 GROUP BY 1,2")]
    ays = [[r['anio'], r['cd'], r['n'], r0(r['v'])] for r in filas(con, 'SELECT anio, cod_distrito cd, count(*) n, sum(importe) v FROM cm_ayuda_social GROUP BY 1,2')]
    ays_tipo = [[r['o'], r['n'], r0(r['v'])] for r in filas(con, '''SELECT CASE WHEN upper(objeto) LIKE '%ALIMENT%' THEN 'Alimentos'
            WHEN upper(objeto) LIKE '%COMEDOR%' THEN 'Comedor escolar' WHEN upper(objeto) LIKE '%ESCUELA INFANTIL%' THEN 'Escuela infantil'
            WHEN upper(objeto) LIKE '%PREPAGO%' OR upper(objeto) LIKE 'TF %' OR upper(objeto) LIKE 'TF(%' THEN 'Tarjeta prepago (necesidades básicas)'
            WHEN upper(objeto) LIKE '%BUCODENTAL%' OR upper(objeto) LIKE '%GAFAS%' OR upper(objeto) LIKE '%TRATAMIENTO%' OR upper(objeto) LIKE '%AUDIFON%' THEN 'Salud (dental, gafas, tratamientos)' WHEN upper(objeto) LIKE '%ALOJAMIENTO%' OR upper(objeto) LIKE '%VIVIENDA%' OR upper(objeto) LIKE '%ALQUILER%' THEN 'Vivienda y alojamiento'
            WHEN upper(objeto) LIKE '%FAMILIAR%' THEN 'Ayudas familiares' ELSE 'Otras (descripción libre del portal)' END o, count(*) n, sum(importe) v
            FROM cm_ayuda_social WHERE anio >= 2021 GROUP BY 1 ORDER BY v DESC''')]
    comp, s_c = [], []
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='cm_ciudad_comparada'").fetchone():
        comp = [list(r) for r in con.execute('''SELECT anio, ciudad, poblacion,
              round(sum(CASE WHEN tipo='gasto' AND capitulo IN ('1','2','3','4','5','6','7') THEN importe END)),
              round(sum(CASE WHEN tipo='gasto' AND capitulo IN ('6','7') THEN importe END)),
              round(sum(CASE WHEN tipo='ingreso' AND capitulo IN ('1','2','3') THEN importe END)),
              round(sum(CASE WHEN tipo='gasto' AND capitulo='1' THEN importe END))
            FROM cm_ciudad_comparada GROUP BY 1, 2 ORDER BY 1, 2''')]
        s_c = srcs(con, 'cm_ciudad_comparada')
        usados.update(s_c)
    ctx, s_x = [], []
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='cm_distrito_contexto'").fetchone():
        ctx = [list(r) for r in con.execute('''SELECT anio, cod_distrito, indicador, detalle, valor FROM cm_distrito_contexto
            WHERE cod_distrito IS NOT NULL AND (detalle='Total' OR indicador='inmuebles') ORDER BY 1, 2''')]
        s_x = srcs(con, 'cm_distrito_contexto')
        usados.update(s_x)
    return dict(ciudad=ciudad, ingresos=ingresos, cap_ingresos=cap_ing, comparada=comp, contexto=ctx, impuestos=impuestos, politicas=politicas,
                nombres_politicas=POLITICAS, distritos=distritos, deuda=deuda, pmp=pmp, futuro=futuro, futuro_pol=futuro_pol,
                ayudas_sociales=ays, ayudas_sociales_tipo=ays_tipo,
                src=dict(ciudad=sorted(set(s_g + s_e + s_p)), ingresos=s_i, politicas=s_g, distritos=sorted(set(s_g + s_v + s_p)),
                         deuda=s_d, pmp=s_m, futuro=s_f, ayudas_sociales=s_a, comparada=s_c, contexto=s_x))


def via(con, usados):
    s_l = srcs(con, 'cm_obra_licencia')
    s_i = srcs(con, 'cm_inversion_principal')
    s_o = srcs(con, 'cm_obra_publica')
    s_v = srcs(con, 'cm_inversion_proyecto')
    s_g = srcs(con, 'cm_gasto')
    usados.update(s_l + s_i + s_o + s_v + s_g)
    lic = [[r['anio'], r['cod_distrito'], r['tipo_obra'], r['n']] for r in
           filas(con, 'SELECT anio, cod_distrito, tipo_obra, count(*) n FROM cm_obra_licencia GROUP BY 1,2,3')]
    calles = {}
    for cd in [None] + list(range(1, 22)):
        w = 'cod_distrito=?' if cd else '1=1'
        args = (cd,) if cd else ()
        top = filas(con, f'''SELECT max(via) via, count(*) n, count(DISTINCT anio) anios, min(anio) desde,
                               sum(tipo_obra='Avería urgente') av, sum(tipo_obra='Cala programada') ca, sum(tipo_obra='Canalización') cn,
                               sum(tipo_obra='Alcantarillado') al, sum(tipo_obra='Obra municipal') om, group_concat(DISTINCT cod_distrito) ds
                             FROM cm_obra_licencia WHERE {w} AND via_clave IS NOT NULL GROUP BY via_clave ORDER BY n DESC LIMIT {50 if cd is None else 30}''', *args)
        calles[str(cd or 0)] = [[t['via'], t['n'], t['anios'], t['desde'], t['av'], t['ca'], t['cn'], t['al'], t['om'], t['ds']] for t in top]
    ult = filas(con, '''SELECT i.* FROM cm_inversion_principal i
                        JOIN (SELECT codigo_pep, max(anio_datos) a FROM cm_inversion_principal GROUP BY 1) u
                          ON u.codigo_pep = i.codigo_pep AND u.a = i.anio_datos''')
    inv = [[r['codigo_pep'], r['denominacion'], r['cod_distrito'], r['direccion'], r['lat'], r['lng'], r['linea'], r['estado'],
            r['ano_inicio'], r['ano_fin'], r0(r['presupuesto_total']), r0(r['gasto_ejecutado']), r['gestor'], r['url_fotografia'],
            r['anio_datos'], r['_descarga_id']] for r in ult]
    ob = filas(con, 'SELECT * FROM cm_obra_publica')
    obras = [dict(nombre=r.get('denominaci'), cd=r.get('cod_distrito'), calles=r.get('viario_afe'), presupuesto=r.get('presupuest'),
                  empresa=r.get('empresa'), plazo=r.get('plazo_ejec'), inicio=r.get('fecha_inic'), fin=r.get('fecha_fina'),
                  descripcion=r.get('descripcio'), expediente=r.get('n_expedi'), src=r['_descarga_id']) for r in ob]
    gasto_via = {}
    for pref, nombre in VIA:
        for r in filas(con, f'''SELECT anio, cod_distrito cd, sum(obligaciones_reconocidas) v FROM cm_inversion_proyecto
                                WHERE programa LIKE '{pref}%' AND cod_distrito BETWEEN 1 AND 21 GROUP BY 1,2'''):
            gasto_via.setdefault(pref, []).append([r['anio'], r['cd'], r0(r['v'])])
    ciudad_via = {}
    for pref, nombre in VIA:
        for r in filas(con, f'''SELECT anio, sum(obligaciones_reconocidas) v FROM cm_gasto
                                WHERE programa LIKE '{pref}%' GROUP BY 1'''):
            ciudad_via.setdefault(pref, []).append([r['anio'], r0(r['v'])])
    s_as = srcs(con, 'cm_asfalto')
    usados.update(s_as)
    asf = [[r['anio'], r['cd'], r['n'], r0(r['sup']), r0(r['precio'])] for r in filas(con, 'SELECT anio, cod_distrito cd, count(*) n, sum(superficie_m2) sup, sum(precio_aprox) precio FROM cm_asfalto GROUP BY 1,2')]
    asf_calles = [[r['anio'], r['cod_distrito'], r['calle'], r['tramo'], r['estado'], r0(r['precio_aprox']), r['lat'], r['lng'], r['_descarga_id']]
                  for r in filas(con, 'SELECT * FROM cm_asfalto ORDER BY anio DESC, cod_distrito, calle')]
    T3 = {}
    def L(sql):
        return [list(r) for r in con.execute(sql)]
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='cm_accidente_anio'").fetchone():
        T3['accidentes'] = L('SELECT anio, cod_distrito, accidentes, heridos_leves, heridos_graves, fallecidos, atropellos, con_alcohol FROM cm_accidente_anio WHERE cod_distrito IS NOT NULL ORDER BY 1, 2')
        T3['accidentes_lugar'] = {}
        for cd in [0] + list(range(1, 22)):
            w = '' if cd == 0 else f' AND cod_distrito = {cd}'
            T3['accidentes_lugar'][str(cd)] = L(f'''SELECT lugar, count(DISTINCT accidente) n, count(DISTINCT CASE WHEN gravedad IN ('grave','fallecido') THEN accidente END) g,
                count(DISTINCT CASE WHEN tipo_accidente LIKE 'Atropello%' THEN accidente END) a
                FROM cm_accidente WHERE anio >= 2022 AND lugar IS NOT NULL AND lugar <> ''{w} GROUP BY 1 ORDER BY 2 DESC LIMIT 20''')
        T3['accidentes_src'] = srcs(con, 'cm_accidente_anio')
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='cm_multa_circulacion'").fetchone():
        T3['multas'] = L('SELECT anio, boletines, round(recaudacion_voluntaria) FROM cm_multa_circulacion ORDER BY 1')
        T3['multas_src'] = srcs(con, 'cm_multa_circulacion')
        T3['limpieza'] = L('SELECT anio, cod_distrito, count(*), round(sum(importe)) FROM cm_sancion_limpieza WHERE anio >= 2016 GROUP BY 1, 2 ORDER BY 1, 2')
        T3['limpieza_src'] = srcs(con, 'cm_sancion_limpieza')
        T3['arbolado'] = L('SELECT anio, cod_distrito, arboles, recien_plantados, viejos FROM cm_arbolado ORDER BY 1, 2')
        T3['arbolado_src'] = srcs(con, 'cm_arbolado')
        T3['farolas'] = L('SELECT cod_distrito, farolas FROM cm_farola WHERE cod_distrito IS NOT NULL ORDER BY 1')
        T3['farolas_src'] = srcs(con, 'cm_farola')
        T3['senales'] = L('SELECT cod_distrito, tipo, en_servicio, altas_desde_2020 FROM cm_senal WHERE cod_distrito IS NOT NULL ORDER BY 1, 2')
        T3['senales_src'] = srcs(con, 'cm_senal')
    for k, v in T3.items():
        if k.endswith('_src'):
            usados.update(v)
    return dict(asfalto=asf, asfalto_calles=asf_calles, t3=T3, licencias=lic, calles=calles, inversiones=inv, obras=obras, programas=dict(VIA),
                inversion_via_distrito=gasto_via, gasto_via_ciudad=ciudad_via,
                src=dict(licencias=s_l, inversiones=s_i, obras=s_o, inversion_via=s_v, gasto_via=s_g, asfalto=s_as))


def servicios(con, usados):
    s = srcs(con, 'cm_contrato')
    usados.update(s)
    enc, s_en = [], []
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='cm_encargo'").fetchone():
        enc = [list(r) for r in con.execute('''SELECT tipo, fecha, anio, area, substr(objeto,1,260), encargado, round(importe,2), documento, _descarga_id
                                              FROM cm_encargo ORDER BY anio DESC, fecha DESC''')]
        s_en = srcs(con, 'cm_encargo')
        usados.update(s_en)
    nom = "CASE WHEN persona_fisica=1 THEN 'Persona física' ELSE max(adjudicatario) END"
    clave = "CASE WHEN persona_fisica=1 THEN 'PF' ELSE COALESCE(NULLIF(nif,''), upper(adjudicatario)) END"
    por_anio = [[r['anio'], r['tipo_registro'], r['n'], r0(r['v'])] for r in
                filas(con, 'SELECT anio, tipo_registro, count(*) n, sum(importe_iva_inc) v FROM cm_contrato WHERE anio IS NOT NULL GROUP BY 1,2')]
    por_dist = [[r['anio'], r['cd'], r['tipo_registro'], r['n'], r0(r['v'])] for r in
                filas(con, 'SELECT anio, cod_distrito cd, tipo_registro, count(*) n, sum(importe_iva_inc) v FROM cm_contrato '
                           'WHERE cod_distrito IS NOT NULL AND anio IS NOT NULL GROUP BY 1,2,3')]
    ranking = {}
    for cd in [None] + list(range(1, 22)):
        w = 'cod_distrito=?' if cd else '1=1'
        args = (cd,) if cd else ()
        top = filas(con, f'''SELECT {clave} k, {nom} nombre, max(persona_fisica) pf, count(*) n, sum(importe_iva_inc) v,
                                    sum(tipo_registro='menor') nm, min(anio) desde, max(anio) hasta, count(DISTINCT cod_distrito) nd
                             FROM cm_contrato WHERE {w} AND COALESCE(nif, adjudicatario) IS NOT NULL
                             GROUP BY {clave} ORDER BY v DESC LIMIT {50 if cd is None else 20}''', *args)
        ranking[str(cd or 0)] = [[t['nombre'], (None if t['pf'] else t['k']), t['n'], r0(t['v']), t['nm'], t['desde'], t['hasta'], t['nd']] for t in top]
    s_p, s_e = srcs(con, 'cm_pago'), srcs(con, 'cm_lista_espera')
    usados.update(s_p + s_e)
    pag_anio = [[r['anio'], r['cd'], r0(r['v'])] for r in filas(con, 'SELECT anio, cod_distrito cd, sum(importe) v FROM cm_pago GROUP BY 1,2')]
    pclave = "CASE WHEN persona_fisica=1 THEN 'PF' ELSE COALESCE(NULLIF(nif,''), upper(tercero)) END"
    pagos = {}
    for cd in [None] + list(range(1, 22)):
        w, args = ('cod_distrito=?', (cd,)) if cd else ('1=1', ())
        top = filas(con, f'''SELECT {pclave} k, CASE WHEN max(persona_fisica)=1 THEN 'Persona física' ELSE max(tercero) END nombre, max(persona_fisica) pf,
                                    sum(importe) v, sum(CASE WHEN anio=(SELECT max(anio) FROM cm_pago) THEN importe END) vu, count(DISTINCT anio) anios,
                                    min(anio) desde, max(anio) hasta, max(tipo_tercero) tipo
                             FROM cm_pago WHERE {w} AND importe > 0 GROUP BY {pclave} ORDER BY v DESC LIMIT {40 if cd is None else 20}''', *args)
        pagos[str(cd or 0)] = [[t['nombre'].rstrip(' .'), None if t['pf'] else t['k'], r0(t['v']), r0(t['vu']), t['desde'], t['hasta'], t['tipo']] for t in top]
    espera = [[r['servicio'], r['cd'], r['n'], r['med'], r['mx']] for r in filas(con, '''
        SELECT servicio, cod_distrito cd, count(*) n, CAST(avg(dias_espera) AS INTEGER) med, max(dias_espera) mx FROM cm_lista_espera GROUP BY 1,2''')]
    fecha_espera = con.execute('SELECT max(fecha_datos) FROM cm_lista_espera').fetchone()[0]
    return dict(por_anio=por_anio, por_distrito=por_dist, ranking=ranking, pagos_anio=pag_anio, pagos=pagos,
                espera=espera, espera_fecha=fecha_espera, encargos=enc, src=dict(contratos=s, pagos=s_p, espera=s_e, encargos=s_en))


def ayudas(con, usados):
    s_a, s_f, s_c = srcs(con, 'cm_ayuda_recibida'), srcs(con, 'cm_fondo_europeo'), srcs(con, 'cm_convenio')
    usados.update(s_a + s_f + s_c)
    rec = [[r['nivel'], r['administracion_concedente'], r['organo_concedente'], r['convocatoria'], r['fecha'], r['anio'],
            r['beneficiario'], r0(r['importe'], 2), r['codigo_bdns'], r['url_bases_reguladoras'], r['_descarga_id']]
           for r in filas(con, 'SELECT * FROM cm_ayuda_recibida ORDER BY importe DESC')]
    fe = [[r['subproyecto'], r['denominacion'], r['anio'], r0(r['importe_concedido'], 2), r0(r['coste_real_iva'], 2), r['tipo_de_subvencion'],
           r['territorio'], r['cod_distrito'], r['nombre_beneficiario'], r['url'], r['_descarga_id']]
          for r in filas(con, 'SELECT * FROM cm_fondo_europeo ORDER BY importe_concedido DESC')]
    conv = [[r['fecha_suscripcion'], r['anio'], r['organo'], r['cod_distrito'], (r['titulo_objeto'] or '')[:220],
             (r['otras_entidades_firmantes'] or '')[:160], r0(r['obligacion_ayuntamiento']), r0(r['obligacion_otras']),
             r['documento_del_convenio'], r['_descarga_id']]
            for r in filas(con, 'SELECT * FROM cm_convenio ORDER BY fecha_suscripcion DESC')]
    sub, s_s = {}, []
    if con.execute("SELECT 1 FROM sqlite_master WHERE name='cm_subvencion'").fetchone():
        s_s = srcs(con, 'cm_subvencion')
        usados.update(s_s)
        sub['anio'] = [list(r) for r in con.execute('SELECT anio, cod_distrito, count(*), round(sum(importe)) FROM cm_subvencion WHERE anio IS NOT NULL GROUP BY 1, 2 ORDER BY 1, 2')]
        sub['ranking'], sub['lineas'] = {}, {}
        for cd in [0] + list(range(1, 22)):
            w = '' if cd == 0 else f'AND cod_distrito = {cd}'
            sub['ranking'][str(cd)] = [list(r) for r in con.execute(f'''SELECT beneficiario, max(nif), count(*), round(sum(importe)), min(anio), max(anio)
                FROM cm_subvencion WHERE anio >= 2019 {w} GROUP BY upper(beneficiario) ORDER BY 4 DESC LIMIT 25''')]
            sub['lineas'][str(cd)] = [list(r) for r in con.execute(f'''SELECT coalesce(nullif(linea,''),'Sin clasificar'), count(*), round(sum(importe))
                FROM cm_subvencion WHERE anio >= 2019 {w} GROUP BY 1 ORDER BY 3 DESC LIMIT 12''')]
    return dict(recibidas=rec, fondos_europeos=fe, convenios=conv, subvenciones=sub,
                src=dict(recibidas=s_a, fondos=s_f, convenios=s_c, subvenciones=s_s))


def main():
    con = P.abrir()
    OUT.mkdir(parents=True, exist_ok=True)
    usados = set()
    for nombre, fn in [('ciudadano', ciudadano), ('via', via), ('servicios', servicios), ('ayudas', ayudas)]:
        d = fn(con, usados)
        txt = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
        (OUT / f'{nombre}.json').write_text(txt, encoding='utf-8')
        print(f'{nombre:10} {len(txt) / 1024:8.0f} KB')
    F = {}
    for r in filas(con, f"SELECT * FROM v_procedencia WHERE descarga_id IN ({','.join(map(str, sorted(usados)))})"):
        F[r['descarga_id']] = dict(f=r['fuente'], k=r['clave'], o=r['organismo'], fi=r['url_ficha'], l=r['licencia'], r=r['recurso'],
                                   u=r['url'], d=r['fecha'], h=r['sha256'], a=r['archivo_url'], p=r['pasos'], s=r['script'], c=r['commit_git'])
    txt = json.dumps(F, ensure_ascii=False, separators=(',', ':'))
    (OUT / 'fuentes.json').write_text(txt, encoding='utf-8')
    print(f'fuentes    {len(txt) / 1024:8.0f} KB  ({len(F)} descargas)')


if __name__ == '__main__':
    main()
