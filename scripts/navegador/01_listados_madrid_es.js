/*
 * 01 · Listados de centros de madrid.es (21 distritos)
 * ----------------------------------------------------
 * Extrae, para cada distrito, los listados «Direcciones y teléfonos» y
 * «Recursos educativos públicos» de www.madrid.es y descarga
 * madrid_listados_21distritos.json  ({dir:{Distrito:{declared,n,items}}, edu:{...}}).
 *
 * Uso: abrir https://www.madrid.es/portales/munimadrid/es/Inicio/El-Ayuntamiento/Distritos/
 *      en el navegador, abrir la consola (F12) y pegar este archivo entero.
 *      Tarda unos minutos. Cada listado se comprueba contra el total que
 *      declara la propia web (campo `declared`).
 *
 * Después: el JSON se convierte en datos/centros_madrid_21_distritos_ITE.xlsx
 * (hoja «Centros + ITE»), que es lo que lee scripts/build_db.py. La clasificación
 * por tipo (CLS, abajo) es la inicial; scripts/reclasificacion.py la corrige.
 */
(async () => {
  const P = new DOMParser();
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const gt = async u => { for (let i = 0; i < 3; i++) { try { return await (await fetch(u)).text(); } catch (e) { await sleep(1500); } } throw new Error('fetch ' + u); };
  const g = async u => P.parseFromString(await gt(u), 'text/html');

  // 1. Portales de distrito
  const d0 = await g('/portales/munimadrid/es/Inicio/El-Ayuntamiento/Distritos/');
  const distritos = [...new Map([...d0.querySelectorAll('a')]
    .map(a => [a.textContent.trim(), a.getAttribute('href')])
    .filter(x => x[1] && /El-Ayuntamiento\/[^/]+\/\?/.test(x[1]))
    .map(x => [x[1], x])).values()];

  // 2. En cada portal, enlaces a «Direcciones y teléfonos» y a «Recursos educativos públicos»
  const DL = {};
  for (const [nombre, href] of distritos) {
    const slug = (href.match(/El-Ayuntamiento\/([^/]+)\//) || [])[1]; if (!slug || slug === 'Distritos') continue;
    const d = await g(href);
    const links = [...d.querySelectorAll('a')].map(a => [a.textContent.trim().replace(/\s+/g, ' '), a.getAttribute('href') || '']);
    const dir = links.find(([t, h]) => /Direcciones-y-telefonos/i.test(h));
    const rec = links.find(([t, h]) => /ecursos-educativos/i.test(h));
    let edu = null;
    if (rec) {
      const dr = await g(rec[1]);
      edu = [...dr.querySelectorAll('a')].map(a => [a.textContent.trim(), a.getAttribute('href') || ''])
        .find(([t, h]) => /ecursos-educativos-de/i.test(h) && /blic/i.test(t + h));
    }
    DL[slug] = { nombre, dir: dir && dir[1], edu: edu && edu[1] };
  }

  // 3. Parser de una página de listado (25 resultados por página)
  const parseList = d => [...d.querySelectorAll('a.event-link')].map(a => {
    const li = a.closest('li') || a.parentElement, loc = li.querySelector('.event-location'), href = a.getAttribute('href');
    return {
      oid: (href.match(/vgnextoid=([0-9a-zA-Z]+)/) || [])[1] || href,
      name: (a.getAttribute('title') || a.textContent).trim().replace(/\s+/g, ' '),
      addr: loc ? loc.getAttribute('data-direction').replace(/\s+,/g, ',').trim() : '',
      phone: loc ? (loc.getAttribute('data-phone') || '') : (li.querySelector('.event-phone')?.textContent.trim() || ''),
      lat: loc?.getAttribute('data-latitude') || '', lon: loc?.getAttribute('data-longitude') || '',
      url: 'https://www.madrid.es' + href
    };
  });
  const total = t => +((t.match(/resultados\s*=\s*'(\d+)'/) || [])[1] || 0);
  const scrapeList = async base => {
    const t0 = await gt(base), declared = total(t0), map = new Map();
    const add = t => parseList(P.parseFromString(t, 'text/html')).forEach(x => map.set(x.oid, x));
    add(t0);
    const urls = []; for (let p = 1; p < Math.ceil(declared / 25); p++) urls.push(base + '&page=' + p);
    for (let r = 0; r < 3 && (r === 0 || map.size < declared); r++)
      for (let i = 0; i < urls.length; i += 4) await Promise.all(urls.slice(i, i + 4).map(async u => add(await gt(u))));
    return { declared: [declared], n: map.size, items: [...map.values()] };
  };

  // 4. Extracción
  const OUT = { dir: {}, edu: {} };
  for (const [k, v] of Object.entries(DL)) {
    if (v.dir) OUT.dir[k] = await scrapeList(new URL(v.dir, location.origin).href);
    if (v.edu) OUT.edu[k] = await scrapeList(new URL(v.edu, location.origin).href);
    console.log(k, OUT.dir[k]?.n, '/', OUT.dir[k]?.declared[0], '· edu', OUT.edu[k]?.n);
  }

  // 5. Descarga
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(OUT)], { type: 'application/json' }));
  a.download = 'madrid_listados_21distritos.json'; a.click();
  window.OUT = OUT;
})();

/* Clasificación inicial por nombre del centro (primera coincidencia gana). */
window.CLS = [
  [/S\.A\.U?\.?|S\.L\.U?\.?|S\.Coop|Sociedad Anónima/i, 'Empresa', 'Empresas / emprendimiento'],
  [/^Sala[s]? de [Ee]studio/i, 'Cultural', 'Sala de estudio'],
  [/^Biblioteca|Biblioteca Pública \(|Servicio de Documentación y Biblioteca/i, 'Cultural', 'Biblioteca'],
  [/^Centro Cultural|^Centro Sociocultural|^Centro Socio ?cultural/i, 'Cultural', 'Centro cultural'],
  [/^Auditorio|^Teatro|^Cine/i, 'Cultural', 'Auditorio / teatro'],
  [/^Museo|^Galería|^Exposici/i, 'Cultural', 'Museo / galería'],
  [/^Casa de Niños|^Escuela Infantil|^Escuela infantil/i, 'Educativo', 'Escuela infantil'],
  [/^Colegio Público|^CEIP|^Colegio de Educación Infantil y Primaria/i, 'Educativo', 'Colegio público (CEIP / CPEE)'],
  [/^Colegio|^Centro de Enseñanza|^Centro Educativo/i, 'Educativo', 'Colegio (no público)'],
  [/^Instituto de Educación Secundaria|^IES/i, 'Educativo', 'Instituto (IES)'],
  [/Escuela Municipal|Educación de Adultos|Centro de Recursos Educativos|Escuelas Infantiles/i, 'Educativo', 'Otros centros formativos'],
  [/CEPA|Escuela Oficial de Idiomas|Escuela Profesional|UFIL|Educación Especial|Escuela de Tiempo Libre|Conservatorio|Escuela de Música|Universidad|Facultad|Escuela de Arte|Escuela Técnica|Formación Profesional|Centro de Formación/i, 'Educativo', 'Otros centros formativos'],
  [/Centro de Día Infantil|Quedamos al salir|QuedaT|Centro Juvenil|Espacio Joven|Ludoteca/i, 'Servicios sociales', 'Infancia y juventud'],
  [/^Centro de Salud|Especialidades|Transfusión|Rehabilitación Psicosocial|Adicciones|CMSc|Menni|^Hospital|^Clínica|Salud Mental|Centro Municipal de Salud|Urgencias(?! Sociales)|Farmacia|SAMUR(?! Social)/i, 'Sanitario', 'Centro sanitario'],
  [/Discapacidad|ASPAYM|CEAPAT|Atención Temprana|ocupacional|lesionado medular|Fundación Carlos Martín|Asociación|Centro Base|Funprodami/i, 'Servicios sociales', 'Discapacidad / asociaciones'],
  [/Residencia|[Mm]ayores|Centro de [Dd]ía|Intergeneracional/i, 'Servicios sociales', 'Mayores / centro de día / residencia'],
  [/Servicios Sociales|Urgencias Sociales|Apoyo a las Familias|Atención a la Infancia|ASPA|Espacio Mujer|Espacio de Igualdad|Violencia de Género|Comedor|Albergue|SAMUR Social|Acogida/i, 'Servicios sociales', 'Servicios sociales'],
  [/Deportiv|^Estadio|^Polideportivo|^Piscina|^Pabellón|Campo de Fútbol|Rocódromo|Golf|Hipódromo/i, 'Deportivo', 'Instalación deportiva'],
  [/^Parque(?! de Bomberos)|^Jardín|^Jardines|^Huerto|^Zona Verde|^Dehesa|^Monte|^Quinta|^Bosque|^Paseo/i, 'Zona verde', 'Parque / jardín'],
  [/^Parroquia|^Iglesia|^Mezquita|^Sinagoga|^Templo|^Capilla|^Ermita|^Basílica|^Catedral|^Monasterio|^Convento|Evangélica/i, 'Religioso', 'Iglesia / templo'],
  [/Comisaría|Policía|Agente Tutor|Bomberos|Guardia Civil|Protección Civil/i, 'Seguridad y emergencias', 'Policía / bomberos'],
  [/^Mercad|Galería Comercial/i, 'Comercio', 'Mercado / mercadillo'],
  [/^Aparcamiento|Intercambiador|Estación|Cercanías|Metro|EMT|Aeropuerto/i, 'Transporte y movilidad', 'Transporte / aparcamiento'],
  [/Junta Municipal|Atención a la Ciudadanía|Agencia de Proximidad|Participación Ciudadana|OMIC|Tarjeta Familia|DNI|Asamblea|Consulado|Embajada|Seguridad Social|Correos|Empleo|Madrid Calle 30|Ayuntamiento|Ministerio|Consejería|Juzgado|Tribunal|Registro|Agencia|Hacienda|Tesorería|Oficina|Notar/i, 'Administración y servicios públicos', 'Oficinas y organismos'],
  [/Punto Limpio|regeneradora|Depuradora|Planta de/i, 'Medio ambiente', 'Punto limpio / instalaciones'],
  [/Vivero de empresas|CREA|Empresa|Coworking/i, 'Empresa', 'Empresas / emprendimiento'],
  [/Cementerio|Tanatorio/i, 'Servicios funerarios', 'Cementerio / tanatorio'],
  [/Hotel|Hostal/i, 'Alojamiento', 'Hotel / hostal'],
  [/Complejo Cultural|Casa del Lector|Danza|Matadero|Sala de lectura|Castillo|Capricho|Palacio|Centro Dotacional|Intermediae|Cultural|Casa de (la )?Cultura|Teatro|Arte/i, 'Cultural', 'Centro cultural / patrimonio'],
  [/CEPI|Inmigrantes|rehabilitación laboral|Integración|Inserción/i, 'Servicios sociales', 'Servicios sociales'],
  [/^Base \d+|SAMUR/i, 'Seguridad y emergencias', 'SAMUR / emergencias'],
  [/Grúa|Depósito de vehículos/i, 'Transporte y movilidad', 'Transporte / aparcamiento'],
  [/Departamento|Dirección General|Servicio|Subdirección|Área de Gobierno|Coordinación|Sección|Unidad|Instituto|Archivo|Información|Cita previa|Disciplina|Negociado|Gerencia|Secretaría|Delegación|Concejalía|Comunidad de Madrid|IFEMA|Institución|Ferial|Inspección/i, 'Administración y servicios públicos', 'Oficinas y organismos'],
  [/^Plaza|Bulevar|Mirador|Fuente/i, 'Zona verde', 'Espacio público'],
  [/Depósito|Residuos/i, 'Medio ambiente', 'Punto limpio / instalaciones']
];
window.cls = n => { for (const [rx, c, s] of CLS) if (rx.test(n)) return [c, s]; return ['Otros', 'Sin clasificar']; };
