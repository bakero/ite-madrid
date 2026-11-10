"""Contratos de servicios de edificios (limpieza, seguridad, auxiliares, mantenimiento) de las 21 Juntas de Distrito.
Uso: python empresas_distritos.py todos.json salida.json [enlaces.json]
Si el objeto inscrito es solo el nombre del lote («Lote 1 - Colegios»), la categoría se toma del título de la licitación en la Plataforma (enlaces.json)."""
import json,re,sys,pathlib,collections,datetime
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from comun import *
T=json.load(open(sys.argv[1]))
L=json.load(open(sys.argv[3])) if len(sys.argv)>3 else {}
ACT=r'ACTIVIDAD|CAMPAMENT|PELUQU|COMEDOR|CATERING|CAFETER|TRANSPORTE|PROGRAMA|PROYECTO|FIESTA|CABALGATA|TALLER|ANIMACI|MEDIACI|APOYO|ATENCION|SOCIOEDUC|FESTIVAL|INTERVENCI|NAVID|ESPECTAC|DINAMIZ|OCIO|OBRAS|REDACCI'
def titulo(exp):
    v=L.get(exp)
    return ' '.join(t for _,t in v) if isinstance(v,list) else ''
DN={'CHAMBERO':'CHAMBERI','FUENCARRAL - EL PARDO':'FUENCARRAL-EL PARDO','SAN BLAS - CANILLEJAS':'SAN BLAS-CANILLEJAS'}
def meses(p):
    try:return float(str(p).replace(',','.'))
    except ValueError:return None
C={};P=[]
for o in T:
    cen=E.nrm(o['org']+' | '+o['cen'])
    m=re.search(r'DISTRITO DE ([A-ZÑ\- ]+?)\s*(\||$)',cen)
    if not m or not re.search('SERVICIO',E.nrm(o['tip'])) or o['kind'] not in('formalizado','prorroga'):continue
    txt=E.nrm(o['obj']+' | '+o['der'])
    if re.search(EXCL,txt):continue
    c=cats(txt) or EXP_CAT.get(o['exp'].strip(),[])
    if not c and re.match(r'\s*LOTE\s*\d',E.nrm(o['obj'])) and not re.search(ACT,E.nrm(o['obj'])):
        tt=E.nrm(titulo(o['exp'].strip()))
        if tt and not re.search(EXCL,tt):c=cats(tt)
    if not c:continue
    d=m.group(1).strip();d=DN.get(d,d)
    lote=re.match(r'\s*Lote\s*(\d+)',o['obj'],re.I);lote=lote.group(1) if lote else ''
    if o['kind']=='prorroga':P.append((d,o,lote));continue
    k=(d,o['exp'].strip(),lote)
    x=C.setdefault(k,{'distrito':d,'exp':o['exp'].strip(),'lote':lote,'objeto':re.sub(r'\s+',' ',o['obj']).strip()[:180],'cats':c,'empresa':emp(o['adj']),
        'fecha':o['fecha'],'meses':meses(o['plazo']),'importe':0,'prorrogas':[]})
    x['importe']+=o['imp'] or 0
for d,o,lote in P:
    for x in C.values():
        if x['distrito']==d and x['exp']==o['exp'].strip() and (x['lote']==lote or not lote) and o['fecha'] and x['fecha'] and o['fecha']>x['fecha']:
            p={'fecha':o['fecha'],'meses':meses(o['plazo']),'importe':o['imp'] or 0}
            if p not in x['prorrogas']:x['prorrogas'].append(p)
hoy=datetime.date.today();H=hoy.year*12+hoy.month
for x in C.values():
    if x['fecha'] and x['meses']:
        f=int(round(int(x['fecha'][:4])*12+int(x['fecha'][5:7])+x['meses']+sum(p['meses'] or 0 for p in x['prorrogas'])))
        x['fin']=f'{(f-1)//12:04d}-{(f-1)%12+1:02d}';x['vigente']=f>=H
        x['anual']=round(x['importe']*12/x['meses'],2) if x['importe'] else None
    else:x['fin']=None;x['vigente']=False;x['anual']=None
# Un contrato posterior del mismo servicio y lote en el distrito lo sustituye: sus prórrogas no pueden llegar
# más allá del inicio del nuevo (el plazo inicial se respeta siempre).
def mes(f):return int(f[:4])*12+int(f[5:7])
for x in C.values():
    if not(x['fecha'] and x['meses'] and x['fin']):continue
    ini=int(round(mes(x['fecha'])+x['meses']))
    for y in C.values():
        if y is x or y['distrito']!=x['distrito'] or y['cats'][0]!=x['cats'][0] or not y['fecha'] or y['fecha']<=x['fecha']:continue
        if x['lote'] and y['lote'] and x['lote']!=y['lote']:continue
        f=max(ini,mes(y['fecha']))
        if f<mes(x['fin']+'-01')+1:
            x['fin']=f'{(f-1)//12:04d}-{(f-1)%12+1:02d}';x['vigente']=f>=H;x['sustituido']=y['exp']
out=sorted(C.values(),key=lambda x:(x['distrito'],x['cats'][0],x['fecha'] or ''))
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
V=[x for x in out if x['vigente']]
print(len(out),'contratos ·',len(V),'vigentes ·',len({x['distrito'] for x in out}),'distritos')
cov=collections.defaultdict(set)
for x in V:cov[x['cats'][0]].add(x['distrito'])
print({k:len(v) for k,v in cov.items()})
e=collections.Counter()
for x in V:e[(x['empresa'][:35],x['cats'][0])]+=x['anual'] or 0
for k,v in e.most_common(25):print(f'{v:>12,.0f}',k)
