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

