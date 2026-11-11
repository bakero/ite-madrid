"""Lee las tablas de edificios de los pliegos (columna por posición bajo la cabecera) y calcula la cuota de cada
edificio sobre el total del lote, contando también las filas que no se reconocen como edificio del mapa."""
import json,os,re,sys,collections
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','inversiones'));import edificios as E
BK={b['key']:b for b in E.B.values()}
T=os.environ.get('PLIEGOS_TXT','pliegos_txt')
C=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','datos','servicios','empresas_distritos.json')))
V=[c for c in C if c['vigente'] and c['distrito']!='PUENTE DE VALLECAS']
exps=collections.OrderedDict()
for c in V:exps.setdefault(c['exp'],[]).append(c)
docs=collections.defaultdict(list)
for f in sorted(os.listdir(T)):
    if f.endswith('.txt'):docs[f.split('__')[0]].append(f)
HDR={'m2':r'M2\s*CONSTR|CONSTRUID|CONSTRUIDA|SUP\.?\s*CONST|SUPERFICIE\s+CONST|M2\s+CONST|M²\s*CONST',
     'horas':r'HORAS|H\.?\s*/\s*A[ÑN]O|N[ºO]\s*HORAS'}
CATW={'limpieza':'m2','mantenimiento':'m2','auxiliares':'horas','seguridad':'horas'}
NUM=re.compile(r'(?<![\d.,A-Za-z²])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)(?![\d.,])')
SK=re.compile(r'Código de verificación|Verificacion|Firmado por|Fecha Firma|URL de Verif|CSV :|munimadrid|Para la verificación|SECRETARI|JEFA? DE|^\s*P[áa]gina',re.I)
def num(s):return float(s.replace('.','').replace(',','.'))
def lote_de(L,i):
    for j in range(i,max(0,i-300),-1):
        if re.search(r'LOTES|LOTE\s*\d\s*(Y|,)\s*LOTE',L[j],re.I):continue
        m=re.search(r'\bLOTE\s*(?:N[ºO.]\s*)?(\d)\b',L[j],re.I)
        if m:return m.group(1)
    return ''
ABR=[(r'\bC\.?\s?S\.?\s?S\.?(?=\s|$)','CENTRO DE SERVICIOS SOCIALES'),(r'\bC\.?\s?M\.?\s?M\.?(?=\s|$)','CENTRO MUNICIPAL DE MAYORES'),(r'\bC\.\s?M\.(?=\s)','CENTRO DE MAYORES'),
 (r'\bC\.\s?DIA\b|\bC\.\s?D\.(?=\s)','CENTRO DE DIA'),(r'\bC\.?\s?S\.?\s?C\.?(?=\s|$)','CENTRO SOCIOCULTURAL'),(r'\bC\.\s?C\.(?=\s)','CENTRO CULTURAL'),
 (r'\bJ\.\s?M\.(?:\s?D\.)?(?=\s)','JUNTA MUNICIPAL'),(r'\bI\.?\s?D\.?\s?B\.?(?=\s|$)','INSTALACION DEPORTIVA BASICA'),(r'\bC\.?\s?D\.?\s?M\.?(?=\s|$)','CENTRO DEPORTIVO MUNICIPAL'),(r'\bOAC\b','OFICINA DE ATENCION A LA CIUDADANIA')]
def expand(t):
    for a,b in ABR:t=re.sub(a,b,t,flags=re.I)
    return t
GEN=set('CENTRO CENTROS DE DEL LA EL LOS LAS MUNICIPAL MUNICIPALES CULTURAL SOCIAL SOCIALES SERVICIOS SERVICIO MAYORES DIA COLEGIO PUBLICO ESCUELA INFANTIL INSTALACION INSTALACIONES DEPORTIVA DEPORTIVO BASICA JUNTA DISTRITO SEDE EDIFICIO EDIFICIOS Y A EN CON SIN COMUNITARIO SOCIOCULTURAL CEIP CEPA CEE CPEE IES IDB CDM CSS CSC CM CC CD BIBLIOTECA OFICINA ATENCION CIUDADANIA PLAZA CALLE AVENIDA AVDA PASEO NUM NTRA SRA NUESTRA SENORA SAN SANTA SANTO PARQUE ESPACIO ZONA ZONAS AULA CASA'.split())
def toks(t):return {w for w in re.findall(r'[A-Z]{3,}',E.nrm(t)) if w not in GEN}
DT={}
def fuzzy(txt,cd):
    if cd not in DT:DT[cd]=[(b['key'],toks(' '.join(b['cents'])),E.nrm(' '.join(b['cents']))) for b in E.B.values() if b['cd']==cd]
    name=txt.split('|')[0] if txt.count('|')>=1 and len(txt.split('|')[0])>6 else txt
    name=re.sub(r'^\s*\d+[.)]?\s*\|?','',name)
    tk={w for w in toks(name) if w not in toks(DISTN.get(cd,''))}
    if not tk:return None,'0'
    sc=[]
    for k,bt,full in DT[cd]:
        hit=sum(1 for w in tk if w in bt or any(len(w)>=6 and x.startswith(w[:5]) for x in bt))
        if hit:sc.append((hit,k))
    KW=[('DIA',r'\bDIA\b'),('MAY',r'MAYORES|\bC\.?\s?M\.?\s'),('DEP',r'DEPORTIV|I\.?D\.?B|C\.?D\.?M|POLIDEPORTIVO|PABELLON'),('CUL',r'CULTURAL|\bC\.\s?C\.'),('SS',r'SERVICIOS SOCIALES|C\.?S\.?S'),('EDU',r'CEIP|COLEGIO|ESCUELA|E\.?I\.?')]
    rk={a for a,r in KW if re.search(r,E.nrm(expand(name)))}
    full={k:f for k,_,f in DT[cd]}
    sc=[(h+0.5*len([a for a,r in KW if a in rk and re.search(r,full[k])]),k) for h,k in sc]
    sc.sort(reverse=True)
    if sc and int(sc[0][0])==len(tk) and (len(sc)==1 or sc[1][0]<sc[0][0]):return sc[0][1],'fz'
    return None,'0'
DISTN={}
def resolve(txt,cd):
    k,how=resolve1(txt,cd)
    if k is None:
        k2,how2=resolve1(expand(txt),cd)
        if k2:return k2,how2+'+abr'
        k3,how3=fuzzy(txt,cd)
        if k3:return k3,how3
    return k,how
def resolve1(txt,cd):
    h=[x for x in E.match(E.nrm(txt),cd) if BK.get(x[0],{}).get('cd')==cd]
    if len(h)==1:return h[0][0],'1'
    if len(h)>1:
        d=[x for x in h if str(x[1]).startswith('dirección')]
        if len(d)==1:return d[0][0],'dir'
        ks={x[0] for x in h}
        if len(ks)==1:return h[0][0],'1'
        n=E.nrm(txt)
        # 1) el edificio cuya dirección (calle y número) aparece en la fila
        def addr_ok(k):
            a=E.nrm(str(BK[k].get('addr') or ''));m=re.search(r'([A-Z][A-Z ]{3,}?)\s*,?\s*(?:NUM\s*)?(\d+)',a)
            if not m:return False
            st=m.group(1).split()[-1];return st in n and re.search(r'\b'+m.group(2)+r'\b',n) is not None
        ok=[k for k in ks if addr_ok(k)]
        if len(ok)==1:return ok[0],'addr'
        # 2) el nombre que aparece antes en la fila (la columna de nombre va antes que la dirección)
        pos=[]
        for k,why in h:
            t=str(why).split(': ',1)[-1];i=n.find(t)
            pos.append((i if i>=0 else 9999,k))
        pos.sort()
        if pos[0][0]<pos[1][0] and pos[0][0]<9999:return pos[0][1],'pos'
        return None,f'amb{len(h)}'
    return None,'0'
def tablas(f,cd,kind,cfg={}):
    L=open(os.path.join(T,f),encoding='utf-8',errors='replace').read().split('\n')
    hdr=cfg.get('hdr',HDR[kind]);rows=[];col=None;gap=0;prev=''
    for i,l in enumerate(L):
        if cfg.get('desde') and i<cfg['desde']:continue
        if cfg.get('hasta') and i>cfg['hasta']:break
        m=re.search(hdr,l,re.I)
        if m:col=(m.start()+m.end())/2+cfg.get('dx',0);gap=0;prev='';continue
        if col is None:continue
        if re.search(r'^\s*TOTAL|TOTAL\s+(CENTROS|EDIFICIOS|LOTE|M)',l,re.I):col=None;continue
        if SK.search(l) or not l.strip():continue
        ns=[(num(mm.group(1)),(mm.start()+mm.end())/2) for mm in NUM.finditer(l)]
        if re.search(r'(M[áa]s de|Menos de|\bDe\s+[\d.]+\s+a\s+[\d.]+)\s*m2|^\s*(LOTE|TOTAL|SUMA|M[áa]s de|Menos de|Hasta)\b|\bLOTE\s*\d\s*\|?\s*[\d.]+,\d\d',l,re.I):continue
        ns=[(v,p) for v,p in ns if not (28000<=v<=28999 and v==int(v) and not re.search(r'\d\.\d{3}',l[int(p)-4:int(p)+4]))]
        hit=[(v,p) for v,p in ns if abs(p-col)<=cfg.get('tol',14)]
        if hit and re.search(r'[A-Za-zÁÉÍÓÚÑ]{3}',l) and len(re.findall(r'\b[a-záéíóúñ]{4,}\b',l))<=3:
            v=min(hit,key=lambda x:abs(x[1]-col))[0];gap=0
            k,how=resolve(l,cd)
            if k is None and prev:
                k2,how2=resolve(prev+' '+l,cd)
                if k2:k,how=k2,how2+'+prev'
            rows.append({'i':i,'v':v,'lote':lote_de(L,i),'key':k,'how':how,'txt':re.sub(r'\s{2,}',' | ',l.strip())[:120]})
            prev=''
        else:
            gap+=1;prev=l.strip()
            if gap>25:col=None
    return rows
def run(exp,cfg={}):
    cs=exps[exp];cd=E.cod_distrito(cs[0]['distrito']);kind=cfg.get('kind',CATW[cs[0]['cats'][0]])
    best=None
    for f in docs.get(exp.replace('/','_'),[]):
        if cfg.get('doc') and f!=cfg['doc']:continue
        r=tablas(f,cd,kind,cfg)
        sc=sum(1 for x in r if x['key'])
        if r and (best is None or sc>best[0]):best=(sc,f,r)
    return cd,kind,best
