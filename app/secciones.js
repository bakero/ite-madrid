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
const kpi=(v,l,c,inf)=>`<div class="kpi"><div class="v">${v}</div><div class="l">${l}${inf?info(inf[0],inf[1]):''}</div>${c?`<div class="cmpv">${c}</div>`:''}</div>`;
/* Icono ⓘ: al pasar el cursor (o con el teclado) muestra cómo se calcula; al pulsarlo abre los ficheros de origen. */
let infN=0;
function info(txt,ids){const id='inf'+(++infN),k=(ids||[]).filter(x=>x!=null).join(',');
  return `<span class="inf"><button type="button" class="infb" aria-describedby="${id}" data-src="${k}" aria-label="De dónde sale esta cifra">i</button><span class="infp" role="tooltip" id="${id}">${txt}${k?'<br><em>Pulsa el icono para ver los ficheros, sus direcciones y los pasos.</em>':''}</span></span>`}
document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('.infb');if(b&&b.dataset.src){e.preventDefault();openSrc(b.dataset.src.split(',').map(Number))}});
const card=(t,body,src,sub)=>`<section class="card"><h2 class="sxh">${t}</h2>${sub?`<p class="sub">${sub}</p>`:''}${body}${src?`<div class="sxf">${src}</div>`:''}</section>`;
const hbars=(rows,fmt,o={})=>{const mx=Math.max(...rows.map(r=>r[1]||0))||1;
  return `<div class="sxhb">${rows.map(r=>`<span class="l${r[2]?' on':''}">${esc(r[0])}</span><span class="t"><i style="width:${(100*(r[1]||0)/mx).toFixed(1)}%;background:${r[2]?'#e8590c':(o.c||AZ)}"></i></span><span class="v${r[2]?' on':''}">${fmt(r[1])}</span>`).join('')}</div>`};
const colChart=(rows,o={})=>{rows=rows.filter(r=>r[1]!=null);if(!rows.length)return '<p class="sub">Sin datos.</p>';
  const W=560,H=170,L=46,B=22,T=10,mx=Math.max(...rows.map(r=>r[1]))||1,cw=(W-L-6)/rows.length,bw=Math.max(3,Math.min(28,cw-4));
  const nice=v=>{const p=Math.pow(10,Math.floor(Math.log10(v)));const m=v/p;return (m<=1?1:m<=2?2:m<=5?5:10)*p},top=nice(mx),sy=v=>T+(H-T-B)*(1-v/top);
  let g=`<line x1="${L}" x2="${W}" y1="${sy(0)}" y2="${sy(0)}" stroke="#c9c6bf"/>`;
  for(const f of [.5,1])g+=`<line x1="${L}" x2="${W}" y1="${sy(top*f)}" y2="${sy(top*f)}" stroke="#ecebe7"/><text x="${L-4}" y="${sy(top*f)+3}" text-anchor="end" class="ax">${grp(nf(top*f))}</text>`;
  rows.forEach((r,k)=>{const x=L+k*cw+(cw-bw)/2;g+=`<rect x="${x.toFixed(1)}" y="${sy(r[1]).toFixed(1)}" width="${bw.toFixed(1)}" height="${(sy(0)-sy(r[1])).toFixed(1)}" fill="${r[2]?'#e8590c':(o.c||AZ)}" rx="1"><title>${r[0]}: ${grp(nf(r[1],o.d||0))} ${o.u||''}</title></rect>`;
    const step=rows.length>14?Math.ceil(rows.length/12):1;if(k%step===0||k===rows.length-1)g+=`<text x="${(x+bw/2).toFixed(1)}" y="${H-5}" text-anchor="middle" class="ax">${String(r[0]).length===4&&rows.length>10?String(r[0]).slice(2):r[0]}</text>`});
  return `<figure class="chart"><svg viewBox="-10 0 ${W+10} ${H}" role="img" aria-label="${esc(o.title||'Gráfico')}">${g}</svg>${o.unit?`<figcaption><span class="sub">${esc(o.unit)}</span></figcaption>`:''}</figure>`};
const tabla=(cab,filas,o={})=>`<div class="sxt"><table><thead><tr>${cab.map((c,i)=>`<th${o.num&&o.num.includes(i)?' class="n"':''}>${c}</th>`).join('')}</tr></thead><tbody>${filas.map(f=>`<tr${f.on?' class="on"':''}>${f.map((v,i)=>`<td${o.num&&o.num.includes(i)?' class="n"':''}>${v??'—'}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
const ambBar=v=>`<p class="sxamb">Ámbito: <b>${esc(amb())}</b>. ${CM.DSEL==null?'Elige un distrito arriba para ver sus datos.':`<a href="${lk(v,curP(v),null)}" data-dclear="1">Ver todo Madrid</a>`}</p>`;
document.addEventListener('click',e=>{const a=e.target.closest('[data-dclear]');if(a){e.preventDefault();setDistrict(null)}});

// ---------- páginas de cada sección (pestañas) ----------
const SECS={
  inicio:{t:'Ciudadano Madrid',s:'Los datos públicos de tu ciudad y tu distrito, con el camino para comprobar cada cifra'},
  ciudadano:{t:'Presupuesto',s:'Cuánto ingresa y gasta el Ayuntamiento, en qué y en qué distrito',
    p:[['resumen','Ingresos y gastos'],['distritos','Por distritos'],['deuda','Deuda y pagos'],['ciudades','Otras ciudades']]},
  via:{t:'Calles y obras',s:'Quién abre la calle, qué se asfalta y cuánto se invierte en la vía pública',
    p:[['obras','Obras en la calle'],['asfalto','Asfaltado'],['inversion','Inversión']]},
  servicios:{t:'Contratos',s:'Qué empresas trabajan para el Ayuntamiento, por cuánto y cuánto se les paga',
    p:[['contratos','Contratos adjudicados'],['pagos','Pagos a proveedores']]},
  social:{t:'Servicios sociales',s:'Ayudas a vecinos y esperas en los servicios para mayores',
    p:[['ayudas','Ayudas a vecinos'],['espera','Listas de espera']]},
  ayudas:{t:'Fondos y convenios',s:'Dinero que el Ayuntamiento recibe de otras administraciones y acuerdos que firma',
    p:[['recibidas','Fondos recibidos'],['convenios','Convenios']]}};
function curP(v){const P=(SECS[v]||{}).p;if(!P)return null;const m=(location.hash.match(/[?&]p=([\w-]+)/)||[])[1];return P.some(x=>x[0]===m)?m:P[0][0]}
function lk(v,p,cd){const a=[];if(p)a.push('p='+p);if(cd!==null&&(cd!==undefined?cd:CM.DSEL)!=null)a.push('d='+(cd!==undefined?cd:CM.DSEL));return '#'+v+(a.length?'?'+a.join('&'):'')}
const cab=(v,extra)=>{const S=SECS[v],cp=curP(v);
  return `<h1>${S.t}</h1><p class="sxsub">${S.s}</p>${S.p?`<div class="sxtabs" role="tablist">${S.p.map(([k,n])=>`<a role="tab" href="${lk(v,k)}"${k===cp?' class="on" aria-selected="true"':' aria-selected="false"'}>${n}</a>`).join('')}</div>`:''}${ambBar(v)}${extra||''}`};

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
  const pg=curP('ciudadano');
  if(pg==='deuda'){el.innerHTML=cab('ciudadano')+deudaPagos(C);return}
  if(pg==='ciudades'){el.innerHTML=cab('ciudadano')+comparada(C);return}
  if(pg==='distritos'){el.innerHTML=cab('ciudadano',`<p class="lead">${esc(frase)}</p>`)+distritos(C,D,yD);mapas(D,yD);return}
  el.innerHTML=`${cab('ciudadano',`<p class="lead">${esc(frase)}</p>`)}
  <div class="kpis">${kpi(M(u.gasto),`gastado en ${u.anio} (sin deuda ni préstamos)`,`${nf(u.pct,1)} % de lo presupuestado`,
      [`<b>Cálculo:</b> obligaciones reconocidas de los capítulos 1 a 7 (personal, compras y servicios, intereses, transferencias e inversiones) del Ayuntamiento y sus organismos autónomos, menos las operaciones internas entre ellos (para no contar dos veces el mismo euro). No incluye devolver deuda (capítulo 9) ni préstamos concedidos (capítulo 8).<br><b>Porcentaje:</b> gastado ÷ crédito definitivo (presupuesto final del año).<br><b>Fuente:</b> «Presupuestos. Ejecución anual» y «Eliminaciones» de datos.madrid.es.${u.aprox?'<br>Hasta 2022 las operaciones internas son aproximadas.':''}`,C.src.ciudad])}
   ${kpi(N(uh.hab_gasto)+' €',`por habitante en ${uh.anio}`,`${N(uh.hab)} habitantes a 1 de enero`,
      [`<b>Cálculo:</b> el gasto anterior ÷ habitantes empadronados a 1 de enero de ese año.<br><b>Fuente:</b> ejecución presupuestaria y «Población por distrito y barrio» (padrón) de datos.madrid.es.`,C.src.ciudad])}
   ${kpi(M(tribut),`impuestos, tasas y precios cobrados en ${yI}`,'Ayuntamiento, derechos reconocidos',
      [`<b>Cálculo:</b> derechos reconocidos netos de los capítulos de ingresos 1 (impuestos directos: IBI, plusvalía, IAE, vehículos), 2 (impuestos indirectos: construcciones, IVA cedido…) y 3 (tasas y precios públicos). Solo el Ayuntamiento, sin organismos autónomos. «Reconocido» es lo que el Ayuntamiento tiene derecho a cobrar ese año; lo cobrado de verdad puede ser algo menor.<br><b>Fuente:</b> ejecución del presupuesto de ingresos de datos.madrid.es.`,C.src.ingresos])}
   ${kpi(M((I['4']||0)+(I['7']||0)),`transferencias recibidas en ${yI}`,'del Estado, la Comunidad y la UE',
      [`<b>Cálculo:</b> derechos reconocidos de los capítulos de ingresos 4 (transferencias corrientes, sobre todo la participación en los tributos del Estado) y 7 (transferencias de capital para inversiones). Solo el Ayuntamiento.<br><b>Fuente:</b> ejecución del presupuesto de ingresos de datos.madrid.es.`,C.src.ingresos])}
   ${sel?kpi(nf(sel.pag_hab)+' €',`gasto de la Junta de ${esc(DISTN[CM.DSEL])} por habitante (${yD})`,`media de los 21 distritos: ${nf(media('pag_hab'))} €`,
      [`<b>Cálculo:</b> obligaciones reconocidas de la sección presupuestaria de la Junta Municipal (colegios, centros culturales y de mayores, servicios sociales, mantenimiento del distrito…) ÷ habitantes del distrito a 1 de enero. No incluye lo que gastan en el distrito las Áreas de gobierno.<br><b>Fuente:</b> ejecución presupuestaria y padrón de datos.madrid.es.`,C.src.distritos])
     +kpi(nf(sel.inv_hab)+' €',`inversión en ${esc(DISTN[CM.DSEL])} por habitante (${yD})`,`media: ${nf(media('inv_hab'))} €`,
      [`<b>Cálculo:</b> pagos de los proyectos de inversión asignados al distrito (de la Junta y de las Áreas) ÷ habitantes. Los proyectos que afectan a varios distritos no se reparten, y una obra grande puede disparar un año concreto.<br><b>Fuente:</b> «Proyectos de inversión» de la ejecución presupuestaria y padrón de datos.madrid.es.`,C.src.distritos]):''}</div>
  <div class="grid2">${card('Gasto por año',barChart(serie,[{n:'Gastado (consolidado)',c:AZ,i:1}],{title:'Gasto por año',unit:'Capítulos 1 a 7, Ayuntamiento + organismos autónomos, sin operaciones internas'}),srcBtn(C.src.ciudad),
      ci.some(r=>r.aprox)?'Hasta 2022 el portal solo publica el importe presupuestado de las operaciones internas: esos años son una aproximación.':'')}
   ${card(`En qué se gasta (${u.anio})`,hbars(pol.slice(0,12).map(([k,v])=>[C.nombres_politicas[k]||k,v]),M),srcBtn(C.src.politicas),'Políticas de gasto, sin descontar operaciones internas. «Seguridad y movilidad» incluye policía, bomberos y tráfico.')}</div>
  <div class="grid2">${card('De dónde salen los ingresos',barChart(ingS,[{n:'Impuestos',c:AZ,i:1},{n:'Tasas y precios',c:'#6f9fd0',i:2},{n:'Transferencias',c:'#e8590c',i:3},{n:'Patrimonio y ventas',c:'#2b8a3e',i:4},{n:'Préstamos y activos',c:GR,i:5}],{stack:true,title:'Ingresos por año',unit:'Ayuntamiento (sin organismos), derechos reconocidos'}),srcBtn(C.src.ingresos))}
   ${card(`Impuestos y tasas principales (${yI})`,hbars(imp,M,{c:'#6f9fd0'}),srcBtn(C.src.ingresos),'IBI, plusvalía, IAE, vehículos, construcciones… tal como los nombra el presupuesto.')}</div>
  ${mas('ciudadano',[['distritos','Cómo se reparte entre los 21 distritos'],['deuda','Deuda, días de pago y presupuesto de 2027'],['ciudades','Madrid frente a otras grandes ciudades']])}`}

function distritos(C,D,yD){
  return `<h2 class="asec">Comparativa de los 21 distritos (${yD})</h2>
  <p class="sub">El gasto de la Junta es lo que gestiona cada distrito (colegios, centros culturales, servicios sociales, mantenimiento…). La inversión incluye además lo que las Áreas invierten en el distrito. Los proyectos que afectan a varios distritos no se reparten.</p>
  <div class="grid2"><div class="card"><h2 class="sxh">Gasto de la Junta por habitante</h2><div id="sxM1"></div>${srcBtn(C.src.distritos)}</div><div class="card"><h2 class="sxh">Inversión pagada por habitante</h2><div id="sxM2"></div>${srcBtn(C.src.distritos)}</div></div>
  ${card('Los 21 distritos',tabla(['Distrito','Habitantes','Presupuesto Junta','Gastado','Sin gastar','% ejecución','€/hab. Junta','Inversión pagada','€/hab. inversión'],
     D.slice().sort((a,b)=>a.cd-b.cd).map(r=>Object.assign([`<a href="${lk('ciudadano','distritos',r.cd)}">${esc(DISTN[r.cd])}</a>`,N(r.hab),M(r.cdf),M(r.pag),M(r.nog),nf(r.pct,1)+' %',nf(r.pag_hab),M(r.invp),nf(r.inv_hab)],{on:r.cd===CM.DSEL})),{num:[1,2,3,4,5,6,7,8]}),srcBtn(C.src.distritos))}
  ${presupJuntas(C)}${contexto(C)}`}
function mapas(D,yD){
  const o={cd:CM.DSEL,per:String(yD)};
  choro('sxM1',D.map(r=>({cd:r.cd,v:r.pag_hab})),Object.assign({},o,{fmt:v=>nf(v),u:'€ por habitante',fuente:'Ejecución presupuestaria (datos.madrid.es 211496) y padrón (300557)'}));
  choro('sxM2',D.map(r=>({cd:r.cd,v:r.inv_hab})),Object.assign({},o,{fmt:v=>nf(v),u:'€ por habitante',aviso:'Una sola obra grande puede disparar un año la cifra de un distrito.',fuente:'Proyectos de inversión territorializados (211496) y padrón (300557)'}))}

function contexto(C){
  const X=C.contexto||[];if(!X.length)return '';const cd=CM.DSEL;
  const ult=ind=>Math.max(...X.filter(r=>r[2]===ind).map(r=>r[0]));
  const val=(ind,c,det,y)=>{y=y||ult(ind);return X.filter(r=>r[0]===y&&r[1]===c&&r[2]===ind&&(det==null||r[3]===det)).reduce((a,r)=>a+(r[4]||0),0)};
  const yP=ult('pensionistas'),yE=ult('unidades_productivas'),yI=ult('inmuebles'),e0=Math.min(...X.filter(r=>r[2]==='unidades_productivas').map(r=>r[0]));
  const yH=Math.max(...C.distritos.map(x=>x.anio)),hab=c=>{const d=C.distritos.find(r=>r.anio===yH&&r.cd===c);return d?d.hab:0};
  const rows=Array.from({length:21},(_,i)=>i+1).map(c=>{const h=hab(c),p=val('pensionistas',c,'Total'),u=val('unidades_productivas',c,'Total'),u0=val('unidades_productivas',c,'Total',e0),
    o=val('ocupados',c,'Total'),v=val('inmuebles',c,'Viviendas colectivas')+val('inmuebles',c,'Viviendas unifamiliares');
    return Object.assign([`<a href="${lk('ciudadano','distritos',c)}">${esc(DISTN[c])}</a>`,N(p),h?nf(100*p/h,1):'—',N(u),u0?((u>=u0?'+':'−')+nf(Math.abs(100*(u-u0)/u0),1)+' %'):'—',N(o),N(v),N(val('inmuebles',c,'Comercial')),N(val('inmuebles',c,'Oficinas'))],{on:c===cd})});
  const usos=cd!=null?['Viviendas colectivas','Viviendas unifamiliares','Aparcamientos','Comercial','Oficinas','Industrial','Resto de usos'].map(u=>[u,val('inmuebles',cd,u)]):null;
  return `<h2 class="asec">Cómo es cada distrito</h2>
  ${card('Pensionistas, empresas e inmuebles por distrito',tabla(['Distrito',`Pensionistas (${yP})`,'Por cada 100 hab.',`Empresas y locales (${yE})`,`Cambio desde ${e0}`,`Empleos (${yE})`,`Viviendas (${yI})`,'Locales comerciales','Oficinas'],rows,{num:[1,2,3,4,5,6,7,8]}),srcBtn(C.src.contexto),'Datos del Instituto de Estadística de la Comunidad de Madrid. Pensionistas: pensiones contributivas de la Seguridad Social. Empresas: unidades productivas con actividad en el distrito. Inmuebles: recibos del Catastro por uso.')}
  ${usos?'<div class="sxhalf">'+card(`Inmuebles de ${esc(DISTN[cd])} por uso (${yI})`,hbars(usos,N,{c:'#6f9fd0'}),srcBtn(C.src.contexto))+'</div>':''}`;
}
function comparada(C){
  const R=C.comparada||[];if(!R.length)return '';
  const yU=Math.max(...R.map(r=>r[0])),U=R.filter(r=>r[0]===yU),ciu=[...new Set(R.map(r=>r[1]))];
  const ph=(v,p)=>p?v/p:0,rk=(i)=>U.map(r=>[r[1],ph(r[i]||0,r[2])]).sort((a,b)=>b[1]-a[1]),E=v=>N(v)+' €';
  const mad=R.filter(r=>r[1]==='Madrid').map(r=>[r[0],Math.round(ph(r[3],r[2]))]);
  const bcn=Object.fromEntries(R.filter(r=>r[1]==='Barcelona').map(r=>[r[0],ph(r[3],r[2])]));
  const med=Object.fromEntries([...new Set(R.map(r=>r[0]))].map(y=>{const t=R.filter(r=>r[0]===y);return [y,t.reduce((a,r)=>a+(r[3]||0),0)/t.reduce((a,r)=>a+r[2],0)]}));
  const tb=U.slice().sort((a,b)=>ph(b[3],b[2])-ph(a[3],a[2])).map(r=>Object.assign([esc(r[1]),N(r[2]),E(ph(r[3],r[2])),E(ph(r[5]||0,r[2])),E(ph(r[4]||0,r[2])),E(ph(r[6]||0,r[2]))],{on:r[1]==='Madrid'}));
  return `<h2 class="asec">Madrid frente a otras grandes ciudades</h2>
  <div class="grid2">${card(`Gasto por habitante (${yU})`,hbars(rk(3),E),srcBtn(C.src.comparada),'Gasto no financiero (capítulos 1 a 7) consolidado de cada ayuntamiento con sus organismos y empresas, según la liquidación que cada ciudad envía a Hacienda (CONPREL).')}
   ${card(`Impuestos y tasas por habitante (${yU})`,hbars(rk(5),E,{c:'#6f9fd0'}),srcBtn(C.src.comparada),'Ingresos de los capítulos 1 a 3: impuestos directos, indirectos y tasas.')}</div>
  <div class="grid2">${card('Gasto por habitante a lo largo del tiempo',barChart(mad.map(([y,v])=>[y,v,Math.round(bcn[y]||0),Math.round(med[y]||0)]),[{n:'Madrid',c:AZ,i:1},{n:'Barcelona',c:'#e8590c',i:2},{n:'Media de las 10 ciudades',c:GR,i:3}],{title:'€ por habitante',unit:'gasto no financiero consolidado',eur:false}),srcBtn(C.src.comparada))}
   ${card(`Las ${ciu.length} ciudades en ${yU}`,tabla(['Ciudad','Habitantes','Gasto/hab','Impuestos y tasas/hab','Inversión/hab','Personal/hab'],tb,{num:[1,2,3,4,5]}),srcBtn(C.src.comparada),'Mismas reglas para todas las ciudades, por eso las cifras de Madrid pueden diferir algo de las del presupuesto municipal.')}</div>`;
}
function deudaPagos(C){
  const D=C.deuda.filter(r=>r[1]==='TOTAL DEUDA LARGO Y CORTO PLAZO'),dU=last(D),d0=D.find(r=>r[0]===2012);
  const pm={};C.pmp.forEach(r=>{(pm[r[0]]=pm[r[0]]||[]).push(r[2])});const pU=last(C.pmp);
  return `<p class="sub">Son cifras de todo el Ayuntamiento: no se reparten por distritos.</p>
  <div class="kpis">${kpi(M(dU[2]),`deuda a 31/12/${dU[0]}`,d0?`${M(d0[2])} en 2012`:'',[`<b>Cálculo:</b> «Total deuda a largo y corto plazo» del Ayuntamiento a 31 de diciembre: préstamos y emisiones pendientes de devolver.<br><b>Fuente:</b> «Deuda viva» de datos.madrid.es.`,C.src.deuda])}
   ${kpi(nf(pU[2],1)+' días',`tarda en pagar a proveedores (${pU[1]}/${pU[0]})`,'el máximo legal es 30 días',[`<b>Cálculo:</b> periodo medio de pago a proveedores del mes, tal como lo publica el Ayuntamiento según la fórmula legal (Real Decreto 635/2014).<br><b>Fuente:</b> «Periodo medio de pago a proveedores» de datos.madrid.es.`,C.src.pmp])}</div>
  <div class="grid2">${card('Deuda del Ayuntamiento',barChart(D.map(r=>[r[0],r[2]]),[{n:'Deuda a 31 de diciembre',c:AZ,i:1}],{title:'Deuda por año',unit:'Préstamos y emisiones a largo y corto plazo del Ayuntamiento'}),srcBtn(C.src.deuda))}
   ${card('Días que tarda en pagar a proveedores',colChart(Object.keys(pm).map(Number).sort().map(y=>[y,pm[y].reduce((a,b)=>a+b,0)/pm[y].length]),{u:'días',d:1,title:'Periodo medio de pago',unit:'media de los meses de cada año · el año en curso, incompleto'}),srcBtn(C.src.pmp))}</div>`}
function presupJuntas(C){
  const cd=CM.DSEL,fut=C.futuro.filter(r=>cd==null||r[2]===cd),sumF=(a,e)=>fut.filter(r=>r[0]===a&&r[1]===e).reduce((x,r)=>x+(r[3]||0),0);
  const yD=Math.max(...C.distritos.map(x=>x.anio)),dd=cd!=null?C.distritos.find(r=>r.anio===yD&&r.cd===cd):null;
  const f26=sumF(2026,'aprobado'),f27=sumF(2027,'proyecto');
  const tabF=Array.from({length:21},(_,i)=>i+1).map(c=>{const a=C.futuro.filter(r=>r[2]===c&&r[0]===2026).reduce((x,r)=>x+r[3],0),b=C.futuro.filter(r=>r[2]===c&&r[0]===2027).reduce((x,r)=>x+r[3],0);
    return Object.assign([`<a href="${lk('ciudadano','distritos',c)}">${esc(DISTN[c])}</a>`,M(a),M(b),a?((b>=a?'+':'−')+nf(Math.abs(100*(b-a)/a),1)+' %'):'—'],{on:c===cd})});
  return `<h2 class="asec">Presupuesto de las Juntas: 2026 aprobado y 2027 en proyecto</h2>
  ${cd==null?card('Presupuesto de cada Junta',tabla(['Distrito','2026 aprobado','2027 proyecto','Cambio'],tabF,{num:[1,2,3]}),srcBtn(C.src.futuro),'Solo lo que gestiona la Junta; el proyecto de 2027 puede cambiar hasta que lo apruebe el Pleno.')
     :'<div class="sxhalf">'+card(`Presupuesto de la Junta de ${esc(DISTN[cd])}`,barChart([[yD,dd?dd.pag:0,0,0],[2026,0,f26,0],[2027,0,0,f27]],[{n:'Gastado',c:AZ,i:1},{n:'Aprobado',c:'#6f9fd0',i:2},{n:'Proyecto',c:'#e8590c',i:3}],{stack:true,title:'Presupuesto',unit:`${yD} gastado · 2026 aprobado · 2027 en proyecto`}),srcBtn([...C.src.futuro,...C.src.distritos]),
       f26?`2027: ${M(f27)} (${f27>=f26?'+':'−'}${nf(Math.abs(100*(f27-f26)/f26),1)} % frente a 2026).`:'')+'</div>'}`}
/* Enlaces al final de una página hacia las otras pestañas */
const mas=(v,L)=>`<div class="sxmas"><b>Sigue en ${SECS[v].t}:</b> ${L.map(([k,t])=>`<a href="${lk(v,k)}">${t} →</a>`).join('')}</div>`;

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
  const pg=curP('via'),invT=CM.DSEL==null?porD.reduce((a,r)=>a+r.v,0):(porD.find(r=>r.cd===CM.DSEL)||{}).v;
  if(pg==='asfalto'){el.innerHTML=cab('via')+asfalto(V);return}
  if(pg==='inversion'){
    el.innerHTML=`${cab('via')}
  <div class="kpis">${kpi(M(invT),`invertido en vía pública en ${yv}`,'calles, zonas verdes, alumbrado, tráfico y limpieza',[`<b>Cálculo:</b> pagos de los proyectos de inversión con distrito asignado de los programas de vías públicas, parques y jardines, alumbrado, tráfico y limpieza.<br><b>Fuente:</b> «Proyectos de inversión» de la ejecución presupuestaria de datos.madrid.es.`,V.src.inversion_via])}
   ${kpi(nf(inv.length),'inversiones principales con ubicación',`${M(inv.reduce((a,r)=>a+(r[10]||0),0))} presupuestados`,[`<b>Cálculo:</b> número de inversiones del listado municipal de «Inversiones principales» de este ámbito y suma de su presupuesto.<br><b>Fuente:</b> datos.madrid.es.`,V.src.inversiones])}</div>
  <div class="grid2"><div class="card"><h2 class="sxh">Inversión en vía pública por distrito (${yv})</h2><div id="sxM3"></div>${srcBtn(V.src.inversion_via)}</div>
   ${card('Inversión en vía pública por año',barChart(serieInv,prog.map((p,i)=>({n:V.programas[p],c:PAL[i],i:i+1})),{stack:true,title:'Inversión pagada',unit:`${esc(amb())} · proyectos de inversión con distrito asignado`}),srcBtn(V.src.inversion_via))}</div>
  ${card(`Inversiones principales en ${esc(amb())}`,tabla(['Inversión','Dirección','Línea','Estado','Presupuesto','Gastado','Mapa'],inv.slice(0,40).map(r=>[esc(r[1]),esc(r[3]||''),esc(r[6]||''),esc(r[7]||''),eurS(r[10]),eurS(r[11]),r[4]?`<a href="https://www.openstreetmap.org/?mlat=${r[4]}&mlon=${r[5]}#map=18/${r[4]}/${r[5]}" target="_blank" rel="noopener">Ver</a>`:'—']),{num:[4,5]})+(inv.length>40?`<p class="sub">Las 40 de mayor presupuesto de ${nf(inv.length)}.</p>`:''),srcBtn(V.src.inversiones))}`;
    choro('sxM3',porD,{cd:CM.DSEL,per:String(yv),fmt:v=>nf(v/1e6,1),u:'M€',aviso:'Total del distrito, no por habitante: los distritos grandes reciben más.',fuente:'Proyectos de inversión (datos.madrid.es 211496), programas de vías públicas, zonas verdes, alumbrado, tráfico y limpieza'});return}
  el.innerHTML=`${cab('via',`<p class="lead">${esc(frase)}</p>`)}
  <div class="kpis">${kpi(N(tot),'licencias de obras en vía pública desde 2017',`${nf(rows.find(r=>r[0]===ya)?rows.find(r=>r[0]===ya).slice(1).reduce((a,b)=>a+b,0):0)} en ${ya}`,[`<b>Cálculo:</b> licencias de obras en la vía pública finalizadas (calas, canalizaciones, alcantarillado, averías urgentes y obras municipales), contadas por su dirección.<br><b>Fuente:</b> «Licencias de obras en vía pública» de datos.madrid.es, desde abril de 2017.`,V.src.licencias])}
   ${kpi(nf(obras.length),'obras públicas planificadas o en marcha','según el Ayuntamiento',[`<b>Cálculo:</b> obras del listado municipal de obras planificadas y en ejecución de este ámbito.<br><b>Fuente:</b> datos.madrid.es.`,obras.map(o=>o.src)])}</div>
  <div class="grid2">${card('Licencias de obras por año y tipo',barChart(rows,TIPOS.map((t,i)=>({n:t[0],c:t[1],i:i+1})),{stack:true,title:'Licencias por año',unit:'licencias finalizadas; 2017 desde abril; el año en curso, incompleto'}),srcBtn(V.src.licencias),
      'Cada licencia es una apertura de la calle por una compañía de servicios o por el Ayuntamiento. No incluye su coste, que no se publica.')}
   ${card('Calles con más intervenciones',tabla(['Calle','Total','Averías','Calas','Canaliz.','Desde'],calles.slice(0,15).map(c=>[esc(c[0]),N(c[1]),nf(c[4]),nf(c[5]),nf(c[6]),c[3]]),{num:[1,2,3,4]}),srcBtn(V.src.licencias),
      `${esc(amb())} · misma calle escrita de varias formas, agrupada`)}</div>
  ${card('Obras públicas planificadas y en ejecución',obras.length?tabla(['Obra','Calles','Empresa','Presupuesto','Inicio','Fin'],obras.map(o=>[esc(o.nombre),esc((o.calles||'').slice(0,120)),esc(o.empresa||'—'),o.presupuesto?eurS(+String(o.presupuesto).replace(',','.')):'—',esc(o.inicio||''),esc(o.fin||'')]),{num:[3]}):'<p class="sub">No hay obras de este ámbito en el listado actual.</p>',srcBtn(obras.map(o=>o.src)))}
  ${mas('via',[['asfalto','Calles asfaltadas cada año'],['inversion','Cuánto se invierte en calles, parques y alumbrado']])}`}

function asfalto(V){const cd=CM.DSEL,A=V.asfalto.filter(r=>cd==null||r[1]===cd),años=[...new Set(V.asfalto.map(r=>r[0]))].sort();
  const serie=años.map(y=>[y,A.filter(r=>r[0]===y).reduce((x,r)=>x+r[2],0)]),yU=last(años);
  const pr=A.filter(r=>r[4]).reduce((x,r)=>x+r[4],0),yP=(A.find(r=>r[4])||[])[0];
  const L=V.asfalto_calles.filter(r=>(cd==null||r[1]===cd)&&r[0]>=yU-1);
  return card(`Operación Asfalto · ${esc(amb())}`,`<div class="grid2"><div>${colChart(serie,{u:'tramos',title:'Tramos asfaltados por año',unit:'tramos de calle de la Operación Asfalto'})}${pr?`<p class="sub">Precio aproximado de los tramos de ${yP}: <b>${M(pr)}</b>.</p>`:''}</div>
    <div>${tabla(['Año','Calle','Tramo','Estado','Precio aprox.','Mapa'],L.slice(0,40).map(r=>[r[0],esc(r[2]||''),esc((r[3]||'').slice(0,60)),esc(r[4]||''),r[5]?eurS(r[5]):'—',r[6]?`<a href="https://www.openstreetmap.org/?mlat=${r[6].toFixed(5)}&mlon=${r[7].toFixed(5)}#map=17/${r[6].toFixed(5)}/${r[7].toFixed(5)}" target="_blank" rel="noopener">Ver</a>`:'—']),{num:[4]})}
    ${L.length>40?`<p class="sub">40 de ${N(L.length)} tramos de ${yU-1} y ${yU}.</p>`:''}</div></div>`,srcBtn(V.src.asfalto),'Calles y tramos de la campaña anual de asfaltado, tomados del Geoportal del Ayuntamiento.')}

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
  if(curP('servicios')==='pagos'){el.innerHTML=cab('servicios')+pagos(S);return}
  el.innerHTML=`${cab('servicios',`<p class="lead">${esc(frase)}</p>`)}
  <div class="kpis">${kpi(N(n),'contratos desde 2015','registro de contratos y contratos menores')}${kpi(M(tot),'importe adjudicado','IVA incluido')}${kpi(N(nm),'contratos menores',`${nf(100*nm/Math.max(n,1),0)} % del número de contratos`)}</div>
  ${CM.DSEL!=null?'<p class="chw">En un distrito solo se cuentan los contratos de su Junta. Los contratos de las Áreas que dan servicio a toda la ciudad (limpieza, recogida de basuras…) están en el ámbito Madrid.</p>':''}
  <div class="grid2">${card('Importe adjudicado por año',barChart(rows,ks.map((k,i)=>({n:TR[k][0],c:TR[k][1],i:i+1})),{stack:true,title:'Importe por año',unit:'IVA incluido · en los acuerdos marco es el techo de gasto, no lo pagado'}),srcBtn(S.src.contratos))}
   ${card('Número de contratos por año',barChart(nrow,ks.map((k,i)=>({n:TR[k][0],c:TR[k][1],i:i+1})),{stack:true,title:'Contratos por año',unit:'contratos inscritos'}),srcBtn(S.src.contratos))}</div>
  ${card(`Empresas con más importe adjudicado · ${esc(amb())}`,tabla(['Empresa','NIF','Contratos','Importe','Menores','Años'],R.map(r=>[esc(r[0]),esc(r[1]||'—'),N(r[2]),M(r[3]),nf(r[4]),r[5]===r[6]?r[5]:r[5]+'–'+r[6]]),{num:[2,3,4]}),srcBtn(S.src.contratos),
    'Importe adjudicado, no pagado. Las personas físicas no se muestran por su nombre. Las UTE cuentan aparte de sus socias.')}
  ${mas('servicios',[['pagos','Lo que se paga de verdad y a quién']])}`}
function pagos(S){const cd=CM.DSEL,P=S.pagos[String(cd||0)]||[],PA=S.pagos_anio.filter(r=>cd==null||r[1]===cd),años=[...new Set(PA.map(r=>r[0]))].sort();
  const serie=años.map(y=>[y,PA.filter(r=>r[0]===y).reduce((x,r)=>x+(r[2]||0),0)]),yU=last(años);
  return `<p class="sub">El contrato fija cuánto se puede gastar; aquí está lo que el Ayuntamiento reconoce que debe pagar cada año a cada proveedor, entidad o administración.</p>
  <div class="grid2">${card('Pagado por año',barChart(serie,[{n:'Pagado',c:AZ,i:1}],{title:'Pagado por año',unit:cd==null?'Ayuntamiento y organismos autónomos, todos los perceptores':'Pagos de la Junta del distrito'}),srcBtn(S.src.pagos),'Pagos a terceros: lo que el Ayuntamiento reconoce que debe pagar a cada proveedor, entidad o administración, no lo adjudicado.')}
   ${card('Quién cobra más (2011–'+yU+')',tabla(['Perceptor','NIF','Total','Último año','Años'],P.slice(0,20).map(r=>[esc(r[0]),esc(r[1]||'—'),M(r[2]),M(r[3]),r[4]===r[5]?r[4]:r[4]+'–'+r[5]]),{num:[2,3]}),srcBtn(S.src.pagos),'Incluye empresas, entidades y otras administraciones (como el Consorcio de Transportes).')}</div>`}

// ---------- Servicios sociales ----------
async function social(el){const [C,S]=await Promise.all([get('ciudadano'),get('servicios')]);const cd=CM.DSEL;
  if(curP('social')==='espera'){
    const E=S.espera.filter(r=>cd==null||r[1]===cd),sv=[...new Set(S.espera.map(r=>r[0]))];
    const tE=sv.map(v=>{const x=E.filter(r=>r[0]===v),n=x.reduce((a,r)=>a+r[2],0),med=n?Math.round(x.reduce((a,r)=>a+r[3]*r[2],0)/n):null;return [esc(v),N(n),med==null?'—':N(med)+' días',x.length?N(Math.max(...x.map(r=>r[4])))+' días':'—']});
    const tot=E.reduce((a,r)=>a+r[2],0);
    el.innerHTML=`${cab('social')}<div class="kpis">${kpi(N(tot),'personas mayores esperando un servicio',`a ${esc((S.espera_fecha||'').slice(0,10))}`,[`<b>Cálculo:</b> solicitudes en lista de espera de los servicios municipales para mayores (ayuda a domicilio, centros de día, residencias…), contadas por distrito. La espera es la diferencia entre la fecha de entrada de la solicitud y la fecha de los datos.<br><b>Fuente:</b> «Listas de espera de servicios sociales» de datos.madrid.es. El fichero incluye DNI parcial e iniciales, que no se usan.`,S.src.espera])}</div>
    ${card('Listas de espera de servicios para mayores · '+esc(amb()),tabla(['Servicio','Personas esperando','Espera media','Espera máxima'],tE,{num:[1,2,3]}),srcBtn(S.src.espera),'Solo cifras: no se muestra ningún dato de las personas.')}
    ${mas('social',[['ayudas','Ayudas que reciben los vecinos']])}`;return}
  const AS=C.ayudas_sociales.filter(r=>cd==null||r[1]===cd),años=[...new Set(AS.map(r=>r[0]))].sort();
  const asN=años.map(y=>[y,AS.filter(r=>r[0]===y).reduce((x,r)=>x+r[2],0)]),asV=años.map(y=>[y,AS.filter(r=>r[0]===y).reduce((x,r)=>x+(r[3]||0),0)]);
  const yC=last(años.filter(y=>y<new Date().getFullYear())),nC=(asN.find(r=>r[0]===yC)||[])[1]||0,vC=(asV.find(r=>r[0]===yC)||[])[1]||0;
  el.innerHTML=`${cab('social')}
  <div class="kpis">${kpi(N(nC),`ayudas concedidas en ${yC}`,M(vC)+(cd!=null&&yC>=2024?' · desde 2024 el portal solo indica el distrito en parte de las ayudas: la cifra real es mayor':''),[`<b>Cálculo:</b> ayudas económicas de servicios sociales concedidas ese año (alimentos, comedor, escuela infantil, necesidades básicas, vivienda…), contadas por el distrito que indica el portal.<br><b>Fuente:</b> «Ayudas económicas de servicios sociales» de datos.madrid.es. Sin datos de las personas beneficiarias.`,C.src.ayudas_sociales])}</div>
  <div class="grid2">${card('Ayudas concedidas por año',colChart(asN,{u:'ayudas',title:'Ayudas por año',unit:'número de ayudas'}),srcBtn(C.src.ayudas_sociales),
      cd!=null?'De 2016 a 2018 el portal no indica el distrito; desde 2024 solo en parte de las ayudas.':'Sin datos de las personas beneficiarias.')}
   ${card('Para qué son (desde 2021, toda la ciudad)',hbars(C.ayudas_sociales_tipo.map(r=>[r[0],r[2]]),M,{c:'#6f9fd0'}),srcBtn(C.src.ayudas_sociales))}</div>
  ${mas('social',[['espera','Cuánto se espera para un servicio de mayores']])}`}

// ---------- Ayudas y convenios ----------
async function ayudas(el){const A=await get('ayudas');
  const rec=A.recibidas,niv={};rec.forEach(r=>{niv[r[0]]=(niv[r[0]]||0)+(r[7]||0)});
  const fe=A.fondos_europeos.filter(r=>CM.DSEL==null||r[7]===CM.DSEL||r[7]==null),feT=fe.reduce((a,r)=>a+(r[3]||0),0);
  const cv=A.convenios.filter(r=>CM.DSEL==null||r[3]===CM.DSEL),cy={};cv.forEach(r=>{if(r[1])cy[r[1]]=(cy[r[1]]||0)+1});
  const cRows=Object.keys(cy).map(Number).sort().map(y=>[y,cy[y]]);
  const frase=`Otras administraciones han concedido al Ayuntamiento, sus organismos y empresas ${nf(rec.length)} ayudas por ${M(rec.reduce((a,r)=>a+(r[7]||0),0))} según su registro. Además, ha obtenido ${M(A.fondos_europeos.reduce((a,r)=>a+(r[3]||0),0))} de fondos europeos (Plan de Recuperación y FEDER) en ${nf(A.fondos_europeos.length)} proyectos.`;
  if(curP('ayudas')==='convenios'){
    el.innerHTML=`${cab('ayudas')}<div class="kpis">${kpi(nf(cv.length),'convenios firmados desde nov. 2018','con empresas, entidades y administraciones',[`<b>Cálculo:</b> convenios inscritos en el registro municipal${CM.DSEL!=null?' cuyo órgano firmante es la Junta del distrito':''}.<br><b>Fuente:</b> «Convenios inscritos» de datos.madrid.es.`,A.src.convenios])}</div>
  <div class="grid2">${card('Convenios por año',barChart(cRows,[{n:'Convenios',c:AZ,i:1}],{title:'Convenios por año',unit:'convenios inscritos (2018 desde noviembre)'}).replace(/ M€|€/g,''),srcBtn(A.src.convenios))}
   ${card('Buscar convenios',`<input type="search" id="sxCq" placeholder="Empresa, entidad o tema (p. ej. «fundación», «universidad», «Iberdrola»)" class="sxin" aria-label="Buscar convenios"><div id="sxCl"></div>`,srcBtn(A.src.convenios),'Con quién firma el Ayuntamiento, para qué y qué se compromete a pagar cada parte.')}</div>`;
    const q=document.getElementById('sxCq'),out=document.getElementById('sxCl');
    const pinta=()=>{const t=(q.value||'').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');const f=cv.filter(r=>!t||(r[4]+' '+r[5]+' '+r[2]).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').includes(t));
      out.innerHTML=`<p class="sub">${nf(f.length)} convenios${t?' que contienen «'+esc(q.value)+'»':''}; se muestran los 25 más recientes.</p>`+tabla(['Fecha','Con','Objeto','Paga el Ayto.'],f.slice(0,25).map(r=>[esc(r[0]||''),esc(r[5]||''),r[8]?`<a href="${esc(r[8])}" target="_blank" rel="noopener">${esc(r[4])}</a>`:esc(r[4]),r[6]?eurS(r[6]):'—']),{num:[3]})};
    q.oninput=pinta;pinta();return}
  el.innerHTML=`${cab('ayudas',`<p class="lead">${esc(frase)}</p>`)}
  <div class="kpis">${Object.entries(niv).sort((a,b)=>b[1]-a[1]).map(([k,v])=>kpi(M(v),({'AUTONÓMICA':'ayudas autonómicas','ESTATAL':'ayudas estatales','LOCAL':'ayudas locales','OTROS':'otras ayudas'})[k]||esc(k))).join('')}${kpi(M(feT),'fondos europeos'+(CM.DSEL!=null?' (distrito o toda la ciudad)':''))}</div>
  ${CM.DSEL!=null?'<p class="chw">Las ayudas recibidas son para toda la ciudad: no se asignan a distritos. Los fondos europeos y convenios sí se filtran cuando el organismo indica el distrito.</p>':''}
  ${card('Ayudas recibidas de otras administraciones',tabla(['Concede','Convocatoria','Fecha','Beneficiario','Importe','Bases'],rec.slice(0,60).map(r=>[esc(r[1])+'<br><span class="sub">'+esc(r[2]||'')+'</span>',esc(r[3]),esc(r[4]||''),esc(r[6]||''),eurS(r[7]),r[9]?`<a href="${esc(r[9])}" target="_blank" rel="noopener">BOE/BOCM</a>`:'—']),{num:[4]})+(rec.length>60?`<p class="sub">Las 60 de mayor importe de ${nf(rec.length)}.</p>`:''),srcBtn(A.src.recibidas))}
  ${card('Fondos europeos',tabla(['Programa','Proyecto','Año','Concedido','Ámbito'],fe.slice(0,60).map(r=>[esc(r[0]),r[9]?`<a href="${esc(r[9])}" target="_blank" rel="noopener">${esc(r[1])}</a>`:esc(r[1]),r[2]||'—',eurS(r[3]),esc(r[6]||'')]),{num:[3]}),srcBtn(A.src.fondos),'Kohesio (portal de la Comisión Europea) se añadirá para contrastar cuando se pueda acceder a él.')}
  ${mas('ayudas',[['convenios','Convenios con empresas y entidades']])}`}

// ---------- Inicio ----------
async function inicio(el){
  const [C,V,S,A]=await Promise.all(['ciudadano','via','servicios','ayudas'].map(get));const cd=CM.DSEL,yA=new Date().getFullYear()-1;
  const ci=C.ciudad.filter(r=>r.gasto),u=last(ci),uh=last(ci.filter(r=>r.hab_gasto));
  const D=C.distritos.filter(r=>r.anio===Math.max(...C.distritos.map(x=>x.anio))),sel=cd!=null?D.find(r=>r.cd===cd):null;
  const lic=V.licencias.filter(r=>(cd==null||r[1]===cd)&&r[0]===yA).reduce((a,r)=>a+r[3],0);
  const yAs=Math.max(...V.asfalto.map(r=>r[0])),asf=V.asfalto.filter(r=>(cd==null||r[1]===cd)&&r[0]===yAs).reduce((a,r)=>a+r[2],0);
  const base=cd==null?S.por_anio.map(r=>[r[0],r[1],r[2],r[3]]):S.por_distrito.filter(r=>r[1]===cd).map(r=>[r[0],r[2],r[3],r[4]]);
  const conImp=base.filter(r=>r[0]===yA).reduce((a,r)=>a+(r[3]||0),0),conN=base.filter(r=>r[0]===yA).reduce((a,r)=>a+(r[2]||0),0);
  const esp=S.espera.filter(r=>cd==null||r[1]===cd).reduce((a,r)=>a+r[2],0);
  const AS=C.ayudas_sociales.filter(r=>(cd==null||r[1]===cd)&&r[0]===yA),asN=AS.reduce((a,r)=>a+r[2],0);
  const fe=A.fondos_europeos.reduce((a,r)=>a+(r[3]||0),0),cv=A.convenios.filter(r=>cd==null||r[3]===cd).length;
  const bloque=(v,ico,t,dato,txt,links)=>`<a class="inib" href="${lk(v,null)}"><span class="inii" aria-hidden="true">${ico}</span><span class="init">${t}</span><span class="iniv">${dato}</span><span class="inix">${txt}</span><span class="inil">${links}</span></a>`;
  el.innerHTML=`<div class="inih"><h1>${cd==null?'Los datos públicos de Madrid':'Los datos públicos de '+esc(DISTN[cd])}</h1>
  <p class="lead">Qué ingresa y gasta el Ayuntamiento, qué obras se hacen en tu calle, quién cobra por los servicios y cómo están los edificios municipales. Cada cifra tiene un botón «De dónde sale» con el fichero oficial y los pasos para repetir el cálculo.</p>
  ${ambBar('inicio')}</div>
  <div class="inig">
   ${bloque('ciudadano','€','Presupuesto',sel?nf(sel.pag_hab)+' €/hab.':N(uh.hab_gasto)+' €/hab.',sel?`por habitante gastó la Junta de ${esc(DISTN[cd])} en ${D[0].anio} (media de los distritos: ${nf(D.reduce((a,r)=>a+r.pag_hab,0)/D.length)} €)`:`por habitante gastó el Ayuntamiento en ${u.anio}: ${M(u.gasto)} en total`,'Ingresos y gastos · Por distritos · Deuda y pagos · Otras ciudades')}
   ${bloque('via','⛏','Calles y obras',N(lic)+' licencias',`de obras en la vía pública en ${yA} · ${N(asf)} tramos asfaltados en ${yAs}`,'Obras en la calle · Asfaltado · Inversión')}
   ${bloque('servicios','✎','Contratos',M(conImp),`adjudicados en ${yA} en ${N(conN)} contratos${cd!=null?' de la Junta':''}`,'Contratos adjudicados · Pagos a proveedores')}
   ${bloque('social','♥','Servicios sociales',N(esp)+' personas',`mayores en lista de espera · ${N(asN)} ayudas a vecinos en ${yA}`,'Ayudas a vecinos · Listas de espera')}
   ${bloque('ayudas','⇄','Fondos y convenios',M(fe),`de fondos europeos para la ciudad · ${N(cv)} convenios firmados desde 2018`,'Fondos recibidos · Convenios')}
   <a class="inib" href="#mapa${cd!=null?'?d='+cd:''}"><span class="inii" aria-hidden="true">⌂</span><span class="init">Edificios municipales</span><span class="iniv">${CM.nEdif?N(CM.nEdif)+' edificios':'Mapa ITE'}</span><span class="inix">colegios, centros culturales, de mayores, deportivos… y el estado de su inspección técnica (ITE)</span><span class="inil">Mapa ITE · Mi distrito · Más urgentes · Cifras ITE · Inversión en edificios · Informe PDF</span></a>
  </div>
  <p class="sub">Las cifras de cada bloque son del último año completo disponible. Cómo se obtiene cada dato: <a href="#ayuda">Ayuda y datos</a>.</p>`}

const R={inicio,ciudadano,via,servicios,social,ayudas};
window.SEC={render(v){const el=document.getElementById('sx-'+v);if(!el||!R[v])return;
  if(!el.innerHTML)el.innerHTML='<p class="sub">Cargando datos…</p>';
  R[v](el).catch(e=>{el.innerHTML=`<p class="chw">No se han podido cargar los datos (${esc(e.message)}). Prueba a recargar la página.</p>`})}};
})();
