import shutil, os
dst = r"e:\SAAS - Copie\ka_phone\www\img"
os.makedirs(dst, exist_ok=True)
src = r"E:\SAAS - Copie\photorealistic_harmonic_system\generated_images\final_results"
files = {
    "photorealistic_batch001_img001.png": "screen_home.png",
    "photorealistic_batch001_img002.png": "screen_chat.png",
    "photorealistic_batch001_img003.png": "screen_camera.png",
    "photorealistic_batch002_img001.png": "screen_calls.png",
    "photorealistic_batch002_img002.png": "screen_system.png",
}
for sn, dn in files.items():
    sp = os.path.join(src, sn)
    dp = os.path.join(dst, dn)
    if os.path.exists(sp):
        shutil.copy2(sp, dp)
        print(f"OK {dn} ({os.path.getsize(dp)//1024} KB)")
    else:
        print(f"MISSING {sp}")