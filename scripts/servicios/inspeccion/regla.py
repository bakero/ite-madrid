import os
import sys,re
f,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
L=open(os.environ.get('PLIEGOS_TXT','pliegos_txt')+'/'+f,encoding='utf-8',errors='replace').read().split('\n')
seg=[L[i] for i in range(a,b) if L[i].strip()]
o=min(len(l)-len(l.lstrip()) for l in seg) if seg else 0
W=int(sys.argv[4]) if len(sys.argv)>4 else 160
print(f'off={o}  '+''.join(str((o+i)//10%10) if (o+i)%10==0 else ' ' for i in range(W)))
for i in range(a,b):
    if L[i].strip():print(f'{i:5}   '+L[i][o:o+W])
