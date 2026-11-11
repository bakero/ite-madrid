"""Categorías y utilidades comunes de los contratos de servicios."""
import re,sys,pathlib,urllib.parse
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'inversiones'))
import edificios as E
CAT=[('limpieza',r'\bLIMPIEZA'),
     ('seguridad',r'VIGILANCIA|SEGURIDAD PRIVADA|SERVICIOS? DE SEGURIDAD|SEGURIDAD DE (LOS |LAS )?(EDIFICIOS|CENTROS|DEPENDENCIAS|INSTALACIONES|EQUIPAMIENTOS)|SEGURIDAD Y CONTROL|ACUDA|CUSTODIA DE LLAVES'),
     ('auxiliares',r'AUXILIARES (DE )?(INFORMACI|SERVICIOS|CONTROL)|CONSERJ|CONTROL DE (ENTRADAS|ACCESOS)|ATENCION AL PUBLICO|INFORMADORES'),
     ('mantenimiento',r'MANTENIMIENTO (INTEGRAL|TECNICO|DE (LAS |LOS )?(INSTALACIONES|EDIFICIOS|EQUIPAMIENTOS|CENTROS|COLEGIOS|POLIDEPORTIVOS|ASCENSORES|CLIMATIZACI|CALEFACCI|CALDERAS|SISTEMAS DE PROTECCI)|PREVENTIVO|Y CONSERVACI)|GESTION INTEGRAL|SERVICIOS COMPLEMENTARIOS|CONSERVACION Y MANTENIMIENTO DE (LOS )?(EDIFICIOS|EQUIPAMIENTOS|INSTALACIONES)'),
     ('jardinería',r'JARDINER'),
     ('control de plagas',r'DESINFECCI|DESINSECT|DESRATIZ|PLAGAS|LEGIONEL')]
EXCL=r'VIGILANCIA DE (LAS )?OBRAS|INSPECCION Y VIGILANCIA|LIMPIEZA (VIARIA|URBANA|DE (LA )?VIA|DE PINTADAS|DE GRAFIT|DE SOLARES|DE CONTENEDORES|Y RECOGIDA)|NEVADA|VIAS PUBLICAS|SEGURIDAD Y SALUD|SEGURIDAD VIAL|ALUMBRADO|SEMAFOR|FUENTES|ZONAS VERDES Y ARBOLADO|ARBOLADO|PARQUES Y JARDINES DE LA CIUDAD|VEHICULOS|TUNELES|PUENTES|GALERIAS|APARCAMIENTO|ESTACIONES DE REPOSTADO|AUTOBUS|M-30|INFORMATIC|APLICACION|SOFTWARE|LICENCIA'
EXP_CAT={'300/2024/00115':['mantenimiento']}
PVDIST=r'PUENTE (DE )?VALLECAS|PTE\.? (DE )?VALLECAS|P\.? VALLECAS'
def cats(t):return [c for c,rx in CAT if re.search(rx,t)]
def emp(a):
    a=re.sub(r'\s*PYME:.*$','',a or '',flags=re.I).strip()
    a=re.sub(r'^\([A-Z0-9]{8,10}\)\s*','',a);a=re.sub(r'\s+',' ',a).strip(' ,.;')
    return a
def empkey(a):return re.sub(r'[^A-Z0-9]','',re.sub(r'\b(S\.?A\.?U?|S\.?L\.?U?|SOCIEDAD ANONIMA|SL|SA|SAU|SLU)\b','',E.nrm(a)))
PLAT='https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl='
def _pal(s):return {w for w in re.findall(r'[A-Z]{4,}',E.nrm(s))}-{'CONTRATO','SERVICIO','SERVICIOS','DISTRITO','PARA','LOTE','LOTES','LOS','LAS','DEL'}
def plataforma_url(L,exp,texto=''):
    """Enlace público a la licitación en la Plataforma de Contratación (enlaces.json: exp -> [[idEvl, texto de la fila]])."""
    c=L.get(exp)
    if not isinstance(c,list) or not c:return None
    if len(c)==1:return PLAT+urllib.parse.quote(c[0][0],safe='')
    pal=_pal(texto);best=max(c,key=lambda r:len(pal&_pal(r[1])))
    return PLAT+urllib.parse.quote(best[0],safe='')


import datetime as _dt
def meses_prorroga(ps):
    """Meses de prórroga. Las prórrogas con la misma duración formalizadas con menos de un mes de diferencia son la
    misma prórroga de distintos lotes del expediente (p. ej. Tetuán 300/2018/00448: dos de 24 meses el 01/07/2021) y
    cuentan una vez. Las demás se suman (prórrogas sucesivas)."""
    tot=0;vistas=[]
    for p in sorted(ps,key=lambda p:p['fecha'] or ''):
        d=_dt.date.fromisoformat(p['fecha']) if p['fecha'] else None
        if d and any(m==p['meses'] and abs((d-v).days)<31 for v,m in vistas):continue
        tot+=p['meses'] or 0
        if d:vistas.append((d,p['meses']))
    return tot

def prorrogas_mezclan_lotes(ps):
    """¿Hay prórrogas de distintos lotes del expediente (misma duración, menos de un mes de diferencia)? Entonces no se
    sabe qué importe corresponde al lote del contrato."""
    return meses_prorroga(ps)<sum(p['meses'] or 0 for p in ps)
