"""Extracción por contrato con configuración explícita (cfg2.json):
 {exp: {"doc": f, "medida": "m2"|"horas", "tablas": [{"desde":a,"hasta":b,"lote":"1","col":x,"tol":8,"name_end":60}], "nota": "..."}}
Cada edificio es un bloque: empieza en una línea con texto en la zona de nombre (antes de name_end) que no sea una categoría
de trabajador ni un total; su peso es la suma de los números de la columna x (±tol) en las líneas del bloque."""
import json,os,re,sys,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from pliegos_tablas import resolve,exps,T,num,SK
NUM=re.compile(r'(?<![\d.,A-Za-z²])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)(?![\d.,])')
ROL=r'LIMPIADOR|PE[OÓ]N|ESPECIALISTA|CRISTALER|ENCARGAD|CONSERJ|OPERARI|VIGILANTE|AUXILIAR DE|OFICIAL|CATEGOR|TOTAL|HORAS|PUESTO|^\s*(LUNES|MARTES|DE LUNES|S[ÁA]BADO|DOMINGO|FESTIVO)'
def extraer(exp,c):
    cd=None
    import edificios as E
    cd=E.cod_distrito(exps[exp][0]['distrito'])
    L=open(os.path.join(T,c['doc']),encoding='utf-8',errors='replace').read().split('\n')
    filas=[]
    for t in c['tablas']:
        cur=None;ne=t.get('name_end',60);x=t['col'];tol=t.get('tol',8);rol=t.get('rol',ROL)
        for i in range(t['desde'],t['hasta']+1):
            l=L[i]
            if SK.search(l) or not l.strip():continue
            head=l[:ne]
            if re.search(r'[A-Za-zÁÉÍÓÚÑ]{3}',head) and not head.strip().startswith('(') and not re.search(rol,head.strip(),re.I) and not re.search(t.get('skip',r'^$a'),l,re.I):
                cur={'i':i,'txt':re.sub(r'\s{2,}',' | ',l.strip())[:120],'v':0.0,'lote':t.get('lote') if t.get('lote') is not None else '','cont':[]};filas.append(cur)
            elif cur is not None and re.search(r'[A-Za-z]{3}',head) is None and re.search(r'^\s{0,3}\S',l) and not NUM.search(l[:ne]):
                pass
            if cur is None:continue
            if cur['i']!=i and re.search(r'[a-záéíóú]{3}',l[:ne]) and not re.search(rol,l[:ne],re.I):cur['cont'].append(l[:ne].strip())
            for mm in NUM.finditer(l):
                p=(mm.start()+mm.end())/2
                if abs(p-x)<=tol:cur['v']+=num(mm.group(1))
    for f in filas:
        k,how=resolve(f['txt']+' '+' '.join(f['cont'][:2]),cd)
        f['key'],f['how']=k,how
    return [f for f in filas if f['v']>0]

def extraer_totales(exp,c):
    """Una tabla pequeña por edificio: nombre en la columna izquierda (puede ocupar varias líneas), peso en la fila
    TOTAL bajo la columna de la cabecera (hdr). Las tablas repetidas en el documento se cuentan una vez."""
    import edificios as E
    cd=E.cod_distrito(exps[exp][0]['distrito'])
    L=open(os.path.join(T,c['doc']),encoding='utf-8',errors='replace').read().split('\n')
    filas=[];col=None;cur=None;ne=c.get('name_end',40);seen=set()
    for i,l in enumerate(L):
        if c.get('desde') and i<c['desde']:continue
        if c.get('hasta') and i>c['hasta']:break
        m=re.search(c['hdr'],l,re.I)
        if m:col=(m.start()+m.end())/2;cur={'i':i,'parts':[],'v':0.0,'lote':c.get('lote','')};continue
        if col is None or SK.search(l) or not l.strip():continue
        if re.search(r'TOTAL',l,re.I):
            ns=[(num(mm.group(1)),(mm.start()+mm.end())/2) for mm in NUM.finditer(l)]
            hit=[v for v,p in ns if abs(p-col)<=c.get('tol',8)]
            if hit and cur and cur['parts']:
                cur['v']=hit[0];cur['txt']=' '.join(cur['parts'])[:120]
                if (cur['txt'],cur['v']) not in seen:seen.add((cur['txt'],cur['v']));filas.append(cur)
            cur=None;col=None;continue
        frag=l[:ne].strip()
        if cur is not None and frag and re.search(r'[A-Za-zÁÉÍÓÚÑ]{2}',frag) and not re.search(r'HORARIO|PUESTOS|SEMANAS|^\(?LIMPIADOR|^\(?PE[OÓ]N|^\(?CRISTALER|^CENTRO$',frag,re.I):cur['parts'].append(frag)
    for f in filas:
        k,how=resolve(f['txt'],cd);f['key'],f['how']=k,how
    return filas

def extraer_ancla(exp,c):
    """Cada número en la columna col (±tol) entre desde y hasta es un edificio; los trozos de texto de la zona de nombre
    (antes de name_end) se asignan al número más cercano en líneas (el nombre puede quedar partido alrededor)."""
    import edificios as E
    cd=E.cod_distrito(exps[exp][0]['distrito'])
    L=open(os.path.join(T,c['doc']),encoding='utf-8',errors='replace').read().split('\n')
    out=[]
    for t in c['tablas']:
        an=[];fr=[]
        for i in range(t['desde'],t['hasta']+1):
            l=L[i]
            if SK.search(l) or not l.strip():continue
            for mm in NUM.finditer(l):
                if abs((mm.start()+mm.end())/2-t['col'])<=t.get('tol',6):an.append({'i':i,'v':num(mm.group(1)),'parts':[],'lote':t.get('lote','')})
            f=l[t.get('name_start',0):t['name_end']].strip()
            if f and re.search(r'[A-Za-zÁÉÍÓÚÑ]{2}',f) and not re.search(t.get('skip',r'^(TOTAL|CENTRO|HORAS)\b'),f,re.I):fr.append((i,f))
        for i,f in fr:
            if an:min(an,key=lambda a:(abs(a['i']-i),a['i']<i))['parts'].append((i,f))
        for a in an:
            a['txt']=' '.join(f for _,f in sorted(a['parts']))[:120];k,how=resolve(a['txt'],cd);a['key'],a['how']=k,how
        out+=[a for a in an if a['v']>0]
    return out
