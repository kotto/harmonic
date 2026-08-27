# -*- coding: utf-8 -*-
"""Applique le design compress.html au ka_index.html servi."""
import io

path = 'E:/SAAS - Copie/ka-mobile-android/www/ka_index.html'
with io.open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ── PATCH 1 : HTML s-demo ──
old_start = content.find('<!-- ═══ DÉMO « LE CHOC »')
old_end = content.find('<!-- ═══ ONBOARDING ═══')
if old_start == -1 or old_end == -1:
    print('ERREUR: sections demo HTML introuvables')
else:
    new_demo = open('E:/SAAS - Copie/engine/patch_sdemo.html', 'r', encoding='utf-8').read()
    content = content[:old_start] + new_demo + content[old_end:]
    print('OK PATCH 1')

# ── PATCH 2 : fonctions demo JS ──
js_start = content.find('// ═══ DÉMO « LE CHOC »')
if js_start == -1:
    js_start = content.find('function demoArithmetic()')
    if js_start != -1:
        js_start = content.rfind('\n', 0, js_start) + 1
if js_start == -1:
    print('ERREUR: fonctions demo JS introuvables')
else:
    js_end = content.find('function demoDone()')
    if js_end == -1:
        print('ERREUR: demoDone introuvable')
    else:
        brace = content.find('}', content.find('\n', js_end))
        js_end = brace + 1
        while js_end < len(content) and content[js_end] in ' \n':
            js_end += 1
        new_js = open('E:/SAAS - Copie/engine/patch_demojs.txt', 'r', encoding='utf-8').read()
        content = content[:js_start] + new_js + content[js_end:]
        print('OK PATCH 2')

# ── PATCH 3 : storage conversationnel ──
if 'function proposeStorageScan' not in content:
    storage_js = open('E:/SAAS - Copie/engine/patch_storagejs.txt', 'r', encoding='utf-8').read()
    insert_at = content.find('// Service Worker')
    if insert_at == -1:
        insert_at = content.find('</script>')
    content = content[:insert_at] + storage_js + '\n' + content[insert_at:]
    print('OK PATCH 3')

with io.open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('FICHIER ECRIT')
