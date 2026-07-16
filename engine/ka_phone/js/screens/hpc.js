/**
 * KA Phone — HPC Lab (Protein Folding, Quantum, HCV)
 */
/* global API_URL */

// ── HPC LAB ──
let hpcMode='protein';
function setQuality(val, label){
  document.getElementById('hpc-quality').value = val;
  document.getElementById('hpc-q-label').textContent = label;
  ['eco','std','pro','max'].forEach(function(id){
    var el=document.getElementById('hpc-q-'+id);
    el.style.background='rgba(255,255,255,.04)';el.style.border='.5px solid var(--b2)';el.style.color='var(--t3)';
  });
  var map={20:'eco',45:'std',70:'pro',100:'max'};
  var sel=document.getElementById('hpc-q-'+map[val]);
  if(sel){sel.style.background='var(--life-d)';sel.style.border='.5px solid var(--life)';sel.style.color='var(--life)';}
  hpcRun();
}
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

