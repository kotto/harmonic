<script>
'use strict';
const K={txt:'',shift:false,lock:false,ts:0,alt:false,voice:false,vt:null,emo:false};
const KR=[[['1','~'],['2','@'],['3','#'],['4','$'],['5','%'],['6','^'],['7','&'],['8','*'],['9','('],['0',')']],[['a','à'],['z','æ'],['e','€'],['r','®'],['t','™'],['y','¥'],['u','ù'],['i','ï'],['o','œ'],['p','°']],[['q',''],['s','ß'],['d',''],['f',''],['g',''],['h',''],['j',''],['k',''],['l',''],['m','µ']],[['w',''],['x',''],['c','ç'],['v',''],['b',''],['n','ñ']]];
const EM=['😊','😂','❤️','🔥','✨','🙏','👍','🎉','😄','😍','🤔','😎','🥰','💪','🙌','👋','🎶','🌟','💡','🚀','🌍','🍕','☕','🎯','💬','✅','😘','🫶','🤩','😅','🫠','🤝','🌸','⭐','🎵'];
const SD={'':['Sophie','Appeler','Réunion','Oui','Super','Merci','Demain'],'so':['Sophie','Soirée','Souvenir'],'ap':['Appeler','Appelle','Après'],'me':['Merci','Message','Même'],'ou':['Oui','Ouvert','Ouais'],'to':['Tokyo','Toi','Toujours'],'de':['Demain','Décision','Depuis'],'re':['Réunion','Rendez-vous','Retrouve'],'su':['Super','Sur','Surtout'],'bi':['Bientôt','Bien','Bises'],'bo':['Bonjour','Bonsoir','Bon'],'co':['Comment','Comme','Contact'],'pr':['Prépare','Prendre','Prochain'],'pa':['Paris','Parfait','Partager'],'ma':['Maintenant','Matin','Mais'],'vo':['Voici','Voilà','Voyage'],'sa':['Salut','Samedi','Sans'],'tr':['Très','Travail','Trouver']};
	const RP=['Je suis KA, votre assistant personnel intelligent. Posez-moi une question !','Que voulez-vous savoir ? Je suis là pour vous aider.','Bonjour ! Je suis KA. Que puis-je faire pour vous ?'];
	// Note : RP n'est utilisé qu'en mode déconnecté temporaire
	
		// === CONNEXION À L'IA HARMONIC ===
		// Auto-détection : même serveur que la page (local/Render), sauf si override
		const h = location.hostname;
		const isLocal = h==='localhost'||h==='127.0.0.1'||h.startsWith('192.168.')||h.startsWith('10.')||h.startsWith('172.16.');
		const API_URL = isLocal ? `http://${h}:8765` : 'https://ka-api.onrender.com';
	let API_ONLINE = false;
	
		// Vérifier la connexion au démarrage
		(async function checkAPI(){
		  try {
		    const r = await fetch(API_URL + '/api/health', {signal: AbortSignal.timeout(5000)});
		    if (r.ok) { API_ONLINE = true; console.log('✅ KA connecté'); }
		  } catch(e) { 
		    API_ONLINE = false;
		    console.log('⚠️ Serveur inaccessible — mode dégradé'); 
		    // Afficher un indicateur discret dans l'UI
		    const sb = document.querySelector('.sb__t');
		    if(sb) sb.textContent = 'KA · ⚠️';
		  }
		})();
	
		async function askKA(message) {
		  if (!API_ONLINE) return RP[Math.floor(Math.random() * RP.length)];
		  try {
		    // Récupérer/générer un user_id persistant
		    let uid = localStorage.getItem('ka_user_id');
		    if (!uid) { uid = 'user_' + Date.now().toString(36) + Math.random().toString(36).slice(2,6); localStorage.setItem('ka_user_id', uid); }
		    
		    const res = await fetch(API_URL + '/api/chat', {
		      method: 'POST',
		      headers: {'Content-Type': 'application/json'},
		      body: JSON.stringify({message: message, user_id: uid})
		    });
		    if (!res.ok) throw new Error('API error');
		    const data = await res.json();
		    
		    // Afficher les infos de spécialisation si présentes
		    if (data.specialization) {
		      const spec = data.specialization;
		      setTimeout(() => {
		        const el = document.getElementById('spec-info');
		        if (el && spec.success) {
		          el.innerHTML = '🎯 '+spec.domain+' · '+spec.triplets_count.toLocaleString()+' faits';
		          el.style.display = 'block';
		        }
		      }, 500);
		    }
		    
		    return data.response || RP[Math.floor(Math.random() * RP.length)];
		  } catch(e) {
		    API_ONLINE = false;
		    return RP[Math.floor(Math.random() * RP.length)];
		  }
		}

const CALL_SCREENS=new Set(['s-call']);
const NAV_MAP={'s-home':'nb-h','s-msg':'nb-m','s-mem':'nb-mm'};
let cur='s-home';

function go(id){
  if(id===cur)return;
  document.querySelectorAll('.sc').forEach(s=>s.classList.remove('sc--on','sc--in'));
  const el=document.getElementById(id);
  el.classList.add('sc--on','sc--in');
  cur=id;
  const nb=document.getElementById('nav-bar');
  nb.style.display=CALL_SCREENS.has(id)?'none':'flex';
  Object.entries(NAV_MAP).forEach(([sid,nid])=>{document.getElementById(nid)?.classList.toggle('nb--on',sid===id);});
  if(!Object.values(NAV_MAP).includes('nb-'+id)) document.getElementById('nb-more')?.classList.remove('nb--on');
  if(id==='s-call'){startCall();}else{stopCall();}
  if(id==='s-cap'){buildCapWave();}
  closeMore();
}
function showMore(){document.getElementById('more-panel').style.display='block';document.getElementById('nb-more').classList.add('nb--on');}

// ── QUALITÉ INTUITIVE ──
function setQuality(val, label){
  document.getElementById('hpc-quality').value = val;
  document.getElementById('hpc-q-label').textContent = label;
  // Reset pill styles
  ['eco','std','pro','max'].forEach(id=>{
    const el=document.getElementById('hpc-q-'+id);
    el.style.background='rgba(255,255,255,.04)';
    el.style.border='.5px solid var(--b2)';
    el.style.color='var(--t3)';
  });
  // Highlight selected
  const map={20:'eco',45:'std',70:'pro',100:'max'};
  const sel=document.getElementById('hpc-q-'+map[val]);
  if(sel){sel.style.background='var(--life-d)';sel.style.border='.5px solid var(--life)';sel.style.color='var(--life)';}
  hpcRun();
}

function closeMore(){const p=document.getElementById('more-panel');if(p)p.style.display='none';document.getElementById('nb-more')?.classList.remove('nb--on');}

function mk(lbl,alt,w,cls,fn){
  const el=document.createElement('div');el.className='key'+(cls?' '+cls:'');el.style.width=w+'px';
  el.setAttribute('role','button');
  el.innerHTML=`<span class="key__c">${lbl}</span>${alt?`<span class="key__a">${alt}</span>`:''}`;
  el.addEventListener('pointerdown',e=>{e.preventDefault();el.classList.add('key--p');setTimeout(()=>el.classList.remove('key--p'),115);fn();});
  return el;
}
function buildKbd(){
  const rn=document.getElementById('rn');rn.innerHTML='';
  KR[0].forEach(([c,a])=>{const d=K.alt?(a||c):c,s=K.alt?c:a;rn.appendChild(mk(d,s,32,'',()=>type(d)));});
  ['r1','r2'].forEach((id,ri)=>{
    const r=document.getElementById(id);r.innerHTML='';
    KR[ri+1].forEach(([c,a])=>{const d=(K.shift||K.lock)?c.toUpperCase():c;r.appendChild(mk(d,a,33,'',()=>{type(d);if(K.shift&&!K.lock){K.shift=false;buildKbd();}}));});
  });
  const r3=document.getElementById('r3');r3.innerHTML='';
  r3.appendChild(mk(K.lock?'⇪':'⇧','',43,'key--sp'+((K.shift||K.lock)?' key--sft':''),()=>{
    const n=Date.now();if(n-K.ts<280){K.lock=!K.lock;K.shift=K.lock;}else{K.shift=!K.shift;K.lock=false;}K.ts=n;buildKbd();
  }));
  KR[3].forEach(([c,a])=>{const d=(K.shift||K.lock)?c.toUpperCase():c;r3.appendChild(mk(d,a,35,'',()=>{type(d);if(K.shift&&!K.lock){K.shift=false;buildKbd();}}));});
  r3.appendChild(mk('⌫','',43,'key--sp key--del',()=>{K.txt=K.txt.slice(0,-1);upd();}));
  const rs=document.getElementById('rs');rs.innerHTML='';
  rs.appendChild(mk(K.alt?'ABC':'123','',49,'key--sp',()=>{K.alt=!K.alt;buildKbd();}));
  const sp=document.createElement('div');sp.className='key key--spc';sp.style.flex='1';
  sp.innerHTML='<span class="key__c">espace</span>';
  sp.addEventListener('pointerdown',e=>{e.preventDefault();sp.classList.add('key--p');setTimeout(()=>sp.classList.remove('key--p'),115);type(' ');});
  rs.appendChild(sp);
  rs.appendChild(mk('Envoyer','',82,'key--life',()=>sendMsg()));
}
function type(c){K.txt+=c;upd();}
function upd(){document.getElementById('ftxt').textContent=K.txt;document.getElementById('sbtn').classList.toggle('ib__snd--on',K.txt.length>0);renderSugs();}
function getSugs(t){const l=(t.trim().split(' ').pop()||'').toLowerCase();for(const[k,v]of Object.entries(SD)){if(k&&l.startsWith(k))return v.slice(0,6);}return SD[''].slice(0,6);}
function renderSugs(){
  const c=document.getElementById('sgs');c.innerHTML='';
  getSugs(K.txt).forEach((w,i)=>{
    const d=document.createElement('div');d.className='sg'+(i===0?' sg--h':'');
    d.setAttribute('role','option');d.textContent=w;
    d.addEventListener('pointerdown',e=>{e.preventDefault();const p=K.txt.trim().split(' ');p[p.length-1]=w;K.txt=p.join(' ')+' ';upd();});
    c.appendChild(d);
  });
}
function paste(){const w=['Sophie','Réunion demain ?','Ok pour 19h !','Super idée !'];K.txt+=w[Math.floor(Math.random()*w.length)];upd();}
	function sendMsg(){
	  const val=K.txt.trim();if(!val)return;
	  const c=document.getElementById('msglist');
	  // Message utilisateur
	  const m=document.createElement('div');m.className='msg msg--m';m.textContent=val;c.appendChild(m);c.scrollTop=c.scrollHeight;
	  K.txt='';upd();
	  // Indicateur "KA réfléchit..."
	  const think=document.createElement('div');think.className='msg msg--t';think.style.opacity='0.6';
	  think.innerHTML='<span style="animation:pulse 1.2s ease-in-out infinite">●</span> KA réfléchit…';
	  think.id='ka-thinking';c.appendChild(think);c.scrollTop=c.scrollHeight;
	  // Appeler l'IA
	  askKA(val).then(reply => {
	    const t = document.getElementById('ka-thinking');
	    if (t) t.remove();
	    const r=document.createElement('div');r.className='msg msg--t';r.textContent=reply;c.appendChild(r);c.scrollTop=c.scrollHeight;
	  });
	}
function toggleVoice(){
  K.voice=!K.voice;const btn=document.getElementById('tbv'),lbl=document.getElementById('vl');
  btn.classList.toggle('tbn--on',K.voice);btn.setAttribute('aria-pressed',K.voice);
  if(K.voice){
    lbl.textContent='● Écoute…';K.txt='';
    const phrases=['Rendez-vous demain à 19h ?','Appelle Sophie','Prépare ma réunion','Envoie les photos de Rome à Sophie'];
    const phrase=phrases[Math.floor(Math.random()*phrases.length)];let i=0;
    K.vt=setInterval(()=>{if(!K.voice||i>=phrase.length){clearInterval(K.vt);if(K.voice){K.voice=false;btn.classList.remove('tbn--on');lbl.textContent='Voix';btn.setAttribute('aria-pressed','false');}return;}K.txt+=phrase[i++];upd();},72);
  }else{clearInterval(K.vt);lbl.textContent='Voix';}
}
function toggleEmoji(){
  K.emo=!K.emo;const ep=document.getElementById('ep'),kd=document.getElementById('kbd'),btn=document.getElementById('tbe');
  btn.classList.toggle('tbn--on',K.emo);btn.setAttribute('aria-pressed',K.emo);
  if(K.emo){ep.innerHTML='';EM.forEach(e=>{const b=document.createElement('div');b.className='eb';b.setAttribute('role','button');b.textContent=e;b.addEventListener('pointerdown',ev=>{ev.preventDefault();type(e);});ep.appendChild(b);});ep.classList.add('ep--on');kd.style.display='none';}
  else{ep.classList.remove('ep--on');kd.style.display='block';}
}
let callSecs=0,callIv=null;
function startCall(){
  callSecs=0;clearInterval(callIv);
  callIv=setInterval(()=>{callSecs++;const m=String(Math.floor(callSecs/60)).padStart(2,'0'),s=String(callSecs%60).padStart(2,'0');const el=document.getElementById('ctmr');if(el)el.textContent=m+':'+s;},1000);
  const w=document.getElementById('cwv');if(!w)return;w.innerHTML='';
  for(let i=0;i<22;i++){const b=document.createElement('div');b.className='wb';b.style.cssText='--wh:'+(3+Math.random()*22)+'px;animation-duration:'+(0.35+Math.random()*0.5)+'s;animation-delay:'+(Math.random()*0.4)+'s';w.appendChild(b);}
}
function stopCall(){clearInterval(callIv);}
function buildCapWave(){
  const w=document.getElementById('capwv');if(!w)return;w.innerHTML='';
  for(let i=0;i<18;i++){const b=document.createElement('div');b.style.cssText='width:2.5px;border-radius:2px;background:rgba(61,219,160,.6);--wh:'+(3+Math.random()*16)+'px;animation:wave '+(0.35+Math.random()*0.5)+'s ease-in-out infinite alternate '+(Math.random()*0.4)+'s';w.appendChild(b);}
}
function tick(){const n=new Date();document.getElementById('clk').textContent=String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0');}
tick();setInterval(tick,10000);
buildKbd();renderSugs();

// ── HPC LAB ──
let hpcMode='protein';
function hpcRun(){
  const mode=hpcMode;
  const res=document.getElementById('hpc-result');
  res.style.display='block';res.innerHTML='<span style="color:var(--soul-l);animation:pulse 1.2s ease-in-out infinite">●</span> Calcul en cours…';
  const inp=document.getElementById('hpc-input');
  const seqEl=document.getElementById('hpc-seq');
  const compressUI=document.getElementById('hpc-compress-ui');
  
  // Reset visibility
  seqEl.style.display=(mode==='protein')?'block':'none';
  if(compressUI) compressUI.style.display=(mode==='compress')?'block':'none';
  
  if(mode==='protein'){
    const seq=(document.getElementById('hpc-seq')?.value||'ALAARGASN').toUpperCase().replace(/[^A-Z]/g,'');
    fetch(API_URL+'/api/hpc/protein',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sequence:seq||'ALAARGASN'})})
      .then(r=>r.json()).then(d=>{
        res.innerHTML=`<div class="sec-lbl">🧬 PROTEIN FOLDING</div><div style="font-size:13px;color:var(--t2);line-height:1.6">Énergie libre : <b style="color:var(--life)">${d.free_energy_kcal_mol} kcal/mol</b><br>Confiance : <b>${Math.round(d.confidence*100)}%</b><br>Hélice α ${d.secondary_structure.helix_percent}% | Feuillet β ${d.secondary_structure.sheet_percent}% | Boucle ${d.secondary_structure.loop_percent}%<br><span style="color:var(--life)">Accélération φ : ${d.harmonic_speedup}</span></div>`;
        inp.style.display='block';
      }).catch(()=>{res.innerHTML='<span style="color:var(--coral)">⚠️ API inaccessible</span>';});
  }else if(mode==='quantum'){
    inp.style.display='none';
    fetch(API_URL+'/api/hpc/quantum',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({n_qubits:8})})
      .then(r=>r.json()).then(d=>{
        res.innerHTML=`<div class="sec-lbl">⚛️ SIMULATION QUANTIQUE</div><div style="font-size:13px;color:var(--t2);line-height:1.6">Énergie fondamentale : <b style="color:var(--soul-l)">${d.ground_state_energy}</b><br>Spectre : ${d.energy_spectrum.slice(0,4).map(e=>e.toFixed(3)).join(', ')}…<br><span style="color:var(--soul-l)">Efficacité harmonique : ${d.harmonic_efficiency}</span></div>`;
      }).catch(()=>{res.innerHTML='<span style="color:var(--coral)">⚠️ API inaccessible</span>';});
	  }else if(mode==='compress'){
	    inp.style.display='block';
	    document.getElementById('hpc-seq').style.display='none';
	    document.getElementById('hpc-compress-ui').style.display='block';
	    const q=parseInt(document.getElementById('hpc-quality').value)||45;
	    const label=document.getElementById('hpc-q-label');
	    fetch(API_URL+'/api/harmonic/encode',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({quality:q,mode:'image'})})
	      .then(r=>r.json()).then(d=>{
	        if(d.error){res.innerHTML='<span style=\"color:var(--coral)\">'+d.error+'</span>';return;}
	        const qualLabel=d.psnr_db>=99?'🌟 Parfaite — sans aucune perte':d.psnr_db>=50?'✨ Excellente — indiscernable':'🌱 Économique — très légère';
	        res.innerHTML=`<div class=\"sec-lbl\">📦 COMPRESSION HARMONIQUE</div>
	          <div style=\"font-size:13px;color:var(--t2);line-height:1.8\">
	          ${d.resolution} · ${(d.original_bytes/1024).toFixed(0)} Ko → <b style=\"color:var(--life)\">${(d.compressed_bytes/1024).toFixed(1)} Ko</b><br>
	          <b style=\"color:var(--life)\">${d.ratio}x</b> plus léger · ${d.gain_percent}% d'espace libéré<br>
	          Qualité : <b>${qualLabel}</b><br>
	          <span style=\"color:var(--t4);font-size:11px\">${d.dict_patches.toLocaleString()} fragments de mémoire · ${d.encode_ms} ms</span></div>`;
	      }).catch(()=>{res.innerHTML='<span style=\"color:var(--coral)\">⚠️ KA ne peut pas accéder au serveur</span>';});
	  }
}

// ── SANTÉ : CAMÉRA PPG ──
let santeCamStream=null,santeCamTimer=null,santeCamBPM=null,santeCamSamples=[],santeCamAllSamples=[];
async function santeCamStart(){
  const ui=document.getElementById('sante-cam-ui');
  const btn=document.getElementById('sante-cam-btn');
  const video=document.getElementById('sante-cam-video');
  const msg=document.getElementById('sante-cam-msg');
  try{
    santeCamStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:320,height:240},audio:false});
    video.srcObject=santeCamStream;
    ui.style.display='block'; btn.style.display='none';
    santeCamSamples=[]; santeCamBPM=null; santeCamAllSamples=[];
    document.getElementById('sante-cam-bpm').textContent='--';
    document.getElementById('sante-cam-apply').style.display='none';
    document.getElementById('sante-indicators').style.display='none';
    msg.textContent='Placez votre visage dans le cadre · Restez immobile · Patientez 10s...';
    // Démarrer l'analyse PPG après un court délai (le temps que l'exposition se stabilise)
    setTimeout(()=>{santeCamAnalyze();},1500);
  }catch(e){
    msg.textContent='⚠️ Caméra non disponible : '+e.message;
  }
}
function santeCamStop(){
  if(santeCamStream){santeCamStream.getTracks().forEach(t=>t.stop());santeCamStream=null;}
  if(santeCamTimer){clearInterval(santeCamTimer);santeCamTimer=null;}
  document.getElementById('sante-cam-ui').style.display='none';
  document.getElementById('sante-cam-btn').style.display='block';
  document.getElementById('sante-cam-video').srcObject=null;
}
function santeCamApply(){
  if(santeCamBPM){
    document.getElementById('sante-fc').value=Math.round(santeCamBPM);
    document.getElementById('sante-fc-cam').style.display='inline';
    // Calculer les indicateurs avancés si assez de données
    if(santeCamAllSamples&&santeCamAllSamples.length>120){
      const indicators=santeComputeAllIndicators(santeCamAllSamples);
      if(indicators){
        let html='<div class="sec-lbl">📡 INDICATEURS HARMONIQUES (caméra)</div>';
        html+='<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:10px">';
        if(indicators.hrv_sdnn) html+=`<div>🫀 HRV SDNN <b>${indicators.hrv_sdnn}</b> ms</div>`;
        if(indicators.hrv_rmssd) html+=`<div>🧠 HRV RMSSD <b>${indicators.hrv_rmssd}</b> ms</div>`;
        if(indicators.coherence_phi) html+=`<div style="color:${indicators.coherence_phi>70?'var(--life)':'var(--coral)'}">φ Cohérence <b>${indicators.coherence_phi}%</b></div>`;
        if(indicators.resp_rate) html+=`<div>🫁 Respiration <b>${indicators.resp_rate}</b> rpm</div>`;
        if(indicators.arythmia_score!==undefined) html+=`<div>∛ Arythmie <b>${indicators.arythmia_score}%</b> <span style="color:var(--t4)">${indicators.arythmia_risk}</span></div>`;
        if(indicators.rise_time_ms) html+=`<div>📈 Rigidité <b>${indicators.rise_time_ms}</b>ms <span style="color:var(--t4)">${indicators.arterial_stiffness}</span></div>`;
        if(indicators.vitality_score) html+=`<div style="grid-column:1/-1;text-align:center;margin-top:4px;font-size:13px">✨ Vitalité <b style="font-size:18px;color:var(--life)">${indicators.vitality_score}%</b></div>`;
        html+='</div>';
        document.getElementById('sante-indicators').innerHTML=html;
        document.getElementById('sante-indicators').style.display='block';
      }
    }
    santeCamStop();
  }
}
function santeCamAnalyze(){
  const video=document.getElementById('sante-cam-video');
  const canvas=document.getElementById('sante-cam-canvas');
  const ctx=canvas.getContext('2d');
  const bpmEl=document.getElementById('sante-cam-bpm');
  const msg=document.getElementById('sante-cam-msg');
  const applyBtn=document.getElementById('sante-cam-apply');
  let samples=[];
  let startTime=Date.now();
  santeCamTimer=setInterval(()=>{
    if(!santeCamStream){clearInterval(santeCamTimer);return;}
    // Capturer le frame
    canvas.width=video.videoWidth||320; canvas.height=video.videoHeight||240;
    ctx.drawImage(video,0,0,canvas.width,canvas.height);
    // Extraire la région d'intérêt (centre du visage — zone du front)
    const rx=Math.floor(canvas.width*0.3),ry=Math.floor(canvas.height*0.2);
    const rw=Math.floor(canvas.width*0.4),rh=Math.floor(canvas.height*0.3);
    const imgData=ctx.getImageData(rx,ry,rw,rh);
    // Calculer la moyenne du canal rouge (le sang absorbe le vert, reflète le rouge)
    let sum=0;
    for(let i=0;i<imgData.data.length;i+=4){
      sum+=imgData.data[i]; // canal rouge
    }
    const avg=sum/(imgData.data.length/4);
    samples.push({t:Date.now()-startTime,v:avg});
    santeCamAllSamples.push({t:Date.now()-startTime,v:avg});
    if(santeCamAllSamples.length>1200) santeCamAllSamples=santeCamAllSamples.slice(-900); // ~30s max
    // Garder ~15 secondes de données
    if(samples.length>450) samples=samples.slice(-450);
    // Calculer la FC toutes les ~2 secondes si assez de données
    if(samples.length>90&&samples.length%30===0){
      const bpm=santeCamComputeBPM(samples);
      if(bpm>40&&bpm<180){
        santeCamBPM=bpm;
        bpmEl.textContent=Math.round(bpm);
        // Vérifier si la mesure est stable (écart-type faible sur les 5 dernières mesures)
        if(santeCamSamples.length>=4){
          const recent=santeCamSamples.slice(-5).concat([bpm]);
          const mean=recent.reduce((a,b)=>a+b,0)/recent.length;
          const std=Math.sqrt(recent.reduce((s,x)=>s+(x-mean)**2,0)/recent.length);
          if(std<3&&recent.length>=5){
            msg.textContent='✅ Mesure stable · FC = '+Math.round(bpm)+' bpm';
            applyBtn.style.display='inline-block';
          }
        }
        santeCamSamples.push(bpm);
        if(santeCamSamples.length>10)santeCamSamples=santeCamSamples.slice(-10);
      }
    }
    // Timeout après 30s
    if(Date.now()-startTime>30000&&santeCamBPM){
      msg.textContent='⏱ Mesure terminée · FC = '+Math.round(santeCamBPM)+' bpm';
      applyBtn.style.display='inline-block';
      clearInterval(santeCamTimer);
    }
  },33); // ~30 fps
}
function santeCamComputeBPM(samples){
  // Détection des pics dans le signal PPG (canal rouge moyen)
  // Le signal PPG a une fréquence correspondant au rythme cardiaque
  // On utilise l'autocorrélation pour trouver la période dominante
  const n=samples.length;
  if(n<60) return null;
  // Normaliser le signal (enlever la tendance)
  const signal=samples.map(s=>s.v);
  // Filtre passe-bande simple : différences successives (détrend)
  const filtered=[];
  for(let i=2;i<n;i++){
    filtered.push(signal[i]-signal[i-2]);
  }
  // Détection de pics (zero-crossing du signal filtré)
  let peaks=[];
  for(let i=2;i<filtered.length-1;i++){
    if(filtered[i]>filtered[i-1]&&filtered[i]>filtered[i+1]&&filtered[i]>0.5){
      peaks.push(i);
    }
  }
  if(peaks.length<2) return null;
  // Calculer les intervalles entre pics (en ms)
  const intervals=[];
  for(let i=1;i<peaks.length;i++){
    const dt=samples[peaks[i]].t-samples[peaks[i-1]].t;
    if(dt>300&&dt<2000) intervals.push(dt); // filtrer les artefacts (20-200 BPM)
  }
  if(intervals.length<2) return null;
  // Médiane des intervalles (robuste aux outliers)
  intervals.sort((a,b)=>a-b);
  const medianInterval=intervals[Math.floor(intervals.length/2)];
  const bpm=60000/medianInterval;
	  return Math.round(bpm);
	}

// ── SANTÉ : INDICATEURS HARMONIQUES AVANCÉS ──
function santeComputeAllIndicators(ppgSamples){
  // ppgSamples = [{t: ms, v: red_avg}, ...]
  // Retourne un objet avec tous les indicateurs harmoniques
  const n=ppgSamples.length;
  if(n<120) return null; // besoin d'au moins 4 secondes de données

  // 1. Extraire le signal et normaliser
  const signal=ppgSamples.map(s=>s.v);
  const mean=signal.reduce((a,b)=>a+b,0)/n;
  const std=Math.sqrt(signal.reduce((s,x)=>s+(x-mean)**2,0)/n);
  const normalized=signal.map(v=>(v-mean)/std);

  // 2. Détection des intervalles RR (battement à battement)
  const filtered=[];
  for(let i=2;i<n;i++) filtered.push(normalized[i]-normalized[i-2]);
  const peaks=[];
  for(let i=2;i<filtered.length-1;i++){
    if(filtered[i]>filtered[i-1]&&filtered[i]>filtered[i+1]&&filtered[i]>0.3){
      peaks.push(i+2); // index dans le signal original
    }
  }
  const rrIntervals=[];
  for(let i=1;i<peaks.length;i++){
    const dt=ppgSamples[peaks[i]].t-ppgSamples[peaks[i-1]].t;
    if(dt>300&&dt<2000) rrIntervals.push(dt);
  }

  const result={};

  // ── FC (BPM) ── π : périodicité cardiaque
  if(rrIntervals.length>=2){
    const sorted=[...rrIntervals].sort((a,b)=>a-b);
    const medRR=sorted[Math.floor(sorted.length/2)];
    result.bpm=Math.round(60000/medRR);
  }

  // ── HRV SDNN (ms) ── φ : variabilité globale
  if(rrIntervals.length>=4){
    const rrMean=rrIntervals.reduce((a,b)=>a+b,0)/rrIntervals.length;
    result.hrv_sdnn=Math.round(Math.sqrt(rrIntervals.reduce((s,x)=>s+(x-rrMean)**2,0)/rrIntervals.length));
  }

  // ── HRV RMSSD (ms) ── φ : variabilité court terme (tonus vagal)
  if(rrIntervals.length>=4){
    let sumSq=0;
    for(let i=1;i<rrIntervals.length;i++) sumSq+=(rrIntervals[i]-rrIntervals[i-1])**2;
    result.hrv_rmssd=Math.round(Math.sqrt(sumSq/(rrIntervals.length-1)));
  }

  // ── Cohérence φ cardiaque ── φ : ratio optimal = φ
  if(result.hrv_sdnn&&result.bpm){
    const phi=1.618033988749895;
    const rrMean=60000/result.bpm;
    const cv=result.hrv_sdnn/rrMean; // coefficient de variation
    // Score de cohérence : CV proche de 1/φ² est optimal
    const target=1/(phi*phi); // ~0.382
    result.coherence_phi=Math.round(Math.max(0,Math.min(100,100*(1-Math.abs(cv-target)/target))));
  }

  // ── Fréquence respiratoire (rpm) ── π : modulation lente du PPG
  // On extrait l'enveloppe du signal PPG (amplitude des pics)
  if(peaks.length>=6){
    const amplitudes=peaks.map(i=>ppgSamples[i].v);
    const ampFiltered=[];
    for(let i=2;i<amplitudes.length;i++) ampFiltered.push(amplitudes[i]-amplitudes[i-2]);
    // Détection des cycles respiratoires (pics d'amplitude PPG = inspiration)
    let respPeaks=0;
    for(let i=2;i<ampFiltered.length-1;i++){
      if(ampFiltered[i]>ampFiltered[i-1]&&ampFiltered[i]>ampFiltered[i+1]&&ampFiltered[i]>0.2) respPeaks++;
    }
    const durationSec=(ppgSamples[ppgSamples.length-1].t-ppgSamples[0].t)/1000;
    if(durationSec>5&&respPeaks>=2){
      result.resp_rate=Math.round(respPeaks*60/durationSec);
    }
  }

  // ── Indice d'arythmie √3 ── irrégularité cubique
  if(rrIntervals.length>=8){
    const rrMean=rrIntervals.reduce((a,b)=>a+b,0)/rrIntervals.length;
    // √3 = 1.732... la stabilité du rythme est gouvernée par √3
    const s3=1.732050807568877;
    const cv_rr=Math.sqrt(rrIntervals.reduce((s,x)=>s+(x-rrMean)**2,0)/rrIntervals.length)/rrMean;
    // Un rythme sain a CV < 0.1 (régulier comme √3)
    result.arythmia_score=Math.round(Math.max(0,Math.min(100,100*(1-cv_rr*10/s3))));
    result.arythmia_risk=cv_rr>0.15?'élevé':cv_rr>0.10?'modéré':'faible';
  }

  // ── Indice de rigidité artérielle ── e : temps de montée du pic
  if(peaks.length>=4){
    const riseTimes=[];
    for(const pi of peaks){
      // Chercher le creux précédent
      let trough=pi;
      for(let j=pi-1;j>Math.max(0,pi-30);j--){
        if(normalized[j]<normalized[trough]) trough=j;
      }
      const riseTime=ppgSamples[pi].t-ppgSamples[trough].t;
      if(riseTime>50&&riseTime<400) riseTimes.push(riseTime);
    }
    if(riseTimes.length>=3){
      const avgRise=riseTimes.reduce((a,b)=>a+b,0)/riseTimes.length;
      result.rise_time_ms=Math.round(avgRise);
      // Temps de montée normal : 100-150ms. >200ms = rigidité
      result.arterial_stiffness=avgRise>200?'élevée':avgRise>150?'modérée':'normale';
    }
  }

  // ── Score de vitalité harmonique ── φ·π·e fusion
  let vitalityScore=0, vitalityCount=0;
  if(result.coherence_phi!==undefined){vitalityScore+=result.coherence_phi;vitalityCount++;}
  if(result.arythmia_score!==undefined){vitalityScore+=result.arythmia_score;vitalityCount++;}
  if(result.bpm&&result.bpm>=55&&result.bpm<=85){vitalityScore+=100;vitalityCount++;}
  else if(result.bpm){vitalityScore+=Math.max(0,100-Math.abs(result.bpm-64)*3);vitalityCount++;}
  if(result.hrv_rmssd&&result.hrv_rmssd>30){vitalityScore+=100;vitalityCount++;}
  else if(result.hrv_rmssd){vitalityScore+=Math.min(100,result.hrv_rmssd*3);vitalityCount++;}
  if(result.resp_rate&&result.resp_rate>=12&&result.resp_rate<=18){vitalityScore+=100;vitalityCount++;}
  result.vitality_score=vitalityCount>0?Math.round(vitalityScore/vitalityCount):null;

  return result;
}

// ── SANTÉ HARMONIQUE ──
async function santeDiagnostic(){
  const r=document.getElementById('sante-result');
  const l=document.getElementById('sante-loading');
  r.style.display='none'; l.style.display='block';
  // Collecter les données
  const symptomes=document.getElementById('sante-symptomes').value.split(',').map(s=>s.trim()).filter(Boolean);
  const vitaux={};
  const fc=parseFloat(document.getElementById('sante-fc').value);
  const temp=parseFloat(document.getElementById('sante-temp').value);
  const sys=parseFloat(document.getElementById('sante-sys').value);
  const dia=parseFloat(document.getElementById('sante-dia').value);
  const spo2=parseFloat(document.getElementById('sante-spo2').value);
  const age=parseInt(document.getElementById('sante-age').value)||null;
  if(fc)vitaux.frequence_cardiaque=fc;
  if(temp)vitaux.temperature=temp;
  if(sys)vitaux.pression_systolique=sys;
  if(dia)vitaux.pression_diastolique=dia;
  if(spo2)vitaux.saturation_oxygene=spo2;
  try{
    const resp=await fetch(API_URL+'/api/health/diagnostic',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({symptomes,vitaux,age})
    });
    const d=await resp.json();
    l.style.display='none'; r.style.display='block';
    let html='';
    // Score global
    const sc=d.score_harmonique_global||0;
    const color=sc>0.75?'var(--life)':sc>0.5?'var(--sun)':'var(--coral)';
    html+=`<div style="text-align:center;margin-bottom:12px"><div style="font-size:28px;font-weight:700;color:${color}">${(sc*100).toFixed(0)}%</div><div style="font-size:10px;color:var(--t4)">Score harmonique global</div></div>`;
    // Diagnostic principal
    if(d.diagnostic_harmonique){
      const diag=d.diagnostic_harmonique;
      html+=`<div class="sec-lbl" style="color:var(--sun)">🧬 DIAGNOSTIC</div>`;
      html+=`<div style="font-size:14px;color:var(--t1);font-weight:600;margin-bottom:4px">${diag.pathologie_principale||'—'}</div>`;
      html+=`<div style="font-size:11px;color:var(--t2);margin-bottom:2px">Constante altérée : <b style="color:var(--soul-l)">${diag.constante_alteree||'—'}</b></div>`;
      html+=`<div style="font-size:11px;color:var(--t4);margin-bottom:8px">${diag.mecanisme_harmonique||''}</div>`;
    }
    // Différentiel
    if(d.analyse_symptomes&&d.analyse_symptomes.resultats){
      html+=`<div class="sec-lbl">📊 DIFFÉRENTIEL</div>`;
      d.analyse_symptomes.resultats.slice(0,4).forEach(x=>{
        const bar='█'.repeat(Math.round(x.score_resonance*25));
        html+=`<div style="font-size:11px;margin-bottom:3px;color:var(--t1)"><span style="color:var(--t4)">${x.pathologie}</span> <span style="font-size:9px;color:var(--t4)">${(x.score_resonance*100).toFixed(1)}%</span><br><span style="font-family:monospace;color:var(--soul-l)">${bar}</span></div>`;
      });
    }
    // Vitaux
    if(d.analyse_vitales&&d.analyse_vitales.scores_individuels){
      html+=`<div class="sec-lbl" style="margin-top:8px">🩺 CONSTANTES</div>`;
      Object.entries(d.analyse_vitales.scores_individuels).forEach(([k,v])=>{
        const em=v.score_coherence>0.7?'✓':v.score_coherence>0.4?'⚠':'✗';
        html+=`<div style="font-size:10px;color:var(--t2)">${em} ${k}: <b>${v.valeur}</b> ${v.unite} (écart ${v.ecart_pct}%)</div>`;
      });
    }
    // Fréquences
    if(d.frequences_therapeutiques){
      html+=`<div class="sec-lbl" style="margin-top:8px">🎵 FRÉQUENCES</div>`;
      d.frequences_therapeutiques.forEach(f=>{
        html+=`<div style="font-size:10px;color:var(--t2)">• ${f.freq_hz.toFixed(1)} Hz — ${f.effet}</div>`;
      });
    }
    // Recommandations
    if(d.recommandations){
      html+=`<div class="sec-lbl" style="margin-top:8px">💡 RECOMMANDATIONS</div>`;
      d.recommandations.slice(0,3).forEach((rec,i)=>{
        html+=`<div style="font-size:10px;color:var(--t2);margin-bottom:2px">${i+1}. ${rec}</div>`;
      });
    }
    r.innerHTML=html||'<div style="color:var(--t4);text-align:center">Aucun résultat. Fournir symptômes et/ou constantes.</div>';
  }catch(e){
    l.style.display='none'; r.style.display='block';
    r.innerHTML=`<span style="color:var(--coral)">⚠️ Erreur: ${e.message}</span>`;
  }
}

// ── CODE STUDIO ──
function codeGen(){
  const prompt=document.getElementById('code-prompt')?.value?.trim();
  const lang=document.getElementById('code-lang')?.value||'python';
  const res=document.getElementById('code-result');
  if(!prompt){res.style.display='block';res.innerHTML='<span style="color:var(--coral)">Veuillez décrire le code souhaité</span>';return;}
  res.style.display='block';res.innerHTML='<span style="color:var(--soul-l);animation:pulse 1.2s ease-in-out infinite">●</span> Génération…';
  fetch(API_URL+'/api/code/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,language:lang})})
    .then(r=>r.json()).then(d=>{res.textContent=d.code;res.style.color='var(--life)';})
    .catch(()=>{res.innerHTML='<span style="color:var(--coral)">⚠️ API inaccessible — essayez "tri" ou "fibonacci"</span>';
      // Fallback local
      const p=prompt.toLowerCase();
      if(p.includes('tri')||p.includes('sort'))res.textContent=lang==='python'?'def tri_rapide(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[0]\n    gauche = [x for x in arr[1:] if x <= pivot]\n    droite = [x for x in arr[1:] if x > pivot]\n    return tri_rapide(gauche) + [pivot] + tri_rapide(droite)':'function quickSort(arr) {\n  if (arr.length <= 1) return arr;\n  const pivot = arr[0];\n  const left = arr.slice(1).filter(x => x <= pivot);\n  const right = arr.slice(1).filter(x => x > pivot);\n  return [...quickSort(left), pivot, ...quickSort(right)];\n}';
      else if(p.includes('fibo'))res.textContent=lang==='python'?'def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b':'function* fibonacci(n) {\n  let a = 0, b = 1;\n  for (let i = 0; i < n; i++) {\n    yield a;\n    [a, b] = [b, a + b];\n  }\n}';
      else res.textContent=lang==='python'?`def solve(data):\n    """${prompt.slice(0,50)}"""\n    return data`:`function solve(data) {\n  // ${prompt.slice(0,50)}\n  return data;\n}`;
    });
}
}

// ═══════════════════════════════════════════════════════════════════
// ÉCRANS DYNAMIQUES — hooks appelés au chargement de chaque écran
// ═══════════════════════════════════════════════════════════════════

const SCREEN_HOOKS={
  's-mem': loadMemory,
  's-prep': loadPrep,
  's-jrn': loadJourney,
  's-dec': loadDecision,
  's-cap': loadCapture,
  's-rel': loadRelation,
  's-sante': loadSante,
};

// Intercepter go() pour déclencher les hooks
const _originalGo = go;
go = function(id) {
  _originalGo(id);
  const hook = SCREEN_HOOKS[id];
  if (hook) setTimeout(hook, 100);
};

// ── MÉMOIRE ──
async function loadMemory() {
  const body = document.querySelector('#s-mem .sp-body');
  if (!body || body.dataset.loaded) return;
  body.dataset.loaded = '1';
  try {
    const r = await fetch(API_URL + '/api/memory/recent', {signal: AbortSignal.timeout(5000)});
    const data = await r.json();
    if (data.memories && data.memories.length) {
      let html = '';
      data.memories.forEach(function(m) {
        html += '<div class="tl-item" style="margin-top:10px"><div class="tl-dot tl-dot--soul"></div><div style="font-size:13px;color:var(--t2)">'+(m.title||(m.content||'').slice(0,60))+'</div><div style="font-size:11px;color:var(--t4)">'+(m.date||'')+'</div></div>';
      });
      var tl = body.querySelector('.tl');
      if (tl) tl.innerHTML = html || tl.innerHTML;
    }
  } catch(e) {}
}

// ── PRÉPARER ──
async function loadPrep() {
  var briefing = document.querySelector('#s-prep .insight--soul div:last-child');
  if (!briefing || briefing.dataset.loaded) return;
  briefing.dataset.loaded = '1';
  try {
    var r = await fetch(API_URL + '/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: 'genere un briefing pour une reunion produit', user_id: localStorage.getItem('ka_user_id')||'web'}),
      signal: AbortSignal.timeout(8000)
    });
    var d = await r.json();
    if (d.response && d.response.length > 20) briefing.textContent = d.response.slice(0, 300);
  } catch(e) {}
}

// ── VOYAGE ──
async function loadJourney() {
  var container = document.querySelector('#s-jrn .sp-body');
  if (!container || container.dataset.loaded) return;
  container.dataset.loaded = '1';
  try {
    var r = await fetch(API_URL + '/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: 'suggere un itineraire de voyage original', user_id: localStorage.getItem('ka_user_id')||'web'}),
      signal: AbortSignal.timeout(8000)
    });
    var d = await r.json();
    if (d.response) {
      var card = document.createElement('div');
      card.className = 'insight insight--wisdom';
      card.style.marginTop = '12px';
      card.innerHTML = '<div class="sec-lbl">💡 SUGGESTION KA</div><div style="font-size:13px;color:var(--t2);line-height:1.5">'+d.response.slice(0,250)+'</div>';
      container.appendChild(card);
    }
  } catch(e) {}
}

// ── DÉCISION ──
async function loadDecision() {
  var container = document.querySelector('#s-dec .sp-body');
  if (!container || container.dataset.loaded) return;
  container.dataset.loaded = '1';
  try {
    var r = await fetch(API_URL + '/api/reason', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: 'analyse les pour et contre de changer de voiture', user_id: localStorage.getItem('ka_user_id')||'web'}),
      signal: AbortSignal.timeout(8000)
    });
    var d = await r.json();
    if (d.response) {
      var card = document.createElement('div');
      card.className = 'insight insight--soul';
      card.style.marginTop = '12px';
      card.innerHTML = '<div class="sec-lbl">🧠 ANALYSE KA</div><div style="font-size:13px;color:var(--t2);line-height:1.5">'+d.response.slice(0,300)+'</div>';
      container.appendChild(card);
    }
  } catch(e) {}
}

// ── CAPTURE ──
async function loadCapture() {
  var input = document.querySelector('#s-cap .home__ib span');
  if (!input || input.dataset.hooked) return;
  input.dataset.hooked = '1';
  var ib = document.querySelector('#s-cap .home__ib');
  if (ib) {
    ib.onclick = async function() {
      var idea = prompt('Votre idée :');
      if (!idea) return;
      try {
        await fetch(API_URL + '/api/chat', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({message: 'apprends: ' + idea, user_id: localStorage.getItem('ka_user_id')||'web'})
        });
        input.textContent = '✨ Idée capturée !';
        setTimeout(function(){ input.textContent = 'Nouvelle idée…'; }, 2000);
      } catch(e) { input.textContent = '⚠️ Hors ligne'; }
    };
  }
}

// ── RELATION ──
async function loadRelation() {
  var container = document.querySelector('#s-rel .sp-body');
  if (!container || container.dataset.loaded) return;
  container.dataset.loaded = '1';
  try {
    var r = await fetch(API_URL + '/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: 'resume ma relation avec Sophie en 2 phrases', user_id: localStorage.getItem('ka_user_id')||'web'}),
      signal: AbortSignal.timeout(5000)
    });
    var d = await r.json();
    if (d.response) {
      var card = document.createElement('div');
      card.className = 'insight insight--rose';
      card.style.marginTop = '14px';
      card.innerHTML = '<div class="sec-lbl">💭 RÉSUMÉ KA</div><div style="font-size:13px;color:var(--t2);line-height:1.5">'+d.response.slice(0,200)+'</div>';
      container.appendChild(card);
    }
  } catch(e) {}
}

// ═══════════════════════════════════════════════════════════════════
// STORAGE OPTIMIZER
// ═══════════════════════════════════════════════════════════════════
let stoQuality = 'standard';
let stoFiles = [];
let stoUpscale4K = false;

function storageSetQuality(q) {
  stoQuality = q;
  ['arc','std','eco'].forEach(function(id) {
    var el = document.getElementById('sto-q-' + id);
    if (!el) return;
    el.className = 'pill';
    el.style.background = '';
    el.style.borderColor = '';
    el.style.color = '';
  });
  var sel = document.getElementById('sto-q-' + (q === 'archive' ? 'arc' : q === 'standard' ? 'std' : 'eco'));
  if (sel) {
    if (q === 'standard') { sel.className = 'pill pill--life'; }
    else if (q === 'eco') { sel.style.background = 'rgba(240,149,149,.12)'; sel.style.borderColor = 'rgba(240,149,149,.3)'; sel.style.color = 'var(--coral)'; }
    else { sel.style.background = 'rgba(139,131,255,.12)'; sel.style.borderColor = 'rgba(139,131,255,.3)'; sel.style.color = 'var(--soul-l)'; }
  }
}

function storageToggle4K() {
  stoUpscale4K = !stoUpscale4K;
  var bg = document.getElementById('sto-4k-toggle');
  var knob = document.getElementById('sto-4k-knob');
  var label = document.getElementById('sto-4k-label');
  if (stoUpscale4K) {
    bg.style.background = 'var(--life)';
    knob.style.left = '22px';
    label.textContent = '4K';
    label.style.color = 'var(--life)';
  } else {
    bg.style.background = 'var(--g1)';
    knob.style.left = '2px';
    label.textContent = 'OFF';
    label.style.color = 'var(--t4)';
  }
}

function storageSetQuality(q) {
  stoQuality = q;
  ['arc','std','eco'].forEach(function(id) {
    var el = document.getElementById('sto-q-' + id);
    if (!el) return;
    el.className = 'pill';
    el.style.background = '';
    el.style.borderColor = '';
    el.style.color = '';
  });
  var sel = document.getElementById('sto-q-' + (q === 'archive' ? 'arc' : q === 'standard' ? 'std' : 'eco'));
  if (sel) {
    if (q === 'standard') { sel.className = 'pill pill--life'; }
    else if (q === 'eco') { sel.style.background = 'rgba(240,149,149,.12)'; sel.style.borderColor = 'rgba(240,149,149,.3)'; sel.style.color = 'var(--coral)'; }
    else { sel.style.background = 'rgba(139,131,255,.12)'; sel.style.borderColor = 'rgba(139,131,255,.3)'; sel.style.color = 'var(--soul-l)'; }
  }
}

function fmtSize(bytes) {
  if (bytes < 1024) return bytes + ' o';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' Ko';
  return (bytes / 1048576).toFixed(1) + ' Mo';
}

function storageSelectFiles(fileList) {
  stoFiles = Array.from(fileList);
  var gauge = document.getElementById('sto-gauge');
  var results = document.getElementById('sto-results');
  var btn = document.getElementById('sto-optimize-btn');
  if (!stoFiles.length) { gauge.style.display = 'none'; btn.style.opacity = '.5'; btn.style.pointerEvents = 'none'; return; }

  // Analyser le lot
  var fd = new FormData();
  stoFiles.forEach(function(f) { fd.append('files', f); });
  results.innerHTML = '<div style="text-align:center;padding:14px;color:var(--t4);font-size:12px"><span style="animation:pulse 1.2s ease-in-out infinite">●</span> Analyse…</div>';

  fetch(API_URL + '/api/storage/optimize-batch', { method: 'POST', body: fd, signal: AbortSignal.timeout(30000) })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.error) { results.innerHTML = '<span style="color:var(--coral)">⚠️ ' + d.error + '</span>'; return; }
      gauge.style.display = 'block';
      btn.style.opacity = '1'; btn.style.pointerEvents = 'auto';

      var pct = d.total_original > 0 ? Math.round(d.total_saved / d.total_original * 100) : 0;
      document.getElementById('sto-saved-total').textContent = fmtSize(d.total_saved);
      document.getElementById('sto-orig-total').textContent = fmtSize(d.total_original);
      document.getElementById('sto-after-total').textContent = fmtSize(d.total_estimated_after);
      document.getElementById('sto-bar').style.width = Math.min(pct, 100) + '%';

      // Liste
      var html = '<div class="sec-lbl" style="margin-bottom:6px">FICHIERS (' + d.n_files + ')</div>';
      d.files.forEach(function(f) {
        var icon = f.media_type.indexOf('image') >= 0 ? '🖼️' : f.media_type.indexOf('video') >= 0 ? '🎬' : f.media_type.indexOf('voice') >= 0 ? '🎤' : '📄';
        html += '<div class="card" style="display:flex;align-items:center;gap:10px;margin-bottom:6px;padding:10px 12px"><span style="font-size:16px">' + icon + '</span>';
        html += '<div style="flex:1;min-width:0"><div style="font-size:12px;color:var(--t1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + f.filename + '</div>';
        html += '<div style="font-size:10px;color:var(--t4)">' + fmtSize(f.original_size) + ' → <span style="color:var(--life)">' + fmtSize(f.estimated_after) + '</span> (' + f.estimated_ratio + '×)</div></div>';
        html += '<span style="font-size:13px;font-weight:700;color:var(--life)">-' + Math.round(f.estimated_saved / f.original_size * 100) + '%</span></div>';
      });
      results.innerHTML = html;
    })
    .catch(function(e) {
      results.innerHTML = '<span style="color:var(--coral)">⚠️ API inaccessible — réessayez plus tard</span>';
      gauge.style.display = 'none';
    });
}

function storageOptimize() {
  if (!stoFiles.length) return;
  var results = document.getElementById('sto-results');
  var btn = document.getElementById('sto-optimize-btn');
  btn.style.opacity = '.5'; btn.style.pointerEvents = 'none';
  btn.textContent = '⏳ Optimisation…';

  var done = 0;
  var totalSaved = 0;
  var totalOrig = 0;

  stoFiles.forEach(function(f, idx) {
    var fd = new FormData();
    fd.append('file', f);
    fd.append('quality', stoQuality);

    fetch(API_URL + '/api/storage/optimize', { method: 'POST', body: fd, signal: AbortSignal.timeout(60000) })
      .then(function(r) {
        var ratio = parseFloat(r.headers.get('X-Ratio') || '1');
        var saved = parseInt(r.headers.get('X-Saved') || '0');
        var orig = parseInt(r.headers.get('X-Original-Size') || '0');
        var warning = r.headers.get('X-Warning') || '';
        totalSaved += saved; totalOrig += orig; done++;

        // Mettre à jour la liste pour ce fichier
        var cards = results.querySelectorAll('.card');
        if (cards[idx]) {
          var badge = cards[idx].querySelector('span:last-child');
          if (badge) {
            badge.textContent = warning ? '⚠️' : '✅';
            badge.style.color = warning ? 'var(--coral)' : 'var(--life)';
          }
        }

        if (done === stoFiles.length) {
          btn.textContent = '✅ Terminé';
          document.getElementById('sto-saved-total').textContent = fmtSize(totalSaved);
        }
      })
      .catch(function() {
        done++;
        if (done === stoFiles.length) { btn.textContent = '✅ Terminé'; }
      });
  });
}

// ── SANTÉ : bouton diagnostic ──
async function loadSante() {
  var resultEl = document.querySelector('#s-sante .result');
  var assessBtn = document.querySelector('#s-sante .btn--assess');
  if (!assessBtn || assessBtn.dataset.hooked) return;
  assessBtn.dataset.hooked = '1';
  assessBtn.onclick = async function() {
    var fc = document.getElementById('sante-fc')?.value;
    var spo2 = document.getElementById('sante-spo2')?.value;
    var temp = document.getElementById('sante-temp')?.value;
    if (!fc && !spo2 && !temp) {
      if (resultEl) { resultEl.style.display = 'block'; resultEl.innerHTML = '<div class="verdict verdict--treat">Veuillez entrer au moins une valeur vitale</div>'; }
      return;
    }
    if (resultEl) { resultEl.style.display = 'block'; resultEl.innerHTML = '<span style="color:var(--soul-l);animation:pulse 1.2s ease-in-out infinite">●</span> Analyse harmonique…'; }
    try {
      var resp = await fetch(API_URL + '/api/health/diagnostic', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          symptomes: [],
          vitaux: {
            frequence_cardiaque: parseInt(fc)||null,
            saturation_oxygene: parseInt(spo2)||null,
            temperature: parseFloat(temp)||null
          }
        }),
        signal: AbortSignal.timeout(10000)
      });
      var d = await resp.json();
      if (resultEl) {
        // Format de réponse: diagnostic_harmonique, analyse_vitales, recommandations
        var diag = d.diagnostic_harmonique;
        var vitales = d.analyse_vitales;
        var recos = d.recommandations || [];
        
        if (diag && diag.score_confiance > 0.6) {
          resultEl.innerHTML = '<div class="verdict verdict--urgent">🫀 '+(diag.pathologie_principale||'Anomalie détectée')+' — confiance '+(diag.score_confiance*100).toFixed(0)+'%</div>';
        } else if (vitales && vitales.score_harmonique_global < 0.7) {
          resultEl.innerHTML = '<div class="verdict verdict--treat">⚠️ Cohérence harmonique faible ('+(vitales.score_harmonique_global*100).toFixed(0)+'%)</div>';
        } else if (vitales && vitales.score_harmonique_global >= 0.7) {
          resultEl.innerHTML = '<div class="verdict verdict--ok">✅ Constantes harmoniques normales ('+(vitales.score_harmonique_global*100).toFixed(0)+'%)</div>';
        } else {
          resultEl.innerHTML = '<div class="verdict verdict--ok">✅ Aucune anomalie détectée</div>';
        }
        if (recos.length) {
          resultEl.innerHTML += '<div style="font-size:11px;color:var(--t4);margin-top:6px;text-align:center">'+recos.slice(0,2).join(' · ')+'</div>';
        }
      }
    } catch(e) {
      if (resultEl) resultEl.innerHTML = '<div class="verdict verdict--treat">⚠️ API inaccessible</div>';
    }
  };
}
			</script>
