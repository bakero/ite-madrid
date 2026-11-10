import json,re,collections,sys,io,sqlite3
_o=sys.stdout;sys.stdout=io.StringIO()
import edificios as E
sys.stdout=_o
import os;os.chdir(E.BASE/'datos'/'inversiones');DB=E.DB
con=sqlite3.connect(DB)
# ---- edificios + año de construcción / ITE
info={}
for b in E.B.values():
    info[b['key']]={'key':b['key'],'nombres':sorted(set(b['cents'])),'dir':b['addr'],'tipos':sorted(b['tipos']),'ev':[]}
rows=con.execute("""select c.lat,c.lng,i.anio_construccion,i.fecha_presentacion,i.estado_inspeccion,i.dictamen from centros c left join ite i on i.direccion=c.direccion
 where c.lat is not null and c.cod_barrio in (select cod from barrios where cod_distrito=13)""").fetchall()
for lat,lng,ac,fp,est,dic in rows:
    k=f'{round(lat,5):.5f},{round(lng,5):.5f}'
    if k in info and ac and str(ac).strip().isdigit():info[k]['anio_construccion']=int(ac)
    if k in info and fp:info[k].setdefault('ite',[]).append(str(fp)[:10])
def add(k,ev):
    if k in info:info[k]['ev'].append(ev)
# ---- A) inversiones (ejecución presupuestaria, pagos reales) 2014-2025
f=lambda s:float((s or '0').replace('.','').replace(',','.') or 0)
d=json.load(open('inversiones_pv_2014_2025.json'))
agg=collections.defaultdict(lambda:{'obl':0,'cd':0,'anios':set()})
def cat(t):
    if re.search(r'ADQUISICI.N (DE )?SUELO|ADQUISICI.N$|\. ADQUISICI.N|EXPROPIACI',t):return 'suelo / compra'
    if re.search(r'CONSTRUCCI.N|NUEVA PLANTA|AMPLIACI',t) and not re.search(r'EQUIPAMIENTO|MOBILIARIO',t):return 'construcción / ampliación'
    if re.search(r'EQUIPAMIENTO|MOBILIARIO|EQUIPOS|ENSERES|APLICACIONES|VEH.CULO|INSTALACIONES BOMBEROS',t):return 'equipamiento'
    return 'obras / reforma'
for anio,proj,tit,dist,lin,sub,prog,subc,cd,obl in d['rows']:
    if dist not in('PUENTE DE VALLECAS','VARIOS DISTRITOS'):continue
    t=E.nrm(tit);pv=dist=='PUENTE DE VALLECAS' or 'VALLECAS' in t
    h=E.match(t,pv)
    if len(h)!=1:continue
    a=agg[(h[0][0],proj,tit)];a['obl']+=f(obl);a['cd']+=f(cd);a['anios'].add(anio);a['why']=h[0][1]
for (k,proj,tit),a in agg.items():
    if a['obl']<=0 and a['cd']<=0:continue
    y0=int(proj[:4]) if proj[:4].isdigit() else min(a['anios'])
    add(k,{'fuente':'inversiones','anio':min(a['anios']),'anio_proyecto':y0,'anios':sorted(a['anios']),'texto':tit,'importe':round(a['obl'],2),'importe_tipo':'pagado','credito':round(a['cd'],2),'cat':cat(E.nrm(tit)),'ref':proj,'why':a['why']})
# ---- B) contratos 2015-2026 (actividad contractual + menores)
C=json.load(open('contratos_norm.json'))
INV=r'\bOBRA|REFORMA|REHABILIT|ACONDICION|IMPERMEABILIZ|CUBIERTA|SUSTITUC|ACCESIBILID|CLIMATIZ|CALEFACC|CALDERA|ASCENSOR|VENTANA|CARPINTER|FACHADA|PAVIMENT|REPARAC|MEJORA|ADECUACI|DEMOLIC|CONSTRUCC|AMPLIAC|PINTURA|SANEAMIENTO|ILUMINAC|ELECTRIC|FONTANER|EFICIENCIA ENERG|PATOLOG|EMERGENCIA|SEGURIDAD ESTRUCTURAL'
seen=set()
for c in C:
    txt=E.nrm(c['der'] if (c['der'] or '').strip() else c['obj'])
    pv=('PUENTE DE VALLECAS' in txt or 'PUENTE VALLECAS' in txt or 'PUENTE DE VALLECAS' in E.nrm(c['centro']+' '+c['org']))
    if re.search(E.NOEDIF,txt):continue
    if not (re.search(INV,txt) or E.nrm(c['tipo']).startswith('OBRA')):continue
    if re.search(r'COORDINACI.N (EN MATERIA )?DE SEGURIDAD Y SALUD|DIRECCI.N FACULTATIVA|REDACCI.N DE(L)? PROYECTO|ASISTENCIA T.CNICA|CONTROL DE CALIDAD',txt):cat2='servicios técnicos de obra'
    else:cat2='obras / reforma / mantenimiento'
    h=E.match(txt,pv)
    if len(h)!=1:continue
    sig=(h[0][0],round(c['imp'] or 0),c['year'])
    if sig in seen:continue
    seen.add(sig)
    add(h[0][0],{'fuente':'contratos','anio':c['year'],'texto':(c['der'] or c['obj']).strip()[:300],'importe':c['imp'],'importe_tipo':'adjudicado','cat':cat2,'tipo_contrato':c['kind'],'adj':(c['adj'] or '')[:80],'why':h[0][1]})
# ---- C) BOE 1995-2014
for r in json.load(open('boe_match.json')):
    if len(r['hits'])!=1:continue
    add(r['hits'][0][0],{'fuente':'BOE','anio':r['anio'],'texto':r['obj'][:300],'importe':r['importe'],'importe_tipo':r['importe_tipo'],'cat':'obras / construcción','ref':r['anuncios'][0],'anuncios':r['anuncios'],'organismo':r['ent'],'why':r['hits'][0][1]})
# ---- resumen
out=[v for v in info.values()]
for v in out:
    v['ev'].sort(key=lambda e:e['anio'])
    v['n']=len(v['ev'])
    v['tot_pagado']=round(sum(e['importe'] for e in v['ev'] if e['fuente']=='inversiones'),2)
    v['tot_contratos']=round(sum(e['importe'] or 0 for e in v['ev'] if e['fuente']=='contratos'),2)
    v['tot_boe']=round(sum(e['importe'] or 0 for e in v['ev'] if e['fuente']=='BOE'),2)
    v['primer_dato']=v['ev'][0]['anio'] if v['ev'] else None
json.dump(out,open('historial_pv.json','w'),ensure_ascii=False)
con_ev=[v for v in out if v['ev']]
print('edificios:',len(out),'con algún dato:',len(con_ev))
print('por fuente:',collections.Counter(e['fuente'] for v in out for e in v['ev']))
print('edificios por fuente:',{s:sum(1 for v in out if any(e['fuente']==s for e in v['ev'])) for s in ['inversiones','contratos','BOE']})
print('con año construcción:',sum(1 for v in out if v.get('anio_construccion')))
dec=collections.Counter()
for v in out:
    for e in v['ev']:dec[(e['anio']//5*5,e['fuente'])]+=1
print(sorted(dec.items()))
print('€ pagados (inv):',round(sum(v['tot_pagado'] for v in out)),'· € contratos:',round(sum(v['tot_contratos'] for v in out)),'· € BOE:',round(sum(v['tot_boe'] for v in out)))
for v in sorted(out,key=lambda v:-(v['tot_pagado']+v['tot_boe']))[:20]:
    print(f"{v['tot_pagado']:>12,.0f} {v['tot_boe']:>11,.0f} {v['tot_contratos']:>11,.0f} | {v.get('anio_construccion')} | {v['nombres'][0][:55]} | {v['n']}")

# ---- export para la app: app/inversiones.js
import datetime
FU=['BOE','inversiones','contratos']
TI=['pagado','adjudicado','adjudicación','licitación']
ED={}
for v in out:
    if not v['ev']:continue
    ev=[]
    for e in sorted(v['ev'],key=lambda e:(-e['anio'],-(e['importe'] or 0))):
        t=re.sub(r'\s+',' ',e['texto']).strip()
        ev.append([e['anio'],FU.index(e['fuente']),t[:220],round(e['importe'],2) if e['importe'] else None,TI.index(e['importe_tipo']) if e['importe_tipo'] in TI else -1])
    ED[v['key']]={'t':[v['tot_boe'],v['tot_pagado'],v['tot_contratos']],'ev':ev}
js={'generado':datetime.date.today().isoformat(),'distritos':[13],'fuentes':FU,'tipos':TI,'edificios':ED}
open(E.BASE/'app'/'inversiones.js','w',encoding='utf-8').write('window.INVERSIONES='+json.dumps(js,ensure_ascii=False,separators=(',',':'))+';\n')
print('app/inversiones.js:',len(ED),'edificios',sum(len(x['ev']) for x in ED.values()),'registros')
