import requests, zipfile, io, os, shutil

os.chdir(os.path.dirname(__file__))

url = 'https://api.github.com/repos/ggerganov/llama.cpp/releases?per_page=3'
r = requests.get(url, timeout=30)
releases = r.json()

target = None
target_tag = ""
for rel in releases:
    for a in rel.get('assets', []):
        name = a['name'].lower()
        if 'win' in name and ('x64' in name or 'amd64' in name) and name.endswith('.zip') and 'cublas' not in name and 'cuda' not in name and 'vulkan' not in name:
            target = a['browser_download_url']
            target_tag = rel['tag_name']
            size_mb = a['size'] / 1024 / 1024
            print(f'FOUND: {target_tag} / {a["name"]} ({size_mb:.0f} Mo)')
            break
    if target:
        break

if not target:
    print("NO BINARY FOUND")
    exit(1)

print(f'Downloading {target[:80]}...')
r = requests.get(target, timeout=300, stream=True)
data = io.BytesIO()
total = 0
for chunk in r.iter_content(8192):
    data.write(chunk)
    total += len(chunk)
print(f'Downloaded {total/1024/1024:.0f} Mo')

data.seek(0)
z = zipfile.ZipFile(data)

exe_files = [f for f in z.filelist if f.filename.lower().endswith('.exe')]
print(f'\nEXE files in archive ({len(exe_files)}):')
for f in exe_files:
    print(f'  {f.filename}')

# Find llama-cli.exe or llama-run.exe or main.exe
priority = ['llama-cli.exe', 'llama-run.exe', 'main.exe', 'llama.exe']
found = None
for p in priority:
    for f in exe_files:
        bn = os.path.basename(f.filename).lower()
        if bn == p.lower():
            found = f
            break
    if found: break

if not found:
    # Take the first small exe
    exe_files.sort(key=lambda x: x.file_size)
    found = exe_files[0]

print(f'\nExtracting: {found.filename}')
z.extract(found, '.')
target_path = os.path.join('.', os.path.basename(found.filename))
if not target_path.lower().endswith('llama-cli.exe'):
    shutil.move(target_path, 'llama-cli.exe')
    print(f'Renamed to llama-cli.exe')
else:
    print(f'OK: {target_path}')

size = os.path.getsize('llama-cli.exe')
print(f'\n✅ llama-cli.exe ready ({size/1024/1024:.1f} Mo)')