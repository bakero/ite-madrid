#!/bin/bash
# Carga en la BD el volcado de resultados ITE más reciente que haya en Descargas
# (ite_resultados_*.json o el .tmp de una descarga sin confirmar), regenera el
# Excel y app/data.js y deja una copia del volcado en datos/.
set -e
cd "$(dirname "$0")/.."
DL=..
best=""; bestn=0
for f in $(ls -t "$DL"/ite_resultados_*.json "$DL"/*.tmp datos/ite_resultados_*.json 2>/dev/null | head -12); do
  n=$(python3 -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(len(d) if isinstance(d,dict) and all(isinstance(v,list) for v in list(d.values())[:5]) else 0)" "$f" 2>/dev/null || echo 0)
  if [ "$n" -gt "$bestn" ]; then best="$f"; bestn=$n; fi
done
[ -z "$best" ] && { echo "sin volcados"; exit 1; }
stamp=$(date +%Y%m%d_%H%M)
cp "$best" "datos/ite_resultados_$stamp.json"
echo "volcado: $best ($bestn direcciones)"
cp ite_madrid.sqlite /tmp/ite_madrid.sqlite
ITE_DB=/tmp/ite_madrid.sqlite python3 scripts/ingest_export.py "datos/ite_resultados_$stamp.json"
cp /tmp/ite_madrid.sqlite ite_madrid.sqlite
python3 -c "import sqlite3;c=sqlite3.connect('file:ite_madrid.sqlite?mode=ro',uri=True);print('BD: ite',c.execute('select count(*) from ite').fetchone()[0],'centros',c.execute('select count(*) from centros').fetchone()[0])"
