"""Selecciona, de todos los contratos del Ayuntamiento (salida de scripts/servicios/normaliza_todo.py),
los de obras, reformas y mejoras en edificios, con el esquema que usa historial.py.

Uso: python contratos_obras.py todos.json   → datos/inversiones/contratos_obras.json
"""
import json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from normaliza import nrm

INV = r'\bOBRA|REFORMA|REHABILIT|ACONDICION|IMPERMEABILIZ|CUBIERTA|SUSTITUC|ACCESIBILID|CLIMATIZ|CALEFACC|CALDERA|ASCENSOR|VENTANA|CARPINTER|FACHADA|PAVIMENT|REPARAC|MEJORA|ADECUACI|DEMOLIC|CONSTRUCC|AMPLIAC|PINTURA|SANEAMIENTO|ILUMINAC|ELECTRIC|FONTANER|EFICIENCIA ENERG|PATOLOG|EMERGENCIA|SEGURIDAD ESTRUCTURAL'
# compras de material, alquileres y producciones artísticas no son inversión en el edificio
NO = r'FUNGIBLE|CONSUMIBLE|ARRENDAMIENTO|ALQUILER|COMPRA (DE )?MATERIAL|PRODUCCION (DEL|DE LA|DE ESPECTACULO)|ESPECTACULO|DISEÑO ARTISTICO|MURAL|ESCENOGRAF|VESTUARIO DE|EXPOSICION'
T = json.load(open(sys.argv[1]))
out = []
for o in T:
    if o['kind'] == 'prorroga':
        continue
    txt = nrm(o['der'] if (o['der'] or '').strip() else o['obj'])
    if not (re.search(INV, txt) or nrm(o['tip']).startswith('OBRA')):
        continue
    if re.search(NO, txt) and not nrm(o['tip']).startswith('OBRA'):
        continue
    y = int(o['fecha'][:4]) if o.get('fecha') else None
    if not y:
        m = re.search(r'/(20\d\d)/', o.get('exp') or '')
        y = int(m.group(1)) if m else None
    if not y:
        continue
    out.append({'kind': o['kind'], 'obj': o['obj'], 'der': o['der'], 'imp': o['imp'], 'centro': o['cen'], 'org': o['org'],
                'tipo': o['tip'], 'adj': o['adj'], 'year': y, 'exp': o.get('exp', '')})
dst = pathlib.Path(__file__).resolve().parents[2] / 'datos' / 'inversiones' / 'contratos_obras.json'
json.dump(out, open(dst, 'w'), ensure_ascii=False)
print(len(out), 'contratos →', dst)
