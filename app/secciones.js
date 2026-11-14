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

// ---------- Secciones (divisiones) y sus 4 páginas, iguales en todas ----------
const PAGS=[['resumen','Resumen'],['informe','Informe'],['graficos','Gráficos'],['metodo','Cómo se calcula y datos']];
const SECS={
  inicio:{t:'Ciudadano Madrid',s:'Los datos públicos de tu ciudad y tu distrito, con el camino para comprobar cada cifra'},
  ciudadano:{t:'Presupuesto',s:'Cuánto ingresa y gasta el Ayuntamiento, en qué y en qué distrito',c:'#1f5fa8',i:'€'},
  via:{t:'Calles y obras',s:'Obras en la calle, asfaltado, inversión en la vía pública, árboles y alumbrado',c:'#e8590c',i:'⛏'},
  seguridad:{t:'Seguridad y convivencia',s:'Accidentes de tráfico, multas y sanciones de limpieza',c:'#c92a2a',i:'⚠'},
  servicios:{t:'Contratos',s:'Qué empresas trabajan para el Ayuntamiento, por cuánto y cuánto se les paga',c:'#845ef7',i:'✎'},
  social:{t:'Servicios sociales',s:'Ayudas a vecinos y esperas en los servicios para mayores',c:'#d6336c',i:'♥'},
  ayudas:{t:'Fondos y convenios',s:'Dinero que el Ayuntamiento recibe y reparte en subvenciones, y acuerdos que firma',c:'#2b8a3e',i:'⇄'},
  edificios:{t:'Edificios municipales',s:'Colegios, centros culturales, de mayores, deportivos… y el estado de su inspección técnica (ITE)',c:'#0b7285',i:'⌂'},
  completo:{t:'Informe completo',s:'Cómo está cada distrito en todas las secciones y qué puesto ocupa en Madrid',c:'#495057',i:'≡'}};
// Zonas de la portada: cada sección ocupa un grupo de distritos contiguos
const ZONAS={completo:[1,7,4,3],edificios:[8],ciudadano:[9,10],via:[6,5,16,21],seguridad:[15,20,19],servicios:[11,12,2],social:[17,18],ayudas:[13,14]};
let EMBED=null;
const part=v=>EMBED&&EMBED.v===v?EMBED.p:null;
function curP(v){if(!SECS[v]||v==='inicio')return null;const m=(location.hash.match(/[?&]p=([\w-]+)/)||[])[1];return PAGS.some(x=>x[0]===m)?m:'resumen'}
function lk(v,p,cd){const a=[];if(p)a.push('p='+p);if(cd!==null&&(cd!==undefined?cd:CM.DSEL)!=null)a.push('d='+(cd!==undefined?cd:CM.DSEL));return '#'+v+(a.length?'?'+a.join('&'):'')}
const cab=(v,extra)=>{if(EMBED)return extra||'';const S=SECS[v],cp=curP(v);
  return `<h1><span class="sxico" style="background:${S.c||'#123f73'}" aria-hidden="true">${S.i||''}</span>${S.t}</h1><p class="sxsub">${S.s}</p>${v!=='inicio'?`<div class="sxtabs" role="tablist">${PAGS.map(([k,n])=>`<a role="tab" href="${lk(v,k)}"${k===cp?' class="on" aria-selected="true"':' aria-selected="false"'}>${n}</a>`).join('')}</div>`:''}${ambBar(v)}${extra||''}`};
const mas=()=> '';

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
  const pg=part('ciudadano');
  if(pg==='deuda'){el.innerHTML=cab('ciudadano')+deudaPagos(C);return}
  if(pg==='ciudades'){el.innerHTML=cab('ciudadano')+comparada(C);return}
  if(pg==='distritos'){el.innerHTML=cab('ciudadano',`<p class="lead">${esc(frase)}</p>`)+distritos(C,D,yD);mapas(D,yD);if(CM._rentaMap)CM._rentaMap();return}
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
  const R0=C.renta||[],yR0=R0.length?Math.max(...R0.map(r=>r[0])):null;
  const rows=Array.from({length:21},(_,i)=>i+1).map(c=>{const h=hab(c),rp=(R0.find(r=>r[0]===yR0&&r[1]===c&&r[2]==='p')||[])[3],p=val('pensionistas',c,'Total'),u=val('unidades_productivas',c,'Total'),u0=val('unidades_productivas',c,'Total',e0),
    o=val('ocupados',c,'Total'),v=val('inmuebles',c,'Viviendas colectivas')+val('inmuebles',c,'Viviendas unifamiliares');
    return Object.assign([`<a href="${lk('ciudadano','distritos',c)}">${esc(DISTN[c])}</a>`,rp?N(rp)+' €':'—',N(p),h?nf(100*p/h,1):'—',N(u),u0?((u>=u0?'+':'−')+nf(Math.abs(100*(u-u0)/u0),1)+' %'):'—',N(o),N(v),N(val('inmuebles',c,'Comercial')),N(val('inmuebles',c,'Oficinas'))],{on:c===cd})});
  const usos=cd!=null?['Viviendas colectivas','Viviendas unifamiliares','Aparcamientos','Comercial','Oficinas','Industrial','Resto de usos'].map(u=>[u,val('inmuebles',cd,u)]):null;
  const R=C.renta||[],yR=R.length?Math.max(...R.map(r=>r[0])):null,ren=(c,k,y)=>(R.find(r=>r[0]===(y||yR)&&r[1]===c&&r[2]===k)||[])[3];
  const rMad=ren(0,'p'),rSel=cd!=null?ren(cd,'p'):null,r0=cd!=null?ren(cd,'p',2015):ren(0,'p',2015);
  const rentaHTML=R.length?`<div class="grid2"><div class="card"><h2 class="sxh">Renta neta media por persona (${yR})</h2><div id="sxM5"></div>${srcBtn(C.src.renta)}</div>
   ${card('Renta por año',barChart([...new Set(R.map(r=>r[0]))].sort().map(y=>[y,Math.round(ren(0,'p',y)||0),cd!=null?Math.round(ren(cd,'p',y)||0):0]),[{n:'Madrid',c:GR,i:1}].concat(cd!=null?[{n:DISTN[cd],c:AZ,i:2}]:[]),{title:'Renta neta media por persona',unit:'euros al año · año de los ingresos (el INE los publica con unos dos años de retraso)'}),srcBtn(C.src.renta),
     `${cd!=null?`${esc(DISTN[cd])}: ${N(rSel)} € por persona, ${nf(100*rSel/rMad,0)} % de la media de Madrid (${N(rMad)} €).`:`Madrid: ${N(rMad)} € por persona en ${yR}.`} Desde 2015: ${r0?((cd!=null?rSel:rMad)>=r0?'+':'−')+nf(Math.abs(100*((cd!=null?rSel:rMad)-r0)/r0),0)+' %':'—'}.`)}</div>`:'';
  CM._rentaMap=R.length?()=>choro('sxM5',Array.from({length:21},(_,i)=>i+1).map(c=>({cd:c,v:ren(c,'p')})),{cd,per:String(yR),fmt:v=>nf(v),u:'€ por persona',fuente:'INE, Atlas de Distribución de Renta de los Hogares (tabla 31097)'}):null;
  return `<h2 class="asec">Cómo es cada distrito</h2>${rentaHTML}
  ${card('Pensionistas, empresas e inmuebles por distrito',tabla(['Distrito',`Renta/persona (${yR0})`,`Pensionistas (${yP})`,'Por cada 100 hab.',`Empresas y locales (${yE})`,`Cambio desde ${e0}`,`Empleos (${yE})`,`Viviendas (${yI})`,'Locales comerciales','Oficinas'],rows,{num:[1,2,3,4,5,6,7,8,9]}),srcBtn([...C.src.contexto,...(C.src.renta||[])]),'Renta: INE (Atlas de Distribución de Renta de los Hogares). Resto: Instituto de Estadística de la Comunidad de Madrid. Pensionistas: pensiones contributivas de la Seguridad Social. Empresas: unidades productivas con actividad en el distrito. Inmuebles: recibos del Catastro por uso.')}
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
  const pg=part('via'),invT=CM.DSEL==null?porD.reduce((a,r)=>a+r.v,0):(porD.find(r=>r.cd===CM.DSEL)||{}).v;
  if(pg==='asfalto'){el.innerHTML=cab('via')+asfalto(V);return}
  if(pg==='seguridad'){el.innerHTML=cab('via')+seguridad(V);const A=V.t3.accidentes,yU=Math.max(...A.map(r=>r[0]))-1;
    choro('sxM4',Array.from({length:21},(_,i)=>i+1).map(cd=>({cd,v:A.filter(r=>r[0]===yU&&r[1]===cd).reduce((a,r)=>a+r[2],0)})),{cd:CM.DSEL,per:String(yU),fmt:v=>nf(v),u:'accidentes',aviso:'Total del distrito, no por habitante ni por kilómetro de calle.',fuente:'Accidentes de tráfico (datos.madrid.es 300228)'});return}
  if(pg==='entorno'){el.innerHTML=cab('via')+entorno(V);return}
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
  ${mas('via',[['asfalto','Calles asfaltadas cada año'],['inversion','Cuánto se invierte en calles, parques y alumbrado'],['seguridad','Accidentes y multas'],['entorno','Árboles, farolas, señales y sanciones de limpieza']])}`}

function seguridad(V){const T=V.t3,cd=CM.DSEL;if(!T.accidentes)return '<p class="sub">Sin datos.</p>';
  const A=T.accidentes.filter(r=>cd==null||r[1]===cd),años=[...new Set(T.accidentes.map(r=>r[0]))].sort(),yU=last(años)-1;
  const sum=(y,i)=>A.filter(r=>r[0]===y).reduce((a,r)=>a+(r[i]||0),0);
  const sAcc=años.map(y=>[y,sum(y,2),y===last(años)]),sGr=años.filter(y=>y>=2019).map(y=>[y,sum(y,4),sum(y,5)]);
  const Lg=T.accidentes_lugar[String(cd||0)]||[],M2=T.multas||[],mU=M2.filter(r=>r[0]<new Date().getFullYear()).slice(-1)[0];
  const tit=s=>s.toLowerCase().replace(/(^|[\s(\/])\S/g,m=>m.toUpperCase());
  return `<p class="lead">En ${yU} hubo ${N(sum(yU,2))} accidentes de tráfico en ${esc(amb())}: ${N(sum(yU,4))} heridos graves y ${N(sum(yU,5))} fallecidos. ${N(sum(yU,6))} fueron atropellos.</p>
  <div class="kpis">${kpi(N(sum(yU,2)),`accidentes en ${yU}`,`${N(sum(yU,6))} atropellos · ${N(sum(yU,7))} con alcohol positivo`,[`<b>Cálculo:</b> accidentes distintos (número de expediente) atendidos por la Policía Municipal en el año, con o sin heridos.<br><b>Ojo:</b> hasta 2018 solo se publicaban los accidentes con víctimas; por eso desde 2019 el número casi se duplica.<br><b>Fuente:</b> «Accidentes de tráfico de la ciudad de Madrid» de datos.madrid.es.`,T.accidentes_src])}
   ${kpi(N(sum(yU,4)),`heridos graves en ${yU}`,'ingreso hospitalario de más de 24 horas',[`<b>Cálculo:</b> personas con lesividad «ingreso superior a 24 horas» (código 3).<br><b>Ojo:</b> hasta 2018 se usaba la clasificación «herido grave» del atestado, que no es comparable.<br><b>Fuente:</b> datos.madrid.es.`,T.accidentes_src])}
   ${kpi(N(sum(yU,5)),`fallecidos en ${yU}`,'en las 24 horas siguientes',[`<b>Cálculo:</b> personas con lesividad «fallecido en 24 horas» (código 4); no incluye a quien muere días después en el hospital.<br><b>Fuente:</b> datos.madrid.es.`,T.accidentes_src])}
   ${cd==null&&mU?kpi(N(mU[1]),`multas de circulación en ${mU[0]}`,`${M(mU[2])} cobrados en periodo voluntario`,[`<b>Cálculo:</b> «número total de boletines de denuncia formulados» y «recaudación en vía voluntaria» de la fila TOTAL de cada año. Solo hay datos para toda la ciudad.<br><b>Fuente:</b> «Multas de circulación» (estadísticas) de datos.madrid.es.`,T.multas_src]):''}</div>
  <div class="grid2">${card('Accidentes por año',colChart(sAcc,{u:'accidentes',title:'Accidentes por año',unit:'el último año, incompleto · desde 2019 incluye accidentes sin heridos'}),srcBtn(T.accidentes_src))}
   ${card('Heridos graves y fallecidos (desde 2019)',barChart(sGr,[{n:'Heridos graves',c:'#e8590c',i:1},{n:'Fallecidos',c:'#1d2228',i:2}],{stack:true,title:'Víctimas graves',unit:'personas · el último año, incompleto'}).replace(/ M€|€/g,''),srcBtn(T.accidentes_src))}</div>
  <div class="grid2"><div class="card"><h2 class="sxh">Accidentes por distrito (${yU})</h2><div id="sxM4"></div>${srcBtn(T.accidentes_src)}</div>
   ${card('Cruces y calles con más accidentes (desde 2022)',tabla(['Lugar','Accidentes','Con heridos graves o muertos','Atropellos'],Lg.slice(0,15).map(r=>[esc(tit(r[0])),N(r[1]),N(r[2]),N(r[3])]),{num:[1,2,3]}),srcBtn(T.accidentes_src),esc(amb())+' · la dirección tal como la escribe el atestado')}</div>
  ${cd==null&&M2.length?card('Multas de circulación por año',barChart(M2.map(r=>[r[0],r[2]]),[{n:'Cobrado en periodo voluntario',c:AZ,i:1}],{title:'Recaudación',unit:'toda la ciudad · el año en curso, incompleto'}),srcBtn(T.multas_src),`Boletines de denuncia: ${M2.slice(-4).map(r=>r[0]+': '+N(r[1])).join(' · ')}.`):''}`}

function entorno(V){const T=V.t3,cd=CM.DSEL,f=r=>cd==null||r[1]===cd;if(!T.arbolado)return '<p class="sub">Sin datos.</p>';
  const yA=Math.max(...T.arbolado.map(r=>r[0])),aU=T.arbolado.filter(r=>r[0]===yA&&f(r));
  const arb=aU.reduce((a,r)=>a+r[2],0),rec=aU.reduce((a,r)=>a+(r[3]||0),0);
  const serA=[...new Set(T.arbolado.map(r=>r[0]))].sort().map(y=>[y,T.arbolado.filter(r=>r[0]===y&&f(r)).reduce((a,r)=>a+r[2],0)]);
  const far=T.farolas.filter(r=>cd==null||r[0]===cd).reduce((a,r)=>a+r[1],0);
  const S=T.senales.filter(r=>cd==null||r[0]===cd),sen=S.reduce((a,r)=>a+r[2],0),tipos={};S.forEach(r=>tipos[r[1]]=(tipos[r[1]]||0)+r[2]);
  const Lm=T.limpieza.filter(f),aL=[...new Set(Lm.map(r=>r[0]))].sort(),serL=aL.map(y=>[y,Lm.filter(r=>r[0]===y).reduce((a,r)=>a+r[2],0)]);
  const tabD=Array.from({length:21},(_,i)=>i+1).map(c=>Object.assign([`<a href="${lk('via','entorno',c)}">${esc(DISTN[c])}</a>`,N((T.arbolado.find(r=>r[0]===yA&&r[1]===c)||[])[2]),N((T.arbolado.find(r=>r[0]===yA&&r[1]===c)||[])[3]),N((T.farolas.find(r=>r[0]===c)||[])[1]),N(T.senales.filter(r=>r[0]===c).reduce((a,r)=>a+r[2],0))],{on:c===cd}));
  return `<div class="kpis">${kpi(N(arb),`árboles en calles y zonas verdes (${yA})`,`${N(rec)} recién plantados`,[`<b>Cálculo:</b> total de árboles del inventario de zonas verdes, distritos y calles; no incluye parques históricos, singulares y forestales (Retiro, Casa de Campo…).<br><b>Fuente:</b> «Arbolado en parques y zonas verdes de Madrid» de datos.madrid.es.`,T.arbolado_src])}
   ${kpi(N(far),'farolas','inventario de 2022',[`<b>Cálculo:</b> unidades luminosas del inventario municipal de alumbrado, por distrito.<br><b>Fuente:</b> «Unidades luminosas (farolas)» de datos.madrid.es (último fichero publicado: 2022).`,T.farolas_src])}
   ${kpi(N(sen),'señales de tráfico en servicio','sin fecha de baja',[`<b>Cálculo:</b> señales verticales del inventario sin fecha de baja real (las que tienen «31/12/99» siguen en servicio).<br><b>Fuente:</b> «Señalización vertical» de datos.madrid.es.`,T.senales_src])}
</div>
  <div class="grid2">${card('Árboles por año',colChart(serA,{u:'árboles',title:'Árboles',unit:'calles y zonas verdes · 2018 sin datos'}),srcBtn(T.arbolado_src))}
   ${card('Farolas por distrito',hbars(T.farolas.map(r=>[DISTN[r[0]],r[1],r[0]===cd]).sort((a,b)=>b[1]-a[1]),N,{c:'#f0b429'}),srcBtn(T.farolas_src),'Inventario de 2022')}</div>
  <div class="grid2">${card('Señales por tipo',hbars(Object.entries(tipos).sort((a,b)=>b[1]-a[1]),N,{c:'#6f9fd0'}),srcBtn(T.senales_src))}
   ${card('Por distrito',tabla(['Distrito',`Árboles (${yA})`,'Recién plantados','Farolas','Señales'],tabD,{num:[1,2,3,4]}),srcBtn([...T.arbolado_src,...T.farolas_src,...T.senales_src]))}</div>`}

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
  if(part('servicios')==='pagos'){el.innerHTML=cab('servicios')+pagos(S);return}
  if(part('servicios')==='encargos'){const E=S.encargos||[];
    el.innerHTML=`${cab('servicios')}<p class="sub">Trabajos que el Ayuntamiento encarga directamente, sin concurso, a sus propias empresas y organismos (EMVS, Madrid Destino, Informática del Ayuntamiento…). Son de toda la ciudad: no se reparten por distritos.</p>
    <div class="kpis">${kpi(N(E.length),'encargos y encomiendas publicados','desde 2014',[`<b>Cálculo:</b> encargos a medios propios personificados (desde 2018) y encomiendas de gestión (2014–2026) publicados por el Ayuntamiento, incluidas modificaciones y prórrogas.<br><b>Fuente:</b> «Encargos a medios propios personificados» y «Encomiendas de gestión» de datos.madrid.es.`,S.src.encargos])}${kpi(M(E.reduce((a,r)=>a+(r[6]||0),0)),'importe total','lo que se compromete a pagar el Ayuntamiento')}</div>
    ${card('Encargos y encomiendas',tabla(['Fecha','Tipo','Quién encarga','A quién','Para qué','Importe'],E.map(r=>[esc(r[1]||''),esc(r[0]),esc(r[3]||''),esc(r[5]||''),r[7]&&/^https?:/.test(r[7])?`<a href="${esc(r[7])}" target="_blank" rel="noopener">${esc(r[4])}</a>`:esc(r[4]),r[6]?eurS(r[6]):'—']),{num:[5]}),srcBtn(S.src.encargos))}`;return}
  el.innerHTML=`${cab('servicios',`<p class="lead">${esc(frase)}</p>`)}
  <div class="kpis">${kpi(N(n),'contratos desde 2015','registro de contratos y contratos menores')}${kpi(M(tot),'importe adjudicado','IVA incluido')}${kpi(N(nm),'contratos menores',`${nf(100*nm/Math.max(n,1),0)} % del número de contratos`)}</div>
  ${CM.DSEL!=null?'<p class="chw">En un distrito solo se cuentan los contratos de su Junta. Los contratos de las Áreas que dan servicio a toda la ciudad (limpieza, recogida de basuras…) están en el ámbito Madrid.</p>':''}
  <div class="grid2">${card('Importe adjudicado por año',barChart(rows,ks.map((k,i)=>({n:TR[k][0],c:TR[k][1],i:i+1})),{stack:true,title:'Importe por año',unit:'IVA incluido · en los acuerdos marco es el techo de gasto, no lo pagado'}),srcBtn(S.src.contratos))}
   ${card('Número de contratos por año',barChart(nrow,ks.map((k,i)=>({n:TR[k][0],c:TR[k][1],i:i+1})),{stack:true,title:'Contratos por año',unit:'contratos inscritos'}),srcBtn(S.src.contratos))}</div>
  ${card(`Empresas con más importe adjudicado · ${esc(amb())}`,tabla(['Empresa','NIF','Contratos','Importe','Menores','Años'],R.map(r=>[esc(r[0]),esc(r[1]||'—'),N(r[2]),M(r[3]),nf(r[4]),r[5]===r[6]?r[5]:r[5]+'–'+r[6]]),{num:[2,3,4]}),srcBtn(S.src.contratos),
    'Importe adjudicado, no pagado. Las personas físicas no se muestran por su nombre. Las UTE cuentan aparte de sus socias.')}
  ${mas('servicios',[['pagos','Lo que se paga de verdad y a quién'],['encargos','Trabajos encargados a las empresas municipales']])}`}
function pagos(S){const cd=CM.DSEL,P=S.pagos[String(cd||0)]||[],PA=S.pagos_anio.filter(r=>cd==null||r[1]===cd),años=[...new Set(PA.map(r=>r[0]))].sort();
  const serie=años.map(y=>[y,PA.filter(r=>r[0]===y).reduce((x,r)=>x+(r[2]||0),0)]),yU=last(años);
  return `<p class="sub">El contrato fija cuánto se puede gastar; aquí está lo que el Ayuntamiento reconoce que debe pagar cada año a cada proveedor, entidad o administración.</p>
  <div class="grid2">${card('Pagado por año',barChart(serie,[{n:'Pagado',c:AZ,i:1}],{title:'Pagado por año',unit:cd==null?'Ayuntamiento y organismos autónomos, todos los perceptores':'Pagos de la Junta del distrito'}),srcBtn(S.src.pagos),'Pagos a terceros: lo que el Ayuntamiento reconoce que debe pagar a cada proveedor, entidad o administración, no lo adjudicado.')}
   ${card('Quién cobra más (2011–'+yU+')',tabla(['Perceptor','NIF','Total','Último año','Años'],P.slice(0,20).map(r=>[esc(r[0]),esc(r[1]||'—'),M(r[2]),M(r[3]),r[4]===r[5]?r[4]:r[4]+'–'+r[5]]),{num:[2,3]}),srcBtn(S.src.pagos),'Incluye empresas, entidades y otras administraciones (como el Consorcio de Transportes).')}</div>`}

// ---------- Servicios sociales ----------
async function social(el){const [C,S]=await Promise.all([get('ciudadano'),get('servicios')]);const cd=CM.DSEL;
  if(part('social')==='espera'){
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
  if(part('ayudas')==='subvenciones'){const SB=A.subvenciones||{},cd=CM.DSEL,Y=(SB.anio||[]).filter(r=>cd==null||r[1]===cd),años=[...new Set(Y.map(r=>r[0]))].sort();
    const ser=años.map(y=>[y,Y.filter(r=>r[0]===y).reduce((a,r)=>a+(r[3]||0),0)]),yC=last(años.filter(y=>y<new Date().getFullYear())),uc=(ser.find(r=>r[0]===yC)||[])[1]||0,nc=Y.filter(r=>r[0]===yC).reduce((a,r)=>a+r[2],0);
    const Rk=(SB.ranking||{})[String(cd||0)]||[],Ln=(SB.lineas||{})[String(cd||0)]||[];
    el.innerHTML=`${cab('ayudas')}${cd!=null?'<p class="chw">En un distrito solo se cuentan las subvenciones que concede su Junta. Las de las Áreas de gobierno están en el ámbito Madrid.</p>':''}
    <div class="kpis">${kpi(M(uc),`concedidos en subvenciones en ${yC}`,`${N(nc)} subvenciones`,[`<b>Cálculo:</b> suma del importe concedido de las subvenciones del Ayuntamiento${cd!=null?' cuyo órgano gestor es la Junta del distrito':''}, por año de concesión.<br><b>Fuente:</b> «Subvenciones» de datos.madrid.es (2014–2018 y desde 2019). Las personas físicas aparecen sin nombre.`,A.src.subvenciones])}</div>
    <div class="grid2">${card('Subvenciones concedidas por año',barChart(ser,[{n:'Importe concedido',c:AZ,i:1}],{title:'Subvenciones por año',unit:'el año en curso, incompleto · 2014 y 2015 parecen incompletos'}),srcBtn(A.src.subvenciones))}
     ${card('Para qué (desde 2019)',hbars(Ln.map(r=>[r[0].charAt(0)+r[0].slice(1).toLowerCase(),r[2]]),M,{c:'#6f9fd0'}),srcBtn(A.src.subvenciones))}</div>
    ${card('Quién recibe más (desde 2019)',tabla(['Beneficiario','Subvenciones','Importe','Años'],Rk.map(r=>[esc(r[0]),N(r[2]),M(r[3]),r[4]===r[5]?r[4]:r[4]+'–'+r[5]]),{num:[1,2]}),srcBtn(A.src.subvenciones),'«Persona física» agrupa a todos los particulares (becas, ayudas…), que el portal publica sin nombre.')}`;return}
  if(part('ayudas')==='convenios'){
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
  ${card('Fondos europeos',tabla(['Programa','Proyecto','Año','Concedido','Ámbito'],fe.slice(0,60).map(r=>[esc(r[0]),r[9]?`<a href="${esc(r[9])}" target="_blank" rel="noopener">${esc(r[1])}</a>`:esc(r[1]),r[2]||'—',eurS(r[3]),esc(r[6]||'')]),{num:[3]}),srcBtn(A.src.fondos),'Plan de Recuperación y FEDER, según el Ayuntamiento.')}
  ${(A.proyectos_ue||[]).length?card('Proyectos de investigación de la UE con el Ayuntamiento como socio',`<p class="sub">${nf(A.proyectos_ue.length)} proyectos de los programas marco de investigación (Horizonte 2020 y Horizonte Europa) con ${M(A.proyectos_ue.reduce((a,r)=>a+(r[4]||0),0))} de aportación de la UE al Ayuntamiento.</p>`+tabla(['Proyecto','Título','Inicio','Fin','Para el Ayuntamiento','Coste total del proyecto'],A.proyectos_ue.map(r=>[`<a href="${esc(r[6])}" target="_blank" rel="noopener">${esc(r[0])}</a>`,esc(r[1]),esc((r[2]||'').slice(0,10)),esc((r[3]||'').slice(0,10)),eurS(r[4]),r[5]?eurS(r[5]):"—"]),{num:[4,5]}),srcBtn(A.src.proyectos_ue),'Fuente: CORDIS (Comisión Europea). Solo el Ayuntamiento (NIF P2807900B); las empresas y organismos municipales con NIF propio no están incluidos.'):''}
  ${mas('ayudas',[['subvenciones','Subvenciones que reparte el Ayuntamiento'],['convenios','Convenios con empresas y entidades']])}`}

// =====================================================================
// Datos comunes de todas las secciones e indicadores por distrito
// =====================================================================
const YC=new Date().getFullYear()-1;   // último año completo
const D21=Array.from({length:21},(_,i)=>i+1);
async function edif(){for(let i=0;i<40;i++){const e=CM.edif;if(e&&e.length)return e;await new Promise(r=>setTimeout(r,250))}return CM.edif||[]}
let BASE=null;
async function datos(){if(BASE)return BASE;
  const [C,V,S,A]=await Promise.all(['ciudadano','via','servicios','ayudas'].map(get));const E=await edif();
  const yH=Math.max(...C.distritos.map(x=>x.anio)),HAB={};C.distritos.filter(r=>r.anio===yH).forEach(r=>HAB[r.cd]=r.hab);HAB[0]=D21.reduce((a,c)=>a+(HAB[c]||0),0);
  const T=V.t3||{},I={};
  const add=(k,o)=>{o.k=k;I[k]=o};const por=(v,c,m)=>HAB[c]?m*v/HAB[c]:null;
  const DD=C.distritos.filter(r=>r.anio===yH);
  add('gasto_junta_hab',{n:'Gasto de la Junta por habitante',sec:'ciudadano',u:'€ por habitante',per:yH,fmt:v=>N(v),v:Object.fromEntries(DD.map(r=>[r.cd,r.pag_hab])),src:C.src.distritos,
    calc:'Obligaciones reconocidas de la sección presupuestaria de la Junta Municipal ÷ habitantes empadronados a 1 de enero. No incluye lo que gastan en el distrito las Áreas de gobierno.'});
  add('inv_hab',{n:'Inversión pagada por habitante',sec:'ciudadano',u:'€ por habitante',per:yH,fmt:v=>N(v),v:Object.fromEntries(DD.map(r=>[r.cd,r.inv_hab])),src:C.src.distritos,
    calc:'Pagos de los proyectos de inversión asignados al distrito (de la Junta y de las Áreas) ÷ habitantes. Los proyectos de varios distritos no se reparten.'});
  const R=C.renta||[],yR=R.length?Math.max(...R.map(r=>r[0])):null;
  if(yR)add('renta',{n:'Renta neta media por persona',sec:'ciudadano',u:'€ al año',per:yR,fmt:v=>N(v),v:Object.fromEntries(D21.map(c=>[c,(R.find(r=>r[0]===yR&&r[1]===c&&r[2]==='p')||[])[3]])),src:C.src.renta,
    calc:'Renta neta media por persona del Atlas de Distribución de Renta de los Hogares del INE (tabla 31097), a partir de datos tributarios. Año de los ingresos; se publica con unos dos años de retraso.'});
  const X=C.contexto||[],yP=X.length?Math.max(...X.filter(r=>r[2]==='pensionistas').map(r=>r[0])):null;
  if(yP)add('pens_100',{n:'Pensionistas por cada 100 habitantes',sec:'ciudadano',u:'por 100 hab.',per:yP,fmt:v=>nf(v,1),v:Object.fromEntries(D21.map(c=>[c,por(X.filter(r=>r[0]===yP&&r[1]===c&&r[2]==='pensionistas'&&r[3]==='Total').reduce((a,r)=>a+r[4],0),c,100)])),src:C.src.contexto,
    calc:'Pensionistas de pensiones contributivas de la Seguridad Social en el distrito (Instituto de Estadística de la Comunidad de Madrid) ÷ habitantes × 100.'});
  const prog=Object.keys(V.programas||{}),IV=V.inversion_via_distrito||{},yv=prog.length?Math.max(...(IV[prog[0]]||[]).map(r=>r[0])):null;
  if(yv)add('via_hab',{n:'Inversión en vía pública por habitante',sec:'via',u:'€ por habitante',per:yv,fmt:v=>nf(v,1),v:Object.fromEntries(D21.map(c=>[c,por(prog.reduce((a,p)=>a+(IV[p]||[]).filter(r=>r[0]===yv&&r[1]===c).reduce((s,r)=>s+r[2],0),0),c,1)])),src:V.src.inversion_via,
    calc:'Pagos de los proyectos de inversión con distrito asignado de los programas de vías públicas, parques y jardines, alumbrado, tráfico y limpieza ÷ habitantes.'});
  add('licencias_1000',{n:'Licencias de obras en la calle por 1.000 habitantes',sec:'via',u:'por 1.000 hab.',per:YC,fmt:v=>nf(v,1),v:Object.fromEntries(D21.map(c=>[c,por(V.licencias.filter(r=>r[0]===YC&&r[1]===c).reduce((a,r)=>a+r[3],0),c,1000)])),src:V.src.licencias,
    calc:'Licencias de obras en la vía pública finalizadas en el año (calas, canalizaciones, alcantarillado, averías y obras municipales) ÷ habitantes × 1.000.'});
  if(T.arbolado){const yA=Math.max(...T.arbolado.map(r=>r[0]));add('arboles_1000',{n:'Árboles por 1.000 habitantes',sec:'via',u:'por 1.000 hab.',per:yA,fmt:v=>N(v),v:Object.fromEntries(D21.map(c=>[c,por((T.arbolado.find(r=>r[0]===yA&&r[1]===c)||[])[2]||0,c,1000)])),src:T.arbolado_src,
    calc:'Árboles del inventario de calles y zonas verdes (sin parques históricos, singulares y forestales) ÷ habitantes × 1.000.'})}
  if(T.accidentes){const yU=YC;add('acc_1000',{n:'Accidentes de tráfico por 1.000 habitantes',sec:'seguridad',u:'por 1.000 hab.',per:yU,fmt:v=>nf(v,1),v:Object.fromEntries(D21.map(c=>[c,por(T.accidentes.filter(r=>r[0]===yU&&r[1]===c).reduce((a,r)=>a+r[2],0),c,1000)])),src:T.accidentes_src,
    calc:'Accidentes distintos (número de expediente) atendidos por la Policía Municipal en el año, con o sin heridos ÷ habitantes × 1.000.'});
    add('graves_100k',{n:'Heridos graves y fallecidos por 100.000 habitantes',sec:'seguridad',u:'por 100.000 hab.',per:yU,fmt:v=>nf(v,1),v:Object.fromEntries(D21.map(c=>[c,por(T.accidentes.filter(r=>r[0]===yU&&r[1]===c).reduce((a,r)=>a+r[4]+r[5],0),c,1e5)])),src:T.accidentes_src,
    calc:'Personas con ingreso hospitalario de más de 24 horas o fallecidas en las 24 horas siguientes al accidente ÷ habitantes × 100.000.'})}
  if(T.limpieza)add('limpieza_1000',{n:'Sanciones de limpieza por 1.000 habitantes',sec:'seguridad',u:'por 1.000 hab.',per:YC,fmt:v=>nf(v,2),v:Object.fromEntries(D21.map(c=>[c,por(T.limpieza.filter(r=>r[0]===YC&&r[1]===c).reduce((a,r)=>a+r[2],0),c,1000)])),src:T.limpieza_src,
    calc:'Expedientes sancionadores de la ordenanza de limpieza de los espacios públicos y zonas verdes con infracción en el año ÷ habitantes × 1.000.'});
  add('contr_hab',{n:'Contratos de la Junta por habitante',sec:'servicios',u:'€ por habitante',per:YC,fmt:v=>nf(v,1),v:Object.fromEntries(D21.map(c=>[c,por(S.por_distrito.filter(r=>r[0]===YC&&r[1]===c).reduce((a,r)=>a+(r[4]||0),0),c,1)])),src:S.src.contratos,
    calc:'Importe adjudicado (IVA incluido) de los contratos inscritos por la Junta del distrito en el año, incluidos los menores ÷ habitantes. No incluye los contratos de las Áreas que dan servicio a toda la ciudad.'});
  add('espera_1000',{n:'Mayores en lista de espera por 1.000 habitantes',sec:'social',u:'por 1.000 hab.',per:(S.espera_fecha||'').slice(0,10),fmt:v=>nf(v,2),v:Object.fromEntries(D21.map(c=>[c,por(S.espera.filter(r=>r[1]===c).reduce((a,r)=>a+r[2],0),c,1000)])),src:S.src.espera,
    calc:'Solicitudes en lista de espera de los servicios municipales para mayores en la fecha de los datos ÷ habitantes × 1.000.'});
  const SB=(A.subvenciones||{}).anio||[];
  add('subv_hab',{n:'Subvenciones de la Junta por habitante',sec:'ayudas',u:'€ por habitante',per:YC,fmt:v=>nf(v,2),v:Object.fromEntries(D21.map(c=>[c,por(SB.filter(r=>r[0]===YC&&r[1]===c).reduce((a,r)=>a+(r[3]||0),0),c,1)])),src:A.src.subvenciones,
    calc:'Importe de las subvenciones concedidas en el año por la Junta del distrito ÷ habitantes. No incluye las que conceden las Áreas para toda la ciudad.'});
  if(E.length){const cnt=c=>E.filter(b=>b.cd===c);add('ite_desf',{n:'Edificios municipales con ITE desfavorable sin subsanar',sec:'edificios',u:'% de sus edificios',per:'Registro de Edificios',fmt:v=>nf(v,1),v:Object.fromEntries(D21.map(c=>{const t=cnt(c);return [c,t.length?100*t.filter(b=>b.s==='desf').length/t.length:null]})),src:C.src.edificios,
    calc:'Edificios municipales del distrito cuya última inspección técnica (ITE) en el Registro de Edificios es desfavorable y no consta que se hayan subsanado las deficiencias ÷ edificios municipales del distrito × 100.'})}
  BASE={C,V,S,A,E,T,HAB,yH,I};return BASE}
const rkOf=(o,c)=>{const ok=D21.filter(x=>o.v[x]!=null).sort((a,b)=>o.v[b]-o.v[a]);return [ok.indexOf(c)+1,ok.length]};
const media=o=>{const ok=D21.map(c=>o.v[c]).filter(x=>x!=null);return ok.reduce((a,b)=>a+b,0)/(ok.length||1)};
const puesto=(o,c)=>{const [p,n]=rkOf(o,c);return p?`puesto ${p}.º de ${n}`:''};
const pctDif=(v,m)=>m?((v>=m?'+':'−')+nf(Math.abs(100*(v-m)/m),0)+' %'):'';
function mapCard(o,id,cd){return `<div class="card sxmap"><h2 class="sxh">${esc(o.n)} (${esc(String(o.per))})${info(`<b>Cálculo:</b> ${o.calc}`,o.src)}</h2><div id="${id}"></div>${srcBtn(o.src)}</div>`}
function mapDraw(o,id){choro(id,D21.map(c=>({cd:c,v:o.v[c]})),{cd:CM.DSEL,per:String(o.per),fmt:o.fmt,u:o.u,fuente:esc(o.n)})}
function compBars(o){const cd=CM.DSEL,m=media(o),rows=D21.filter(c=>o.v[c]!=null).sort((a,b)=>o.v[b]-o.v[a]).map(c=>[DISTN[c],o.v[c],c===cd]);
  return card(`${esc(o.n)} en los 21 distritos (${esc(String(o.per))})`,hbars(rows,v=>o.fmt(v)+' '+o.u.split(' ')[0])+`<p class="sub">Media de los 21 distritos: <b>${o.fmt(m)}</b> ${esc(o.u)}.${cd!=null&&o.v[cd]!=null?` ${esc(DISTN[cd])}: ${o.fmt(o.v[cd])} (${puesto(o,cd)}, ${pctDif(o.v[cd],m)} frente a la media).`:''}</p>`,srcBtn(o.src))}
const P=s=>`<p>${s}</p>`;
const cmpTxt=(o,cd)=>{const v=o.v[cd],m=media(o);return v==null?'':`${o.fmt(v)} ${o.u}, ${puesto(o,cd)} (la media es ${o.fmt(m)}; ${pctDif(v,m)})`};
const sum=(a,f)=>a.reduce((x,r)=>x+(f(r)||0),0);

// =====================================================================
// Definición de cada sección: mapa, 4 cifras, informe, gráficos, cálculo y datos
// =====================================================================
const DEF={};
// ---------- Presupuesto ----------
DEF.ciudadano={mapa:'gasto_junta_hab',
  kpis(B){const {C}=B,cd=CM.DSEL,ci=C.ciudad.filter(r=>r.gasto),u=last(ci),uh=last(ci.filter(r=>r.hab_gasto));
    const yI=Math.max(...Object.keys(C.ingresos).map(Number)),I=C.ingresos[yI]||{},trib=(I['1']||0)+(I['2']||0)+(I['3']||0);
    const Dd=C.deuda.filter(r=>r[1]==='TOTAL DEUDA LARGO Y CORTO PLAZO'),dU=last(Dd);
    if(cd==null)return [kpi(M(u.gasto),`gastado en ${u.anio}`,`${nf(u.pct,1)} % de lo presupuestado`,[`<b>Cálculo:</b> obligaciones reconocidas de los capítulos 1 a 7 (personal, compras y servicios, intereses, transferencias e inversiones) del Ayuntamiento y sus organismos autónomos, menos las operaciones internas entre ellos. Sin devolución de deuda ni préstamos.<br><b>Fuente:</b> ejecución presupuestaria de datos.madrid.es.`,C.src.ciudad]),
      kpi(N(uh.hab_gasto)+' €',`por habitante en ${uh.anio}`,`${N(uh.hab)} habitantes`,[`<b>Cálculo:</b> gasto anterior ÷ habitantes empadronados a 1 de enero.<br><b>Fuente:</b> ejecución presupuestaria y padrón de datos.madrid.es.`,C.src.ciudad]),
      kpi(M(trib),`impuestos, tasas y precios (${yI})`,'derechos reconocidos',[`<b>Cálculo:</b> derechos reconocidos netos de los capítulos de ingresos 1, 2 y 3 del Ayuntamiento (IBI, plusvalía, IAE, vehículos, construcciones, tasas…).<br><b>Fuente:</b> ejecución del presupuesto de ingresos de datos.madrid.es.`,C.src.ingresos]),
      kpi(M(dU[2]),`deuda a 31/12/${dU[0]}`,'préstamos y emisiones',[`<b>Cálculo:</b> «Total deuda a largo y corto plazo» del Ayuntamiento a 31 de diciembre.<br><b>Fuente:</b> «Deuda viva» de datos.madrid.es.`,C.src.deuda])];
    const sel=C.distritos.find(r=>r.anio===B.yH&&r.cd===cd)||{},I2=B.I;
    return [kpi(M(sel.pag),`gastó la Junta en ${B.yH}`,`${nf(sel.pct,1)} % de su presupuesto · sin gastar ${M(sel.nog)}`,[`<b>Cálculo:</b> obligaciones reconocidas de la sección presupuestaria de la Junta Municipal; porcentaje sobre el crédito definitivo.<br><b>Fuente:</b> ejecución presupuestaria de datos.madrid.es.`,C.src.distritos]),
      kpi(N(sel.pag_hab)+' €','de la Junta por habitante',puesto(I2.gasto_junta_hab,cd),[`<b>Cálculo:</b> ${I2.gasto_junta_hab.calc}`,C.src.distritos]),
      kpi(N(sel.inv_hab)+' €','de inversión por habitante',puesto(I2.inv_hab,cd),[`<b>Cálculo:</b> ${I2.inv_hab.calc}`,C.src.distritos]),
      I2.renta?kpi(N(I2.renta.v[cd])+' €',`renta por persona (${I2.renta.per})`,puesto(I2.renta,cd),[`<b>Cálculo:</b> ${I2.renta.calc}`,I2.renta.src]):''];},
  informe(B){const {C,I}=B,cd=CM.DSEL,ci=C.ciudad.filter(r=>r.gasto),u=last(ci),u5=ci.find(r=>r.anio===u.anio-5);
    const pol=Object.entries(C.politicas[u.anio]||{}).filter(([k,v])=>v>0).sort((a,b)=>b[1]-a[1]),polT=sum(pol,r=>r[1]);
    const yI=Math.max(...Object.keys(C.ingresos).map(Number)),In=C.ingresos[yI]||{},inT=sum(Object.values(In),x=>x),trib=(In['1']||0)+(In['2']||0)+(In['3']||0),trf=(In['4']||0)+(In['7']||0);
    const Dd=C.deuda.filter(r=>r[1]==='TOTAL DEUDA LARGO Y CORTO PLAZO'),dU=last(Dd),d0=Dd.find(r=>r[0]===2012),pU=last(C.pmp);
    let h=`<h2>Madrid</h2>`+P(`En ${u.anio} el Ayuntamiento y sus organismos autónomos gastaron <b>${M(u.gasto)}</b> en servicios e inversiones, ${u5?`un ${pctDif(u.gasto,u5.gasto)} más que en ${u5.anio} (${M(u5.gasto)})`:''}. Es el ${nf(u.pct,1)} % de lo que tenían presupuestado.`)
      +P(`Las políticas con más gasto fueron ${pol.slice(0,3).map(([k,v])=>`${(C.nombres_politicas[k]||k).toLowerCase()} (${nf(100*v/polT,0)} %)`).join(', ')}.`)
      +P(`De los ingresos de ${yI}, los impuestos, tasas y precios suponen ${M(trib)} (${nf(100*trib/inT,0)} %) y las transferencias del Estado, la Comunidad y la UE ${M(trf)} (${nf(100*trf/inT,0)} %).`)
      +P(`La deuda era de ${M(dU[2])} a final de ${dU[0]}${d0?`, frente a ${M(d0[2])} en 2012`:''}. El Ayuntamiento tardaba ${nf(pU[2],1)} días en pagar a sus proveedores (${pU[1]}/${pU[0]}); el máximo legal es 30.`)
      +card('Gasto por año',barChart(ci.map(r=>[r.anio,r.gasto]),[{n:'Gastado',c:AZ,i:1}],{title:'Gasto por año',unit:'capítulos 1 a 7, sin operaciones internas'}),srcBtn(C.src.ciudad));
    if(cd!=null){const s=C.distritos.find(r=>r.anio===B.yH&&r.cd===cd)||{};const f26=sum(C.futuro.filter(r=>r[2]===cd&&r[0]===2026),r=>r[3]),f27=sum(C.futuro.filter(r=>r[2]===cd&&r[0]===2027),r=>r[3]);
      h+=`<h2>${esc(DISTN[cd])}</h2>`+P(`En ${B.yH} la Junta de ${esc(DISTN[cd])} tenía un presupuesto de ${M(s.cdf)}, gastó ${M(s.pag)} (${nf(s.pct,1)} %) y dejó sin gastar ${M(s.nog)}. Por habitante gastó ${cmpTxt(I.gasto_junta_hab,cd)}.`)
        +P(`La inversión pagada en el distrito, sumando la de las Áreas, fue de ${M(s.invp)}: ${cmpTxt(I.inv_hab,cd)}.`)
        +(I.renta?P(`La renta neta media es de ${cmpTxt(I.renta,cd)}.`):'')
        +(f26?P(`Para 2026 la Junta tiene aprobados ${M(f26)} y el proyecto de 2027 prevé ${M(f27)} (${pctDif(f27,f26)}).`):'')
        +compBars(I.gasto_junta_hab)}
    return h},
  graficos:[['Ingresos y gastos','ciudadano','resumen'],['Por distritos','ciudadano','distritos'],['Deuda y pagos','ciudadano','deuda'],['Madrid frente a otras grandes ciudades','ciudadano','ciudades']],
  metodo(B){const C=B.C;return [
    ['Gasto consolidado','Obligaciones reconocidas de los capítulos 1 a 7 del Ayuntamiento y sus organismos autónomos menos las operaciones internas («eliminaciones»). Hasta 2022 las eliminaciones son aproximadas porque el portal solo publica su importe presupuestado.',C.src.ciudad],
    ['Gasto por habitante','Gasto consolidado ÷ habitantes empadronados a 1 de enero.',C.src.ciudad],
    ['Ingresos','Derechos reconocidos netos por capítulo del Ayuntamiento (sin organismos autónomos).',C.src.ingresos],
    ['Gasto de la Junta e inversión por distrito',B.I.gasto_junta_hab.calc+' '+B.I.inv_hab.calc,C.src.distritos],
    ['Presupuesto 2026 y 2027','Créditos iniciales de la sección de cada Junta en el presupuesto aprobado de 2026 y en el proyecto de 2027.',C.src.futuro],
    ['Deuda y periodo medio de pago','Deuda viva a 31 de diciembre y periodo medio de pago mensual publicado por el Ayuntamiento.',[...C.src.deuda,...C.src.pmp]],
    ['Renta por persona',B.I.renta?B.I.renta.calc:'',C.src.renta||[]],
    ['Pensionistas, empresas e inmuebles','Datos por distrito del Instituto de Estadística de la Comunidad de Madrid (pensiones contributivas, unidades productivas y Catastro).',C.src.contexto||[]],
    ['Comparativa con otras ciudades','Liquidaciones consolidadas que cada ayuntamiento envía a Hacienda (CONPREL): gasto de los capítulos 1 a 7 e ingresos de los capítulos 1 a 3 ÷ población del padrón.',C.src.comparada||[]]]},
  csv(B){const C=B.C;return [
    ['presupuesto_distritos',['anio','cod_distrito','distrito','habitantes','presupuesto_junta','gastado_junta','sin_gastar','pct_ejecucion','gasto_junta_por_hab','inversion_pagada','inversion_por_hab'],C.distritos.map(r=>[r.anio,r.cd,DISTN[r.cd],r.hab,r.cdf,r.pag,r.nog,r.pct,r.pag_hab,r.invp,r.inv_hab]),C.src.distritos],
    ['presupuesto_ciudad',['anio','gasto_consolidado','presupuesto_definitivo','pct_ejecucion','habitantes','gasto_por_hab'],C.ciudad.map(r=>[r.anio,r.gasto,r.presup,r.pct,r.hab,r.hab_gasto]),C.src.ciudad],
    ['renta_distritos',['anio','cod_distrito','indicador','euros'],(C.renta||[]).map(r=>[r[0],r[1],{p:'renta neta por persona',h:'renta neta por hogar',m:'mediana por unidad de consumo'}[r[2]],r[3]]),C.src.renta||[]],
    ['ciudades_conprel',['anio','ciudad','poblacion','gasto_no_financiero','inversion','impuestos_y_tasas','personal'],(C.comparada||[]).map(r=>r.slice(0,7)),C.src.comparada||[]]]}};
// ---------- Calles y obras ----------
DEF.via={mapa:'via_hab',
  kpis(B){const {V,T,I}=B,cd=CM.DSEL,f=r=>cd==null||r[1]===cd;
    const lic=sum(V.licencias.filter(r=>r[0]===YC&&f(r)),r=>r[3]);
    const yAs=Math.max(...V.asfalto.map(r=>r[0])),asf=sum(V.asfalto.filter(r=>r[0]===yAs&&f(r)),r=>r[2]);
    const o=I.via_hab,inv=cd==null?sum(D21,c=>(o.v[c]||0)*(B.HAB[c]||0)):(o.v[cd]||0)*(B.HAB[cd]||0);
    const yA=T.arbolado?Math.max(...T.arbolado.map(r=>r[0])):null,arb=yA?sum(T.arbolado.filter(r=>r[0]===yA&&f(r)),r=>r[2]):0,rec=yA?sum(T.arbolado.filter(r=>r[0]===yA&&f(r)),r=>r[3]):0;
    return [kpi(N(lic),`licencias de obras en la calle (${YC})`,cd!=null?puesto(I.licencias_1000,cd)+' por habitante':'calas, canalizaciones, averías…',[`<b>Cálculo:</b> licencias de obras en la vía pública finalizadas en el año.<br><b>Fuente:</b> «Licencias de obras en vía pública» de datos.madrid.es.`,V.src.licencias]),
      kpi(N(asf),`tramos asfaltados (${yAs})`,'Operación Asfalto',[`<b>Cálculo:</b> tramos de calle de la campaña anual de asfaltado.<br><b>Fuente:</b> Geoportal del Ayuntamiento (servicio OBRAS/OPERACION_ASFALTO).`,V.src.asfalto]),
      kpi(M(inv),`invertido en vía pública (${o.per})`,cd!=null?puesto(o,cd)+' por habitante':'calles, parques, alumbrado, tráfico',[`<b>Cálculo:</b> ${o.calc.replace(' ÷ habitantes.','.')}<br><b>Fuente:</b> «Proyectos de inversión» de datos.madrid.es.`,o.src]),
      kpi(N(arb),`árboles en calles y zonas verdes (${yA})`,`${N(rec)} recién plantados`,[`<b>Cálculo:</b> árboles del inventario de calles y zonas verdes; no incluye parques históricos, singulares y forestales.<br><b>Fuente:</b> «Arbolado en parques y zonas verdes» de datos.madrid.es.`,T.arbolado_src])]},
  informe(B){const {V,T,I}=B,cd=CM.DSEL,f=r=>cd==null||r[1]===cd,amb_=esc(amb());
    const años=[...new Set(V.licencias.map(r=>r[0]))].sort(),lic=y=>sum(V.licencias.filter(r=>r[0]===y&&f(r)),r=>r[3]);
    const tipos={};V.licencias.filter(r=>r[0]===YC&&f(r)).forEach(r=>tipos[r[2]]=(tipos[r[2]]||0)+r[3]);const tt=Object.entries(tipos).sort((a,b)=>b[1]-a[1]);
    const calles=V.calles[String(cd||0)]||[],yAs=Math.max(...V.asfalto.map(r=>r[0])),asf=y=>sum(V.asfalto.filter(r=>r[0]===y&&f(r)),r=>r[2]);
    let h=P(`En ${YC} se cerraron <b>${N(lic(YC))}</b> licencias de obras en la vía pública de ${amb_}, frente a ${N(lic(YC-1))} el año anterior. La mayoría fueron ${tt.slice(0,2).map(([k,v])=>`${k.toLowerCase()} (${N(v)})`).join(' y ')}.${calles[0]?` La calle con más intervenciones desde 2017 es ${esc(calles[0][0])}, con ${N(calles[0][1])}.`:''}`)
      +P(`La Operación Asfalto tiene ${N(asf(yAs))} tramos en ${yAs} y ${N(asf(yAs-1))} en ${yAs-1}.`)
      +P(`La inversión en calles, parques, alumbrado, tráfico y limpieza ${cd!=null?`fue de ${cmpTxt(I.via_hab,cd)}`:`fue de media de ${I.via_hab.fmt(media(I.via_hab))} € por habitante en los distritos en ${I.via_hab.per}`}.`)
      +(I.arboles_1000&&cd!=null?P(`Hay ${cmpTxt(I.arboles_1000,cd)}.`):'')
      +card('Licencias de obras en la calle por año',colChart(años.map(y=>[y,lic(y),y===años[años.length-1]]),{u:'licencias',title:'Licencias por año',unit:'2017 desde abril · el año en curso, incompleto'}),srcBtn(V.src.licencias));
    if(cd!=null)h+=compBars(I.via_hab);return h},
  graficos:[['Obras en la calle','via','obras'],['Asfaltado','via','asfalto'],['Inversión','via','inversion'],['Árboles, farolas y señales','via','entorno']],
  metodo(B){const {V,T,I}=B;return [
    ['Licencias de obras en la calle','Licencias de obras en la vía pública finalizadas, contadas por su dirección; misma calle escrita de varias formas, agrupada. No incluyen su coste, que no se publica.',V.src.licencias],
    ['Operación Asfalto','Tramos de la campaña anual de asfaltado tomados del Geoportal del Ayuntamiento; en 2025 incluye un precio aproximado por tramo.',V.src.asfalto],
    ['Inversión en vía pública',I.via_hab.calc,V.src.inversion_via],
    ['Inversiones principales y obras públicas','Listados municipales de inversiones principales (con dirección y coordenadas) y de obras planificadas o en ejecución.',[...V.src.inversiones,...(V.src.obras||[])]],
    ['Árboles, farolas y señales','Inventarios municipales de arbolado (por año), unidades luminosas (2022) y señalización vertical (en servicio = sin fecha de baja real).',[...(T.arbolado_src||[]),...(T.farolas_src||[]),...(T.senales_src||[])]]]},
  csv(B){const {V,T}=B;return [
    ['licencias_via_publica',['anio','cod_distrito','tipo','licencias'],V.licencias,V.src.licencias],
    ['asfalto_tramos',['anio','cod_distrito','calle','tramo','estado','precio_aprox','lat','lng'],V.asfalto_calles.map(r=>[r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7]]),V.src.asfalto],
    ['arbolado_distritos',['anio','cod_distrito','arboles','recien_plantados','viejos'],T.arbolado||[],T.arbolado_src||[]],
    ['farolas_distritos',['cod_distrito','farolas'],T.farolas||[],T.farolas_src||[]],
    ['senales_distritos',['cod_distrito','tipo','en_servicio','altas_desde_2020'],T.senales||[],T.senales_src||[]]]}};
// ---------- Seguridad y convivencia ----------
function limpiezaHTML(B){const T=B.T,cd=CM.DSEL,Lm=T.limpieza.filter(r=>cd==null||r[1]===cd),aL=[...new Set(Lm.map(r=>r[0]))].sort();
  const ser=aL.map(y=>[y,sum(Lm.filter(r=>r[0]===y),r=>r[2]),y===aL[aL.length-1]]),imp=aL.map(y=>[y,sum(Lm.filter(r=>r[0]===y),r=>r[3])]);
  return `<div class="grid2">${card('Sanciones de limpieza por año',colChart(ser,{u:'sanciones',title:'Sanciones',unit:'por año de la infracción · el año en curso, incompleto'}),srcBtn(T.limpieza_src),'Tirar basura, orinar en la calle, pintadas, no recoger excrementos…')}
   ${card('Importe de las sanciones',barChart(imp,[{n:'Importe',c:AZ,i:1}],{title:'Importe por año',unit:'importe impuesto, no necesariamente cobrado'}),srcBtn(T.limpieza_src))}</div>${compBars(B.I.limpieza_1000)}`}
DEF.seguridad={mapa:'acc_1000',
  kpis(B){const {T,I}=B,cd=CM.DSEL,A=T.accidentes.filter(r=>cd==null||r[1]===cd),s=i=>sum(A.filter(r=>r[0]===YC),r=>r[i]);
    const L=sum(T.limpieza.filter(r=>r[0]===YC&&(cd==null||r[1]===cd)),r=>r[2]);
    return [kpi(N(s(2)),`accidentes de tráfico (${YC})`,`${N(s(6))} atropellos${cd!=null?' · '+puesto(I.acc_1000,cd)+' por habitante':''}`,[`<b>Cálculo:</b> ${I.acc_1000.calc.replace(' ÷ habitantes × 1.000.','.')} Desde 2019 incluye los accidentes sin heridos.<br><b>Fuente:</b> «Accidentes de tráfico de la ciudad de Madrid» de datos.madrid.es.`,T.accidentes_src]),
      kpi(N(s(4)),`heridos graves (${YC})`,'ingreso de más de 24 horas',[`<b>Cálculo:</b> personas con lesividad «ingreso superior a 24 horas».<br><b>Fuente:</b> datos.madrid.es.`,T.accidentes_src]),
      kpi(N(s(5)),`fallecidos (${YC})`,'en las 24 horas siguientes',[`<b>Cálculo:</b> personas con lesividad «fallecido en 24 horas»; no incluye a quien muere días después.<br><b>Fuente:</b> datos.madrid.es.`,T.accidentes_src]),
      kpi(N(L),`sanciones de limpieza (${YC})`,cd!=null?puesto(I.limpieza_1000,cd)+' por habitante':'basura, orines, pintadas…',[`<b>Cálculo:</b> expedientes sancionadores de la ordenanza de limpieza con infracción en el año.<br><b>Fuente:</b> «Denuncias y sanciones sobre limpieza urbana y zonas verdes» de datos.madrid.es.`,T.limpieza_src])]},
  informe(B){const {T,I}=B,cd=CM.DSEL,A=T.accidentes.filter(r=>cd==null||r[1]===cd),s=(y,i)=>sum(A.filter(r=>r[0]===y),r=>r[i]);
    const Lg=T.accidentes_lugar[String(cd||0)]||[],M2=T.multas||[],mU=M2.filter(r=>r[0]<=YC).slice(-1)[0];
    let h=P(`En ${YC} hubo <b>${N(s(YC,2))}</b> accidentes de tráfico en ${esc(amb())} (${N(s(YC-1,2))} en ${YC-1}): ${N(s(YC,4))} heridos graves, ${N(s(YC,5))} fallecidos y ${N(s(YC,6))} atropellos. En ${N(s(YC,7))} accidentes algún implicado dio positivo en alcohol.`)
      +(cd!=null?P(`Por habitante, ${esc(DISTN[cd])} tiene ${cmpTxt(I.acc_1000,cd)}. En heridos graves y fallecidos: ${cmpTxt(I.graves_100k,cd)}.`):'')
      +(Lg[0]?P(`Desde 2022, el lugar con más accidentes es ${esc(Lg[0][0])} (${N(Lg[0][1])}), seguido de ${Lg.slice(1,3).map(r=>`${esc(r[0])} (${N(r[1])})`).join(' y ')}.`):'')
      +(cd==null&&mU?P(`En ${mU[0]} se pusieron ${N(mU[1])} multas de circulación y se cobraron ${M(mU[2])} en periodo voluntario.`):'')
      +P(`Por limpieza se abrieron ${N(sum(T.limpieza.filter(r=>r[0]===YC&&(cd==null||r[1]===cd)),r=>r[2]))} expedientes sancionadores en ${YC}${cd!=null?`: ${cmpTxt(I.limpieza_1000,cd)}`:''}.`)
      +`<p class="chw">Desde 2019 la Policía Municipal publica también los accidentes sin heridos y mide la gravedad por días de ingreso: no se puede comparar con los años anteriores.</p>`
      +card('Accidentes por año',colChart([...new Set(T.accidentes.map(r=>r[0]))].sort().map(y=>[y,s(y,2),y>YC]),{u:'accidentes',title:'Accidentes',unit:'el año en curso, incompleto · desde 2019 incluye accidentes sin heridos'}),srcBtn(T.accidentes_src));
    return h},
  graficos:[['Accidentes y multas','via','seguridad'],['Sanciones de limpieza',B=>limpiezaHTML(B)]],
  metodo(B){const {T,I}=B;return [
    ['Accidentes',I.acc_1000.calc+' Una fila del fichero es una persona implicada; el accidente se identifica por su número de expediente (desde 2019) o de parte (hasta 2018). Desde 2019 se incluyen los accidentes sin heridos.',T.accidentes_src],
    ['Gravedad','Hasta 2018: herido leve, herido grave o muerto según el atestado. Desde 2019: código de lesividad; grave = ingreso de más de 24 horas (3), fallecido = en 24 horas (4); leve = 1, 2, 5, 6 y 7.',T.accidentes_src],
    ['Lugares con más accidentes','Dirección del accidente tal como la escribe el atestado (calle y número o cruce), contando accidentes distintos desde 2022.',T.accidentes_src],
    ['Multas de circulación','Fila TOTAL de cada año: boletines de denuncia formulados y recaudación en vía voluntaria. Solo hay datos de toda la ciudad.',T.multas_src||[]],
    ['Sanciones de limpieza',I.limpieza_1000.calc,T.limpieza_src]]},
  csv(B){const T=B.T;return [
    ['accidentes_por_distrito',['anio','cod_distrito','accidentes','heridos_leves','heridos_graves','fallecidos','atropellos','con_alcohol'],T.accidentes,T.accidentes_src],
    ['accidentes_lugares_desde_2022',['ambito','lugar','accidentes','con_graves_o_muertos','atropellos'],Object.entries(T.accidentes_lugar).flatMap(([k,L])=>L.map(r=>[k==='0'?'Madrid':DISTN[+k],...r])),T.accidentes_src],
    ['multas_circulacion',['anio','boletines','recaudacion_voluntaria'],T.multas||[],T.multas_src||[]],
    ['sanciones_limpieza',['anio','cod_distrito','sanciones','importe'],T.limpieza,T.limpieza_src]]}};
// ---------- Contratos ----------
const contrBase=(S,cd)=>cd==null?S.por_anio.map(r=>[r[0],r[1],r[2],r[3]]):S.por_distrito.filter(r=>r[1]===cd).map(r=>[r[0],r[2],r[3],r[4]]);
DEF.servicios={mapa:'contr_hab',
  kpis(B){const {S,I}=B,cd=CM.DSEL,b=contrBase(S,cd).filter(r=>r[0]===YC),n=sum(b,r=>r[2]),v=sum(b,r=>r[3]),nm=sum(b.filter(r=>r[1]==='menor'),r=>r[2]);
    const pg=sum(S.pagos_anio.filter(r=>r[0]===YC&&(cd==null||r[1]===cd)),r=>r[2]);
    return [kpi(N(n),`contratos inscritos (${YC})`,cd!=null?'de la Junta del distrito':'Ayuntamiento, organismos y empresas',[`<b>Cálculo:</b> contratos del registro municipal y contratos menores con fecha en el año${cd!=null?', cuyo órgano es la Junta del distrito':''}.<br><b>Fuente:</b> «Contratos» y «Contratos menores» de datos.madrid.es.`,S.src.contratos]),
      kpi(M(v),`adjudicados (${YC})`,cd!=null?puesto(I.contr_hab,cd)+' por habitante':'IVA incluido',[`<b>Cálculo:</b> suma del importe de adjudicación con IVA. En los acuerdos marco es el techo de gasto, no lo pagado.<br><b>Fuente:</b> datos.madrid.es.`,S.src.contratos]),
      kpi(n?nf(100*nm/n,0)+' %':'—','son contratos menores',`${N(nm)} contratos menores`,[`<b>Cálculo:</b> contratos menores (sin concurso, hasta 15.000 € en servicios y suministros y 40.000 € en obras, IVA excluido) ÷ contratos del año.<br><b>Fuente:</b> datos.madrid.es.`,S.src.contratos]),
      kpi(M(pg),`pagado a proveedores (${YC})`,cd!=null?'por la Junta':'todos los perceptores',[`<b>Cálculo:</b> pagos a terceros reconocidos en el año (lo que se paga de verdad, no lo adjudicado).<br><b>Fuente:</b> «Pagos a terceros» de datos.madrid.es.`,S.src.pagos])]},
  informe(B){const {S,I}=B,cd=CM.DSEL,b=contrBase(S,cd),años=[...new Set(b.map(r=>r[0]))].filter(y=>y>=2015&&y<=YC).sort();
    const v=y=>sum(b.filter(r=>r[0]===y),r=>r[3]),n=y=>sum(b.filter(r=>r[0]===y),r=>r[2]),R=S.ranking[String(cd||0)]||[],Pg=S.pagos[String(cd||0)]||[];
    let h=P(`En ${YC} ${cd==null?'el Ayuntamiento, sus organismos y empresas inscribieron':'la Junta de '+esc(DISTN[cd])+' inscribió'} <b>${N(n(YC))}</b> contratos por <b>${M(v(YC))}</b> (IVA incluido), frente a ${N(n(YC-1))} y ${M(v(YC-1))} en ${YC-1}.`)
      +(R.length?P(`Desde 2015, las empresas con más importe adjudicado son ${R.slice(0,3).map(r=>`${esc(r[0])} (${M(r[3])})`).join(', ')}.`):'')
      +(Pg.length?P(`En pagos reales, quien más ha cobrado desde 2011 es ${esc(Pg[0][0])} (${M(Pg[0][2])}).`):'')
      +(cd!=null?P(`Por habitante, los contratos de la Junta suman ${cmpTxt(I.contr_hab,cd)}. Los contratos de las Áreas para toda la ciudad (limpieza, basuras…) no se cuentan aquí.`):'')
      +card('Importe adjudicado por año',barChart(años.map(y=>[y,v(y)]),[{n:'Adjudicado',c:AZ,i:1}],{title:'Importe por año',unit:'IVA incluido'}),srcBtn(S.src.contratos));
    return h},
  graficos:[['Contratos adjudicados','servicios','contratos'],['Pagos a proveedores','servicios','pagos'],['Encargos a empresas municipales','servicios','encargos']],
  metodo(B){const S=B.S;return [
    ['Contratos adjudicados','Registro de contratos del Ayuntamiento, contratos menores, basados en acuerdos marco y homologaciones. Importe de adjudicación con IVA. Las personas físicas no se muestran por su nombre.',S.src.contratos],
    ['Contratos por distrito',B.I.contr_hab.calc,S.src.contratos],
    ['Pagos a proveedores','Pagos a terceros publicados por el Ayuntamiento (desde 2011): lo que se reconoce que se debe pagar a cada perceptor en el año.',S.src.pagos],
    ['Encargos a empresas municipales','Encargos a medios propios personificados y encomiendas de gestión publicados por el Ayuntamiento, con el importe que se compromete a pagar.',S.src.encargos||[]]]},
  csv(B){const S=B.S;return [
    ['contratos_por_distrito',['anio','cod_distrito','tipo','contratos','importe_iva'],S.por_distrito,S.src.contratos],
    ['contratos_ciudad',['anio','tipo','contratos','importe_iva'],S.por_anio,S.src.contratos],
    ['empresas_ranking',['ambito','empresa','nif','contratos','importe','menores','desde','hasta'],Object.entries(S.ranking).flatMap(([k,L])=>L.map(r=>[k==='0'?'Madrid':DISTN[+k],...r])),S.src.contratos],
    ['pagos_por_anio',['anio','cod_distrito','pagado'],S.pagos_anio,S.src.pagos],
    ['encargos',['tipo','fecha','anio','area','objeto','encargado','importe','documento'],(S.encargos||[]).map(r=>r.slice(0,8)),S.src.encargos||[]]]}};
// ---------- Servicios sociales ----------
DEF.social={mapa:'espera_1000',
  kpis(B){const {C,S,I}=B,cd=CM.DSEL,AS=C.ayudas_sociales.filter(r=>r[0]===YC&&(cd==null||r[1]===cd)),E=S.espera.filter(r=>cd==null||r[1]===cd),n=sum(E,r=>r[2]);
    const med=n?sum(E,r=>r[3]*r[2])/n:null,parc=cd!=null&&YC>=2024?' · el portal solo indica el distrito en parte de las ayudas':'';
    return [kpi(N(sum(AS,r=>r[2])),`ayudas a vecinos (${YC})`,'alimentos, comedor, vivienda…'+parc,[`<b>Cálculo:</b> ayudas económicas de servicios sociales concedidas en el año.<br><b>Fuente:</b> «Ayudas económicas de servicios sociales» de datos.madrid.es.`,C.src.ayudas_sociales]),
      kpi(M(sum(AS,r=>r[3])),`en ayudas a vecinos (${YC})`,'importe concedido',[`<b>Cálculo:</b> suma del importe de esas ayudas.<br><b>Fuente:</b> datos.madrid.es.`,C.src.ayudas_sociales]),
      kpi(N(n),'mayores en lista de espera',cd!=null?puesto(I.espera_1000,cd)+' por habitante':`a ${esc((S.espera_fecha||'').slice(0,10))}`,[`<b>Cálculo:</b> solicitudes en lista de espera de los servicios municipales para mayores (ayuda a domicilio, centros de día, residencias…) en la fecha de los datos.<br><b>Fuente:</b> «Listas de espera» de datos.madrid.es; no se usa ningún dato personal.`,S.src.espera]),
      kpi(med!=null?N(med)+' días':'—','de espera media','desde la fecha de solicitud',[`<b>Cálculo:</b> media de días entre la entrada de la solicitud y la fecha de los datos, ponderada por número de personas.<br><b>Fuente:</b> datos.madrid.es.`,S.src.espera])]},
  informe(B){const {C,S,I}=B,cd=CM.DSEL,AS=C.ayudas_sociales.filter(r=>cd==null||r[1]===cd),n=y=>sum(AS.filter(r=>r[0]===y),r=>r[2]),v=y=>sum(AS.filter(r=>r[0]===y),r=>r[3]);
    const E=S.espera.filter(r=>cd==null||r[1]===cd),sv=[...new Set(S.espera.map(r=>r[0]))].map(s=>[s,sum(E.filter(r=>r[0]===s),r=>r[2])]).sort((a,b)=>b[1]-a[1]);
    let h=P(`En ${YC} se concedieron <b>${N(n(YC))}</b> ayudas económicas de servicios sociales en ${esc(amb())} por ${M(v(YC))} (${N(n(YC-1))} en ${YC-1}). ${C.ayudas_sociales_tipo[0]?`Desde 2021, en toda la ciudad, el mayor importe va a ${esc(C.ayudas_sociales_tipo[1]?C.ayudas_sociales_tipo[1][0].toLowerCase():'')} y ${esc(C.ayudas_sociales_tipo[2]?C.ayudas_sociales_tipo[2][0].toLowerCase():'')}.`:''}`)
      +(cd!=null&&YC>=2024?`<p class="chw">Desde 2024 el portal solo indica el distrito en parte de las ayudas: la cifra del distrito se queda corta.</p>`:'')
      +P(`A ${esc((S.espera_fecha||'').slice(0,10))} había <b>${N(sum(E,r=>r[2]))}</b> personas mayores esperando un servicio municipal. ${sv.slice(0,2).map(([s,k])=>`${esc(s)}: ${N(k)}`).join('; ')}.`)
      +(cd!=null?P(`Por habitante, ${esc(DISTN[cd])} tiene ${cmpTxt(I.espera_1000,cd)}.`):'')
      +card('Ayudas a vecinos por año',colChart([...new Set(AS.map(r=>r[0]))].sort().map(y=>[y,n(y),y>YC]),{u:'ayudas',title:'Ayudas por año',unit:'número de ayudas'}),srcBtn(C.src.ayudas_sociales));
    return h},
  graficos:[['Ayudas a vecinos','social','ayudas'],['Listas de espera','social','espera']],
  metodo(B){const {C,S}=B;return [
    ['Ayudas a vecinos','Ayudas económicas de servicios sociales concedidas cada año, con el distrito que indica el portal (de 2016 a 2018 no lo indica; desde 2024, solo en parte). El tipo se deduce del texto del objeto de la ayuda.',C.src.ayudas_sociales],
    ['Listas de espera','Solicitudes pendientes de los servicios municipales para mayores. El fichero original incluye DNI parcial e iniciales, que no se usan ni se muestran.',S.src.espera]]},
  csv(B){const {C,S}=B;return [
    ['ayudas_sociales',['anio','cod_distrito','ayudas','importe'],C.ayudas_sociales,C.src.ayudas_sociales],
    ['listas_espera',['servicio','cod_distrito','personas','espera_media_dias','espera_maxima_dias'],S.espera,S.src.espera]]}};
// ---------- Fondos y convenios ----------
DEF.ayudas={mapa:'subv_hab',
  kpis(B){const {A,I}=B,cd=CM.DSEL,rec=sum(A.recibidas,r=>r[7]),fe=sum(A.fondos_europeos.filter(r=>cd==null||r[7]===cd),r=>r[3]);
    const SB=(A.subvenciones.anio||[]).filter(r=>r[0]===YC&&(cd==null||r[1]===cd)),cv=A.convenios.filter(r=>cd==null||r[3]===cd).length;
    return [kpi(M(rec),'ayudas recibidas de otras administraciones','toda la ciudad, desde 2022',[`<b>Cálculo:</b> subvenciones y ayudas que el Estado, la Comunidad y otros conceden al Ayuntamiento, sus organismos y empresas, contrastadas con la BDNS.<br><b>Fuente:</b> datos.madrid.es y BDNS.`,A.src.recibidas]),
      kpi(M(fe),'fondos europeos',cd!=null?'proyectos con este distrito':'Plan de Recuperación y FEDER',[`<b>Cálculo:</b> importe concedido de los proyectos con fondos europeos${cd!=null?' cuyo ámbito es el distrito':''}.<br><b>Fuente:</b> «Fondos europeos» de datos.madrid.es.`,A.src.fondos]),
      kpi(M(sum(SB,r=>r[3])),`subvenciones concedidas (${YC})`,cd!=null?'por la Junta · '+puesto(I.subv_hab,cd)+' por habitante':`${N(sum(SB,r=>r[2]))} subvenciones`,[`<b>Cálculo:</b> importe concedido de las subvenciones del Ayuntamiento en el año${cd!=null?' por la Junta del distrito':''}.<br><b>Fuente:</b> «Subvenciones» de datos.madrid.es.`,A.src.subvenciones]),
      kpi(N(cv),'convenios firmados','desde noviembre de 2018',[`<b>Cálculo:</b> convenios inscritos en el registro municipal${cd!=null?' firmados por la Junta':''}.<br><b>Fuente:</b> «Convenios inscritos» de datos.madrid.es.`,A.src.convenios])]},
  informe(B){const {A,I}=B,cd=CM.DSEL,niv={};A.recibidas.forEach(r=>niv[r[0]]=(niv[r[0]]||0)+(r[7]||0));
    const SB=(A.subvenciones.anio||[]).filter(r=>cd==null||r[1]===cd),v=y=>sum(SB.filter(r=>r[0]===y),r=>r[3]),Rk=(A.subvenciones.ranking||{})[String(cd||0)]||[],PU=A.proyectos_ue||[];
    let h=P(`Otras administraciones han concedido al Ayuntamiento ${N(A.recibidas.length)} ayudas por ${M(sum(A.recibidas,r=>r[7]))}: ${Object.entries(niv).sort((a,b)=>b[1]-a[1]).map(([k,x])=>`${k.toLowerCase()} ${M(x)}`).join(', ')}. Los fondos europeos del Plan de Recuperación y FEDER suman ${M(sum(A.fondos_europeos,r=>r[3]))} en ${N(A.fondos_europeos.length)} proyectos${PU.length?`, y el Ayuntamiento es socio de ${N(PU.length)} proyectos europeos de investigación (${M(sum(PU,r=>r[4]))})`:''}.`)
      +P(`El Ayuntamiento${cd!=null?' (Junta de '+esc(DISTN[cd])+')':''} concedió ${M(v(YC))} en subvenciones en ${YC} (${M(v(YC-1))} en ${YC-1}).${Rk[0]?` Desde 2019 quien más ha recibido es ${esc(Rk[0][0])} (${M(Rk[0][3])}).`:''}`)
      +P(`Hay ${N(A.convenios.filter(r=>cd==null||r[3]===cd).length)} convenios firmados desde 2018${cd!=null?' por la Junta':''}.`)
      +card('Subvenciones concedidas por año',barChart([...new Set(SB.map(r=>r[0]))].sort().map(y=>[y,v(y)]),[{n:'Concedido',c:AZ,i:1}],{title:'Subvenciones',unit:'el año en curso, incompleto'}),srcBtn(A.src.subvenciones));
    return h},
  graficos:[['Fondos recibidos','ayudas','recibidas'],['Subvenciones que da','ayudas','subvenciones'],['Convenios','ayudas','convenios']],
  metodo(B){const A=B.A;return [
    ['Ayudas recibidas','Conjunto «Subvenciones y ayudas concedidas al Ayuntamiento» de datos.madrid.es, completado con la Base de Datos Nacional de Subvenciones (coinciden en 84 de 86 concesiones; se añaden las 2 que faltaban).',A.src.recibidas],
    ['Fondos europeos','Proyectos del Plan de Recuperación y FEDER publicados por el Ayuntamiento, con su ámbito (distrito o toda la ciudad).',A.src.fondos],
    ['Proyectos europeos de investigación','Proyectos de CORDIS (Comisión Europea) en los que el socio tiene el NIF del Ayuntamiento (P2807900B), con la aportación de la UE a ese socio.',A.src.proyectos_ue||[]],
    ['Subvenciones que da el Ayuntamiento','Subvenciones concedidas (2014–2018 y desde 2019). Las personas físicas aparecen sin nombre. 2014 y 2015 parecen incompletos.',A.src.subvenciones],
    ['Convenios','Registro de convenios del Ayuntamiento desde noviembre de 2018, con lo que se compromete a pagar cada parte.',A.src.convenios]]},
  csv(B){const A=B.A;return [
    ['ayudas_recibidas',['nivel','administracion','organo','convocatoria','fecha','anio','beneficiario','importe','codigo_bdns','bases'],A.recibidas.map(r=>r.slice(0,10)),A.src.recibidas],
    ['fondos_europeos',['programa','proyecto','anio','concedido','coste_real_iva','tipo','ambito','cod_distrito','beneficiario','url'],A.fondos_europeos.map(r=>r.slice(0,10)),A.src.fondos],
    ['subvenciones_por_anio',['anio','cod_distrito','subvenciones','importe'],A.subvenciones.anio||[],A.src.subvenciones],
    ['convenios',['fecha','anio','organo','cod_distrito','objeto','otras_entidades','obligacion_ayuntamiento','obligacion_otras','documento'],A.convenios.map(r=>r.slice(0,9)),A.src.convenios],
    ['proyectos_ue_cordis',['acronimo','titulo','inicio','fin','aportacion_ue_ayuntamiento','coste_total','url'],(A.proyectos_ue||[]).map(r=>r.slice(0,7)),A.src.proyectos_ue||[]]]}};
// ---------- Edificios municipales ----------
const EST=[['fav','Favorable','#2f9e5b'],['desf','Desfavorable sin subsanar','#d23f3f'],['subs','Desfavorable subsanada','#e8912f'],['iee','IEE complementario','#7a63d4'],['sin','Sin ITE presentada','#9aa1a9'],['nd','Sin dato del Registro','#c4c9ce']];
const edCount=(E,c)=>{const t=E.filter(b=>c==null||b.cd===c),o={total:t.length};EST.forEach(([k])=>o[k]=t.filter(b=>b.s===k).length);o.nd+=t.filter(b=>b.s==='pend').length;return o};
DEF.edificios={mapa:'ite_desf',
  kpis(B){const {E,C}=B,cd=CM.DSEL,k=edCount(E,cd),p=x=>k.total?nf(100*x/k.total,0)+' %':'';const src=C.src.edificios;
    const t=`<b>Cálculo:</b> edificios municipales (agrupando los centros que comparten dirección) según su última inspección en el Registro de Edificios del Ayuntamiento.<br><b>Fuente:</b> listados de centros de los 21 distritos y Registro de Edificios (ITE/IEE).`;
    return [kpi(N(k.total),'edificios municipales','colegios, centros culturales, de mayores…',[t,src]),kpi(N(k.fav),'con ITE favorable',p(k.fav),[t,src]),
      kpi(N(k.desf),'con ITE desfavorable sin subsanar',p(k.desf)+(cd!=null&&B.I.ite_desf?' · '+puesto(B.I.ite_desf,cd):''),[t,src]),kpi(N(k.sin),'sin ITE presentada',p(k.sin),[t,src])]},
  informe(B){const {E,I}=B,cd=CM.DSEL,k=edCount(E,cd),d=cd!=null?'?d='+cd:'';
    return P(`${esc(amb())} tiene <b>${N(k.total)}</b> edificios municipales en el listado de centros. Según el Registro de Edificios, ${N(k.fav)} tienen la ITE favorable, ${N(k.desf)} desfavorable sin constancia de que se hayan subsanado las deficiencias, ${N(k.subs)} desfavorable ya subsanada y ${N(k.sin)} no tienen ITE presentada. De ${N(k.nd)} no se ha podido consultar el Registro.`)
      +(cd!=null&&I.ite_desf?P(`El porcentaje de edificios con ITE desfavorable sin subsanar es de ${cmpTxt(I.ite_desf,cd)}.`):'')
      +card('Estado de la ITE',hbars(EST.map(([s,n,c])=>[n,k[s]]),N,{c:'#5c7cfa'}),srcBtn(B.C.src.edificios))
      +`<div class="sxmas"><b>Informes detallados de edificios:</b><a href="#distrito${d}">Informe del distrito, edificio a edificio →</a><a href="#urgente${d}">Los más urgentes →</a><a href="#mapa${d}">Mapa de edificios →</a><a href="#informe${d}">Informe PDF →</a></div>`},
  graficos:[['Estado de la ITE por distrito',B=>{const E=B.E,cd=CM.DSEL;return card('Edificios por estado de la ITE',tabla(['Distrito','Edificios',...EST.map(e=>e[1])],D21.map(c=>{const k=edCount(E,c);return Object.assign([`<a href="${lk('edificios','graficos',c)}">${esc(DISTN[c])}</a>`,N(k.total),...EST.map(([s])=>N(k[s]))],{on:c===cd})}),{num:[1,2,3,4,5,6,7]}),srcBtn(B.C.src.edificios))
      +`<div class="sxmas"><b>Más gráficos de edificios:</b><a href="#panel${cd!=null?'?d='+cd:''}">Cifras ITE (antigüedad, tipos, plazos) →</a><a href="#inversion${cd!=null?'?d='+cd:''}">Inversión en edificios y servicios por distrito →</a></div>`}]],
  metodo(B){return [
    ['Edificios municipales','Centros de los listados «Direcciones y teléfonos» y «Recursos educativos públicos» de los 21 distritos, geolocalizados con CartoCiudad y agrupados por dirección: varios centros en el mismo edificio cuentan como uno.',B.C.src.edificios],
    ['Estado de la ITE','Última inspección técnica (ITE) o informe de evaluación (IEE) de cada dirección en el Registro de Edificios del Ayuntamiento. Si un edificio tiene varias direcciones se toma la peor. El Registro no tiene carácter de certificado.',B.C.src.edificios],
    ['Porcentaje desfavorable',B.I.ite_desf?B.I.ite_desf.calc:'',B.C.src.edificios]]},
  csv(B){return [['edificios_por_distrito',['cod_distrito','distrito','edificios',...EST.map(e=>e[0])],D21.map(c=>{const k=edCount(B.E,c);return [c,DISTN[c],k.total,...EST.map(([s])=>k[s])]}),B.C.src.edificios]]}};
// ---------- Informe completo ----------
const ORDEN=['renta','pens_100','gasto_junta_hab','inv_hab','via_hab','licencias_1000','arboles_1000','acc_1000','graves_100k','limpieza_1000','contr_hab','espera_1000','subv_hab','ite_desf'];
const inds=B=>ORDEN.map(k=>B.I[k]).filter(Boolean);
DEF.completo={mapa:'renta',
  kpis(B){const cd=CM.DSEL,L=inds(B);
    if(cd==null){const top={};L.forEach(o=>{const c=D21.filter(x=>o.v[x]!=null).sort((a,b)=>o.v[b]-o.v[a])[0];top[c]=(top[c]||0)+1});
      return [kpi(N(L.length),'indicadores comparables','por distrito, en las 7 secciones'),kpi('21','distritos'),kpi(N(B.HAB[0]),'habitantes',`a 1 de enero de ${B.yH}`),kpi(esc(DISTN[+Object.entries(top).sort((a,b)=>b[1]-a[1])[0][0]]),'es primero en más indicadores','el valor más alto, sea bueno o malo')]}
    const arr=L.map(o=>{const [p,n]=rkOf(o,cd);return {o,p,n,m:media(o),v:o.v[cd]}}).filter(x=>x.p);
    return [kpi(N(arr.filter(x=>x.v>x.m).length)+' de '+arr.length,'indicadores por encima de la media','de los 21 distritos'),
      B.I.renta?kpi(N(B.I.renta.v[cd])+' €','renta por persona',puesto(B.I.renta,cd),[`<b>Cálculo:</b> ${B.I.renta.calc}`,B.I.renta.src]):'',
      kpi(N(B.I.gasto_junta_hab.v[cd])+' €','gasto de la Junta por habitante',puesto(B.I.gasto_junta_hab,cd),[`<b>Cálculo:</b> ${B.I.gasto_junta_hab.calc}`,B.I.gasto_junta_hab.src]),
      B.I.acc_1000?kpi(nf(B.I.acc_1000.v[cd],1),'accidentes por 1.000 habitantes',puesto(B.I.acc_1000,cd),[`<b>Cálculo:</b> ${B.I.acc_1000.calc}`,B.I.acc_1000.src]):'']},
  informe(B){const cd=CM.DSEL,L=inds(B);
    if(cd==null){return P('Para cada indicador, el distrito con el valor más alto y el más bajo. Elige un distrito arriba para ver su informe completo y el puesto que ocupa en cada sección.')
      +tabla(['Sección','Indicador','Más alto','Más bajo','Media'],L.map(o=>{const s=D21.filter(c=>o.v[c]!=null).sort((a,b)=>o.v[b]-o.v[a]);return [esc(SECS[o.sec].t),esc(o.n)+` <span class="sub">(${esc(String(o.per))})</span>`,`${esc(DISTN[s[0]])}: ${o.fmt(o.v[s[0]])}`,`${esc(DISTN[s[s.length-1]])}: ${o.fmt(o.v[s[s.length-1]])}`,o.fmt(media(o))+' '+esc(o.u)]}),{num:[4]})}
    let h=`<p>Puesto de <b>${esc(DISTN[cd])}</b> entre los 21 distritos en cada indicador: 1.º es el valor más alto, sea bueno o malo. Los indicadores están divididos por habitante para poder comparar distritos de distinto tamaño.</p>`;
    const secs=[...new Set(L.map(o=>o.sec))];
    for(const s of secs){const Ls=L.filter(o=>o.sec===s);h+=`<h2><a href="${lk(s,'resumen')}">${esc(SECS[s].t)}</a></h2>`+tabla(['Indicador',esc(DISTN[cd]),'Media de los distritos','Diferencia','Puesto'],Ls.map(o=>{const v=o.v[cd],m=media(o);return [esc(o.n)+` <span class="sub">(${esc(String(o.per))})</span>`,v==null?'—':o.fmt(v)+' '+esc(o.u),o.fmt(m),v==null?'—':pctDif(v,m),v==null?'—':puesto(o,cd).replace('puesto ','')]}),{num:[1,2,3,4]})}
    return h},
  graficos:[['Los 21 distritos en cada indicador',B=>inds(B).map(o=>compBars(o)).reduce((a,x,i,arr)=>i%2?a:a+`<div class="grid2">${x}${arr[i+1]||''}</div>`,'')]],
  metodo(B){return inds(B).map(o=>[o.n+` (${SECS[o.sec].t})`,o.calc+` Población: padrón municipal a 1 de enero de ${B.yH}.`,o.src])},
  csv(B){const L=inds(B);return [['informe_completo_distritos',['cod_distrito','distrito','habitantes',...L.map(o=>o.k)],D21.map(c=>[c,DISTN[c],B.HAB[c],...L.map(o=>o.v[c]==null?'':Math.round(o.v[c]*100)/100)]),[...new Set(L.flatMap(o=>o.src||[]))]]]}};

// =====================================================================
// Pintado de las 4 páginas
// =====================================================================
let CSVS=[];
const csvTxt=(cab,filas)=>[cab,...filas].map(r=>r.map(x=>{const s=x==null?'':String(x);return /[";\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}).join(';')).join('\r\n');
document.addEventListener('click',e=>{const b=e.target.closest('[data-csv]');if(!b)return;e.preventDefault();const c=CSVS[+b.dataset.csv];if(!c)return;
  const url=URL.createObjectURL(new Blob(['﻿'+csvTxt(c[1],c[2])],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=c[0]+(CM.DSEL!=null?'':'')+'.csv';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000)});
async function fuentesHTML(ids){const F=await get('fuentes'),L=[...new Set((ids||[]).filter(x=>x!=null))].map(i=>F[i]).filter(Boolean),g={};L.forEach(f=>(g[f.k]=g[f.k]||{f,l:[]}).l.push(f));
  return Object.values(g).map(({f,l})=>`<li><b>${esc(f.f)}</b> · ${esc(f.o||'')} · <a href="${esc(f.fi)}" target="_blank" rel="noopener">ficha en el portal original</a>${f.l?` · licencia: ${esc(f.l)}`:''}
    <br><span class="sub">Dato en bruto (${l.length} fichero${l.length===1?'':'s'}):</span> ${l.slice(-6).reverse().map(x=>`<a href="${esc(x.u)}" target="_blank" rel="noopener">${esc((x.r||x.u).slice(0,70))}</a>`).join(' · ')}</li>`).join('')}
async function pagina(v,el){const B=await datos(),d=DEF[v],p=curP(v),o=B.I[d.mapa];
  if(p==='resumen'){
    el.innerHTML=cab(v)+`<div class="sxres">${o?mapCard(o,'sxMR'):''}<div class="kpis k4">${d.kpis(B).join('')}</div></div>
      <div class="sxmas"><b>En ${esc(SECS[v].t)}:</b>${PAGS.slice(1).map(([k,n])=>`<a href="${lk(v,k)}">${n} →</a>`).join('')}</div>`;
    if(o)mapDraw(o,'sxMR');return}
  if(p==='informe'){el.innerHTML=cab(v)+`<article class="sxinf">${d.informe(B)}</article>`;return}
  if(p==='graficos'){el.innerHTML=cab(v)+(o?compBars(o):'')+d.graficos.map((g,i)=>`<h2 class="asec">${esc(g[0])}</h2><div id="sxG${i}"><p class="sub">Cargando…</p></div>`).join('');
    for(let i=0;i<d.graficos.length;i++){const g=d.graficos[i],box=document.getElementById('sxG'+i);if(!box)return;
      if(typeof g[1]==='function'){box.innerHTML=g[1](B);continue}
      EMBED={v:g[1],p:g[2]};try{await OLD[g[1]](box)}finally{EMBED=null}}
    return}
  // Cómo se calcula y datos
  const met=d.metodo(B),cs=d.csv(B);CSVS=cs;
  const fs=await Promise.all(met.map(m=>fuentesHTML(m[2])));
  el.innerHTML=cab(v)+`<p class="sub">Cada cifra de esta sección sale de ficheros oficiales descargados y guardados con su fecha y su huella SHA-256. Aquí se explica el cálculo y se enlaza el dato en bruto en la página original. Método general: <a href="https://github.com/bakero/ite-madrid/blob/main/docs/trazabilidad.md" target="_blank" rel="noopener">docs/trazabilidad.md</a>.</p>
   <h2 class="asec">Cómo se calcula cada dato</h2>${met.map((m,i)=>`<section class="card sxmet"><h3>${esc(m[0])}</h3><p>${esc(m[1])}</p>${fs[i]?`<ul class="sxsrc">${fs[i]}</ul>`:''}${srcBtn(m[2],'Ver ficheros, huellas y pasos')}</section>`).join('')}
   <h2 class="asec">Descargar los datos de esta sección</h2><p class="sub">Ficheros CSV (separador «;», codificación UTF-8) con los datos ya limpios que usan los gráficos. Códigos de distrito del 1 (Centro) al 21 (Barajas).</p>
   <div class="sxcsv">${cs.map((c,i)=>`<div class="card"><b>${esc(c[0])}.csv</b><span class="sub">${N(c[2].length)} filas · ${c[1].length} columnas</span><button type="button" class="btn" data-csv="${i}">Descargar CSV</button>${srcBtn(c[3],'De dónde sale')}</div>`).join('')}</div>`}

// ---------- Portada: mapa de Madrid dividido en las secciones ----------
async function inicio(el){const G=CM.geo&&CM.geo();
  const zonaDe={};Object.entries(ZONAS).forEach(([s,L])=>L.forEach(c=>zonaDe[c]=s));
  let svg='',labs='';
  if(G){const {DIST,distP}=G;let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;distP.forEach(d=>{x0=Math.min(x0,d.bb[0]);y0=Math.min(y0,d.bb[1]);x1=Math.max(x1,d.bb[2]);y1=Math.max(y1,d.bb[3])});
    const sw=(x1-x0)/400;
    const grupos=Object.keys(ZONAS).map(s=>{const P_=DIST.map((d,i)=>[+d.cod,distP[i]]).filter(([c])=>zonaDe[c]===s);
      const dd=P_.map(([c,dp])=>dp.lines.map(l=>'M'+l.map(p=>p[0].toFixed(5)+','+p[1].toFixed(5)).join('L')+'Z').join('')).join('');
      return `<a href="${lk(s,'resumen')}" class="inz" data-s="${s}" aria-label="${esc(SECS[s].t)}"><path d="${dd}" fill="${SECS[s].c}" stroke="${SECS[s].c}" stroke-width="${sw*1.2}"/><path d="${dd}" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="${sw*0.6}"/></a>`}).join('');
    svg=`<svg viewBox="${x0} ${y0} ${x1-x0} ${y1-y0}" role="group" aria-label="Mapa de Madrid dividido en las secciones de la aplicación">${grupos}</svg>`;
    labs=Object.keys(ZONAS).map(s=>{const P_=DIST.map((d,i)=>[+d.cod,distP[i]]).filter(([c])=>zonaDe[c]===s),cx=P_.reduce((a,[,d])=>a+d.cx,0)/P_.length,cy=P_.reduce((a,[,d])=>a+d.cy,0)/P_.length;
      return `<a class="inzl" href="${lk(s,'resumen')}" style="left:${(100*(cx-x0)/(x1-x0)).toFixed(1)}%;top:${(100*(cy-y0)/(y1-y0)).toFixed(1)}%"><span aria-hidden="true">${SECS[s].i}</span>${esc(SECS[s].t)}</a>`}).join('');
    var ratio=(x1-x0)/(y1-y0)}
  el.innerHTML=`<div class="inih"><h1>${CM.DSEL==null?'Los datos públicos de Madrid':'Los datos públicos de '+esc(DISTN[CM.DSEL])}</h1>
   <p class="lead">Elige una sección en el mapa. Cada una empieza con el mapa de Madrid y sus cifras principales, y tiene un informe, todos los gráficos y la explicación de cómo se calcula cada dato, con enlace al dato original.</p>${ambBar('inicio')}</div>
   <div class="inimap"><div class="inimw" style="aspect-ratio:${ratio||1}">${svg}${labs}</div>
   <ul class="inil2">${Object.keys(ZONAS).map(s=>`<li><a href="${lk(s,'resumen')}"><span class="sxico" style="background:${SECS[s].c}" aria-hidden="true">${SECS[s].i}</span><b>${esc(SECS[s].t)}</b><span class="sub">${esc(SECS[s].s)}</span></a></li>`).join('')}</ul></div>`}

const OLD={ciudadano,via,servicios,social,ayudas};
window.SEC={render(v){const el=document.getElementById('sx-'+v);if(!el)return;
  if(!el.innerHTML)el.innerHTML='<p class="sub">Cargando datos…</p>';
  const run=v==='inicio'?inicio(el):DEF[v]?pagina(v,el):Promise.resolve();
  run.catch(e=>{console.error(e);el.innerHTML=`<p class="chw">No se han podido cargar los datos (${esc(e.message)}). Prueba a recargar la página.</p>`})}};
})();
