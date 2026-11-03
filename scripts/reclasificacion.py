"""Correcciones de la clasificación de centros (tipo / subtipo).

La clasificación inicial se hizo por palabras del nombre del centro y tiene errores.
Cada regla: (ámbito, patrón sobre el nombre normalizado, tipo, subtipo).
  - ámbito: None = cualquier centro; 'Tipo|Subtipo' o 'Tipo|*' = solo centros con esa clasificación ORIGINAL;
            'cat:<texto>' = centros de datos.madrid.es cuya categoría original contiene <texto>.
  - Se aplica la PRIMERA regla que encaje. Los valores originales quedan en tipo_original / subtipo_original.
Se ejecuta en cada exportación (ingest_export.py), así que las correcciones se mantienen.
"""
import re, unicodedata

ADM, OFI = 'Administración y servicios públicos', 'Oficinas y organismos'
INT = 'Organismo internacional'
TUR = 'Información turística'
CUL = 'Cultural'
CC, PAT, FUN, BIB, MUS, AUD, SAL = 'Centro cultural', 'Patrimonio / monumento', 'Fundación / academia', 'Biblioteca / archivo', 'Museo / galería', 'Auditorio / teatro', 'Sala de estudio'
EDU, OTF, CNP, CPU, EI = 'Educativo', 'Otros centros formativos', 'Colegio (no público)', 'Colegio público (CEIP / CPEE)', 'Escuela infantil'
SS, SSG, DIS = 'Servicios sociales', 'Servicios sociales', 'Discapacidad / asociaciones'
SAN, CS = 'Sanitario', 'Centro sanitario'
SEG, POL, MIL = 'Seguridad y emergencias', 'Policía / bomberos / SAMUR', 'Defensa / militar'
DEP, INS = 'Deportivo', 'Instalación deportiva'
EMP, EMPS = 'Empresa', 'Empresas / emprendimiento'
ZV, PJ, EP = 'Zona verde', 'Parque / jardín', 'Espacio público'
MA, PA = 'Medio ambiente', 'Protección animal'
REL, IGL = 'Religioso', 'Iglesia / templo'
COM, MER = 'Comercio', 'Mercado / mercadillo'
OTR, FER = 'Otros', 'Recinto ferial / eventos'
TRA, TRAP = 'Transporte y movilidad', 'Transporte / aparcamiento'

PCC = 'Cultural|Centro cultural / patrimonio'
SIN = 'Otros|Sin clasificar'
RULES = [
    # --- Cultural | Centro cultural / patrimonio: se reparte en centro cultural, patrimonio y fundación/academia
    (PCC, r'SERVICIO DE LIMPIEZA|DIRECCION GENERAL|MINISTERIO', ADM, OFI),
    (PCC, r'AULA DE AGENCIA', ADM, OFI),
    (PCC, r'MOVISTAR ARENA|VISTALEGRE', DEP, INS),
    (PCC, r'IFEMA', OTR, FER),
    (PCC, r'SALA DE LECTURA|ESPACIO DE LECTURA|SALA DE TRABAJO Y LECTURA', CUL, SAL),
    (PCC, r'ACADEMIA DARIO|ARTE DRAMATICO|RESAD|ESCUELA UNIVERSITARIA DE ENFERMERIA|ESCUELA SUPERIOR DE CONSERVACION', EDU, OTF),
    (PCC, r'PUNTO DE INFORMACION TURISTICA', ADM, TUR),
    (PCC, r'PASEO ALBERTO PALACIOS', ZV, EP),
    (PCC, r'CRUZ ROJA', SS, SSG),
    (PCC, r'ARCHIVO', CUL, BIB),
    (PCC, r'PALACIO|CASTILLO|CAPRICHO|FARO DE LA MONCLOA|ESPACIO HOMENAJE|INVERNADERO', CUL, PAT),
    (PCC, r'FUNDACION|REAL ACADEMIA|CIRCULO DE BELLAS ARTES|CASA SAN CRISTOBAL', CUL, FUN),
    (PCC, r'.', CUL, CC),
    # --- Biblioteca pasa a llamarse Biblioteca / archivo
    ('Cultural|Biblioteca', r'.', CUL, BIB),
    # --- errores en otras categorías
    (None, r'^(?!MUSEO).*REAL ACADEMIA', CUL, FUN),
    ('Sanitario|*', r'PARROQUIA', REL, IGL),
    ('Sanitario|*', r'SUBDIRECCION GENERAL DE SAMUR', SEG, POL),
    ('Administración y servicios públicos|*', r'ARCHIVO', CUL, BIB),
    ('Administración y servicios públicos|*', r'IFEMA|RECINTO FERIAL', OTR, FER),
    ('Administración y servicios públicos|*', r'INSTITUCION PROFESIONAL SALESIANA', EDU, OTF),
    ('Administración y servicios públicos|*', r'CRUZ ROJA', SS, SSG),
    ('Administración y servicios públicos|*', r'ORGANIZACION (INTERNACIONAL|DE LAS NACIONES|DE ESTADOS|IBEROAMERICANA)|\(FAO\)|\(OIT\)|\(OIM\)', ADM, INT),
    ('Empresa|*', r'HOSPITAL|CLINICA', SAN, CS),
    ('Empresa|*', r'ESCUELA INFANTIL', EDU, EI),
    ('Empresa|*', r'MATADERO', CUL, CC),
    ('Empresa|*', r'AREA DELEGADA|AREA DE ESPECTACULOS', ADM, OFI),
    ('Empresa|*', r'MUJERES VICTIMAS', SS, SSG),
    ('Empresa|*', r'FUNDACION', CUL, FUN),
    ('Empresa|*', r'\(ITV', TRA, TRAP),
    ('Medio ambiente|*', r'DEPOSITO LEGAL', ADM, OFI),
    ('Educativo|Escuela infantil', r'^COLEGIO', EDU, CNP),
    ('Servicios sociales|*', r'DIRECCION GENERAL DE VIVIENDA|CITA PREVIA', ADM, OFI),
    ('Servicios sociales|*', r'INSTITUTO PROVINCIAL DE REHABILITACION', SAN, CS),
    ('Deportivo|*', r'COMITE OLIMPICO', ADM, OFI),
    ('Educativo|Otros centros formativos', r'CENTRO SOCIOCULTURAL', CUL, CC),
    ('Educativo|Otros centros formativos', r'^PARQUE', ZV, PJ),
    ('Educativo|Otros centros formativos', r'^PLAZA', ZV, EP),
    ('cat:Parques Jardines', r'.', ZV, PJ),
    ('cat:Centros Culturales', r'.', CUL, CC),
    # --- Otros | Sin clasificar
    (SIN, r'AREA DELEGADA DE DEPORTE', ADM, OFI),
    (SIN, r'URIA MENENDEZ|DELOITTE|CLIFFORD CHANCE', EMP, EMPS),
    (SIN, r'PLANETARIO|CAIXAFORUM|MUSEO|SALAS? DE EXPOSICIONES|SALA ALCALA 31|REAL FABRICA DE TAPICES|CASA DE LA MONEDA|CASON DEL BUEN RETIRO', CUL, MUS),
    (SIN, r'FILMOTECA|CINE DORE|TEMPLETE|ESCENARIO PUERTA', CUL, AUD),
    (SIN, r'HEMEROTECA|REAL BIBLIOTECA|DOCUMENTACION|ARCHIV|GESTION DEL CONOCIMIENTO', CUL, BIB),
    (SIN, r'PANTEON|VIAJE DE AGUA|REAL OBSERVATORIO|BETI JAI|CASA DE LA PANADERIA', CUL, PAT),
    (SIN, r'CENTRO DE CULTURA CONTEMPORANEA|ATENEO|CASA ASIA|CASA DE AMERICA|CASA ARABE|CASA DE MEXICO|CENTRO SEFARAD|CASA DE VELAZQUEZ|SOCIEDAD CERVANTINA|TALLER NUEVO|NAVE DE MOTORES|^LA NAVE$|GARAJE|ESPIRITU23|CLUB INTERNACIONAL DE PRENSA|ENSAYO|BANDA SINFONICA|MADRID IN GAME|SILO DE HORTALEZA', CUL, CC),
    (SIN, r'REAL BASILICA|ORATORIO|SANTUARIO|PARROQUIA|ARZOBISPADO|CONCEPCION REAL DE CALATRAVA', REL, IGL),
    (SIN, r'AULA DE ESTUDIO', CUL, SAL),
    (SIN, r'ABC SCHULE|COLEGIO INTERNACIONAL|ESCUELA IDEO', EDU, CNP),
    (SIN, r'^CEE ', EDU, CPU),
    (SIN, r'ESCUELA|AULA MUNICIPAL DE FORMACION|CENTRO INTEGRADO|ENSENANZAS|CENTRO DE ESTUDIOS (CASTILLA|GONZALEZ|DIAZ)|CENTRO UNIVERSITARIO|UEIA|MOVISTAR ACADEMY|AULA CELEBRACION|EUROPA JOVEN|SIETE ESTRELLAS', EDU, OTF),
    (SIN, r'NACIONES UNIDAS|ONU |BANCO (INTERAMERICANO|EUROPEO)|CORPORACION ANDINA|PROGRAMA MUNDIAL|ORGANISMO INTERNACIONAL|UNION DE CIUDADES', ADM, INT),
    (SIN, r'CONGRESO|SENADO|DEFENSOR DEL PUEBLO|FISCALIA|JUNTA ARBITRAL|JUNTA ELECTORAL|CONCEJALES|AREA DELEGADA|CAJA MUNICIPAL|JEFATURA PROVINCIAL DE TRAFICO|CANAL DE ISABEL II|CONSORCIO|ALMACEN DE VILLA|ACUSTICA|DIVISION DE VERTIDOS|CALIDAD DEL AIRE|CONTROL DEL RIO|FILM OFFICE|CONVENTION BUREAU|INFOEUROPEA|OBSERVATORIO REGIONAL|ACREDITACION|INVESTIGACIONES SOCIOLOGICAS|ESTUDIOS POLITICOS|FABRICA NACIONAL|CIEMAT|PREVENCION DE RIESGOS LABORALES', ADM, OFI),
    (SIN, r'CENTRO DE TURISMO', ADM, TUR),
    (SIN, r'AUTISMO|PARKINSON|PSICO - BALLET|DETERIORO COGNITIVO|NEUROCOGNITIVA', SS, DIS),
    (SIN, r'LABORATORIO|DIAGNOSTICO|SANATORIO|MD ANDERSON|PATOLOGIA DUAL|DONACION DE SANGRE|NEUROCIENCIA', SAN, CS),
    (SIN, r'CENTRO DE ATENCION|ENCUENTRO FAMILIAR|CENTRO SOCIAL|COMUNITARIO|SOCIO COMUNITARIO|EMIGRANTES|EXTRANJERO|MIGRACIONES|HIJAS DE LA CARIDAD|ASOCIACIONES FAMILIARES|PLATAFORMA DE ORGANIZACIONES|COORDINADORA DE ORGANIZACIONES|PAZ Y COOPERACION|CENTRO BELMONTE|CENTRO SANDOVAL|NORTE JOVEN|NUMEN|RESHOGAR|EMERGENCIA TEMPORAL|CASA DE BANOS|POLIVALENTE', SS, SSG),
    (SIN, r'BASE AEREA', SEG, MIL),
    (SIN, r'CIFSE', SEG, POL),
    (SIN, r'CLUB DE CAMPO|CIUDAD DE LA RAQUETA|CENTRO DE NATACION|CAJA MAGICA', DEP, INS),
    (SIN, r'PROTECCION ANIMAL|COLONIAS FELINAS', MA, PA),
    (SIN, r'GRAN VIA DE VILLAVERDE', ZV, EP),
    (SIN, r'ZOO|LAGO DE LA CASA DE CAMPO|VIVERO|PINAR|AREA FORESTAL|AULA AMBIENTAL', ZV, PJ),
    (SIN, r'CUESTA DE MOYANO', COM, MER),
    (SIN, r'IMPACT HUB|UTOPIC|TETUAN VALLEY|TOP SEEDS|PUERTA INNOVACION|INTERNATIONAL LAB|UNLTD|COOP57|COOPERATIVA|BAN MADRI|S\.?G\.?R|AVALMADRID|ELKARGI|IBERAVAL|MOMENTUM|MICRODONACIONES|FACTORIA INDUSTRIAL|INNOVACION EN ECONOMIA|VIVERISMO|BOLSA DE MADRID|OBRA SOCIAL|SUBASTAS|QUINTA COCINA|ESCUELA DE COMPETENCIAS|VENTURE LAB|^PUE$', EMP, EMPS),
]

def N(s):
    s = unicodedata.normalize('NFD', str(s or '').upper())
    return ' '.join(''.join(c for c in s if unicodedata.category(c) != 'Mn').split())

def clasificar(nombre, tipo0, sub0, cat0):
    n = N(nombre)
    for amb, pat, t, s in RULES:
        if amb is not None:
            if amb.startswith('cat:'):
                if amb[4:] not in (cat0 or ''):
                    continue
            else:
                at, asub = amb.split('|')
                if at != tipo0 or (asub != '*' and asub != sub0):
                    continue
        if re.search(pat, n):
            return t, s
    return tipo0, sub0

def aplicar(con):
    cols = [r[1] for r in con.execute('PRAGMA table_info(centros)')]
    for c in ('tipo_original', 'subtipo_original'):
        if c not in cols:
            con.execute(f'ALTER TABLE centros ADD COLUMN {c} TEXT')
    con.execute('UPDATE centros SET tipo_original=tipo_edificio, subtipo_original=subtipo WHERE tipo_original IS NULL')
    n = 0
    for cid, nom, t0, s0, cat in con.execute('SELECT id, nombre, tipo_original, subtipo_original, categoria_origen FROM centros').fetchall():
        t, s = clasificar(nom, t0, s0, cat)
        con.execute('UPDATE centros SET tipo_edificio=?, subtipo=? WHERE id=?', (t, s, cid))
        n += (t, s) != (t0, s0)
    con.commit()
    print('reclasificados respecto a la clasificación original:', n)
