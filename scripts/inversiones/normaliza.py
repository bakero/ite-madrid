"""Normaliza las filas de contratos (formatos heterogéneos de datos.madrid.es) a un esquema común."""
import json,re,collections,unicodedata
def nrm(s):
    s=unicodedata.normalize('NFD',str(s).upper());s=''.join(c for c in s if unicodedata.category(c)!='Mn' or c=='̃')
    return re.sub(r'\s+',' ',unicodedata.normalize('NFC',s)).strip()
def main():
    global R,F
    R=json.load(open('contratos_vallecas_filtrados.json'))
    F=R['files']
    FIX=str.maketrans({'¢':'ó','£':'ú','¡':'í','¤':'ñ','µ':'Á','§':'º','?':'€'})
    def fix(v):return str(v).translate(FIX) if re.search('[¢£¡¤µ]',str(v)) else str(v)
    def titulo(h):return (not h) or all(not x for x in h[1:]) # fila de título o vacía en lugar de cabecera
    REF={}
    for f in F:  # cabeceras de referencia por conjunto de datos y nº de columnas
        h=f['h']
        if not titulo(h):REF.setdefault((f['u'][:6],len(h)),h)
    def kind(f,h):
        u=f['u'];H=' | '.join(h).upper()
        if u.startswith('300253'):return 'menor'
        if 'TIPO DE INCIDENCIA' in H or h[0].upper().startswith('INCIDENCIA') or 'IMPORTE MODIFICACION' in H or 'TIPO INCID' in H or 'IMPORTE DE LA MODIFICACI' in H:return 'incidencia'
        if 'C.B.' in H or 'CB/CESDA' in H or 'DERIVADO' in H.replace('FECHA FORMALIZACIÓN DERIVADO','') or 'S.H.' in H:return 'basado'
        return 'formalizado'
    def col(h,*pats,excl=()):
        for p in pats:
            for i,x in enumerate(h):
                X=nrm(x)
                if re.search(p,X) and not any(re.search(e,X) for e in excl):return i
        return None
    def num(s):
        s=str(s).replace('€','').replace('?','').replace(' ','').strip()
        if not s:return None
        if re.match(r'^-?\d{1,3}(\.\d{3})*(,\d+)?$',s) or (',' in s and '.' in s and s.rfind(',')>s.rfind('.')):s=s.replace('.','').replace(',','.')
        elif ',' in s:s=s.replace(',','.')
        try:return float(s)
        except:return None
    def year(*vals):
        for v in vals:
            m=re.search(r'\b\d{1,2}/\d{1,2}/(\d{2,4})\b',str(v or ''))
            if m:y=int(m.group(1));return y+2000 if y<100 else y
            m=re.search(r'\b(20[12]\d)\b',str(v or ''))
            if m:return int(m.group(1))
    out=[];skipped=collections.Counter()
    for row in R['rows']:
        fi,vals=row[0],row[1:];f=F[fi];h=f['h']
        if len(h)>200:skipped['incidencia_rota']+=1;continue
        if titulo(h):
            t=nrm(h[0]) if h else ''
            if re.match(r'^(MODIFIC|PRORR|PENALI|CESION|INCIDEN)',t):skipped['incidencia']+=1;continue
            h=REF.get((f['u'][:6],len(h)),h)
        h=[fix(x) for x in h];vals=[fix(x) for x in vals]
        k=kind(f,h)
        if k=='incidencia':skipped['incidencia']+=1;continue
        g=lambda i:vals[i] if i is not None and i<len(vals) else ''
        io=col(h,r'^OBJETO DEL CONTRATO$',r'^OBJETO$',r'DESCRIPCION CONTRATO',r'TITULO DEL EXPEDIENTE',r'OBJETO_CONTRATO',r'^DESCRIPCION$')
        ider=col(h,r'^OBJETO C\.?B',r'OBJETO DERIVADO',r'^OBJETO CB')
        iimp=col(h,r'IMPORTE ADJUDICACI',r'^IMPORTE$',r'^IMPORTE',excl=(r'LICITACION',r'MODIFIC'))
        icen=col(h,r'^CENTRO - SECCION',r'DESCRIPCION CENTRO',r'^SECCION',r'^CE\.GESTOR',r'^CENTRO$',r'^GESTOR')
        iorg=col(h,r'ORGANO DE CONTRATACION',r'^ORG',r'^ORGANISMO$',r'ORGANISMO_CONTRATANTE')
        itip=col(h,r'^TIPO DE CONTRATO',r'^TIPO CONTRATO',r'^TIPO_CONTRATO',r'^T\. EXPEDIENTE',r'TIPO DE EXPEDIENTE')
        iadj=col(h,r'^ADJUDICATARIO$',r'RAZON SOCIAL',r'NOMBRE/RAZON',r'^CONTRATISTA',r'^TERCERO',r'RAZON_SOCIAL')
        ifec=col(h,r'FECHA DE APROBACION C',r'FECHA APROBACION DERIVADO',r'FECHA DE ADJUDICACION',r'FECHA ADJUDICACION',r'F_APROBACION',r'FECHA APROBACION',r'FECH. APRO',r'FECH/ APRO',r'FE\.CONTAB',r'FECHA DE INSCRIPCION',r'FECHA INSCRIPCION')
        iano=col(h,r'^ANO$',r'^A.O$')
        obj=g(io);der=g(ider)
        out.append({'f':f['u'],'kind':k,'obj':obj,'der':der,'imp':num(g(iimp)),'centro':g(icen),'org':g(iorg),'tipo':g(itip),'adj':g(iadj),
                    'year':year(g(ifec))or (int(g(iano)) if str(g(iano)).isdigit() else None) or year(*vals)})
    print(len(out),skipped,collections.Counter(o['kind'] for o in out))
    print(collections.Counter(o['year'] for o in out).most_common(15))
    print('sin objeto',sum(1 for o in out if not o['obj']),'sin importe',sum(1 for o in out if o['imp'] is None))
    json.dump(out,open('contratos_norm.json','w'),ensure_ascii=False)
    
if __name__=="__main__":
    import os,pathlib
    os.chdir(pathlib.Path(__file__).resolve().parents[2]/"datos"/"inversiones")
    main()
