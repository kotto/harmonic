#!/usr/bin/env python3
import sys
path = sys.argv[1] if len(sys.argv)>1 else r'e:\SAAS - Copie\ka_phone\ka_next_core.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('\u2500','-').replace('\u23f1','T').replace('\u2502','|')
c = c.replace('\u2713','OK').replace('\u2717','KO').replace('\U0001f3a8','[A]')
c = c.replace('\U0001f310','[W]').replace('\U0001f4dd','[S]')
with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed encoding in', path)