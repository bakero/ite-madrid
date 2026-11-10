"""Contratos de servicios (limpieza, seguridad, auxiliares, mantenimiento, jardinería, plagas) que cubren
edificios públicos de Puente de Vallecas. Entrada: todos.json (normaliza_todo.py). Salida: servicios_pv.json"""
import json,re,sys,collections,os,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'inversiones'))
import edificios as E
src=sys.argv[1] if len(sys.argv)>1 else 'todos.json';dst=sys.argv[2] if len(sys.argv)>2 else 'servicios_pv.json'
T=json.load(open(src))
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from comun import *
out=[];why=collections.Counter()
for o in T:
    txt=E.nrm(o['obj']+' | '+o['der']);cen=E.nrm(o['cen']+' | '+o['org'])
    if not re.search(r'SERVICIO',E.nrm(o['tip'])) and not (o['kind']=='menor' and not o['tip']):continue
    if re.search(EXCL,txt):continue
    c=cats(txt) or EXP_CAT.get(o['exp'].strip(),[])
    if not c:continue
    distPV='PUENTE DE VALLECAS' in cen
    ment=bool(re.search(PVDIST,txt))
    h=E.match(E.nrm(o['der'] or o['obj']),distPV or ment) if (distPV or ment or True) else []
    if len(h)>3:h=[]
    if not (distPV or ment or h):continue
    # ámbito
    if h and len(h)==1:amb='edificio'
    elif h:amb='varios edificios'
    elif distPV:amb='distrito'
    elif re.search(r'DISTRITOS?:|LOTE.*(CIUDAD LINEAL|MORATALAZ|USERA|VILLAVERDE|RETIRO|SAN BLAS|VICALVARO|ARGANZUELA)',txt):amb='varios distritos'
    else:amb='distrito'
    why[(amb,distPV,ment)]+=1
    out.append({'fecha':o['fecha'],'anio':int(o['fecha'][:4]) if o['fecha'] else None,'kind':o['kind'],'cats':c,'obj':o['obj'].strip(),'der':o['der'].strip(),
      'empresa':emp(o['adj']),'empkey':empkey(emp(o['adj'])),'cif':o['cif'],'imp':o['imp'],'plazo':o['plazo'],'exp':o['exp'],'organo':(o['org'] or o['cen']).strip(),
      'ambito':amb,'edificios':[k for k,w in h],'cruce':[w for k,w in h],'f':o['f']})
# deduplicar (mismo expediente, empresa, importe y tipo de registro)
seen=set();res=[]
for x in sorted(out,key=lambda x:(x['fecha'] or '')):
    sig=(x['exp'],x['empkey'],round(x['imp'] or 0),x['kind'],x['der'][:40])
    if sig in seen:continue
    seen.add(sig);res.append(x)
json.dump(res,open(dst,'w'),ensure_ascii=False)
print(len(out),'→',len(res),why)
c=collections.Counter();e=collections.defaultdict(float)
for x in res:
    for k in x['cats']:c[(k,x['ambito'])]+=1
    e[(x['empresa'][:40],x['cats'][0],x['ambito'])]+=x['imp'] or 0
for k,v in sorted(c.items()):print(k,v)
for k,v in sorted(e.items(),key=lambda kv:-kv[1])[:40]:print(f'{v:>13,.0f}',k)
