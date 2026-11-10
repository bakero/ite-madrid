"""Lee todos los CSV de contratos de datos.madrid.es (216876 actividad contractual y 300253 menores)
y los pasa a un esquema común. Uso: python normaliza_todo.py <carpeta_csv> <salida.json>"""
import csv,io,json,re,sys,glob,os,unicodedata,collections
def nrm(s):
    s=unicodedata.normalize('NFD',str(s).upper());s=''.join(c for c in s if unicodedata.category(c)!='Mn' or c=='̃')
    return re.sub(r'\s+',' ',unicodedata.normalize('NFC',s)).strip()
FIX=str.maketrans({'¢':'ó','£':'ú','¡':'í','¤':'ñ','µ':'Á','§':'º'})
def fix(v):return str(v).translate(FIX) if re.search('[¢£¡¤µ]',str(v)) else str(v)
def rd(f):
    b=open(f,'rb').read()
    try:t=b.decode('utf-8-sig')
    except UnicodeDecodeError:t=b.decode('cp1252',errors='replace')
    R=list(csv.reader(io.StringIO(t),delimiter=';'))
    i=0
    while i<6 and i<len(R) and sum(1 for x in R[i] if x.strip())<3:i+=1
    return [fix(x).strip() for x in R[i]],[[fix(x) for x in r] for r in R[i+1:] if any(c.strip() for c in r)]
def col(h,*pats,excl=()):
    H=[nrm(x) for x in h]
    for p in pats:
        for i,X in enumerate(H):
            if re.search(p,X) and not any(re.search(e,X) for e in excl):return i
def num(s):
    s=str(s).replace('€','').replace('¿','').replace('?','').replace('\xa0','').replace(' ','').strip()
    if not s:return None
    if re.match(r'^-?\d{1,3}(\.\d{3})*(,\d+)?$',s) or (',' in s and '.' in s and s.rfind(',')>s.rfind('.')):s=s.replace('.','').replace(',','.')
    elif ',' in s:s=s.replace(',','.')
    try:return float(s)
    except ValueError:return None
def fecha(v):
    m=re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',str(v or ''))
    if not m:return None
    y=int(m.group(3));y=y+2000 if y<100 else y
    return f'{y:04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
out=[];cnt=collections.Counter()
for f in sorted(glob.glob(os.path.join(sys.argv[1],'*.csv'))):
    name=os.path.basename(f);h,rows=rd(f);H=' | '.join(nrm(x) for x in h)
    if name.startswith('300253'):kind='menor'
    elif 'IMPORTE PRORROGA' in H:kind='prorroga'
    elif 'TIPO DE INCIDENCIA' in H or 'INCIDENCIA' in nrm(h[0]) or 'IMPORTE MODIFICACI' in H:kind='modificado'
    elif 'CB/CESDA' in H or 'DERIVADO' in H or 'C.B.' in H:kind='basado'
    else:kind='formalizado'
    if kind=='modificado':continue
    I=dict(
     obj=col(h,r'^OBJETO DEL CONTRATO$',r'^OBJETO$',r'DESCRIPCION CONTRATO',r'TITULO DEL EXPEDIENTE',r'OBJETO_CONTRATO',r'OBJETO CTO',r'^DESCRIPCION$'),
     der=col(h,r'^OBJETO CB',r'OBJETO DERIVADO',r'^OBJETO C\.B'),
     imp=col(h,r'IMPORTE PRORROGA') if kind=='prorroga' else col(h,r'IMPORTE ADJUDICACI',r'^IMPORTE$',r'^IMPORTE',excl=(r'LICITACION',r'MODIFIC')),
     cen=col(h,r'^CENTRO - SECCION',r'DESCRIPCION CENTRO',r'^SECCION',r'^CE\.GESTOR',r'^CENTRO$',r'^GESTOR'),
     cend=col(h,r'^DESCRIPCION$') if name.startswith('300253') else None,
     org=col(h,r'ORGANO DE CONTRATACION',r'ORG\.?CONTRATACION',r'ORG_CONTRATACION',r'^ORGANISMO$',r'ORGANISMO_CONTRATANTE'),
     tip=col(h,r'^TIPO DE CONTRATO',r'^TIPO CONTRATO',r'^TIPO_CONTRATO',r'TIPO DE EXPEDIENTE'),
     adj=col(h,r'^ADJUDICATARIO$',r'RAZON SOCIAL',r'NOMBRE/RAZON',r'^CONTRATISTA',r'^TERCERO',r'RAZON_SOCIAL'),
     cif=col(h,r'NIF/CIF',r'^C\.?I\.?F',r'^NIF$',r'^CIF$'),
     fadj=col(h,r'FECHA DE APROBACION CB',r'FECHA APROBACION DERIVADO',r'FECHA DE ADJUDICACION',r'FECHA ADJUDICACION',r'F_APROBACION',r'FECHA APROBACION',r'FECH. APRO',r'FECH/ APRO'),
     fform=col(h,r'FECHA DE FORMALIZACION INC',r'FECHA DE FORMALIZACION CB',r'FECHA FORMALIZACION DERIVADO',r'FECHA DE FORMALIZACION',r'FECHA FORMALIZACION'),
     plazo=col(h,r'^PLAZO CB',r'PLAZO DERIVADO',r'^PLAZO$',r'^PLAZO'),
     exp=col(h,r'N\. DE EXPEDIENTE CB',r'^N\. DE EXPEDIENTE',r'NUMERO EXPEDIENTE',r'NUM\.EXPEDIENTE',r'N. EXPED',r'^EXPEDIENTE$',r'N.? EXPEDIENTE'),
     am=col(h,r'^ACUERDO MARCO$'),
     anio=col(h,r'^ANO$',r'^A.O$'),finsc=col(h,r'FECHA DE INSCRIPCION',r'FECHA INSCRIPCION$',r'^FECHA INSCRIPCION'))
    g=lambda r,k:(r[I[k]].strip() if I[k] is not None and I[k]<len(r) else '')
    for r in rows:
        o={k:g(r,k) for k in ['obj','der','cen','org','tip','adj','cif','plazo','exp']}
        if I['cend'] is not None:o['cen']=g(r,'cend') or o['cen']
        o['imp']=num(g(r,'imp'));o['kind']=kind;o['f']=name
        o['fecha']=(fecha(g(r,'fform')) or fecha(g(r,'finsc'))) if kind=='prorroga' else (fecha(g(r,'fform')) or fecha(g(r,'fadj')) or fecha(g(r,'finsc')))
        if not o['fecha'] and g(r,'anio').isdigit():o['fecha']=g(r,'anio')+'-01-01'
        if not (o['obj'] or o['der']):continue
        out.append(o);cnt[kind]+=1
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False)
print(len(out),cnt,collections.Counter((o['fecha'] or '????')[:4] for o in out).most_common(14))
