# -*- coding: utf-8 -*-
import re, sys
sys.stdout.reconfigure(encoding='utf-8')
_NUM_RE = r'\d+(?:[.,]\d+)?'
s = 'she eats 3 for breakfast every morning and bakes muffins for her friends every day with 4 eggs'
pat = re.compile(r'every\s+(?:day|morning|night)[^.]*?\b(?:with|using|uses?)\s+(' + _NUM_RE + r')\s+([a-z]+)')
print('pattern:', pat.pattern)
m = pat.search(s)
print('match:', m.groups() if m else None)
pat2 = re.compile(r'(\d+)\s+every\s+(morning|night|day|hour)\b')
print('adjacent:', pat2.search(s))
