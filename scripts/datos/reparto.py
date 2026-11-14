"""¿A dónde va cada euro? Sigue el gasto del presupuesto hasta su destino y reparte lo compartido según el uso real.

Cadena: partida (sección = Junta o Área, programa, capítulo) → pagos a terceros (cm_pago: perceptor y concepto) → destino.
  · Capítulo 1 (personal) no tiene pagos a terceros: se toma de la ejecución presupuestaria (cm_gasto).
  · Inversiones de las Áreas (capítulo 6): se reparten por distritos según los proyectos de inversión territorializados (cm_inversion_proyecto)
    del mismo programa.

Destino, del más preciso al menos:
  1. distrito «directo»: la partida es de una Junta, o el concepto del pago nombra el distrito;
  2. distrito «repartido»: gasto de toda la ciudad repartido por el criterio de su tipo de gasto (tabla CRITERIO);
  3. barrio: lo que llega a cada distrito se reparte entre sus barrios con el mismo criterio (o por el concepto si nombra el barrio);
  4. sin destino territorial: deuda, órganos de gobierno, cooperación internacional y servicios centrales; no se reparte.

Salidas: cm_euro_distrito, cm_euro_barrio, cm_euro_resumen. Uso: python3 scripts/datos/reparto.py [años]
"""
import collections, json, pathlib, re, sys, unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import procedencia as P

# tipo de gasto por grupo de programa (3 primeras cifras) y, si hace falta, por programa completo
TIPOS = [  # (prefijo de programa, tipo, criterio de reparto)
    ('011', 'Deuda', None), ('912', 'Órganos de gobierno', None), ('23290', 'Cooperación internacional', None),
    ('91', 'Órganos de gobierno', None), ('92001', 'Administración del distrito', 'poblacion'),
    ('920', 'Servicios centrales', None), ('931', 'Servicios centrales', None), ('932', 'Servicios centrales', None),
    ('934', 'Servicios centrales', None), ('491', 'Servicios centrales', None), ('922', 'Servicios centrales', None), ('925', 'Atención a la ciudadanía', 'poblacion'),
    ('933', 'Edificios municipales', 'edificios'),
    ('132', 'Policía y seguridad', 'poblacion'), ('135', 'SAMUR y protección civil', 'poblacion'), ('136', 'Bomberos', 'poblacion'),
    ('133', 'Tráfico y movilidad', 'poblacion'), ('134', 'Tráfico y movilidad', 'poblacion'),
    ('150', 'Urbanismo y vivienda', 'poblacion'), ('151', 'Urbanismo y vivienda', 'poblacion'), ('152', 'Urbanismo y vivienda', 'poblacion'),
    ('153', 'Calles e infraestructuras', 'poblacion'), ('160', 'Agua y alcantarillado', 'poblacion'), ('161', 'Agua y alcantarillado', 'poblacion'),
    ('162', 'Residuos', 'poblacion'), ('163', 'Limpieza viaria', 'poblacion'), ('165', 'Alumbrado y equipamientos urbanos', 'farolas'),
    ('17', 'Parques, zonas verdes y medio ambiente', 'arboles'),
    ('23103', 'Mayores', 'mayores'), ('231', 'Servicios sociales', 'poblacion'), ('221', 'Acción social del personal', None),
    ('241', 'Empleo', 'paro'), ('311', 'Salud', 'poblacion'), ('312', 'Salud', 'poblacion'),
    ('32', 'Educación', 'menores'), ('338', 'Fiestas y festejos', 'poblacion'),
    ('33', 'Cultura', 'cultura'), ('34', 'Deportes', 'deporte'),
    ('43', 'Comercio, turismo y economía', 'locales'), ('44', 'Transporte público', 'poblacion'),
    ('924', 'Participación ciudadana', 'asociaciones'), ('49', 'Consumo y otros servicios', 'poblacion'),
]
CRITERIO = {
    'poblacion': 'habitantes empadronados', 'edificios': 'número de edificios municipales', 'farolas': 'número de farolas',
    'arboles': 'número de árboles (por distrito) y habitantes (dentro del distrito)', 'mayores': 'población de 65 años o más',
    'menores': 'población de 0 a 14 años', 'cultura': 'centros culturales y bibliotecas municipales', 'deporte': 'instalaciones deportivas municipales',
    'locales': 'locales comerciales abiertos', 'asociaciones': 'asociaciones inscritas', 'paro': 'personas en paro registrado',
}


def tipo_de(prog):
    p = str(prog or '').zfill(5)
    best = None
    for pre, t, c in TIPOS:
        if p.startswith(pre) and (best is None or len(pre) > len(best[0])):
            best = (pre, t, c)
    return (best[1], best[2]) if best else ('Otros servicios', 'poblacion')


def plano(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFD', (s or '').upper()).encode('ascii', 'ignore').decode())


def pesos(con):
    """Peso de cada barrio para cada criterio (el peso de un distrito es la suma de sus barrios, salvo árboles)."""
    W = collections.defaultdict(dict)
    yP = con.execute('SELECT max(anio) FROM cm_poblacion').fetchone()[0]
    for b, n in con.execute('SELECT cod_barrio, sum(personas) FROM cm_poblacion WHERE anio=? GROUP BY 1', (yP,)):
        W['poblacion'][b] = n
    pk = lambda k: dict(con.execute('SELECT cod_barrio, valor FROM cm_barrio_panel WHERE cod_barrio>0 AND indicador=?', (k,)).fetchall())
    W['mayores'] = pk('mayores_65'); W['menores'] = pk('menores_15'); W['paro'] = pk('paro'); W['locales'] = pk('locales_abiertos')
    W['asociaciones'] = pk('asociaciones')
    for k, ks in [('cultura', ('c_culturales', 'bibliotecas')), ('deporte', ('c_deportivos', 'inst_deportivas', 'piscinas'))]:
        acc = collections.Counter()
        for kk in ks:
            for b, v in pk(kk).items():
                acc[b] += v or 0
        W[k] = dict(acc)
    W['farolas'] = dict(con.execute("SELECT cod_barrio, sum(valor) FROM cm_barrio_dato WHERE indicador='farolas' GROUP BY 1").fetchall())
    W['edificios'] = dict(con.execute('SELECT cod_barrio, count(DISTINCT direccion) FROM centros WHERE cod_barrio IS NOT NULL AND coalesce(excluido,0)=0 GROUP BY 1').fetchall())
    W['arboles'] = dict(W['poblacion'])  # dentro del distrito, por habitantes
    bar = dict(con.execute('SELECT cod_barrio, cod_distrito FROM cm_barrio').fetchall())
    for k in W:
        W[k] = {int(b): float(v) for b, v in W[k].items() if b and int(b) in bar and v}
    yA = con.execute('SELECT max(anio) FROM cm_arbolado').fetchone()[0]
    WD_arb = dict(con.execute('SELECT cod_distrito, arboles FROM cm_arbolado WHERE anio=?', (yA,)).fetchall())
    return W, bar, WD_arb


def reparte(total, pes):
    s = sum(pes.values())
    return {k: total * v / s for k, v in pes.items()} if s else {}


def main(anios):
    con = P.abrir()
    W, bar, WD_arb = pesos(con)
    dist_de = collections.defaultdict(list)
    for b, d in bar.items():
        dist_de[d].append(b)
    WD = {k: {d: sum(v.get(b, 0) for b in dist_de[d]) for d in range(1, 22)} for k, v in W.items()}
    WD['arboles'] = {int(d): float(v) for d, v in WD_arb.items() if d}
    nombres_d = {d: plano(n) for d, n in con.execute('SELECT cod, nombre FROM cm_distrito')}
    alias_d = dict(nombres_d); alias_d.update({8: 'FUENCARRAL', 9: 'MONCLOA', 20: 'SAN BLAS', 13: 'PUENTE DE VALLECAS', 18: 'VILLA DE VALLECAS'})
    AMBIG = {1, 3}  # «centro» y «retiro» son palabras comunes: solo cuentan precedidas de «distrito»
    re_d = [(d, re.compile((r'\b(DISTRITO|DTO\.?|JMD|JUNTA MUNICIPAL)( DE)? ' if d in AMBIG else r'\b') + re.escape(n) + r'\b'))
            for d, n in sorted(alias_d.items(), key=lambda x: -len(x[1]))]
    for t in ('cm_euro_distrito', 'cm_euro_barrio', 'cm_euro_resumen'):
        con.execute(f'DROP TABLE IF EXISTS {t}')
    con.execute('CREATE TABLE cm_euro_distrito(anio INTEGER, cod_distrito INTEGER, tipo TEXT, criterio TEXT, metodo TEXT, importe REAL)')
    con.execute('CREATE TABLE cm_euro_barrio(anio INTEGER, cod_barrio INTEGER, cod_distrito INTEGER, tipo TEXT, criterio TEXT, metodo TEXT, importe REAL)')
    con.execute('CREATE TABLE cm_euro_resumen(anio INTEGER, tipo TEXT, criterio TEXT, metodo TEXT, importe REAL)')
    for anio in anios:
        D = collections.defaultdict(float)   # (cd, tipo, criterio, metodo) -> €
        R = collections.defaultdict(float)   # (tipo, criterio, metodo) -> €
        # 1) pagos a terceros (capítulos 2 a 9)
        inv_prog = collections.defaultdict(dict)
        for prog, cd, v in con.execute('''SELECT programa, cod_distrito, sum(obligaciones_reconocidas) FROM cm_inversion_proyecto
                                          WHERE anio=? AND cod_distrito IS NOT NULL GROUP BY 1, 2''', (anio,)):
            inv_prog[str(prog)[:5]][cd] = v or 0
        filas = con.execute('''SELECT cod_distrito, programa, substr(subconcepto,1,1), concepto, sum(importe) FROM cm_pago
                               WHERE anio=? GROUP BY 1, 2, 3, 4''', (anio,)).fetchall()
        for cd, prog, cap, concepto, imp in filas:
            if not imp:
                continue
            tipo, crit = tipo_de(prog)
            if cd:
                D[(cd, tipo, crit or 'poblacion', 'directo')] += imp; R[(tipo, crit or 'poblacion', 'directo')] += imp; continue
            if crit is None:
                R[(tipo, '—', 'sin destino territorial')] += imp; continue
            txt = plano(concepto)
            hit = next((d for d, rx in re_d if rx.search(txt)), None)
            if hit:
                D[(hit, tipo, crit, 'concepto del pago')] += imp; R[(tipo, crit, 'concepto del pago')] += imp; continue
            if cap == '6' and inv_prog.get(str(prog)[:5]):
                for d, v in reparte(imp, inv_prog[str(prog)[:5]]).items():
                    D[(d, tipo, 'proyectos de inversión', 'repartido')] += v
                R[(tipo, 'proyectos de inversión', 'repartido')] += imp; continue
            for d, v in reparte(imp, WD[crit]).items():
                D[(d, tipo, crit, 'repartido')] += v
            R[(tipo, crit, 'repartido')] += imp
        # 2) personal (capítulo 1), desde la ejecución presupuestaria
        for cd, prog, v in con.execute('''SELECT cod_distrito, programa, sum(obligaciones_reconocidas) FROM cm_gasto
                                          WHERE anio=? AND capitulo IN ('1','01') GROUP BY 1, 2''', (anio,)):
            if not v:
                continue
            tipo, crit = tipo_de(prog)
            if cd:
                D[(cd, tipo, crit or 'poblacion', 'directo')] += v; R[(tipo, crit or 'poblacion', 'directo')] += v
            elif crit is None:
                R[(tipo, '—', 'sin destino territorial')] += v
            else:
                for d, x in reparte(v, WD[crit]).items():
                    D[(d, tipo, crit, 'repartido')] += x
                R[(tipo, crit, 'repartido')] += v
        con.executemany('INSERT INTO cm_euro_distrito VALUES (?,?,?,?,?,?)', [(anio, d, t, c, m, v) for (d, t, c, m), v in D.items()])
        con.executemany('INSERT INTO cm_euro_resumen VALUES (?,?,?,?,?)', [(anio, t, c, m, v) for (t, c, m), v in R.items()])
        # 3) de distrito a barrio, con el mismo criterio dentro del distrito
        Bb = collections.defaultdict(float)
        for (d, t, c, m), v in D.items():
            wc = 'poblacion' if c in ('arboles', 'proyectos de inversión') else c
            pes = {b: W[wc].get(b, 0) for b in dist_de[d]}
            if not sum(pes.values()):
                pes = {b: W['poblacion'].get(b, 0) for b in dist_de[d]}
            for b, x in reparte(v, pes).items():
                Bb[(b, d, t, c, 'directo al distrito' if m == 'directo' else m)] += x
        con.executemany('INSERT INTO cm_euro_barrio VALUES (?,?,?,?,?,?,?)', [(anio, b, d, t, c, m, v) for (b, d, t, c, m), v in Bb.items()])
        tot = sum(R.values()); terr = sum(v for (t, c, m), v in R.items() if m != 'sin destino territorial')
        print(anio, f'total {tot / 1e6:,.0f} M€; con destino territorial {terr / 1e6:,.0f} M€; directo {sum(v for k, v in R.items() if k[2] == "directo") / 1e6:,.0f} M€')
    con.execute("INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES ('cm_euro_distrito','Gasto llevado a cada distrito: directo o repartido por el criterio de su tipo', (SELECT count(*) FROM cm_euro_distrito), 'reparto.py')")
    con.execute("INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES ('cm_euro_barrio','Gasto llevado a cada barrio', (SELECT count(*) FROM cm_euro_barrio), 'reparto.py')")
    con.execute("INSERT OR REPLACE INTO cm_tablas(tabla, descripcion, filas, origen) VALUES ('cm_euro_resumen','Gasto por tipo, criterio de reparto y método', (SELECT count(*) FROM cm_euro_resumen), 'reparto.py')")
    con.commit()


if __name__ == '__main__':
    main([int(a) for a in sys.argv[1:]] or [2023, 2024, 2025])
