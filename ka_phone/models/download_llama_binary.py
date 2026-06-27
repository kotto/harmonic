import requests, zipfile, io, os, shutil, json

os.chdir(os.path.dirname(__file__))

# Get exact release asset URL from latest llama.cpp release
print("Recherche du binaire Windows llama.cpp...")
api_url = 'https://api.github.com/repos/ggerganov/llama.cpp/releases?per_page=10'
r = requests.get(api_url, timeout=30)
releases = r.json()

target_url = None
for rel in releases:
    for a in rel.get('assets', []):
        name = a['name'].lower()
        # Chercher un binaire Windows x64 CPU-only (pas CUDA, pas Vulkan)
        if ('win' in name and 'x64' in name and name.endswith('.zip')
            and 'cublas' not in name and 'cuda' not in name
            and 'vulkan' not in name and 'sycl' not in name
            and 'kompute' not in name):
            target_url = a['browser_download_url']
            print(f"Trouve: {rel['tag_name']} / {a['name']} ({a['size']/1024/1024:.0f} Mo)")
            break
    if target_url:
        break

if not target_url:
    print("ERREUR: Aucun binaire Windows CPU trouve")
    exit(1)

print(f"Telechargement...")
r = requests.get(target_url, timeout=120, stream=True)
data = io.BytesIO()
total = 0
for chunk in r.iter_content(65536):
    data.write(chunk)
    total += len(chunk)
print(f"Telecharge: {total/1024/1024:.0f} Mo")

data.seek(0)
z = zipfile.ZipFile(data)

# Lister tous les exe
exe_files = [f for f in z.filelist if f.filename.lower().endswith('.exe')]
print(f"\nFichiers EXE trouves ({len(exe_files)}):")
for f in exe_files:
    print(f"  {f.filename} ({f.file_size} bytes)")

# Priorite de recherche
priority = ['llama-cli.exe', 'llama-run.exe', 'main.exe', 'llama.exe']
found = None
for p in priority:
    for f in exe_files:
        if os.path.basename(f.filename).lower() == p.lower():
            found = f
            break
    if found: break

if not found and exe_files:
    exe_files.sort(key=lambda x: x.file_size)
    for f in exe_files:
        bn = os.path.basename(f.filename).lower()
        if 'llama' in bn:
            found = f
            break
    if not found:
        found = exe_files[0]

if not found:
    print("ERREUR: Aucun EXE trouve dans l'archive")
    # Extraire tous les fichiers pour debug
    for f in z.filelist[:50]:
        print(f"  {f.filename}")
    exit(1)

print(f"\nExtraction de: {found.filename}")
z.extract(found, '.')
extracted = os.path.join('.', os.path.basename(found.filename))

# Renommer en llama-cli.exe
target_path = os.path.join('.', 'llama-cli.exe')
if os.path.exists(target_path):
    os.remove(target_path)
if extracted.lower() != target_path.lower():
    shutil.move(extracted, target_path)
    print(f"Renomme en llama-cli.exe")
else:
    print(f"OK: {target_path}")

size_mb = os.path.getsize(target_path) / 1024 / 1024
print(f"\n✅ SUCCES: llama-cli.exe ({size_mb:.1f} Mo)")