"""Une los contratos de servicios (servicios_pv.json) con el reparto por edificio de los pliegos
(reparto.json) y genera app/servicios.js. Uso:
  python servicios_app.py <servicios_pv.json> <reparto.json> [enlaces.json] [empresas_distritos.json reparto_madrid.json]
Puente de Vallecas: importe estimado por edificio con los pesos de sus pliegos.
Resto de distritos: contratos de servicios de cada Junta (empresas_distritos.json) y edificios que figuran en sus
pliegos (reparto_madrid.json, de reparto_generico.py), sin repartir el importe por edificio."""
import json,re,sys,pathlib,collections,datetime
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'inversiones'))
import edificios as E
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from comun import plataforma_url
S=json.load(open(sys.argv[1]));R=json.load(open(sys.argv[2]))
L=json.load(open(sys.argv[3])) if len(sys.argv)>3 else {}
EDI=json.load(open(sys.argv[4])) if len(sys.argv)>4 else []
RG=json.load(open(sys.argv[5])) if len(sys.argv)>5 else {}
def meses(p):
    try:return float(str(p).replace(',','.'))
    except ValueError:return None
CATS=['limpieza','seguridad','auxiliares','mantenimiento','jardinería','control de plagas']
# 1) contratos: uno por expediente (+ lote), con el importe de la formalización
C={}
for x in S:
    if x['kind']=='prorroga':continue
    lote=re.match(r'\s*Lote\s*(\d+)',x['obj'],re.I);lote=lote.group(1) if lote else ''
    k=(x['exp'] or x['obj'][:60],lote,x['empkey'])
    c=C.setdefault(k,{'exp':x['exp'],'lote':lote,'objeto':re.sub(r'\s+',' ',x['obj']).strip()[:200],'empresa':x['empresa'],'cats':x['cats'],'fecha':x['fecha'],
        'meses':meses(x['plazo']),'importe':0,'tipo':x['kind'],'ambito':x['ambito'],'edificios':x['edificios'],'organo':x['organo']})
    c['importe']+=x['imp'] or 0
    if x['fecha'] and (not c['fecha'] or x['fecha']<c['fecha']):c['fecha']=x['fecha']
# prórrogas posteriores a la formalización: solo como aviso
for x in S:
    if x['kind']!='prorroga':continue
    for c in C.values():
        if c['exp']==x['exp'] and x['fecha'] and c['fecha'] and x['fecha']>c['fecha'] and (not c['lote'] or re.match(r'\s*Lote\s*'+c['lote']+r'\b',x['obj'],re.I) or not re.match(r'\s*Lote',x['obj'],re.I)):
            c['prorrogado']=True;c.setdefault('prorrogas',[])
            p={'fecha':x['fecha'],'meses':meses(x['plazo']),'importe':x['imp'] or 0}
            if p not in c['prorrogas']:c['prorrogas'].append(p)
# 2) reparto por edificio con los pliegos
LOTE={'300/2024/00115':lambda g:'1' if g and g.upper().startswith('COLEGIOS') else '2'}
MET={'300/2025/00051':'horas de limpieza del pliego (anexo III)','300/2022/00668':'horas anuales de limpieza del estudio económico',
     '300/2023/00637':'coste por edificio del estudio económico','300/2024/00115':'m² construidos del estudio económico',
     '300/2020/00777':'m² construidos del pliego (anexo I)'}
ED=collections.defaultdict(list)
for c in C.values():
    r=R.get(c['exp'])
    if not r:
        if c['ambito']=='edificio' and len(c['edificios'])==1:
            ED[c['edificios'][0]].append({'c':c,'cuota':c['importe'],'peso':1,'metodo':'contrato de un solo edificio'})
        continue
    filas=r['filas'];grp={}
    if c['exp'] in LOTE:
        f=LOTE[c['exp']];tot=sum(x['peso'] for x in filas if f(x['grupo'])==c['lote'])
        ok=[e for e in r['edif'] if f(next((x['grupo'] for x in filas if x['texto']==e['texto']),''))==c['lote']]
    else:tot=r['peso_total'];ok=r['edif']
    c['reparto']=MET.get(c['exp']);c['edificios']=sorted({e['key'] for e in ok})
    for e in ok:
        if tot and e['peso']>0:ED[e['key']].append({'c':c,'cuota':c['importe']*e['peso']/tot,'peso':e['peso'],'metodo':MET.get(c['exp'])})
# 3) export
Y0=datetime.date.today().year
# contrato más reciente de cada servicio con reparto por edificio (limpieza de edificios, limpieza de colegios, seguridad, mantenimiento)
ULTIMOS={'300/2025/00051','300/2022/00668','300/2023/00637','300/2024/00115'}
def fin(c):
    if not c['fecha'] or not c['meses']:return None
    y,m=int(c['fecha'][:4]),int(c['fecha'][5:7]);f=y*12+m+c['meses']
    for p in c.get('prorrogas',[]):f+=p['meses'] or 0
    return f
def vigente(c):
    f=fin(c)
    if f is None:return False
    fin_=f
    t=datetime.date.today();return fin_>=t.year*12+t.month
CL=sorted(C.values(),key=lambda c:c['fecha'] or '')
idx={id(c):i for i,c in enumerate(CL)}
contratos=[{'exp':c['exp'],'lote':c['lote'],'objeto':c['objeto'],'empresa':c['empresa'],'cats':c['cats'],'fecha':c['fecha'],'meses':c['meses'],
  'importe':round(c['importe'],2),'ambito':c['ambito'],'reparto':c.get('reparto'),'n_edif':len(c['edificios']),'prorrogado':bool(c.get('prorrogado')),'prorroga_meses':sum(p['meses'] or 0 for p in c.get('prorrogas',[])),'prorroga_importe':round(sum(p['importe'] for p in c.get('prorrogas',[])),2),'vigente':vigente(c),'ultimo':c['exp'] in ULTIMOS,'url':plataforma_url(L,c['exp'],c['objeto'])} for c in CL]
edif={}
for k,LL in ED.items():
    rows=[];anual=collections.defaultdict(float)
    for x in sorted(LL,key=lambda x:x["c"]["fecha"] or "",reverse=True):
        c=x['c'];rows.append([idx[id(c)],round(x['cuota'],2)])
        if vigente(c) and c['meses']:
            for cat in c['cats'][:1]:anual[cat]+=x['cuota']*12/c['meses']
    edif[k]={'s':rows,'anual':{k2:round(v,2) for k2,v in anual.items()},'tot_anual':round(sum(anual.values()),2)}
# ---- resto de distritos: edificios citados en los pliegos de los contratos de cada Junta
TB={b['key']:b['tipos'] for b in E.B.values()}
DIS=set()
def lote_ok(c,e):
    """¿El edificio e (del pliego) es del lote del contrato c?"""
    if not c['lote']:return True
    if e.get('lote'):return e['lote']==c['lote']
    o=E.nrm(c['objeto']);edu='Educativo' in TB.get(e['key'],())
    if re.search(r'COLEGIO|EDUCATIV|ESCUELA|DOCENTE|C\.?E\.?I\.?P',o) and not re.search(r'EDIFICIOS? Y|DEPORTIV|CENTROS? CULTURAL',o):return edu
    if re.search(r'EDIFICIOS|DEPORTIV|CULTURAL|MAYORES|SOCIALES|SEDE|JUNTA',o) and not re.search(r'COLEGIO',o):return not edu
    return True
for c in EDI:
    cd=E.cod_distrito(c['distrito'])
    if cd in (None,13):continue
    r=RG.get(c['exp'])
    if not r:continue
    ok=[e for e in r['edif'] if lote_ok(c,e)]
    if not ok:continue
    DIS.add(cd)
    meses_p=sum((p['meses'] or 0) for p in c.get('prorrogas',[]))
    i=len(contratos)
    contratos.append({'exp':c['exp'],'lote':c['lote'],'objeto':c['objeto'],'empresa':c['empresa'],'cats':c['cats'],'fecha':c['fecha'],'meses':c['meses'],
      'importe':round(c['importe'],2),'ambito':'distrito','reparto':None,'n_edif':len({e['key'] for e in ok}),'prorrogado':bool(c.get('prorrogas')),
      'prorroga_meses':meses_p,'prorroga_importe':round(sum(p['importe'] for p in c.get('prorrogas',[])),2),'vigente':c['vigente'],'ultimo':False,
      'url':plataforma_url(L,c['exp'],c['objeto']),'anual':c['anual'],'fin':c['fin'],'cd':cd,'sin_reparto':True})
    for k in sorted({e['key'] for e in ok}):
        d=edif.setdefault(k,{'s':[],'anual':{},'tot_anual':0})
        d['s'].append([i,None])
for d in edif.values():d['s'].sort(key=lambda x:-(int((contratos[x[0]]['fecha'] or '0')[:4])))
js={'generado':datetime.date.today().isoformat(),'distritos':sorted({13}|DIS),'cats':CATS,'contratos':contratos,'edificios':edif}
out=E.BASE/'app'/'servicios.js'
open(out,'w',encoding='utf-8').write('window.SERVICIOS='+json.dumps(js,ensure_ascii=False,separators=(',',':'))+';\n')
print('contratos',len(contratos),'vigentes',sum(c['vigente'] for c in contratos),'· edificios con reparto',len(edif))
N={b['key']:b['cents'][0] for b in E.B.values()}
for k,v in sorted(edif.items(),key=lambda kv:-kv[1]['tot_anual'])[:15]:print(f"{v['tot_anual']:>10,.0f} €/año",N.get(k,k)[:50],v['anual'])
tot=collections.Counter()
for v in edif.values():
    for c2,a in v['anual'].items():tot[c2]+=a
print({k:round(v) for k,v in tot.items()})
for c in contratos:
    if c['vigente']:print('VIG',c['exp'],c['lote'],c['cats'],c['empresa'][:30],c['importe'],c['meses'],c['fecha'],c['reparto'])
