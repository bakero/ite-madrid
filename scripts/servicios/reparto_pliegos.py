"""Reparto por edificio de los contratos de servicios de las Juntas (fuera de Puente de Vallecas) leyendo la tabla del
pliego que da el peso de cada edificio: m² construidos (limpieza, mantenimiento) u horas al año (limpieza por horas).

Uso: PLIEGOS_TXT=<carpeta con los .txt de descarga_pliegos.py> python reparto_pliegos.py [exp ...]
  (con expedientes, solo se recalculan esos y el resto de la salida se conserva)
Config: datos/servicios/reparto_pliegos_cfg.json  {exp: {modo: linea|bloque|ancla|totales|sin, doc, medida, [tablas...], [anular: textos de filas mal asignadas],
  [fijar: {texto de fila: edificio} comprobado con la dirección del pliego], [motivo: por qué no hay reparto (modo sin)]}}
  linea  = una fila por edificio; el peso es el número más cercano a la columna de la cabecera (pliegos_tablas.py)
  bloque = varias líneas por edificio (una por trabajador); el peso es la suma de la columna (pliegos_bloques.py)
  ancla = cada número de la columna es un edificio; el nombre, partido alrededor, se asigna al más cercano
  manual = filas transcritas a mano cuando la tabla es irregular: [lote, peso, edificio|null, texto, línea del .txt]
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
SAL=os.path.join(BASE,'reparto_pliegos.json')
SOLO=sys.argv[1:]
out=json.load(open(SAL)) if SOLO and os.path.exists(SAL) else {}
for exp,c in CFG.items():
    if SOLO and exp not in SOLO:continue
    if c['modo']=='sin':out.pop(exp,None);print(exp,'sin reparto:',c.get('motivo',''));continue
    if c['modo']=='manual':  # tabla transcrita a mano del pliego: [lote, peso, edificio|null, texto del pliego, línea]
        doc=c['doc'];filas=[{'key':k,'lote':str(l),'peso':float(w),'texto':f'{t} (l. {i})','how':'manual' if k else '0','man':1} for l,w,k,t,i in c['filas']]
    elif c['modo']=='linea' and c.get('tablas'):  # una fila por edificio, en rangos de líneas con su lote
        cd=PT.E.cod_distrito(PT.exps[exp][0]['distrito']);doc=c['doc'];filas=[]
        for t in c['tablas']:
            for r in PT.tablas(doc,cd,t.get('kind','m2'),t):filas.append({'key':r['key'],'lote':t.get('lote',r['lote']),'peso':r['v'],'texto':r['txt'],'how':r['how']})
    elif c['modo']=='linea':
        cd,kind,best=PT.run(exp,{'doc':c['doc']} if c.get('doc') else {})
        if not best:print(exp,'sin tabla');continue
        _,doc,rows=best;filas=[{'key':r['key'],'lote':r['lote'],'peso':r['v'],'texto':r['txt'],'how':r['how']} for r in rows]
    else:
        rows={'totales':PB.extraer_totales,'ancla':PB.extraer_ancla}.get(c['modo'],PB.extraer)(exp,c);doc=c['doc'];filas=[{'key':r['key'],'lote':r['lote'],'peso':r['v'],'texto':r['txt'],'how':r['how']} for r in rows]
    # filas que no son edificios (fechas, IVA, precios, umbrales, nº de expediente): fuera del total
    BAS=re.compile(r'\b(A[ÑN]O|FECHA|IVA|EUROS?|EXPTE|EXPEDIENTE|HASTA|M[ÁA]S DE|MENOS DE|PRECIO|IMPORTE|CARGO|FIRMA)\b|%|€/|/m2',re.I)
    filas=[f for f in filas if f['key'] or f.get('man') or not (BAS.search(f['texto']) or (f['peso']==int(f['peso']) and 1990<=f['peso']<=2100) or not re.search(r'[A-Za-zÁÉÍÓÚÑ]{4}',re.split(r'\d',f['texto'])[0] or f['texto']))]
    for f in filas:  # asignaciones hechas a mano con la dirección que da el pliego (fijar: {texto de la fila: edificio})
        for t,k in c.get('fijar',{}).items():
            if t in f['texto']:f['key']=k;f['how']='manual'
    for f in filas:  # asignaciones revisadas a mano y descartadas: la fila cuenta en el total pero no se asigna
        if f['key'] and any(a in f['texto'] for a in c.get('anular',[])):f['key']=None;f['how']='anulada'
    if c['modo']!='manual' and c.get('filas'):  # filas transcritas a mano que completan la lectura automática
        filas+=[{'key':k,'lote':str(l),'peso':float(w),'texto':f'{t} (l. {i})','how':'manual' if k else '0','man':1} for l,w,k,t,i in c['filas']]
    for l,t in c.get('total_lote',{}).items():  # filas que no se han podido leer: la diferencia con el total del pliego cuenta sin asignar
        d=t-sum(f['peso'] for f in filas if f['lote']==l)
        if d>0.5:filas.append({'key':None,'lote':l,'peso':round(d,2),'texto':'Diferencia con el total del lote en el pliego (filas no leídas)','how':'total'})
    for f in filas:f.pop('man',None)
    malas=[f['key'] for f in filas if f['key'] and f['key'] not in PT.BK]
    if malas:sys.exit(f'{exp}: edificios que no existen en el mapa: {malas}')
    out[exp]={'metodo':c['medida'],'doc':doc,'filas':filas,**{k:c[k] for k in ('cats','nota','medida_lote') if k in c}}
    n=sum(1 for f in filas if f['key']);tot=sum(f['peso'] for f in filas);ok=sum(f['peso'] for f in filas if f['key'])
    print(f'{exp} {doc} filas {len(filas)} reconocidas {n} ({100*ok/tot:.0f} % del peso)')
json.dump(dict(sorted(out.items())),open(SAL,'w'),ensure_ascii=False,indent=0)
