"""Reparto por edificio de los grandes contratos de servicios del distrito de Puente de Vallecas,
a partir de los pliegos y estudios económicos publicados en la Plataforma de Contratación.
Cada función devuelve [(texto_fila, peso)] y el peso se convierte en cuota del importe del contrato."""
import re,sys,pathlib,json,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'inversiones'))
import edificios as E
D=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.')
def num(s):return float(s.replace('.','').replace(',','.'))
def txt(n):return open(D/f'{n}.txt',encoding='utf-8',errors='replace').read().split('\n')
SKIP=r'Código de verificación|VerificacionCove|Firmado por|Cargo:|Fecha:|Página|Servicio de Medio|CL Sierra|Tel\.|ESTUDIO ECON|Pliego de Prescripciones|^\s*\d+\s*$|Para la verificación|^\s*2\.munimadrid'
def tabla_m2(lines,ini,fin_rx=r'Solar Municipal|TOTAL EDIFICIOS|^\s*$'):
    """Tablas «Nombre Dirección m² construidos m² libre %»: filas partidas en varias líneas."""
    rows=[];buf=[];grupo=None
    for l in lines[ini:]:
        if re.search(SKIP,l):continue
        if re.search(r'^\s*(COLEGIOS|EDIFICIOS|POLIDEPORTIVOS|INSTALACIONES DEPORTIVAS)',l.strip()) and (not re.search(r'\d',l) or re.search(r'LOTE\s*\d',l)):grupo=l.strip();buf=[];continue
        if 'TOTAL' in l:buf=[];
        m=re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s+[\d,]+\s?%',l)
        if m and not re.search(r'TOTAL',l,re.I):
            row=' '.join(x.strip() for x in buf+[l[:m.start()]]);rows.append((grupo,row,num(m.group(1))));buf=[]
        elif l.strip() and 'TOTAL' not in l:buf.append(l)
        if len(rows)>5 and re.search(r'ANEXO II\b',l):break
    return rows
def horas_anexo(lines,ini,fin):
    rows=[];cur=None;h=0
    for l in lines[ini:fin]:
        if re.search(SKIP,l):continue
        m=re.match(r'^\s*(\d{1,2})\.\s+(.+)$',l)
        if m and not re.search(r'operario',l,re.I):
            if cur:rows.append(('',cur,h))
            cur=m.group(2).strip();h=0;continue
        for x in re.findall(r'\((\d+(?:,\d+)?)\s*horas?\)',l):h+=float(x.replace(',','.'))
        if re.search(r'^\s*B\.\s+NECESIDADES',l):break
    if cur:rows.append(('',cur,h))
    return rows
def limpieza_colegios(lines):
    rows=[];buf=''
    for l in lines:
        m=re.match(r'^\s*((?:C\. ?P\.|C\. E\. E\.|E\.I\.).*?)\s+(\d+(?:,\d+)?)\s+(\d+(?:,\d+)?)\s+([\d\.]+,\d)\s*$',l)
        if m:rows.append(('',m.group(1),num(m.group(4))));continue
        m=re.match(r'^\s*((?:C\. ?P\.|C\. E\. E\.).*?)\s*$',l)
        if m and not re.search(r'\d',l):buf=m.group(1);continue
        m=re.match(r'^\s*(\d+(?:,\d+)?)\s+(\d+(?:,\d+)?)\s+([\d\.]+,\d)\s*$',l)
        if m and buf:rows.append(('',buf,num(m.group(3))));buf='';continue
        if buf and re.match(r'^\s*[A-ZÁÉÍÓÚa-z]',l) and rows and rows[-1][1]==buf:pass
    # nombres partidos: «C. P. Carlos Sainz de los» + «Terreros»
    out=[]
    for i,(g,n,w) in enumerate(rows):out.append((g,n,w))
    return out
def seguridad(lines):
    rows=[];cur=None;addr='';done=set()
    for l in lines:
        m=re.match(r'^\s*1\.1\.\d+\.\s+(.+)$',l)
        if m:cur=m.group(1).strip();addr='';continue
        m=re.search(r'DIRECCI[ÓO]N:\s*(.+)$',l)
        if m and cur:addr=m.group(1).strip();continue
        m=re.search(r'TOTAL\s+([\d\.]+,\d{2})\s+[\d\.]+,\d{2}\s*$',l)
        if m and cur and cur not in done:rows.append(('',cur+' '+addr,num(m.group(1))));done.add(cur)
    return rows
def norm_row(t):
    t=E.nrm(t).replace('-',' ')
    for a,b in [('SAINZ DE LOS','SAINZ DE LOS TERREROS'),('NUÑEZ DE$','NUÑEZ DE ARENAS')]:t=re.sub(a,b,t)
    t=re.sub(r'\bC\. ?P\.','COLEGIO PUBLICO ',t);t=re.sub(r'\bC\. ?E\. ?E\.','COLEGIO DE EDUCACION ESPECIAL ',t)
    t=re.sub(r'\bC\.?D\.?M\.?\b','CENTRO DEPORTIVO MUNICIPAL ',t);t=re.sub(r'\bC\.?S\.?C\.?\b','CENTRO SOCIOCULTURAL ',t)
    t=re.sub(r'\bC\.?C\.?\b','CENTRO CULTURAL ',t);t=re.sub(r'\bC\.?M\.?M?\.?\b','CENTRO MUNICIPAL DE MAYORES ',t)
    t=re.sub(r'\bC\.?S\.?S\.?\b','CENTRO DE SERVICIOS SOCIALES ',t);t=re.sub(r'\bE\.?I\.?\b','ESCUELA INFANTIL ',t)
    t=re.sub(r'\bC/\s*','CALLE ',t);t=re.sub(r'\bAVDA?\.?\s','AVENIDA ',t)
    return re.sub(r'\s+',' ',t)
def asigna(rows):
    out=[];sin=[]
    for g,t,w in rows:
        h=E.match(norm_row(t),True)
        if len(h)==1:out.append((h[0][0],t,w,h[0][1]))
        elif 1<len(h)<=3:  # mismo recinto con varios puntos en el mapa: se reparte a partes iguales
            for k,why in h:out.append((k,t,w/len(h),why+' (recinto compartido)'))
        else:sin.append((t,w,[k for k,_ in h]))
    return out,sin
if __name__=='__main__':
    C={}
    L=txt('ppt_300_2025_00051');i=[k for k,l in enumerate(L) if 'ANEXO III' in l][-1]
    C['300/2025/00051']=horas_anexo(L,i,len(L))
    C['300/2022/00668']=limpieza_colegios(txt('eco_300_2022_00668'))
    C['300/2023/00637']=seguridad(txt('eco_300_2023_00637'))
    L=txt('eco_300_2024_00115');i=[k for k,l in enumerate(L) if 'COLEGIOS-LOTE 1' in l][0]
    C['300/2024/00115']=tabla_m2(L,i-1)
    L=txt('ppt_300_2020_00777');i=[k for k,l in enumerate(L) if 'RELACIÓN DE EQUIPAMIENTOS OBJETO' in l][-1]
    C['300/2020/00777']=tabla_m2(L,i)
    res={}
    for exp,rows in C.items():
        ok,sin=asigna(rows);tot=sum(w for *_,w in rows) or 1
        print(f'== {exp}: {len(rows)} filas, {len(ok)} asignadas ({100*sum(x[2] for x in ok)/tot:.0f} % del peso)')
        for t,w,c in sin:print('   SIN:',t[:70],w,c)
        res[exp]={'filas':[{'grupo':g,'texto':t,'peso':w} for g,t,w in rows],'edif':[{'key':k,'texto':t,'peso':w,'cruce':why} for k,t,w,why in ok],'peso_total':tot}
    json.dump(res,open(D/'reparto.json','w'),ensure_ascii=False,indent=1)
