import json

d = json.load(open('E:/SAAS - Copie/engine/ka_mobile_stats.json'))
keys = list(d['compressed'].keys())
print('Total keys:', len(keys))

# Find duplicate basenames
seen = {}
for k in keys:
    # Get basename regardless of path separator
    bn = k.replace('\\', '/').split('/')[-1]
    if bn in seen:
        seen[bn].append(k)
    else:
        seen[bn] = [k]

dups = {bn: ks for bn, ks in seen.items() if len(ks) > 1}
print('Duplicates:', len(dups))
for bn, ks in list(dups.items())[:10]:
    print('  %s:' % bn)
    for k in ks:
        v = d['compressed'][k]
        print('    %s: %dKo -> %dKo (x%.1f)' % (k, v['original_size']//1024, v['compressed_size']//1024, v['ratio']))

# Total unique files
unique = 0
for bn, ks in seen.items():
    # Use largest original_size entry
    best = max(ks, key=lambda k: d['compressed'][k]['original_size'])
    if d['compressed'][best]['original_size'] > 1000:
        unique += 1

print('Unique files (real):', unique)
print('Reported files_count:', d['files_count'])
print('Total original bytes:', d['total_original_bytes']/1024/1024, 'MB')
print('Total compressed bytes:', d['total_compressed_bytes']/1024, 'KB')