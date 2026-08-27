# -*- coding: utf-8 -*-
"""Corrige les apostrophes non échappées dans ka_index.html servi."""
import io

PATH = 'E:/SAAS - Copie/ka-mobile-android/www/ka_index.html'
with io.open(PATH, 'r', encoding='utf-8') as f:
    c = f.read()

# Remplacer TOUTES les chaînes 'Je ne peux pas répondre à ça — ce n'est...' 
# par des chaînes à guillemets doubles
old1 = "return 'Je ne peux pas répondre à ça — ce n'est pas dans ce que je connais.';"
old2 = "return rep || 'Je ne peux pas répondre à ça — ce n'est pas dans ce que je connais.';"
new1 = 'return "Je ne peux pas répondre à ça — ce n\'est pas dans ce que je connais.";'
new2 = 'return rep || "Je ne peux pas répondre à ça — ce n\'est pas dans ce que je connais.";'

n1 = c.count(old1)
n2 = c.count(old2)
c = c.replace(old1, new1).replace(old2, new2)
print(f'Corrigé : {n1 + n2} occurrence(s)')

with io.open(PATH, 'w', encoding='utf-8') as f:
    f.write(c)
