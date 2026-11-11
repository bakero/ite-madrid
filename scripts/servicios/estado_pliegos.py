"""Tabla de estado del reparto por edificio de los contratos vigentes de las Juntas (fuera de Puente de Vallecas)
para docs/servicios-pliegos.md. Uso: python estado_pliegos.py  (imprime la tabla en Markdown)."""
import json,os,collections
B=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','datos','servicios')
C=[c for c in json.load(open(os.path.join(B,'empresas_distritos.json'))) if c['vigente'] and c['distrito']!='PUENTE DE VALLECAS']
R=json.load(open(os.path.join(B,'reparto_pliegos.json')));CFG=json.load(open(os.path.join(B,'reparto_pliegos_cfg.json')))
NOTA={'300/2024/01423':'escaneado (sin texto)'}
E=collections.OrderedDict()
for c in sorted(C,key=lambda c:(c['distrito'],c['cats'][0],c['exp'])):E.setdefault(c['exp'],[]).append(c)
def pct(exp,cs):
    r=R[exp];a=t=0
    for c in cs:
        fl=[f for f in r['filas'] if not c['lote'] or f['lote']==c['lote']]
        tot=sum(f['peso'] for f in fl);ok=sum(f['peso'] for f in fl if f['key'])
        if tot:a+=(c['anual'] or 0)*ok/tot
        t+=c['anual'] or 0
    return 100*a/t if t else 0
print('| Expediente | Distrito | Servicios | Miles €/año | Estado | % del importe asignado a edificios del mapa |')
print('|---|---|---|---:|---|---:|')
n=collections.Counter()
for exp,cs in E.items():
    cats=R.get(exp,{}).get('cats') or sorted({x for c in cs for x in c['cats']})
    an=sum(c['anual'] or 0 for c in cs)/1000
    if exp in R:p=pct(exp,cs);est='reparto leído del pliego' if p>0 else 'sin reparto (ningún edificio del pliego se puede asignar)';ps=f'{p:.0f} %'
    elif CFG.get(exp,{}).get('modo')=='sin':est='sin reparto: '+CFG[exp].get('motivo','');ps='—'
    else:est=NOTA.get(exp,'pendiente de revisar');ps='—'
    n[est.split(':')[0].split(' (')[0]]+=1
    print(f"| {exp} | {cs[0]['distrito'].title()} | {', '.join(cats)} | {an:,.0f} | {est} | {ps} |".replace(',','.'))
print();print('Recuento:',', '.join(f'{v} {k}' for k,v in n.items()))
