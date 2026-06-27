#!/usr/bin/env python3
"""
HCS Studio - Benchmark de Performance Complet
Tests: Compression image/video, Decompression, Upscaling image/video
"""
import sys, os, time, json, io, struct, zipfile
import numpy as np
from PIL import Image
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PARENT_DIR)

G="\033[92m"; Y="\033[93m"; R="\033[91m"; C="\033[96m"; B="\033[1m"; E="\033[0m"
def ok(m):   print(f"{G}  [OK] {m}{E}")
def warn(m): print(f"{Y}  [!!] {m}{E}")
def err(m):  print(f"{R}  [KO] {m}{E}")
def hdr(m):  print(f"\n{B}{C}{'='*65}\n  {m}\n{'='*65}{E}")
def row(l,v):print(f"    {l:<38} {B}{v}{E}")

# === Import modules HCS ===
HC=False; KE=False; WO=False; QH=False; HU=False; CV=False

try:
    import cv2; CV=True
except: pass

try:
    from core.hybrid_compressor import HybridCompressor; HC=True
    ok("HybridCompressor importe")
except Exception as e: warn(f"HybridCompressor: {e}")

try:
    from core.k_factor_engine import KFactorEngine; KE=True
except Exception as e: warn(f"KFactorEngine: {e}")

try:
    from core.webp_optimizer import WebPOptimizer; WO=True
except Exception as e: warn(f"WebPOptimizer: {e}")

try:
    from core.quantum_harmonic_compressor import QuantumHarmonicCompressor; QH=True
    ok("QuantumHarmonicCompressor importe")
except Exception as e: warn(f"QHCompressor: {e}")

try:
    from core.harmonic_upscaler import harmonic_upscaler_api; HU=True
    ok("HarmonicUpscalerAPI importe")
except Exception as e: warn(f"HarmonicUpscaler: {e}")

# === Utilitaires ===
HCS_MAGIC = b"HCS\x02"

def make_image(w, h, mode="natural"):
    if mode=="gradient":
        xx,yy=np.meshgrid(np.linspace(0,1,w),np.linspace(0,1,h))
        return np.stack([xx,yy,1-xx*yy],2).astype(np.float32)
    elif mode=="uniform":
        return np.ones((h,w,3),np.float32)*0.5
    elif mode=="noise":
        return np.random.rand(h,w,3).astype(np.float32)
    else:
        base=np.random.rand(h,w,3).astype(np.float32)*0.5+0.25
        for _ in range(5):
            y1,x1=np.random.randint(0,h),np.random.randint(0,w)
            y2,x2=np.random.randint(y1,h),np.random.randint(x1,w)
            base[y1:y2,x1:x2]=np.random.rand(3).astype(np.float32)
        return np.clip(base,0,1)

def make_video(n, w, h):
    frames=[]
    for i in range(n):
        t=i/n
        f=np.random.rand(h,w,3).astype(np.float32)*0.3
        f+=np.array([0.3+0.4*np.sin(t*np.pi*2),0.3+0.3*np.cos(t*np.pi),0.5],np.float32)
        frames.append(np.clip(f,0,1))
    return frames

def calc_psnr(a, b):
    af=a.astype(np.float32)*(255 if a.max()<=1 else 1)
    bf=b.astype(np.float32)*(255 if b.max()<=1 else 1)
    mse=np.mean((af-bf)**2)
    return 100.0 if mse==0 else float(20*np.log10(255/np.sqrt(mse)))

def fmtb(n):
    if n>=1<<30: return f"{n/(1<<30):.2f} GB"
    if n>=1<<20: return f"{n/(1<<20):.2f} MB"
    if n>=1<<10: return f"{n/(1<<10):.2f} KB"
    return f"{n} B"

def make_hcs(webp_bytes, orig_shape, k_shape, k_factor, meta):
    import json as _j
    m=_j.dumps({"orig":list(orig_shape),"ks":list(k_shape),"kf":k_factor,"m":meta}).encode()
    return HCS_MAGIC+struct.pack("<I",len(m))+m+webp_bytes

def read_hcs(data):
    import json as _j
    assert data[:4]==HCS_MAGIC,"bad magic"
    ml=struct.unpack("<I",data[4:8])[0]
    meta=_j.loads(data[8:8+ml])
    return meta,data[8+ml:]

# ============================================================
# 1. COMPRESSION IMAGE
# ============================================================
def bench_compress_image():
    hdr("1. BENCHMARK COMPRESSION IMAGE")
    results=[]
    cfgs=[
        ("Petit 320x240",   320,  240, "natural"),
        ("Moyen 640x480",   640,  480, "natural"),
        ("HD 1280x720",    1280,  720, "gradient"),
        ("FHD 1920x1080", 1920, 1080, "natural"),
        ("Uniforme 640x480",640,  480, "uniform"),
        ("Bruit 640x480",   640,  480, "noise"),
    ]
    if HC:
        comp=HybridCompressor(k_factor=0.02,webp_quality=95)
    elif KE and WO:
        ke=KFactorEngine(0.02); wo=WebPOptimizer(95)

    for name,w,h,mode in cfgs:
        img=make_image(w,h,mode)
        ob=img.nbytes
        t0=time.perf_counter()
        try:
            if HC:
                cdata,meta=comp.compress_image(img)
                kr=meta.get("k_ratio",1); wr=meta.get("webp_ratio",1); hr=meta.get("hybrid_ratio",1)
                ks=meta.get("k_compressed_shape",img.shape)
                hcs=make_hcs(cdata,img.shape,ks,0.02,{"kr":kr,"wr":wr,"hr":hr})
            elif KE and WO:
                ka,km=ke.compress_image(img); cdata,wm=wo.optimize_image(ka)
                kr=km["actual_ratio"]; wr=wm["compression_ratio"]; hr=kr*wr
                hcs=make_hcs(cdata,img.shape,ka.shape,0.02,{"kr":kr,"wr":wr,"hr":hr})
            else:
                buf=io.BytesIO(); Image.fromarray((img*255).astype("uint8")).save(buf,"WEBP",quality=85)
                cdata=buf.getvalue(); kr=1; wr=ob/len(cdata); hr=wr; hcs=cdata
            el=time.perf_counter()-t0
            sp=(1-len(cdata)/ob)*100
            ok(f"{name} ({w}x{h})")
            row("Taille originale",fmtb(ob))
            row("Archive HCS",fmtb(len(hcs)))
            row("Payload WebP",fmtb(len(cdata)))
            row("Ratio K-factor",f"{kr:.1f}:1")
            row("Ratio WebP",f"{wr:.1f}:1")
            row("Ratio HYBRIDE TOTAL",f"{hr:.1f}:1")
            row("Espace economise",f"{sp:.1f}%")
            row("Temps",f"{el*1000:.1f} ms")
            results.append({"name":name,"ob":ob,"hb":len(hcs),"hr":hr,"sp":sp,"ms":el*1000,
                            "hcs":hcs,"img":img})
        except Exception as e:
            err(f"{name}: {e}"); import traceback; traceback.print_exc()
            results.append({"name":name,"error":str(e)})
    return results

# ============================================================
# 2. COMPRESSION VIDEO
# ============================================================
def bench_compress_video():
    hdr("2. BENCHMARK COMPRESSION VIDEO/AUDIO")
    results=[]
    cfgs=[
        ("SD 30f 320x240",  320, 240,  30),
        ("SD 90f 320x240",  320, 240,  90),
        ("HD 30f 640x480",  640, 480,  30),
        ("HD 60f 1280x720",1280, 720,  60),
    ]
    if HC:
        comp=HybridCompressor(k_factor=0.02,webp_quality=85)

    for name,w,h,nf in cfgs:
        frames=make_video(nf,w,h)
        ot=sum(f.nbytes for f in frames)
        print(f"\n  {name}: {nf} frames / {fmtb(ot)}")
        t0=time.perf_counter(); cframes=[]; ratios=[]; ftimes=[]

        for frame in frames:
            tf=time.perf_counter()
            try:
                if HC:
                    cd,m=comp.compress_image(frame); r=m.get("hybrid_ratio",1)
                elif KE and WO:
                    ka,_=KFactorEngine(0.02).compress_image(frame)
                    cd,wm=WebPOptimizer(85).optimize_image(ka); r=frame.nbytes/len(cd)
                else:
                    buf=io.BytesIO(); Image.fromarray((frame*255).astype("uint8")).save(buf,"WEBP",quality=85)
                    cd=buf.getvalue(); r=frame.nbytes/len(cd)
                cframes.append(cd); ratios.append(r)
            except:
                cframes.append(b""); ratios.append(1)
            ftimes.append((time.perf_counter()-tf)*1000)

        el=time.perf_counter()-t0
        zbuf=io.BytesIO()
        with zipfile.ZipFile(zbuf,"w",zipfile.ZIP_STORED) as zf:
            zf.writestr("meta.json",json.dumps({"f":nf,"w":w,"h":h,"codec":"hcs-hybrid"}))
            for i,cd in enumerate(cframes): zf.writestr(f"frame_{i:06d}.webp",cd)
        zs=len(zbuf.getvalue())
        ar=float(np.mean(ratios)); rr=ot/zs; fps=nf/el

        ok(f"{name}")
        row("Taille originale brute",fmtb(ot))
        row("Archive HCS-ZIP",fmtb(zs))
        row("Ratio moyen/frame",f"{ar:.1f}:1")
        row("Ratio archive global",f"{rr:.1f}:1")
        row("Espace economise",f"{(1-zs/ot)*100:.1f}%")
        row("FPS compressions",f"{fps:.1f}")
        row("Temps moyen/frame",f"{float(np.mean(ftimes)):.1f} ms")
        results.append({"name":name,"nf":nf,"ot":ot,"zs":zs,"ar":ar,"rr":rr,"fps":fps,
                        "zip":zbuf.getvalue(),"frames":frames})
    return results

# ============================================================
# 3. DECOMPRESSION IMAGE
# ============================================================
def bench_decomp_image(comp_res):
    hdr("3. BENCHMARK DECOMPRESSION IMAGE")
    results=[]
    for r in comp_res:
        if "error" in r: warn(f'{r["name"]}: skip (compression failed)'); continue
        hcs=r.get("hcs"); img=r.get("img")
        if hcs is None: warn(f'{r["name"]}: no HCS data'); continue
        t0=time.perf_counter()
        try:
            if hcs[:4]==HCS_MAGIC:
                meta,wb=read_hcs(hcs)
                os2=tuple(meta["orig"])
            else:
                wb=hcs; os2=img.shape
            pil_k=Image.open(io.BytesIO(wb)); k_arr=np.array(pil_k)
            th,tw=os2[0],os2[1]
            if k_arr.shape[0]!=th or k_arr.shape[1]!=tw:
                pil_k=pil_k.resize((tw,th),Image.Resampling.LANCZOS); k_arr=np.array(pil_k)
            dec=k_arr.astype(np.float32)/255.0
            if dec.ndim==2: dec=np.stack([dec]*3,2)
            elif dec.shape[2]==4: dec=dec[:,:,:3]
            el=time.perf_counter()-t0
            pv=calc_psnr(img,dec)
            hr=r.get("hr",0)
            ok(f'{r["name"]}')
            row("Ratio compresse",f"{hr:.1f}:1")
            row("Shape orig->decomp",f"{img.shape}->{dec.shape}")
            row("PSNR reconstruit",f"{pv:.2f} dB")
            row("Temps decompression",f"{el*1000:.1f} ms")
            results.append({"name":r["name"],"psnr":pv,"ms":el*1000,"hr":hr})
        except Exception as e:
            err(f'{r["name"]}: {e}'); import traceback; traceback.print_exc()
            results.append({"name":r["name"],"error":str(e)})
    return results

# ============================================================
# 4. DECOMPRESSION VIDEO
# ============================================================
def bench_decomp_video(vid_res):
    hdr("4. BENCHMARK DECOMPRESSION VIDEO")
    results=[]
    for r in vid_res:
        zdata=r.get("zip"); frames=r.get("frames",[])
        if zdata is None: warn(f'{r["name"]}: no zip'); continue
        t0=time.perf_counter(); dframes=[]; psnrs=[]
        try:
            with zipfile.ZipFile(io.BytesIO(zdata),"r") as zf:
                names=sorted(n for n in zf.namelist() if n.endswith(".webp"))
                for i,n in enumerate(names):
                    pil_f=Image.open(io.BytesIO(zf.read(n)))
                    fa=np.array(pil_f).astype(np.float32)/255.0
                    if fa.ndim==2: fa=np.stack([fa]*3,2)
                    dframes.append(fa)
                    if i<len(frames) and fa.shape==frames[i].shape:
                        psnrs.append(calc_psnr(frames[i],fa))
            el=time.perf_counter()-t0
            fps=len(dframes)/el; ap=float(np.mean(psnrs)) if psnrs else 0
            ok(f'{r["name"]} - {len(dframes)} frames')
            row("FPS decompression",f"{fps:.1f}")
            row("Temps total",f"{el*1000:.0f} ms")
            row("PSNR moyen frames",f"{ap:.2f} dB")
            row("Ratio archive",f'{r.get("rr",0):.1f}:1')
            results.append({"name":r["name"],"fps":fps,"ms":el*1000,"psnr":ap})
        except Exception as e:
            err(f'{r["name"]}: {e}'); results.append({"name":r["name"],"error":str(e)})
    return results

# ============================================================
# 5. UPSCALING IMAGE
# ============================================================
def bench_upscale_image():
    hdr("5. BENCHMARK UPSCALING IMAGE")
    results=[]
    cfgs=[
        ("SD 320x240 -> 2x",  320,  240, 2.0),
        ("SD 320x240 -> 4x",  320,  240, 4.0),
        ("HD 640x480 -> 2x",  640,  480, 2.0),
        ("HD 640x480 -> 4x",  640,  480, 4.0),
        ("FHD 1280x720 -> 2x",1280,  720, 2.0),
    ]
    for name,w,h,factor in cfgs:
        img=make_image(w,h,"natural")
        u8=(img*255).astype("uint8")
        tw,th=int(w*factor),int(h*factor)
        t0=time.perf_counter(); method="LANCZOS"; pv=0; sv=0
        try:
            if HU:
                res=harmonic_upscaler_api.upscale_image(u8,factor=f"{int(factor)}x",energy_level="standard")
                if res.get("success"):
                    import base64
                    up=np.array(Image.open(io.BytesIO(base64.b64decode(res["upscaled_image_base64"]))))
                    method="HarmonicUpscaler"
                    qm=res.get("quality_metrics",{})
                    pv=qm.get("psnr",0); sv=qm.get("ssim",0)
                else:
                    up=np.array(Image.fromarray(u8).resize((tw,th),Image.Resampling.LANCZOS))
            else:
                up=np.array(Image.fromarray(u8).resize((tw,th),Image.Resampling.LANCZOS))
            el=time.perf_counter()-t0
            ok(f"{name} [{method}]")
            row("Shape avant->apres",f"{img.shape}->{up.shape}")
            row("Facteur surface",f"{(tw*th)/(w*h):.1f}x")
            row("Temps",f"{el*1000:.1f} ms")
            if pv: row("PSNR",f"{pv:.2f} dB"); row("SSIM",f"{sv:.3f}")
            results.append({"name":name,"method":method,"factor":factor,
                            "ms":el*1000,"shape":up.shape,"psnr":pv,"ssim":sv})
        except Exception as e:
            err(f"{name}: {e}"); import traceback; traceback.print_exc()
            results.append({"name":name,"error":str(e)})
    return results

# ============================================================
# 6. UPSCALING VIDEO
# ============================================================
def bench_upscale_video():
    hdr("6. BENCHMARK UPSCALING VIDEO")
    results=[]
    cfgs=[
        ("SD 30f 320x240 -> 2x", 320, 240, 30, 2.0),
        ("SD 30f 320x240 -> 4x", 320, 240, 30, 4.0),
        ("HD 30f 640x480 -> 2x", 640, 480, 30, 2.0),
    ]
    for name,w,h,nf,factor in cfgs:
        frames=make_video(nf,w,h)
        tw,th=int(w*factor),int(h*factor)
        t0=time.perf_counter(); uf=[]; method="LANCZOS"
        try:
            for frame in frames:
                u8=(frame*255).astype("uint8")
                if HU:
                    res=harmonic_upscaler_api.upscale_image(u8,factor=f"{int(factor)}x",energy_level="economy")
                    if res.get("success"):
                        import base64
                        up=np.array(Image.open(io.BytesIO(base64.b64decode(res["upscaled_image_base64"]))))
                        method="HarmonicUpscaler"
                    else:
                        up=np.array(Image.fromarray(u8).resize((tw,th),Image.Resampling.LANCZOS))
                else:
                    up=np.array(Image.fromarray(u8).resize((tw,th),Image.Resampling.LANCZOS))
                uf.append(up)
            el=time.perf_counter()-t0; fps=nf/el
            ok(f"{name} [{method}]")
            row("Frames traitees",str(len(uf)))
            row("Resolution",f"{w}x{h} -> {tw}x{th}")
            row("FPS upscaling",f"{fps:.1f}")
            row("Temps total",f"{el*1000:.0f} ms")
            results.append({"name":name,"method":method,"nf":nf,"fps":fps,"ms":el*1000,
                            "res":f"{tw}x{th}"})
        except Exception as e:
            err(f"{name}: {e}"); results.append({"name":name,"error":str(e)})
    return results

# ============================================================
# RAPPORT FINAL
# ============================================================
def summary(ic,vc,id_,vd,iu,vu):
    sep="="*65
    print(f"\n{B}{C}{sep}\n  RAPPORT HCS STUDIO - RESUME PERFORMANCE\n{sep}{E}")
    def _stats(lst,key,label):
        v=[r[key] for r in lst if key in r and "error" not in r]
        if v: row(label,f"{float(np.mean(v)):.2f} (min:{min(v):.2f} max:{max(v):.2f})")

    ok_ic=[r for r in ic if "error" not in r]
    if ok_ic:
        print(f"\n  {B}COMPRESSION IMAGE ({len(ok_ic)}/{len(ic)} OK){E}")
        _stats(ok_ic,"hr","Ratio hybride moyen")
        _stats(ok_ic,"sp","Espace economise moyen (%)")
        _stats(ok_ic,"ms","Temps moyen (ms)")

    ok_vc=[r for r in vc if "error" not in r]
    if ok_vc:
        print(f"\n  {B}COMPRESSION VIDEO ({len(ok_vc)}/{len(vc)} OK){E}")
        _stats(ok_vc,"rr","Ratio archive moyen")
        _stats(ok_vc,"fps","FPS compression moyen")

    ok_id=[r for r in id_ if "error" not in r]
    if ok_id:
        print(f"\n  {B}DECOMPRESSION IMAGE ({len(ok_id)}/{len(id_)} OK){E}")
        _stats(ok_id,"psnr","PSNR moyen (dB)")
        _stats(ok_id,"ms","Temps moyen (ms)")

    ok_vd=[r for r in vd if "error" not in r]
    if ok_vd:
        print(f"\n  {B}DECOMPRESSION VIDEO ({len(ok_vd)}/{len(vd)} OK){E}")
        _stats(ok_vd,"fps","FPS decompression moyen")
        _stats(ok_vd,"psnr","PSNR moyen frames (dB)")

    ok_iu=[r for r in iu if "error" not in r]
    if ok_iu:
        print(f"\n  {B}UPSCALING IMAGE ({len(ok_iu)}/{len(iu)} OK){E}")
        row("Methode",ok_iu[0].get("method","?"))
        _stats(ok_iu,"ms","Temps moyen (ms)")

    ok_vu=[r for r in vu if "error" not in r]
    if ok_vu:
        print(f"\n  {B}UPSCALING VIDEO ({len(ok_vu)}/{len(vu)} OK){E}")
        row("Methode",ok_vu[0].get("method","?"))
        _stats(ok_vu,"fps","FPS upscaling moyen")

    print(f"\n  {B}MODULES DISPONIBLES{E}")
    for nm,av in [("HybridCompressor",HC),("KFactorEngine",KE),("WebPOptimizer",WO),
                  ("QuantumHarmonicCompressor",QH),("HarmonicUpscalerAPI",HU),("OpenCV",CV)]:
        s=f"{G}OK{E}" if av else f"{R}Absent{E}"
        print(f"    {nm:<35} {s}")

    # Sauvegarde JSON
    def clean(lst,excl=()):
        return [{k:v for k,v in r.items() if k not in excl and not isinstance(v,np.ndarray)
                 and not isinstance(v,bytes)} for r in lst]
    report={"ts":time.strftime("%Y-%m-%dT%H:%M:%S"),
            "modules":{"HC":HC,"KE":KE,"WO":WO,"QH":QH,"HU":HU,"CV":CV},
            "img_comp":clean(ic,("hcs","img")),
            "vid_comp":clean(vc,("zip","frames")),
            "img_decomp":clean(id_),
            "vid_decomp":clean(vd),
            "img_up":clean(iu),
            "vid_up":clean(vu)}
    out=Path(SCRIPT_DIR)/"benchmark_results.json"
    with open(out,"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2,default=str)
    print(f"\n  {G}Rapport JSON: {out}{E}")
    print(f"  {B}{C}{sep}{E}")

# ============================================================
# MAIN
# ============================================================
if __name__=="__main__":
    print(f"\n{B}{C}{'='*65}")
    print("  HCS STUDIO - BENCHMARK PERFORMANCE COMPLET")
    print("  Compression / Decompression / Upscaling")
    print("  Images + Videos/Audio")
    print(f"{'='*65}{E}")
    print(f"\n  Python {sys.version.split()[0]} | NumPy {np.__version__} | PIL {Image.__version__}")
    print(f"  Core: {PARENT_DIR}")

    t0=time.perf_counter()

    ic=bench_compress_image()
    vc=bench_compress_video()
    id_=bench_decomp_image(ic)
    vd=bench_decomp_video(vc)
    iu=bench_upscale_image()
    vu=bench_upscale_video()

    print(f"\n  {B}Duree totale: {time.perf_counter()-t0:.2f}s{E}")
    summary(ic,vc,id_,vd,iu,vu)
