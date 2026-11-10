"""Genera app/empresas.js: empresa de cada servicio (limpieza, seguridad, auxiliares, mantenimiento) en cada distrito,
con los contratos vigentes de las Juntas de Distrito. Uso: python empresas_app.py empresas_distritos.json [enlaces.json]"""
import json,re,sys,pathlib,collections,datetime,unicodedata
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from comun import *
X=json.load(open(sys.argv[1]))
L=json.load(open(sys.argv[2])) if len(sys.argv)>2 else {}
def k(s):return re.sub(r'[^A-Z]','',E.nrm(s))
DIS={k(d):d for d in ['Villaverde','Villa de Vallecas','Carabanchel','Usera','Puente de Vallecas','Latina','Arganzuela','Vicálvaro','Moratalaz','Retiro','Centro','Ciudad Lineal','San Blas - Canillejas','Moncloa - Aravaca','Salamanca','Chamberí','Chamartín','Tetuán','Barajas','Hortaleza','Fuencarral - El Pardo']}
def ekey(a):
    a=E.nrm(a);a=re.sub(r'\bUTE\b','UTE',a)
    a=re.sub(r'[,\.]',' ',a);a=re.sub(r'\b(S ?A ?U?|S ?L ?U?|SOCIEDAD ANONIMA( UNIPERSONAL)?|SOCIEDAD LIMITADA|SL|SA|SAU|SLU|S COOP|COOP)\b',' ',a)
    return re.sub(r'\s+',' ',a).strip()
def enlace(x):return plataforma_url(L,x['exp'],x['objeto']+' '+x['distrito'])
nombres=collections.defaultdict(collections.Counter)
for x in X:nombres[ekey(x['empresa'])][x['empresa']]+=1
out=[]
for x in X:
    d=DIS.get(k(x['distrito']))
    if not d:continue
    out.append({'d':d,'cat':x['cats'][0],'cats':x['cats'],'emp':nombres[ekey(x['empresa'])].most_common(1)[0][0],'ek':ekey(x['empresa']),'exp':x['exp'],'lote':x['lote'],
      'obj':x['objeto'],'fecha':x['fecha'],'fin':x['fin'],'meses':x['meses'],'importe':round(x['importe'],2),'anual':x['anual'],'pror':len(x['prorrogas']),'vig':x['vigente'],'url':enlace(x)})
js={'generado':datetime.date.today().isoformat(),'cats':['limpieza','seguridad','auxiliares','mantenimiento'],'contratos':out}
open(E.BASE/'app'/'empresas.js','w',encoding='utf-8').write('window.EMPRESAS='+json.dumps(js,ensure_ascii=False,separators=(',',':'))+';\n')
V=[o for o in out if o['vig']]
print(len(out),'contratos,',len(V),'vigentes, con enlace',sum(1 for o in out if o['url']))
for c in js['cats']:
    cov=collections.defaultdict(list)
    for o in V:
        if o['cat']==c:cov[o['d']].append(o['emp'][:22])
    print(c,len(cov),'distritos sin dato:',sorted(set(DIS.values())-set(cov)))
