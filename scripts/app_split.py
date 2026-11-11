#!/usr/bin/env python3
"""Parte los datos completos de build/ en un núcleo ligero (app/) y un detalle por distrito (app/det/NN.json).

Entrada (la generan ingest_export.py e inversiones/historial.py):
  build/data.js         ITE_ROWS completo, DISTRITOS, VULNERABILIDAD
  build/inversiones.js  INVERSIONES con los registros (ev) de cada edificio

  build/calles.js       callejero completo (scripts/navegador/03_calles_geoportal.js)

Salida:
  app/calles.js, app/calles0.js  vías principales / secundarias
  app/data.js           igual, pero con las columnas DET vacías
  app/inversiones.js    sin los registros (ev); con n = número de registros
  app/det/NN.json       por distrito (código de barrio → distrito; 0 = sin barrio):
                        {"cols": [...], "rows": {índice_fila: [valores de cols]}, "ev": {clave_edificio: [...]}}

La app carga el detalle del distrito al abrir la ficha o la ventana de un edificio.
"""
import json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B, A = os.path.join(ROOT, 'build'), os.path.join(ROOT, 'app')
# columnas que solo se ven en la ventana o la ficha de un edificio
DET = ['Ficha madrid.es', 'ITE/IEE anteriores', 'Teléfono', 'Categoría datos.madrid.es', 'Otras fuentes', 'Empresa gestora',
       'Tipo expediente', 'Parcial/Total', 'Dictamen', 'Nº expediente', 'Dependencia actual', 'Fecha resolución', 'Resolución',
       'Deficiencias subsanadas', 'Dirección en el Registro', 'Resultado consulta Registro', 'Fecha consulta']


def leer_js(path):
    """Devuelve {nombre: valor} de un fichero con líneas window.X=...;"""
    out = {}
    for line in open(path, encoding='utf-8'):
        m = re.match(r'window\.(\w+)=(.*);\s*$', line, re.S)
        if m:
            out[m.group(1)] = json.loads(m.group(2))
    return out


def escribir_js(path, d):
    with open(path, 'w', encoding='utf-8') as f:
        for k, v in d.items():
            f.write(f'window.{k}=' + json.dumps(v, ensure_ascii=False, separators=(',', ':')) + ';\n')


def main():
    data = leer_js(os.path.join(B, 'data.js'))
    inv = leer_js(os.path.join(B, 'inversiones.js'))['INVERSIONES']
    cols = data['ITE_COLS']
    C = {c: i for i, c in enumerate(cols)}
    bar = {str(b['cod']): b['cd'] for b in (data.get('VULNERABILIDAD') or {}).get('barrios', [])}
    cd_fila = lambda r: bar.get(str(r[C['Código barrio']]), 0) if 'Código barrio' in C else 0

    det = collections.defaultdict(lambda: {'cols': DET, 'rows': {}, 'ev': {}})
    cds_clave = collections.defaultdict(set)
    for i, r in enumerate(data['ITE_ROWS']):
        cd = cd_fila(r)
        vals = [r[C[k]] for k in DET]
        if any(vals):
            det[cd]['rows'][i] = vals
        for k in DET:
            r[C[k]] = ''
        try:
            lat, lng = float(r[C['Latitud']]), float(r[C['Longitud']])
        except (TypeError, ValueError):
            continue
        if lat and lng:
            cds_clave[f'{lat:.5f},{lng:.5f}'].add(cd)

    for key, e in inv['edificios'].items():
        ev = e.pop('ev', [])
        e['n'] = len(ev)
        for cd in cds_clave.get(key) or {0}:
            det[cd]['ev'][key] = ev

    os.makedirs(os.path.join(A, 'det'), exist_ok=True)
    for f in os.listdir(os.path.join(A, 'det')):
        if f.endswith('.json'):
            os.remove(os.path.join(A, 'det', f))
    for cd, d in det.items():
        with open(os.path.join(A, 'det', f'{cd}.json'), 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, separators=(',', ':'))
    escribir_js(os.path.join(A, 'data.js'), data)
    escribir_js(os.path.join(A, 'inversiones.js'), {'INVERSIONES': inv})
    # callejero: vías principales al arrancar (calles.js), secundarias al acercarse (calles0.js)
    cp = os.path.join(B, 'calles.js')
    if os.path.exists(cp):
        CL = leer_js(cp)['CALLES']
        for nombre, var, ks in (('calles.js', 'CALLES', {1, 2}), ('calles0.js', 'CALLES0', {0})):
            idx = [i for i, k in enumerate(CL['k']) if k in ks]
            usados = sorted({CL['n'][i] for i in idx})
            remap = {o: j for j, o in enumerate(usados)}
            sub = {'fuente': CL['fuente'], 'escala': CL['escala'], 'k': [CL['k'][i] for i in idx], 'p': [CL['p'][i] for i in idx],
                   'n': [remap[CL['n'][i]] for i in idx], 'names': [CL['names'][o] for o in usados]}
            escribir_js(os.path.join(A, nombre), {var: sub})
    print('det:', ', '.join(f'{cd}:{len(d["rows"])}f/{len(d["ev"])}e' for cd, d in sorted(det.items())))


if __name__ == '__main__':
    main()
