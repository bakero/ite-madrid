"""Coordenadas añadidas a mano para direcciones sin coordenadas en madrid.es / datos.madrid.es.
Geocodificadas con CartoCiudad (IGN, www.cartociudad.es), solo coincidencias exactas de vía y número
de portal (en dos casos el código postal de CartoCiudad difiere del de madrid.es; se anota en 'nota'). Uso: ITE_DB=... python3 scripts/coordenadas_manual.py
"""
import os, sqlite3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get('ITE_DB', os.path.join(ROOT, 'ite_madrid.sqlite'))
C = 'CartoCiudad (portal)'
DATA = [
    ('CALLE LUIS CABRERA 63, MADRID', 40.444405, -3.672409, C, 'CALLE LUIS CABRERA 63, 28002'),
    ('Calle Francisco Tomás y Valiente 3, MADRID', 40.54451, -3.697775, C, 'CALLE FRANCISCO TOMAS Y VALIENTE 3, 28049'),
    ('CALLE FRANCISCO TOMAS Y VALIENTE 3,  MADRID', 40.54451, -3.697775, C, 'CALLE FRANCISCO TOMAS Y VALIENTE 3, 28049'),
    ('CARRETERA COLMENAR VIEJO 16, 28048 MADRID', 40.53282, -3.782251, C, 'CARRETERA EL PARDO A COLMENAR VIEJO 16, 28048 (nombre de vía distinto, mismo CP)'),
    ('CARRETERA SOMONTES AL PALACIO DE LA REAL QUINTA 1, 28035 MADRID', 40.490446, -3.754526, C, 'portal 1, CP 28048 en CartoCiudad (28035 en madrid.es)'),
    ('CALLE ANTONIO LÓPEZ TORRES 5, 28042 MADRID', 40.475533, -3.62835, C, 'CALLE ANTONIO LOPEZ TORRES 5, 28055 en CartoCiudad (28042 en madrid.es)'),
    ('CALLE MARÍA DE LAS MERCEDES DE BORBÓN 186, 28055 MADRID', 40.493656, -3.617484, C, 'CALLE MARIA DE LAS MERCEDES DE BORBON 186, 28055'),
    ('AVENIDA RAFAEL ALBERTI 9, 28038 MADRID', 40.391215, -3.637759, C, 'AVENIDA RAFAEL ALBERTI 9, 28038'),
]
con = sqlite3.connect(DB)
con.execute('CREATE TABLE IF NOT EXISTS coordenadas_manual(direccion TEXT PRIMARY KEY, lat REAL, lng REAL, fuente TEXT, nota TEXT)')
con.executemany('INSERT OR REPLACE INTO coordenadas_manual VALUES(?,?,?,?,?)', DATA)
con.commit(); print('coordenadas_manual:', con.execute('SELECT count(*) FROM coordenadas_manual').fetchone()[0])
