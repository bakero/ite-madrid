import os
import sys
f=sys.argv[1];L=open(os.environ.get('PLIEGOS_TXT','pliegos_txt')+'/'+f,encoding='utf-8',errors='replace').read().split('\n')
for a in sys.argv[2:]:
    i,tok=a.split(':',1);l=L[int(i)];j=l.find(tok)
    print(i,tok,'centro=',j+len(tok)/2 if j>=0 else None,'inicio=',j)
