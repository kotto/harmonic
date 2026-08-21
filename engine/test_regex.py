import re

q = 'josh decides to try flipping a house. he buys a house for $80,000 and then puts in $50,000 in repairs. this increased the value of the house by 150%. how much profit did he make?'

# Test each part properly
m = re.search(r'(?:buys?|achète|bought).*?(?:for|pour)\s*[\$€]?\s*([\d,]+(?:\.\d+)?)', q)
print('Buy:', m)
if m: print(m.group(1))

m = re.search(r'puts? in.*?\$?([\d,]+)', q)
print('Puts in:', m)
if m: print(m.group(1))

m = re.search(r'(?:puts? in|investit|repairs?|réparations?)\s*[\$€]?\s*([\d,]+(?:\.\d+)?)', q)
print('Repairs:', m)
if m: print(m.group(1))

m = re.search(r'increased.*?by\s+(\d+(?:[.,]\d+)?)\s*%', q)
print('Increased:', m)
if m: print(m.group(1))

# Full pattern - escape the $ properly
pattern = r'(?:buys?|achète|bought).*?(?:for|pour)\s*[\$€]?\s*([\d,]+(?:\.\d+)?).*?' \
          r'(?:puts? in|investit|repairs?|réparations?)\s*[\$€]?\s*([\d,]+(?:\.\d+)?).*?' \
          r'(?:increased?|augmenté?|increase).*?(?:value|valeur).*?by\s+' \
          r'(\d+(?:[.,]\d+)?)\s*%'
m = re.search(pattern, q)
print('Full:', m)
if m: print(m.groups())