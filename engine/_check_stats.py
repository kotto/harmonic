import json
d = json.load(open('E:/SAAS - Copie/engine/ka_mobile_stats.json'))
print('Files count:', d['files_count'])
print('Compressed keys:', len(d['compressed']))
print('Total original: %.1f Mo' % (d['total_original_bytes']/1024/1024))
print('Total compressed: %.1f Ko' % (d['total_compressed_bytes']/1024))
# Sample keys
keys = list(d['compressed'].keys())
for i in range(min(5, len(keys))):
    print('  ', keys[i])
# Check relpath
has_relpath = any('/' in k for k in d['compressed']) or any('\\' in k for k in d['compressed'])
print('Has relpath keys:', has_relpath)
# First item
first_key = keys[0]
print('First key:', first_key)
print('First val:', d['compressed'][first_key])