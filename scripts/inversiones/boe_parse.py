import json,re,collections,sys,io
_o=sys.stdout;sys.stdout=io.StringIO()
import edificios as E
import os;os.chdir(E.BASE/'datos'/'inversiones')
sys.stdout=_o
B=json.load(open('boe_vallecas_1995_2014.json'))
PTA=166.386
NUM=r'([0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]{1,2})?|[0-9]+(?:,[0-9]{1,2})?)'
def num(s):return float(s.replace('.','').replace(',','.'))
def importe(seg):
    m=re.search(NUM+r'\s*(euros|€|pesetas|ptas)',seg,re.I)
    if not m:return None
    v=num(m.group(1));return round(v/PTA,2) if m.group(2).lower().startswith('p') else v
def parse(o):
    T=o['texto'];tt=o['titulo']
    tipo='formalización' if re.search(r'formaliz',tt,re.I) else 'adjudicación' if re.search(r'adjudicaci',tt,re.I) and not re.search(r'convoca|licitaci|para la adjudicaci',tt,re.I) else 'licitación' if re.search(r'licita|convoca|concurso|subasta|para la adjudicaci',tt,re.I) else 'otro'
    m=re.search(r'Descripci[oó]n(?: del objeto)?:\s*(.+?)(?=\s(?:[a-z]\)|\d\.\d)\s|\s\d+\.\s|$)',T)
    obj=m.group(1) if m else ''
    q=re.search(r'[«"“](.+?)[»"”]',tt)
    if q and len(q.group(1))>=20:obj=q.group(1)
    elif (not obj or len(obj)<25 or re.search(r'v[eé]ase|ver (el )?t[ií]tulo|del t[ií]tulo|indicad',obj,re.I)) and q:obj=q.group(1)
    if not obj:obj=tt
    exp=(re.search(r'(?:N[uú]mero de )?expediente:?\s*([0-9A-Za-z][0-9A-Za-z\/\-\.]{4,24})',T,re.I) or [None,''])[1].rstrip('.')
    lic=None;adj=None
    m=re.search(r'Presupuesto base de licitaci[oó]n[^.]{0,120}?(?:\.\s*)?(.{0,200})',T,re.I)
    if m:lic=importe(m.group(0)+m.group(1))
    m=re.search(r'(?:Importe (?:de|total de) (?:la )?adjudicaci[oó]n|Importe de adjudicaci[oó]n|Adjudicaci[oó]n[^.]{0,200}?Importe|c\) Importe)[^0-9]{0,60}'+NUM+r'\s*(euros|€|pesetas|ptas)',T,re.I)
    if m:
        v=num(m.group(1));adj=round(v/PTA,2) if m.group(2).lower().startswith('p') else v
    ent=('AYTO' if re.search(r'Ayuntamiento de Madrid|Junta Municipal|Distrito de|Gerencia (Municipal|del Distrito)|Madrid Espacios y Congresos|Empresa Municipal',tt+T[:500]) else
         'CAM' if re.search(r'Comunidad de Madrid|Consejer[ií]a|Instituto de la Vivienda|IVIMA|Canal de Isabel|Mintra|Servicio Madrile',tt+T[:500]) else 'OTRO')
    return {'id':o['id'],'fecha':o['fecha'],'anio':int(o['fecha'][:4]),'tipo':tipo,'ent':ent,'exp':exp,'obj':obj.strip()[:400],'lic':lic,'adj':adj,'titulo':tt}
P=[parse(o) for o in B]
P=[p for p in P if p['tipo']!='otro']
print('anuncios de contratación:',len(P),collections.Counter(p['ent'] for p in P),collections.Counter(p['tipo'] for p in P))
out=[]
for p in P:
    txt=E.nrm(p['obj']) if not re.match(r'(ANUNCIO|RESOLUCI)',E.nrm(p['obj'])) else E.nrm(p['obj']+' | '+p['titulo'])
    if E.nrm(p['obj'])!=E.nrm(p['titulo']) and len(p['obj'])<80: txt=E.nrm(p['obj']+' | '+p['titulo'])
    if re.search(r'LIMPIEZA|VIGILANCIA|SEGURIDAD (Y|PRIVADA)|COMEDOR|ALIMENTACI|TRANSPORTE ESCOLAR|AYUDA A DOMICILIO|NOTIFICACI|EXPROPIACI(?!.*SUELO)|GESTION DE SERVICIOS|GESTION INTEGRAL DE LOS SERVICIOS COMPLEMENTARIOS',txt):continue
    _t=E.nrm(p['titulo']+' '+p['obj'])
    pv=bool(re.search(r'PUENTE DE VALLECAS|PUENTE VALLECAS',_t)) or bool(re.search(r'VALLECAS',txt) and not re.search(r'VILLA DE VALLECAS|VALLECAS VILLA|ENSANCHE DE VALLECAS|PAU DE VALLECAS',txt))
    if re.search(r'IMPARTICI|TALLERES|^SERVICIO|SERVICIOS? (DE|PARA)|MANTENIMIENTO|CONSULTORIA|ASISTENCIA TECNICA|DIRECCION (FACULTATIVA|DE (LA )?OBRA)|CONTROL DE CALIDAD|ESCALERAS MECANICAS',txt):continue
    if not re.search(r'OBRA|REFORMA|REHABILIT|ACONDICION|CONSTRUCCI|AMPLIACI|REPARACI|MEJORA|ADECUACI|SUSTITUC|CUBIERTA|CLIMATIZ|CALEFACC|IMPERMEAB|ACCESIBIL|PABELL|ESCUELA INFANTIL EN|EDIFICIO|DOTAR|EQUIPAMIENTO|ADQUISICI|REDACCION DEL PROYECTO',txt):continue
    h=E.match(txt,pv)
    if h:p['hits']=h;out.append(p)
# dedupe: mismo edificio, ±1 año, objeto parecido (o uno es licitación y otro adjudicación)
import difflib
def core(o):return re.sub(r'^(OBRAS? (DE|PARA) (LA |EL |LAS |LOS )?)','',E.nrm(o))[:120]
groups=[]
for p in sorted(out,key=lambda p:p['fecha']):
    ks=tuple(sorted(k for k,w in p['hits']))
    for g in groups:
        q=g[0]
        if tuple(sorted(k for k,w in q['hits']))==ks and abs(q['anio']-p['anio'])<=1 and (difflib.SequenceMatcher(None,core(q['obj']),core(p['obj'])).ratio()>0.75 or re.match(r'(RESOLUCI|ANUNCIO)',E.nrm(p['obj'])) or re.match(r'(RESOLUCI|ANUNCIO)',E.nrm(q['obj']))):
            a1=q['adj'] or q['lic'];a2=p['adj'] or p['lic']
            if a1 and a2 and not (0.6<a1/a2<1.67):continue
            g.append(p);break
    else:groups.append([p])
res=[]
for v in groups:
    v.sort(key=lambda p:(p['adj'] is None, re.match(r'(RESOLUCI|ANUNCIO)',E.nrm(p['obj'])) is not None, p['fecha']))
    best=dict(v[0]);best['anuncios']=[x['id'] for x in v]
    if re.match(r'(RESOLUCI|ANUNCIO)',E.nrm(best['obj'])):
        alt=[x['obj'] for x in v if not re.match(r'(RESOLUCI|ANUNCIO)',E.nrm(x['obj']))]
        if alt:best['obj']=alt[0]
    best['importe']=next((x['adj'] for x in v if x['adj']),None) or next((x['lic'] for x in v if x['lic']),None)
    best['importe_tipo']='adjudicación' if any(x['adj'] for x in v) else ('licitación' if best['importe'] else None)
    best['anio']=min(x['anio'] for x in v)
    res.append(best)
json.dump(res,open('boe_match.json','w'),ensure_ascii=False,indent=0)
print('contratos BOE con edificio:',len(res),'| con importe:',sum(1 for r in res if r['importe']),'| adj:',sum(1 for r in res if r['importe_tipo']=='adjudicación'))
print('edificios:',len({k for r in res for k,w in r['hits']}))
print(collections.Counter(r['anio']//5*5 for r in res))
for r in sorted(res,key=lambda r:r['anio']):
    names=[[b['cents'][0] for b in E.B.values() if b['key']==k][0][:35] for k,w in r['hits']]
    print(r['anio'],r['ent'],r['tipo'][:4],r['importe'],r['importe_tipo'],'|',r['obj'][:95],'|',names,[w for k,w in r['hits']])
