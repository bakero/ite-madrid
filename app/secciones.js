// Ciudadano Madrid · secciones Ciudadano, Vía pública, Servicios y Ayudas.
// Lee app/sec/<sección>.json (generados por scripts/datos/exporta_web.py) y app/sec/fuentes.json.
// Usa las utilidades que index.html expone en window.CM (esc, nf, eurS, barChart, choro, setDistrict, DISTN, DSEL).
(function(){
'use strict';
const CM=window.CM,{esc,nf,grp,choro,setDistrict,DISTN}=CM,eurS=CM.eurS;
// barChart deja 58 px a la izquierda para el eje: se amplía para que quepan «10.000 M€»
const barChart=(...a)=>CM.barChart(...a).replace(/viewBox="0 0 (\d+) (\d+)"/,(m,w,h)=>`viewBox="-26 0 ${+w+26} ${h}"`);
const CACHE={};
const get=n=>CACHE[n]||(CACHE[n]=fetch('sec/'+n+'.json').then(r=>{if(!r.ok)throw new Error(n);return r.json()}));
const AZ='#1f5fa8',GR='#b8c2cc',PAL=['#1f5fa8','#6f9fd0','#e8590c','#2b8a3e','#845ef7','#b8c2cc'];
const M=v=>v==null?'—':grp(nf(v/1e6,Math.abs(v)>=1e8?0:1))+' M€',N=v=>v==null?'—':grp(nf(v));
const amb=()=>CM.DSEL==null?'Madrid':DISTN[CM.DSEL];
const last=a=>a[a.length-1];

// ---------- «De dónde sale» ----------
function srcBtn(ids,txt){ids=[...new Set((ids||[]).filter(x=>x!=null))];if(!ids.length)return '';
  return `<button type="button" class="srcb" data-src="${ids.join(',')}">${txt||'De dónde sale'}</button>`}
async function openSrc(ids){const F=await get('fuentes');let d=document.getElementById('srcDlg');
  if(!d){d=document.createElement('dialog');d.id='srcDlg';d.className='srcdlg';document.body.appendChild(d);
    d.addEventListener('click',e=>{if(e.target===d||e.target.closest('.srcx'))d.close()})}
  const L=ids.map(i=>F[i]).filter(Boolean),g={};L.forEach(f=>(g[f.k]=g[f.k]||{f,l:[]}).l.push(f));
  d.innerHTML=`<div class="srci"><div class="srch"><h2>De dónde sale este dato</h2><button type="button" class="btn srcx" aria-label="Cerrar">Cerrar</button></div>
   <p class="sub">Ficheros oficiales descargados, con la fecha y la huella SHA-256 que permite comprobar que es el mismo fichero. ${L.length} fichero${L.length===1?'':'s'} de ${Object.keys(g).length} fuente${Object.keys(g).length===1?'':'s'}.</p>
   ${Object.values(g).map(({f,l})=>`<section><h3>${esc(f.f)}</h3><p class="sub">${esc(f.o||'')}${f.l?' · Licencia: '+esc(f.l):''} · <a href="${esc(f.fi)}" target="_blank" rel="noopener">Ficha en el portal</a></p>
     <details${l.length<=3?' open':''}><summary>${l.length} fichero${l.length===1?'':'s'}</summary><ul>${l.slice(0,60).map(x=>`<li><a href="${esc(x.u)}" target="_blank" rel="noopener">${esc(x.r||x.u)}</a> · descargado ${esc((x.d||'').slice(0,10))}${x.h?` · SHA-256 <code>${esc(x.h.slice(0,12))}…</code>`:''}${x.a?` · <a href="${esc(x.a)}" target="_blank" rel="noopener">copia archivada</a>`:''}</li>`).join('')}${l.length>60?`<li>… y ${l.length-60} más</li>`:''}</ul></details>
     <p class="srcp"><b>Cómo repetirlo:</b> ${esc((l[0].p||'').replace(/«[^»]*»/,'«…»'))}${l[0].s?` <span class="sub">(script <code>${esc(l[0].s)}</code>${l[0].c?' · commit '+esc(l[0].c):''})</span>`:''}</p></section>`).join('')}
   <p class="sub">Todas las descargas y su procedencia están en la base de datos <code>ciudadano_madrid.sqlite</code> (tablas <code>fuente</code> y <code>descarga</code>). Método: <a href="https://github.com/bakero/ite-madrid/blob/main/docs/trazabilidad.md" target="_blank" rel="noopener">docs/trazabilidad.md</a>.</p></div>`;
  d.showModal()}
document.addEventListener('click',e=>{const b=e.target.closest('.srcb');if(b){e.preventDefault();openSrc(b.dataset.src.split(',').map(Number))}});

// ---------- piezas comunes ----------
const kpi=(v,l,c)=>`<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div>${c?`<div class="cmpv">${c}</div>`:''}</div>`;
const card=(t,body,src,sub)=>`<section class="card"><h2 class="sxh">${t}</h2>${sub?`<p class="sub">${sub}</p>`:''}${body}${src?`<div class="sxf">${src}</div>`:''}</section>`;
const hbars=(rows,fmt,o={})=>{const mx=Math.max(...rows.map(r=>r[1]||0))||1;
  return `<div class="sxhb">${rows.map(r=>`<span class="l${r[2]?' on':''}">${esc(r[0])}</span><span class="t"><i style="width:${(100*(r[1]||0)/mx).toFixed(1)}%;background:${r[2]?'#e8590c':(o.c||AZ)}"></i></span><span class="v${r[2]?' on':''}">${fmt(r[1])}</span>`).join('')}</div>`};
const tabla=(cab,filas,o={})=>`<div class="sxt"><table><thead><tr>${cab.map((c,i)=>`<th${o.num&&o.num.includes(i)?' class="n"':''}>${c}</th>`).join('')}</tr></thead><tbody>${filas.map(f=>`<tr${f.on?' class="on"':''}>${f.map((v,i)=>`<td${o.num&&o.num.includes(i)?' class="n"':''}>${v??'—'}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
const ambBar=v=>`<p class="sxamb">Ámbito: <b>${esc(amb())}</b>. ${CM.DSEL==null?'Elige un distrito arriba para ver sus datos.':`<a href="#${v}" data-dclear="1">Ver todo Madrid</a>`}</p>`;
document.addEventListener('click',e=>{const a=e.target.closest('[data-dclear]');if(a){e.preventDefault();setDistrict(null)}});

// ---------- Ciudadano ----------
const TRIB=[[/^IBI\s*(DE\s*)?NATURALEZA URBANA/i,'IBI (inmuebles urbanos)'],[/^IBI\s*CARACT/i,'IBI (características especiales)'],[/IVTNU|INCREMENTO DE VALOR/i,'Plusvalía municipal (IIVTNU)'],
  [/I\.?R\.?P\.?F/i,'IRPF (parte cedida por el Estado)'],[/VALOR A[ÑN]ADIDO/i,'IVA (parte cedida por el Estado)'],[/ACTIVIDADES ECON/i,'Actividades económicas (IAE)'],
  [/TRACCI[ÓO]N MEC/i,'Vehículos (IVTM)'],[/CONSTRUCCIONES/i,'Construcciones y obras (ICIO)'],[/HIDROCARBUROS/i,'Hidrocarburos (parte cedida)'],[/LABORES DEL TABACO/i,'Tabaco (parte cedida)']];
const tributo=t=>{for(const [re,n] of TRIB)if(re.test(t))return n;return t.charAt(0)+t.slice(1).toLowerCase()};
async function ciudadano(el){const C=await get('ciudadano');
  const ci=C.ciudad.filter(r=>r.gasto),u=last(ci),uh=last(ci.filter(r=>r.hab_gasto));
  const yI=Math.max(...Object.keys(C.ingresos).map(Number)),I=C.ingresos[yI]||{},tribut=(I['1']||0)+(I['2']||0)+(I['3']||0);
  const pol=Object.entries(C.politicas[u.anio]||{}).filter(([k,v])=>v>0).sort((a,b)=>b[1]-a[1]);
  const D=C.distritos.filter(r=>r.anio===Math.max(...C.distritos.map(x=>x.anio))),yD=D[0]&&D[0].anio;
  const sel=CM.DSEL!=null?D.find(r=>r.cd===CM.DSEL):null;
  const media=k=>{const v=D.map(r=>r[k]).filter(x=>x!=null);return v.reduce((a,b)=>a+b,0)/v.length};
  const rank=(k)=>{const s=D.filter(r=>r[k]!=null).sort((a,b)=>b[k]-a[k]);return s.findIndex(r=>r.cd===CM.DSEL)+1};
  let frase=`En ${u.anio} el Ayuntamiento y sus organismos autónomos gastaron ${M(u.gasto)} en servicios e inversiones: ${N(uh.hab_gasto)} € por habitante. Ejecutaron el ${nf(u.pct,1)} % de lo presupuestado.`;
  if(sel)frase+=` La Junta de ${DISTN[CM.DSEL]} gastó ${M(sel.pag)} (${nf(sel.pag_hab)} € por habitante, puesto ${rank('pag_hab')}.º de 21) y dejó sin gastar ${M(sel.nog)}.`;
  const serie=ci.map(r=>[r.anio,r.gasto]);
  const ingS=Object.keys(C.ingresos).map(Number).sort().map(y=>{const x=C.ingresos[y];return [y,(x['1']||0)+(x['2']||0),x['3']||0,(x['4']||0)+(x['7']||0),(x['5']||0)+(x['6']||0),(x['8']||0)+(x['9']||0)]});
  const imp=(C.impuestos[yI]||[]).filter(r=>r[2]>0).sort((a,b)=>b[2]-a[2]).slice(0,8).map(r=>[tributo(r[1]),r[2]]);
  el.innerHTML=`<h1>Ciudadano: cuánto ingresa y gasta el Ayuntamiento</h1>${ambBar('ciudadano')}<p class="lead">${esc(frase)}</p>
  <div class="kpis">${kpi(M(u.gasto),`gastado en ${u.anio} (sin deuda ni préstamos)`,`${nf(u.pct,1)} % de lo presupuestado`)}${kpi(N(uh.hab_gasto)+' €',`por habitante en ${uh.anio}`,`${N(uh.hab)} habitantes a 1 de enero`)}
   ${kpi(M(tribut),`impuestos, tasas y precios cobrados en ${yI}`,'Ayuntamiento, derechos reconocidos')}${kpi(M((I['4']||0)+(I['7']||0)),`transferencias recibidas en ${yI}`,'del Estado, la Comunidad y la UE')}
   ${sel?kpi(nf(sel.pag_hab)+' €',`gasto de la Junta de ${esc(DISTN[CM.DSEL])} por habitante (${yD})`,`media de los 21 distritos: ${nf(media('pag_hab'))} €`)+kpi(nf(sel.inv_hab)+' €',`inversión en ${esc(DISTN[CM.DSEL])} por habitante (${yD})`,`media: ${nf(media('inv_hab'))} €`):''}</div>
  <div class="grid2">${card('Gasto por año',barChart(serie,[{n:'Gastado (consolidado)',c:AZ,i:1}],{title:'Gasto por año',unit:'Capítulos 1 a 7, Ayuntamiento + organismos autónomos, sin operaciones internas'}),srcBtn(C.src.ciudad),
      ci.some(r=>r.aprox)?'Hasta 2022 el portal solo publica el importe presupuestado de las operaciones internas: esos años son una aproximación.':'')}
   ${card(`En qué se gasta (${u.anio})`,hbars(pol.slice(0,12).map(([k,v])=>[C.nombres_politicas[k]||k,v]),M),srcBtn(C.src.politicas),'Políticas de gasto, sin descontar operaciones internas. «Seguridad y movilidad» incluye policía, bomberos y tráfico.')}</div>
  <div class="grid2">${card('De dónde salen los ingresos',barChart(ingS,[{n:'Impuestos',c:AZ,i:1},{n:'Tasas y precios',c:'#6f9fd0',i:2},{n:'Transferencias',c:'#e8590c',i:3},{n:'Patrimonio y ventas',c:'#2b8a3e',i:4},{n:'Préstamos y activos',c:GR,i:5}],{stack:true,title:'Ingresos por año',unit:'Ayuntamiento (sin organismos), derechos reconocidos'}),srcBtn(C.src.ingresos))}
   ${card(`Impuestos y tasas principales (${yI})`,hbars(imp,M,{c:'#6f9fd0'}),srcBtn(C.src.ingresos),'IBI, plusvalía, IAE, vehículos, construcciones… tal como los nombra el presupuesto.')}</div>
  <h2 class="asec">Comparativa de los 21 distritos (${yD})</h2>
  <p class="sub">El gasto de la Junta es lo que gestiona cada distrito (colegios, centros culturales, servicios sociales, mantenimiento…). La inversión incluye además lo que las Áreas invierten en el distrito. Los proyectos que afectan a varios distritos no se reparten.</p>
  <div class="grid2"><div class="card"><h2 class="sxh">Gasto de la Junta por habitante</h2><div id="sxM1"></div>${srcBtn(C.src.distritos)}</div><div class="card"><h2 class="sxh">Inversión pagada por habitante</h2><div id="sxM2"></div>${srcBtn(C.src.distritos)}</div></div>
  ${card('Los 21 distritos',tabla(['Distrito','Habitantes','Presupuesto Junta','Gastado','Sin gastar','% ejecución','€/hab. Junta','Inversión pagada','€/hab. inversión'],
     D.slice().sort((a,b)=>a.cd-b.cd).map(r=>Object.assign([`<a href="#ciudadano?d=${r.cd}">${esc(DISTN[r.cd])}</a>`,N(r.hab),M(r.cdf),M(r.pag),M(r.nog),nf(r.pct,1)+' %',nf(r.pag_hab),M(r.invp),nf(r.inv_hab)],{on:r.cd===CM.DSEL})),{num:[1,2,3,4,5,6,7,8]}),srcBtn(C.src.distritos))}`;
  const o={cd:CM.DSEL,per:String(yD)};
  choro('sxM1',D.map(r=>({cd:r.cd,v:r.pag_hab})),Object.assign({},o,{fmt:v=>nf(v),u:'€ por habitante',fuente:'Ejecución presupuestaria (datos.madrid.es 211496) y padrón (300557)'}));
  choro('sxM2',D.map(r=>({cd:r.cd,v:r.inv_hab})),Object.assign({},o,{fmt:v=>nf(v),u:'€ por habitante',aviso:'Una sola obra grande puede disparar un año la cifra de un distrito.',fuente:'Proyectos de inversión territorializados (211496) y padrón (300557)'}))}

// ---------- Vía pública ----------
const TIPOS=[['Avería urgente','#e8590c',4],['Cala programada','#1f5fa8',5],['Canalización','#6f9fd0',6],['Alcantarillado','#2b8a3e',7],['Obra municipal','#845ef7',8]];
async function via(el){const V=await get('via');
  const L=V.licencias.filter(r=>CM.DSEL==null||r[1]===CM.DSEL),años=[...new Set(L.map(r=>r[0]))].sort();
  const rows=años.map(y=>[y,...TIPOS.map(t=>L.filter(r=>r[0]===y&&r[2]===t[0]).reduce((a,r)=>a+r[3],0))]);
  const tot=L.reduce((a,r)=>a+r[3],0),ya=last(años.filter(y=>y<new Date().getFullYear()));
  const calles=V.calles[String(CM.DSEL||0)]||[];
  const inv=V.inversiones.filter(r=>CM.DSEL==null||r[2]===CM.DSEL).sort((a,b)=>(b[10]||0)-(a[10]||0));
  const prog=Object.keys(V.programas);
  const yv=Math.max(...V.inversion_via_distrito[prog[0]].map(r=>r[0]));
  const porD=Array.from({length:21},(_,i)=>i+1).map(cd=>({cd,v:prog.reduce((a,p)=>a+(V.inversion_via_distrito[p]||[]).filter(r=>r[0]===yv&&r[1]===cd).reduce((s,r)=>s+r[2],0),0)}));
  const serieInv=[...new Set(V.inversion_via_distrito[prog[0]].map(r=>r[0]))].sort().map(y=>[y,...prog.map(p=>(V.inversion_via_distrito[p]||[]).filter(r=>r[0]===y&&(CM.DSEL==null||r[1]===CM.DSEL)).reduce((s,r)=>s+r[2],0))]);
  const obras=V.obras.filter(o=>CM.DSEL==null||o.cd===CM.DSEL);
  const frase=`Desde abril de 2017 se han cerrado ${N(tot)} licencias de obras en la vía pública de ${amb()} (calas, canalizaciones de agua, gas, electricidad y telecomunicaciones, alcantarillado y averías).`+(calles[0]?` La calle con más intervenciones es ${calles[0][0].toLowerCase().replace(/(^|\s)\S/g,m=>m.toUpperCase()).replace(/ (De|Del|La|Las|Los|El)(?= )/g,m=>m.toLowerCase())}, con ${N(calles[0][1])}.`:'');
  el.innerHTML=`<h1>Vía pública: obras, calles, parques y alumbrado</h1>${ambBar('via')}<p class="lead">${esc(frase)}</p>
  <div class="kpis">${kpi(N(tot),'licencias de obras en vía pública desde 2017',`${nf(rows.find(r=>r[0]===ya)?rows.find(r=>r[0]===ya).slice(1).reduce((a,b)=>a+b,0):0)} en ${ya}`)}
   ${kpi(nf(inv.length),'inversiones principales con ubicación',`${M(inv.reduce((a,r)=>a+(r[10]||0),0))} presupuestados`)}
   ${kpi(nf(obras.length),'obras públicas planificadas o en marcha','según el Ayuntamiento')}
   ${kpi(M(CM.DSEL==null?porD.reduce((a,r)=>a+r.v,0):(porD.find(r=>r.cd===CM.DSEL)||{}).v),`invertido en vía pública en ${yv}`,'calles, zonas verdes, alumbrado, tráfico y limpieza')}</div>
  <div class="grid2">${card('Licencias de obras por año y tipo',barChart(rows,TIPOS.map((t,i)=>({n:t[0],c:t[1],i:i+1})),{stack:true,title:'Licencias por año',unit:'licencias finalizadas; 2017 desde abril; el año en curso, incompleto'}),srcBtn(V.src.licencias),
      'Cada licencia es una apertura de la calle por una compañía de servicios o por el Ayuntamiento. No incluye su coste, que no se publica.')}
   ${card('Calles con más intervenciones',tabla(['Calle','Total','Averías','Calas','Canaliz.','Desde'],calles.slice(0,15).map(c=>[esc(c[0]),N(c[1]),nf(c[4]),nf(c[5]),nf(c[6]),c[3]]),{num:[1,2,3,4]}),srcBtn(V.src.licencias),
      `${esc(amb())} · misma calle escrita de varias formas, agrupada`)}</div>
  <div class="grid2"><div class="card"><h2 class="sxh">Inversión en vía pública por distrito (${yv})</h2><div id="sxM3"></div>${srcBtn(V.src.inversion_via)}</div>
   ${card('Inversión en vía pública por año',barChart(serieInv,prog.map((p,i)=>({n:V.programas[p],c:PAL[i],i:i+1})),{stack:true,title:'Inversión pagada',unit:`${esc(amb())} · proyectos de inversión con distrito asignado`}),srcBtn(V.src.inversion_via))}</div>
  ${card('Obras públicas planificadas y en ejecución',obras.length?tabla(['Obra','Calles','Empresa','Presupuesto','Inicio','Fin'],obras.map(o=>[esc(o.nombre),esc((o.calles||'').slice(0,120)),esc(o.empresa||'—'),o.presupuesto?eurS(+String(o.presupuesto).replace(',','.')):'—',esc(o.inicio||''),esc(o.fin||'')]),{num:[3]}):'<p class="sub">No hay obras de este ámbito en el listado actual.</p>',srcBtn(obras.map(o=>o.src)))}
  ${card(`Inversiones principales en ${esc(amb())}`,tabla(['Inversión','Dirección','Línea','Estado','Presupuesto','Gastado','Mapa'],inv.slice(0,40).map(r=>[esc(r[1]),esc(r[3]||''),esc(r[6]||''),esc(r[7]||''),eurS(r[10]),eurS(r[11]),r[4]?`<a href="https://www.openstreetmap.org/?mlat=${r[4]}&mlon=${r[5]}#map=18/${r[4]}/${r[5]}" target="_blank" rel="noopener">Ver</a>`:'—']),{num:[4,5]})+(inv.length>40?`<p class="sub">Las 40 de mayor presupuesto de ${nf(inv.length)}.</p>`:''),srcBtn(V.src.inversiones))}`;
  choro('sxM3',porD,{cd:CM.DSEL,per:String(yv),fmt:v=>nf(v/1e6,1),u:'M€',aviso:'Total del distrito, no por habitante: los distritos grandes reciben más.',fuente:'Proyectos de inversión (datos.madrid.es 211496), programas de vías públicas, zonas verdes, alumbrado, tráfico y limpieza'})}

// ---------- Servicios ----------
const TR={registro:['Contratos (registro)',AZ],'acuerdo marco':['Basados en acuerdo marco','#6f9fd0'],homologación:['Homologación','#845ef7'],menor:['Contratos menores','#e8590c']};
async function servicios(el){const S=await get('servicios');
  const base=CM.DSEL==null?S.por_anio.map(r=>[r[0],r[1],r[2],r[3]]):S.por_distrito.filter(r=>r[1]===CM.DSEL).map(r=>[r[0],r[2],r[3],r[4]]);
  const años=[...new Set(base.map(r=>r[0]))].filter(y=>y>=2015).sort(),ks=Object.keys(TR);
  const rows=años.map(y=>[y,...ks.map(k=>base.filter(r=>r[0]===y&&r[1]===k).reduce((a,r)=>a+(r[3]||0),0))]);
  const nrow=años.map(y=>[y,...ks.map(k=>base.filter(r=>r[0]===y&&r[1]===k).reduce((a,r)=>a+(r[2]||0),0))]);
  const tot=rows.reduce((a,r)=>a+r.slice(1).reduce((x,y)=>x+y,0),0),n=nrow.reduce((a,r)=>a+r.slice(1).reduce((x,y)=>x+y,0),0);
  const R=S.ranking[String(CM.DSEL||0)]||[];
  const nm=nrow.reduce((a,r)=>a+r[4],0);
  const frase=`${CM.DSEL==null?'El Ayuntamiento, sus organismos y empresas':'La Junta de '+DISTN[CM.DSEL]} inscribió desde 2015 ${N(n)} contratos por ${M(tot)} (IVA incluido), de ellos ${N(nm)} contratos menores.`+(R[0]?` El mayor adjudicatario por importe es ${R[0][0]}, con ${M(R[0][3])}.`:'');
  el.innerHTML=`<h1>Servicios: quién presta los servicios y por cuánto</h1>${ambBar('servicios')}<p class="lead">${esc(frase)}</p>
  <div class="kpis">${kpi(N(n),'contratos desde 2015','registro de contratos y contratos menores')}${kpi(M(tot),'importe adjudicado','IVA incluido')}${kpi(N(nm),'contratos menores',`${nf(100*nm/Math.max(n,1),0)} % del número de contratos`)}</div>
  ${CM.DSEL!=null?'<p class="chw">En un distrito solo se cuentan los contratos de su Junta. Los contratos de las Áreas que dan servicio a toda la ciudad (limpieza, recogida de basuras…) están en el ámbito Madrid.</p>':''}
  <div class="grid2">${card('Importe adjudicado por año',barChart(rows,ks.map((k,i)=>({n:TR[k][0],c:TR[k][1],i:i+1})),{stack:true,title:'Importe por año',unit:'IVA incluido · en los acuerdos marco es el techo de gasto, no lo pagado'}),srcBtn(S.src.contratos))}
   ${card('Número de contratos por año',barChart(nrow,ks.map((k,i)=>({n:TR[k][0],c:TR[k][1],i:i+1})),{stack:true,title:'Contratos por año',unit:'contratos inscritos'}),srcBtn(S.src.contratos))}</div>
  ${card(`Empresas con más importe adjudicado · ${esc(amb())}`,tabla(['Empresa','NIF','Contratos','Importe','Menores','Años'],R.map(r=>[esc(r[0]),esc(r[1]||'—'),N(r[2]),M(r[3]),nf(r[4]),r[5]===r[6]?r[5]:r[5]+'–'+r[6]]),{num:[2,3,4]}),srcBtn(S.src.contratos),
    'Importe adjudicado, no pagado. Las personas físicas no se muestran por su nombre. Las UTE cuentan aparte de sus socias.')}`}

// ---------- Ayudas y convenios ----------
async function ayudas(el){const A=await get('ayudas');
  const rec=A.recibidas,niv={};rec.forEach(r=>{niv[r[0]]=(niv[r[0]]||0)+(r[7]||0)});
  const fe=A.fondos_europeos.filter(r=>CM.DSEL==null||r[7]===CM.DSEL||r[7]==null),feT=fe.reduce((a,r)=>a+(r[3]||0),0);
  const cv=A.convenios.filter(r=>CM.DSEL==null||r[3]===CM.DSEL),cy={};cv.forEach(r=>{if(r[1])cy[r[1]]=(cy[r[1]]||0)+1});
  const cRows=Object.keys(cy).map(Number).sort().map(y=>[y,cy[y]]);
  const frase=`Otras administraciones han concedido al Ayuntamiento, sus organismos y empresas ${nf(rec.length)} ayudas por ${M(rec.reduce((a,r)=>a+(r[7]||0),0))} según su registro. Además, ha obtenido ${M(A.fondos_europeos.reduce((a,r)=>a+(r[3]||0),0))} de fondos europeos (Plan de Recuperación y FEDER) en ${nf(A.fondos_europeos.length)} proyectos.`;
  el.innerHTML=`<h1>Ayudas y convenios: dinero de otras administraciones y acuerdos</h1>${ambBar('ayudas')}<p class="lead">${esc(frase)}</p>
  <div class="kpis">${Object.entries(niv).sort((a,b)=>b[1]-a[1]).map(([k,v])=>kpi(M(v),({'AUTONÓMICA':'ayudas autonómicas','ESTATAL':'ayudas estatales','LOCAL':'ayudas locales','OTROS':'otras ayudas'})[k]||esc(k))).join('')}${kpi(M(feT),'fondos europeos'+(CM.DSEL!=null?' (distrito o toda la ciudad)':''))}${kpi(nf(cv.length),'convenios firmados desde nov. 2018')}</div>
  ${CM.DSEL!=null?'<p class="chw">Las ayudas recibidas son para toda la ciudad: no se asignan a distritos. Los fondos europeos y convenios sí se filtran cuando el organismo indica el distrito.</p>':''}
  ${card('Ayudas recibidas de otras administraciones',tabla(['Concede','Convocatoria','Fecha','Beneficiario','Importe','Bases'],rec.slice(0,60).map(r=>[esc(r[1])+'<br><span class="sub">'+esc(r[2]||'')+'</span>',esc(r[3]),esc(r[4]||''),esc(r[6]||''),eurS(r[7]),r[9]?`<a href="${esc(r[9])}" target="_blank" rel="noopener">BOE/BOCM</a>`:'—']),{num:[4]})+(rec.length>60?`<p class="sub">Las 60 de mayor importe de ${nf(rec.length)}.</p>`:''),srcBtn(A.src.recibidas))}
  ${card('Fondos europeos',tabla(['Programa','Proyecto','Año','Concedido','Ámbito'],fe.slice(0,60).map(r=>[esc(r[0]),r[9]?`<a href="${esc(r[9])}" target="_blank" rel="noopener">${esc(r[1])}</a>`:esc(r[1]),r[2]||'—',eurS(r[3]),esc(r[6]||'')]),{num:[3]}),srcBtn(A.src.fondos),'Kohesio (portal de la Comisión Europea) se añadirá para contrastar cuando se pueda acceder a él.')}
  <div class="grid2">${card('Convenios por año',barChart(cRows,[{n:'Convenios',c:AZ,i:1}],{title:'Convenios por año',unit:'convenios inscritos (2018 desde noviembre)'}).replace(/ M€|€/g,''),srcBtn(A.src.convenios))}
   ${card('Buscar convenios',`<input type="search" id="sxCq" placeholder="Empresa, entidad o tema (p. ej. «fundación», «universidad», «Iberdrola»)" class="sxin" aria-label="Buscar convenios"><div id="sxCl"></div>`,srcBtn(A.src.convenios),'Con quién firma el Ayuntamiento, para qué y qué se compromete a pagar cada parte.')}</div>`;
  const q=document.getElementById('sxCq'),out=document.getElementById('sxCl');
  const pinta=()=>{const t=(q.value||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');const f=cv.filter(r=>!t||(r[4]+' '+r[5]+' '+r[2]).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').includes(t));
    out.innerHTML=`<p class="sub">${nf(f.length)} convenios${t?' que contienen «'+esc(q.value)+'»':''}; se muestran los 25 más recientes.</p>`+tabla(['Fecha','Con','Objeto','Paga el Ayto.'],f.slice(0,25).map(r=>[esc(r[0]||''),esc(r[5]||''),r[8]?`<a href="${esc(r[8])}" target="_blank" rel="noopener">${esc(r[4])}</a>`:esc(r[4]),r[6]?eurS(r[6]):'—']),{num:[3]})};
  q.oninput=pinta;pinta()}

const R={ciudadano,via,servicios,ayudas};
window.SEC={render(v){const el=document.getElementById('sx-'+v);if(!el||!R[v])return;
  if(!el.innerHTML)el.innerHTML='<p class="sub">Cargando datos…</p>';
  R[v](el).catch(e=>{el.innerHTML=`<p class="chw">No se han podido cargar los datos (${esc(e.message)}). Prueba a recargar la página.</p>`})}};
})();
