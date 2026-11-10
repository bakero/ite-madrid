import json,re,sqlite3,collections,unicodedata
from normaliza import nrm
import os,pathlib
BASE=pathlib.Path(__file__).resolve().parents[2]
DB=os.environ.get('ITE_DB',str(BASE/'ite_madrid.sqlite'))
con=sqlite3.connect(DB)
rows=con.execute("""select c.id,c.nombre,c.tipo_edificio,c.subtipo,c.direccion,c.lat,c.lng from centros c
  where coalesce(c.excluido,'')='' and c.lat is not null and c.lng is not null and c.cod_barrio in (select cod from barrios where cod_distrito=13)""").fetchall()
B={}
for cid,n,t,st,d,lat,lng in rows:
    k=(round(lat,5),round(lng,5));b=B.setdefault(k,{'key':f'{k[0]:.5f},{k[1]:.5f}','cents':[],'tipos':set(),'addr':d})
    b['cents'].append(n);b['tipos'].add(t or '')
GEN=r'^(INSTALACION DEPORTIVA MUNICIPAL BASICA|INSTALACION DEPORTIVA BASICA|DEPORTIVO BASICO|CENTRO DE MAYORES Y CENTRO DE DIA|COLEGIO PUBLICO|COLEGIO DE EDUCACION INFANTIL Y PRIMARIA|CEIP|C\.?P\.?|COLEGIO|INSTITUTO DE EDUCACION SECUNDARIA|IES\)?|CENTRO CULTURAL|CENTRO SOCIOCULTURAL|CENTRO DEPORTIVO MUNICIPAL|INSTALACION DEPORTIVA (MUNICIPAL )?(BASICA )?|POLIDEPORTIVO|BIBLIOTECA PUBLICA( MUNICIPAL)?|BIBLIOTECA|ESCUELA INFANTIL|CASA DE NIÑOS|CENTRO MUNICIPAL DE MAYORES|CENTRO DE MAYORES|CENTRO DE DIA( MUNICIPAL)?|CENTRO DE SERVICIOS SOCIALES|PARROQUIA|PARQUE|MERCADO|CENTRO DE SALUD|ESPACIO DE IGUALDAD|CENTRO JUVENIL|SALA DE ESTUDIO|CENTRO)\s+(DE |DEL |DE LA |DE LOS )?'
GENERIC={'PUENTE DE VALLECAS','VALLECAS','MADRID','ENTREVIAS','PALOMERAS','NUMANCIA','SAN DIEGO','PORTAZGO','EL POZO','ARAGON','ASTURIAS','LA RIOJA','MADRID SUR','SAN PABLO','SANTO DOMINGO','LA ALBUFERA','RONDA SUR','MIGUEL HERNANDEZ','LOPE DE VEGA','PALOMERAS BAJAS','BUENOS AIRES','LA MILAGROSA','SAN JOSE','LOS TILOS','RETAMAR','TAJAMAR','AZORIN','NAVACERRADA'}
TYPEW={'Educativo':r'COLEGIO|C\.?E\.?I\.?P|ESCUELA|INSTITUTO|I\.?E\.?S\b|EDUCATIV|DOCENTE|CENTROS? ESCOLAR',
 'Deportivo':r'DEPORTIV|POLIDEPORTIVO|PISCINA|I\.?D\.?B|C\.?D\.?M|PABELLON|CAMPO DE FUTBOL|PISTA',
 'Cultural':r'CULTURAL|BIBLIOTECA|AUDITORIO|SALA DE ESTUDIO|TEATRO',
 'Servicios sociales':r'MAYORES|CENTRO DE DIA|SERVICIOS SOCIALES|ESPACIO DE IGUALDAD|CENTRO JUVENIL|FAMILIA|INFANCIA',
 'Administración y servicios públicos':r'JUNTA MUNICIPAL|SEDE|OFICINA|EDIFICIO',
 'Zona verde':r'PARQUE|JARDIN|ZONA VERDE','Sanitario':r'CENTROS? DE SALUD|AMBULATORIO|SANITARI|HOSPITAL|C\.?S\.?\b','Seguridad y emergencias':r'BOMBEROS|POLICIA|SAMUR|COMISARIA','Comercio':r'MERCADO|MERCADILLO'}
def keys_for(n):
    k=nrm(n);k=re.sub(r'\(.*?\)?$','',k).strip();k=re.sub(r'\(.*?\)','',k).strip()
    core=re.sub(GEN,'',k).strip(' .,"\'«»-')
    core=re.sub(r'\b(DE |DEL |DISTRITO )?(PUENTE DE VALLECAS|VALLECAS)\b','',core).strip(' .,-')
    core=re.sub(r'^(MUNICIPAL|PUBLICO|PUBLICA)( DE| DEL)?\s+','',core).strip()
    out=set()
    if len(core)>=5 and core not in ('PUENTE DE VALLECAS','VALLECAS','MADRID') and not core.startswith(('MUNICIPAL','AL AIRE LIBRE')):out.add(core)
    out={k for k in out if not re.match(r'^(Y|DE|DEL|E|O)\b',k) and '  ' not in k}
    return out
# nombres de calles de Madrid (núcleo sin tipo de vía): si un nombre de centro coincide con una calle, se exige el tipo de centro delante
import json as _j
_c=open(BASE/'app'/'calles.js',encoding='utf-8').read();_c=_j.loads(_c[_c.index('{'):_c.rindex('}')+1])

STREET_RE=r'^(CALLE|AVENIDA|PASEO|PLAZA|RONDA|CAMINO|GLORIETA|TRAVESIA|CARRETERA|BULEVAR|COSTANILLA|PASAJE|CALLEJON|CUESTA|PARQUE|JARDIN)\s+(DE LA |DE LOS |DE LAS |DEL |DE )?'
STREET=r'^(CALLE|AVENIDA|PASEO|PLAZA|RONDA|CAMINO|GLORIETA|TRAVESIA|CARRETERA|BULEVAR|COSTANILLA|PASAJE)\s+(DE LA |DE LOS |DE LAS |DEL |DE )?'
def addr_key(a):
    a=nrm(a).split(',')[0];m=re.match(STREET+r'(.+?)\s+(\d+)\b',a)
    return (m.group(3).strip(),m.group(4)) if m else None
STREETNAMES=set(re.sub(STREET_RE,'',nrm(x)).strip() for x in _c['names'] if x)
for b in B.values():
    b['keys']=set().union(*[keys_for(n) for n in b['cents']])
    b['ak']=addr_key(b['addr'])

NOEDIF=r'VIVIENDA|URBANIZACI|CALZADA|ACERAS?\b|VIA PUBLICA|VIAS PUBLICAS|VIALES|PASO DE VEHICULOS|ALUMBRADO PUBLICO|SEÑALIZACI|ARBOLADO|ENTORNO ESCOLAR|CAMINO ESCOLAR'
def match(txt,pv):
    noedif=bool(re.search(NOEDIF,txt))
    hits=[]
    for b in B.values():
        why=None
        for k in b['keys']:
            if re.search(r'(?<![A-Z])'+re.escape(k)+r'(?![A-Z])',txt):
                tw=[TYPEW[t] for t in b['tipos'] if t in TYPEW]
                typed=any(re.search(w,txt) for w in tw) or any(re.search(w,k) for w in tw)
                strong=len(k.split())>=3 or len(k)>=16
                if k in STREETNAMES or k in GENERIC or len(k)<7:
                    one=len(k.split())==1
                    if (pv or not one) and any(re.search(r'('+w+r')[^|]{0,22}?(?<![A-Z])'+re.escape(k)+r'(?![A-Z])',txt) for w in tw):why='nombre: '+k;break
                    continue
                if noedif:continue
                if (pv and (typed or strong)) or (typed and (strong or len(k.split())>=2)):why='nombre: '+k;break
        if not why and b['ak']:
            st,nu=b['ak'];mm=re.search(r'(?<![A-Z])'+re.escape(st)+r'(?![A-Z])\s*,?\s*(?:N[º°O]\.?|NUM(?:ERO)?\.?)?\s*(\d+)\b',txt)
            if mm and mm.group(1)==nu and not re.search(r'VIVIENDA|URBANIZACI|PASO DE VEHICULOS|CALZADA',txt):why=f'dirección: {st} {nu}'
        if why:hits.append((b['key'],why))
    return hits

ALIAS=[(r'POLIDEPORTIVO (MUNICIPAL )?(DE )?PUENTE DE VALLECAS|(CENTRO DEPORTIVO MUNICIPAL|C\.?D\.?M\.?) PUENTE DE VALLECAS|PAYASO FOFO','40.39146,-3.65986'),
 (r'BIBLIOTECA (PUBLICA )?(MUNICIPAL )?(DE )?VALLECAS\b(?! VILLA)','40.39502,-3.66555'),
 (r'CENTRO (MUNICIPAL )?DE MAYORES (Y CENTRO DE DIA )?(DE )?PUENTE DE VALLECAS','40.39042,-3.65812'),
(r'BOMBEROS (N[º°O]\.? ?|NUM(ERO)?\.? ?)?0?8\b','40.39462,-3.65313'),
 (r'(UNIDAD INTEGRAL|COMISARIA INTEGRAL|U\.?I\.?D\.?)( DE)?( LA)? POLICIA MUNICIPAL( DEL? DISTRITO)?( DE)? PUENTE( DE)? VALLECAS|POLICIA MUNICIPAL( DEL? DISTRITO)?( DE)? PUENTE( DE)? VALLECAS','40.38924,-3.65238'),
 (r'(EDIFICIO )?SEDE (DE LA JUNTA MUNICIPAL )?DEL DISTRITO( DE)? PUENTE( DE)? VALLECAS|JUNTA MUNICIPAL( DEL? DISTRITO)?( DE)? PUENTE( DE)? VALLECAS','40.38920,-3.65180'),
 (r'MERCADO (MUNICIPAL )?(DE )?PUENTE DE VALLECAS','40.39525,-3.66775')]
_match=match
def match(txt,pv):
    h=_match(txt,pv)
    if h:return h
    for rx,k in ALIAS:
        if re.search(rx,txt) and not re.search(NOEDIF,txt):return [(k,'alias: '+rx[:30])]
    return []

_match2=match
def match(txt,pv):
    h=_match2(txt,pv)
    if len(h)>1:
        names=[(k,w) for k,w in h if w.startswith(('nombre','alias'))]
        if names:h=names
        ks=[w.split(': ',1)[1] for k,w in h]
        h=[(k,w) for (k,w),kk in zip(h,ks) if not any(kk!=o and kk in o for o in ks)]
    return h
