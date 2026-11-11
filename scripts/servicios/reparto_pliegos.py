"""Reparto por edificio de los contratos de servicios de las Juntas (fuera de Puente de Vallecas) leyendo la tabla del
pliego que da el peso de cada edificio: m² construidos (limpieza, mantenimiento) u horas al año (limpieza por horas).

Uso: PLIEGOS_TXT=<carpeta con los .txt de descarga_pliegos.py> python reparto_pliegos.py
Config: datos/servicios/reparto_pliegos_cfg.json  {exp: {modo: linea|bloque, doc, medida, [tablas...], [anular: textos de filas mal asignadas]}}
  linea  = una fila por edificio; el peso es el número más cercano a la columna de la cabecera (pliegos_tablas.py)
  bloque = varias líneas por edificio (una por trabajador); el peso es la suma de la columna (pliegos_bloques.py)
  ancla = cada número de la columna es un edificio; el nombre, partido alrededor, se asigna al más cercano
  totales = una tabla pequeña por edificio; el peso es su fila TOTAL bajo la columna de la cabecera (pliegos_bloques.py)
Salida: datos/servicios/reparto_pliegos.json {exp: {metodo, doc, filas: [{key|null, lote, peso, texto}]}}
Las filas que no se reconocen como edificio del mapa se guardan con key null: cuentan en el total del lote para que la
cuota de los demás sea la correcta."""
import json,os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import pliegos_tablas as PT, pliegos_bloques as PB
PB.lote_de=PT.lote_de
BASE=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','datos','servicios')
CFG=json.load(open(os.path.join(BASE,'reparto_pliegos_cfg.json')))
out={}
for exp,c in CFG.items():
    if c['modo']=='linea':
        cd,kind,best=PT.run(exp,{'doc':c['doc']} if c.get('doc') else {})
        if not best:print(exp,'sin tabla');continue
        _,doc,rows=best;filas=[{'key':r['key'],'lote':r['lote'],'peso':r['v'],'texto':r['txt'],'how':r['how']} for r in rows]
    else:
        rows={'totales':PB.extraer_totales,'ancla':PB.extraer_ancla}.get(c['modo'],PB.extraer)(exp,c);doc=c['doc'];filas=[{'key':r['key'],'lote':r['lote'],'peso':r['v'],'texto':r['txt'],'how':r['how']} for r in rows]
    # filas que no son edificios (fechas, IVA, precios, umbrales, nº de expediente): fuera del total
    BAS=re.compile(r'\b(A[ÑN]O|FECHA|IVA|EUROS?|EXPTE|EXPEDIENTE|HASTA|M[ÁA]S DE|MENOS DE|PRECIO|IMPORTE|CARGO|FIRMA)\b|%|€/|/m2',re.I)
    filas=[f for f in filas if f['key'] or not (BAS.search(f['texto']) or (f['peso']==int(f['peso']) and 1990<=f['peso']<=2100) or not re.search(r'[A-Za-zÁÉÍÓÚÑ]{4}',re.split(r'\d',f['texto'])[0] or f['texto']))]
    for f in filas:  # asignaciones revisadas a mano y descartadas: la fila cuenta en el total pero no se asigna
        if f['key'] and any(a in f['texto'] for a in c.get('anular',[])):f['key']=None;f['how']='anulada'
    out[exp]={'metodo':c['medida'],'doc':doc,'filas':filas}
    n=sum(1 for f in filas if f['key']);tot=sum(f['peso'] for f in filas);ok=sum(f['peso'] for f in filas if f['key'])
    print(f'{exp} {doc} filas {len(filas)} reconocidas {n} ({100*ok/tot:.0f} % del peso)')
json.dump(out,open(os.path.join(BASE,'reparto_pliegos.json'),'w'),ensure_ascii=False,indent=0)
