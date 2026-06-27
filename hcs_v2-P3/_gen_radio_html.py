"""Generateur du dashboard HTML Radio Broadcast"""
import os
os.makedirs('cdn/frontend', exist_ok=True)

PARTS = []
PARTS.append("""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HCS Radio Broadcast Mondial - Hi-Fi CDN</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#e0e0ff;font-family:system-ui,sans-serif;min-height:100vh}
.hdr{background:linear-gradient(135deg,#1a0533,#0d1b4b);padding:20px 30px;border-bottom:1px solid #7C3AED44;display:flex;align-items:center;gap:16px}
.hdr h1{font-size:1.6rem;background:linear-gradient(90deg,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.badge{background:#7C3AED;color:#fff;padding:3px 10px;border-radius:12px;font-size:.75rem;font-weight:700}
.stats-bar{display:flex;gap:16px;padding:14px 30px;background:#0f0f2a;border-bottom:1px solid #222;flex-wrap:wrap}
.stat{text-align:center;min-width:100px}
.stat .v{font-size:1.3rem;font-weight:700;color:#a78bfa}
.stat .l{font-size:.7rem;color:#888;text-transform:uppercase}
.controls{display:flex;gap:10px;padding:14px 24px;background:#0d0d20;flex-wrap:wrap;align-items:center}
.controls input,.controls select{background:#1a1a3a;border:1px solid #333;color:#e0e0ff;padding:7px 12px;border-radius:8px;font-size:.85rem;outline:none}
.controls input:focus,.controls select:focus{border-color:#7C3AED}
.btn{padding:7px 16px;border-radius:8px;border:none;cursor:pointer;font-size:.85rem;font-weight:600;transition:.2s}
.btn-primary{background:#7C3AED;color:#fff}.btn-primary:hover{background:#6d28d9}
.btn-sm{background:#1e293b;color:#94a3b8;padding:5px 11px;border-radius:6px;border:1px solid #334;cursor:pointer;font-size:.75rem}
.btn-sm.active{background:#7C3AED;color:#fff;border-color:#7C3AED}
.main{display:flex;height:calc(100vh - 198px)}
.list-panel{width:380px;overflow-y:auto;border-right:1px solid #1e1e3a;flex-shrink:0}
.sc{padding:13px 14px;border-bottom:1px solid #111;cursor:pointer;transition:background .15s;display:flex;align-items:center;gap:10px}
.sc:hover{background:#141428}.sc.active{background:#1a1040}
.sdot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.sinfo .sn{font-size:.88rem;font-weight:600;color:#ddd}
.sinfo .sm{font-size:.7rem;color:#666;margin-top:2px}
.sinfo .snp{font-size:.7rem;color:#a78bfa;margin-top:3px;font-style:italic;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:220px}
.hb{font-size:.62rem;background:#7C3AED22;color:#a78bfa;border:1px solid #7C3AED44;padding:1px 5px;border-radius:8px}
.dp{flex:1;overflow-y:auto;padding:20px}
.dc{background:#111124;border:1px solid #1e1e3a;border-radius:12px;padding:22px;max-width:860px;margin:0 auto}
.mg{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0}
.mb{background:#0d0d1e;border:1px solid #1a1a3a;border-radius:8px;padding:12px;text-align:center}
.mb .mv{font-size:1.15rem;font-weight:700;color:#60a5fa}.mb .ml{font-size:.68rem;color:#666;margin-top:3px}
.es{background:#0a0a1c;border:1px solid #1e1e3a;border-radius:8px;padding:14px;margin-top:14px}
.es h3{font-size:.88rem;color:#a78bfa;margin-bottom:10px}
.fg{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:10px}
.fb{padding:7px 5px;background:#111;border:1px solid #222;border-radius:6px;cursor:pointer;text-align:center;transition:.2s}
.fb:hover{border-color:#7C3AED;background:#1a1040}.fb.sel{border-color:#7C3AED;background:#1e1040}
.fb .fn{font-size:.68rem;color:#ddd;font-weight:600}.fb .fd{font-size:.62rem;color:#666}
.fb.hi .fn{color:#a78bfa}
.rb{background:#0d1520;border:1px solid #1e3a50;border-radius:8px;padding:14px;margin-top:10px;display:none}
.rb.show{display:block}
.rr{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #111;font-size:.78rem}
.rr .rk{color:#888}.rr .rv{color:#60a5fa;font-weight:600}
.hc{background:#7C3AED;color:#fff;padding:7px 14px;border-radius:8px;text-align:center;margin-top:10px;font-weight:700;display:none}
.hc.show{display:block}
.al{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.at{font-size:.62rem;background:#1e1040;color:#a78bfa;border:1px solid #7C3AED33;padding:2px 7px;border-radius:10px}
.live{display:inline-flex;align-items:center;gap:5px;font-size:.72rem;color:#4ade80}
.ld{width:6px;height:6px;border-radius:50%;background:#4ade80;animation:p 1.5s infinite}
@keyframes p{0%,100%{opacity:1}50%{opacity:.3}}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:#0a0a1a}::-webkit-scrollbar-thumb{background:#333}
</style></head><body>
<div class="hdr">
  <div style="font-size:2rem">&#127925;</div>
  <div>
    <h1>HCS Radio Broadcast Mondial</h1>
    <div style="font-size:.78rem;color:#888;margin-top:2px">40 stations &bull; 22 pays &bull; Encodage Hi-Fi professionnel a la volee</div>
  </div>
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <span class="badge">HCS-Radio-Encoder v2</span>
    <span class="badge" style="background:#059669">LIVE</span>
  </div>
</div>
<div class="stats-bar">
  <div class="stat"><div class="v" id="stTotal">40</div><div class="l">Stations</div></div>
  <div class="stat"><div class="v" id="stCountries">22</div><div class="l">Pays</div></div>
  <div class="stat"><div class="v" id="stHifi">20</div><div class="l">Hi-Fi</div></div>
  <div class="stat"><div class="v">17</div><div class="l">Formats</div></div>
  <div class="stat"><div class="v" style="font-size:.9rem">FLAC 24/96</div><div class="l">Lossless Max</div></div>
  <div class="stat"><div class="v" style="font-size:.9rem">PCM 32/192</div><div class="l">Studio Master</div></div>
  <div class="stat"><div class="v" style="font-size:.9rem">DSD128</div><div class="l">SACD Ultra</div></div>
  <div class="stat"><div class="v" style="font-size:.9rem">Dolby AC-4</div><div class="l">Broadcast Pro</div></div>
</div>
<div class="controls">
  <input id="si" type="text" placeholder="Rechercher..." style="min-width:160px" oninput="fs()">
  <select id="gf" onchange="fs()"><option value="">Tous genres</option></select>
  <select id="cf" onchange="fs()"><option value="">Tous pays</option></select>
  <button class="btn-sm active" id="ba" onclick="sf(false)">Toutes</button>
  <button class="btn-sm" id="bh" onclick="sf(true)">Hi-Fi only</button>
  <div style="margin-left:auto;display:flex;gap:8px">
    <a href="http://localhost:9019/docs" target="_blank" class="btn btn-primary" style="text-decoration:none;display:inline-flex;align-items:center">API Docs</a>
    <button class="btn btn-primary" onclick="ls()">Refresh</button>
  </div>
</div>
<div class="main">
  <div class="list-panel" id="sl"></div>
  <div class="dp" id="dp">
    <div style="text-align:center;padding:80px 20px;color:#444">
      <div style="font-size:4rem">&#127925;</div>
      <p style="margin-top:16px;font-size:1.1rem;color:#666">Selectionnez une station pour encoder en Hi-Fi</p>
      <p style="margin-top:8px;font-size:.82rem;color:#444">FLAC &bull; PCM 32bit/192kHz &bull; DSD64/128 &bull; Opus &bull; Dolby AC-4 &bull; HCS Hi-Fi</p>
    </div>
  </div>
</div>
<script>
const API='http://localhost:9019';
let ALL=[],FMT='flac_24_96',HFO=false,SEL=null;
const F={
  mp3_128:{n:'MP3 128',d:'Standard',h:false},mp3_320:{n:'MP3 320',d:'HQ',h:false},
  aac_128:{n:'AAC 128',d:'Streaming',h:false},aac_256:{n:'AAC 256',d:'Premium',h:false},
  aac_320:{n:'AAC 320',d:'AAC Max',h:false},aache_64:{n:'HE-AAC 64',d:'Mobile',h:false},
  opus_192:{n:'Opus 192',d:'Moderne',h:false},opus_320:{n:'Opus 320',d:'Opus Max',h:false},
  flac_16:{n:'FLAC 16bit',d:'CD Lossless',h:true},flac_24_96:{n:'FLAC 24/96',d:'Hi-Fi Studio',h:true},
  pcm_32_192:{n:'PCM 32/192',d:'Master',h:true},dsd64:{n:'DSD64',d:'SACD',h:true},
  dsd128:{n:'DSD128',d:'Ultra-Audiophile',h:true},dolby_ac4:{n:'Dolby AC-4',d:'Broadcast',h:true},
  hcs_hifi:{n:'HCS Hi-Fi',d:'HCS Exclusif',h:true}
};
async function ls(){
  const r=await fetch(API+'/stations').catch(()=>null);
  if(!r){document.getElementById('sl').innerHTML='<div style="padding:20px;color:#f87171;font-size:.82rem">Service offline<br>Port 9019<br><br>Demarrer:<br>python cdn/services/svc_radio_broadcast.py</div>';return;}
  const d=await r.json();ALL=d.stations||[];
  document.getElementById('stTotal').textContent=d.total||ALL.length;
  const gn=[...new Set(ALL.map(s=>s.genre))].sort();
  const cn=[...new Set(ALL.map(s=>s.country))].sort();
  const gf=document.getElementById('gf'),cf=document.getElementById('cf');
  gn.forEach(g=>{const o=document.createElement('option');o.value=o.textContent=g;gf.appendChild(o);});
  cn.forEach(c=>{const o=document.createElement('option');o.value=o.textContent=c;cf.appendChild(o);});
  document.getElementById('stHifi').textContent=ALL.filter(s=>s.bitrate>=192).length;
  rl(ALL);
}
function fs(){
  const q=document.getElementById('si').value.toLowerCase();
  const g=document.getElementById('gf').value,c=document.getElementById('cf').value;
  rl(ALL.filter(s=>{
    if(HFO&&s.bitrate<192)return false;
    if(g&&!s.genre.includes(g))return false;
    if(c&&s.country!==c)return false;
    if(q&&!s.name.toLowerCase().includes(q)&&!s.country.toLowerCase().includes(q))return false;
    return true;
  }));
}
function sf(h){
  HFO=h;
  document.getElementById('ba').className='btn-sm'+(h?'':' active');
  document.getElementById('bh').className='btn-sm'+(h?' active':'');
  fs();
}
function rl(stations){
  const el=document.getElementById('sl');el.innerHTML='';
  stations.forEach(s=>{
    const h=s.bitrate>=192,d=document.createElement('div');
    d.className='sc'+(SEL&&SEL.id===s.id?' active':'');
    d.innerHTML='<div class="sdot" style="background:'+s.color+'"></div><div class="sinfo" style="flex:1"><div class="sn">'+s.name+(h?' <span class="hb">Hi-Fi</span>':'')+'</div><div class="sm">'+s.country+' &bull; '+s.genre+' &bull; '+s.bitrate+' kbps</div><div class="snp">'+(s.now_playing||'Live Broadcast')+'</div></div>';
    d.onclick=e=>{SEL=s;document.querySelectorAll('.sc').forEach(c=>c.classList.remove('active'));d.classList.add('active');sd(s);};
    el.appendChild(d);
  });
}
function sd(s){
  const h=s.bitrate>=192;
  let fh='';
  Object.entries(F).forEach(([k,v])=>{
    fh+='<div class="fb'+(v.h?' hi':'')+(k===FMT?' sel':'')+'" onclick="sf2(\''+k+'\',this)"><div class="fn">'+v.n+'</div><div class="fd">'+v.d+'</div></div>';
  });
  document.getElementById('dp').innerHTML='<div class="dc">'+
    '<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">'+
    '<div style="width:13px;height:13px;border-radius:50%;background:'+s.color+'"></div>'+
    '<div><div style="font-size:1.3rem;font-weight:700;color:#fff">'+s.name+(h?' <span class="hb">Hi-Fi Source</span>':'')+'</div>'+
    '<div style="font-size:.78rem;color:#888;margin-top:2px">'+s.country+' &bull; '+s.genre+' &bull; '+s.language.toUpperCase()+' &bull; '+s.bitrate+' kbps source</div></div>'+
    '<span class="live" style="margin-left:auto"><span class="ld"></span>EN DIRECT</span></div>'+
    '<div style="font-size:.83rem;color:#a78bfa;padding:9px 12px;background:#1a1040;border-radius:8px;margin-bottom:14px">&#9834; '+(s.now_playing||'Live Broadcast')+'</div>'+
    '<div class="mg">'+
    '<div class="mb"><div class="mv">'+s.bitrate+' kbps</div><div class="ml">Bitrate source</div></div>'+
    '<div class="mb"><div class="mv">'+(s.listeners?s.listeners.toLocaleString():'?')+'</div><div class="ml">Auditeurs</div></div>'+
    '<div class="mb"><div class="mv">'+Math.round((s.signal_strength||0.95)*100)+'%</div><div class="ml">Signal</div></div>'+
    '</div>'+
    '<div class="es"><h3>&#127911; Encodage Hi-Fi a la volee - HCS Radio Encoder v2</h3>'+
    '<div class="fg">'+fh+'</div>'+
    '<button class="btn btn-primary" style="width:100%" onclick="enc(\''+s.id+'\')">Encoder en '+(F[FMT]?.n||FMT)+'</button>'+
    '<div class="rb" id="rb"><div style="display:flex;justify-content:space-between;margin-bottom:10px"><span style="color:#4ade80;font-weight:700">&#10003; Encodage actif</span><span id="hl2"></span></div><div id="rrs"></div><div style="margin-top:10px"><div style="font-size:.72rem;color:#888;margin-bottom:5px">Algorithmes HCS:</div><div class="al" id="als"></div></div><div style="margin-top:10px;font-size:.72rem;color:#888">HLS: <a id="hla" href="#" target="_blank" style="color:#60a5fa"></a></div></div>'+
    '<div class="hc" id="hce">&#127941; CERTIFIE HCS Hi-Fi - K-Factor &gt; 0.90</div>'+
    '</div></div>';
}
function sf2(k,el){
  FMT=k;
  document.querySelectorAll('.fb').forEach(b=>b.classList.remove('sel'));
  el.classList.add('sel');
}
async function enc(sid){
  const rb=document.getElementById('rb'),btn=event.target;
  btn.textContent='Encodage...';btn.disabled=true;
  try{
    const r=await fetch(API+'/encode',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({station_id:sid,output_format:FMT})});
    const d=await r.json(),q=d.quality||{};
    const rows=[['Format',d.output_format_info?.name||FMT],['Qualite',q.score||'-'],['K-Factor HCS',q.k_factor||'-'],
      ['SNR',q.snr_db||'-'],['Dynamic Range',q.dynamic_range||'-'],['LUFS',q.lufs||'-'],
      ['Freq response',q.freq_response||'-'],['THD',q.thd_pct?q.thd_pct+'%':'-'],['Enhancement',q.enhancement_db||'-']];
    document.getElementById('rrs').innerHTML=rows.map(([k,v])=>'<div class="rr"><span class="rk">'+k+'</span><span class="rv">'+v+'</span></div>').join('');
    document.getElementById('als').innerHTML=(q.algorithms||[]).map(a=>'<span class="at">'+a+'</span>').join('');
    const hl=document.getElementById('hla');hl.href=d.hls_url||'#';hl.textContent=d.hls_url||'';
    document.getElementById('hl2').innerHTML=d.hifi_certified?'<span style="color:#a78bfa">&#10023; Hi-Fi Certified</span>':'';
    rb.className='rb show';
    document.getElementById('hce').className=d.hifi_certified?'hc show':'hc';
  }catch(e){rb.innerHTML='<span style="color:#f87171">Service non disponible. Port: 9019</span>';rb.className='rb show';}
  btn.textContent='Encoder en '+(F[FMT]?.n||FMT);btn.disabled=false;
}
ls();
setInterval(()=>{if(SEL)fetch(API+'/stations/'+SEL.id).then(r=>r.json()).then(d=>{
  const el=document.querySelector('.snp');if(el&&d.now_playing){el.textContent=d.now_playing;}
  const el2=document.querySelector('#dp [style*="a78bfa"]');if(el2&&d.now_playing)el2.textContent='\u266a '+d.now_playing;
}).catch(()=>{});},20000);
</script></body></html>""")

with open('cdn/frontend/radio_world.html', 'w', encoding='utf-8') as f:
    f.write('\n'.join(PARTS))
print("OK: radio_world.html cree ({} octets)".format(len('\n'.join(PARTS))))
