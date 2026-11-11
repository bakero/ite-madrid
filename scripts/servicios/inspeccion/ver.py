import os
import sys,re
f,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
L=open(os.environ.get('PLIEGOS_TXT','pliegos_txt')+'/'+f,encoding='utf-8',errors='replace').read().split('\n')
SK=r'Código de verificación|Verificacion|Firmado por|Fecha Firma|URL de Verif|CSV :|munimadrid.es/|Para la verificación'
for i in range(a,min(b,len(L))):
    l=L[i]
    if not l.strip() or re.search(SK,l):continue
    print(i,re.sub(r'\s{3,}',' | ',l.rstrip())[:170])
