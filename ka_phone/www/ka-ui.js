// KA Phone UI v3.0 — Phone complet (Appels, SMS, GPS, Appareil, Home)
var API='',shift=false,kbTarget=null,smsHist={};
function $(id){return document.getElementById(id)}

// ---- TABS ----
document.querySelectorAll('.kt').forEach(function(btn){
  btn.onclick=function(){
    document.querySelectorAll('.kt').forEach(function(b){b.classList.remove('active')});
    document.querySelectorAll('.ka-tc').forEach(function(c){c.classList.remove('active')});
    btn.classList.add('active');
    var t=$('ka-tab-'+btn.dataset.tab);
    if(t)t.classList.add('active');
    if(btn.dataset.tab!=='sms')hideKeyboard();
  }
});
function switchTab(name){
  hideKeyboard();
  document.querySelectorAll('.kt').forEach(function(b){b.classList.remove('active')});
  document.querySelectorAll('.ka-tc').forEach(function(c){c.classList.remove('active')});
  var btn=document.querySelector('.kt[data-tab="'+name+'"]');
  if(btn)btn.classList.add('active');
  var t=$('ka-tab-'+name);
  if(t)t.classList.add('active');
}

// ---- CLOCK ----
(function updateClock(){var now=new Date();var h=now.getHours().toString().padStart(2,'0');var m=now.getMinutes().toString().padStart(2,'0');var el=$('ka-st-time');if(el)el.textContent=h+':'+m;setTimeout(updateClock,30000)})();

// ---- DIAL PAD ----
function dial(ch){
  var el=$('ka-dial-num');if(!el)return;
  el.value+=ch;
}
function callNum(){
  var num=$('ka-dial-num');if(!num||!num.value.trim())return;
  addSMSMsg('ka-call-log','Appel en cours: '+num.value,'green');
  num.value='';
}

// ---- CHAT ----
async function sendChat(txt){
  var inp=$('ka-inp'),t=txt||inp.value.trim();if(!t)return;addMsg(t,'user');if(!txt)inp.value='';
  try{var r=await fetch(API+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:t})});var d=await r.json();var meta=d.source?d.source+' | '+d.confiance:'KA';addMsg(d.reponse+'<br><small style="color:var(--dim)">['+meta+' | '+d.temps_ms+'ms]</small>','bot')}catch(e){addMsg('Erreur: '+e.message,'bot')}
}
function addMsg(t,w){var d=document.createElement('div');d.className='km km-'+w;d.innerHTML=w==='bot'?'<b>KA</b><br>'+t:t;$('ka-msgs').appendChild(d);d.scrollIntoView({behavior:'smooth'})}
$('ka-send').onclick=function(){sendChat()};$('ka-inp').onkeydown=function(e){if(e.key==='Enter')sendChat()};

// ---- VOICE (Web Speech API - zero dependance) ----
var recognition=null,isListening=false,synth=window.speechSynthesis;
function initVoice(){
  if(!('webkitSpeechRecognition' in window)&&!('SpeechRecognition' in window)){console.log('Voice API non supportee');return false}
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  recognition=new SR();recognition.lang='fr-FR';recognition.interimResults=false;recognition.continuous=false;
  recognition.onresult=function(e){var t=e.results[0][0].transcript;$('ka-inp').value=t;sendChat(t)}
  recognition.onerror=function(e){isListening=false;updateMicButton()}
  recognition.onend=function(){isListening=false;updateMicButton()}
  return true
}
function toggleVoice(){
  if(!recognition&&!initVoice()){alert('Reconnaissance vocale non supportee sur ce navigateur.');return}
  if(isListening){recognition.stop();isListening=false}else{recognition.start();isListening=true}
  updateMicButton()
}
function updateMicButton(){var b=$('ka-mic');if(b)b.style.color=isListening?'var(--red)':'var(--dim)'}
function speakResponse(txt){if(!synth)return;synth.cancel();var u=new SpeechSynthesisUtterance(txt.replace(/<[^>]*>/g,'').replace(/\[.*?\]/g,'').substring(0,500));u.lang='fr-FR';u.rate=1.1;synth.speak(u)}
// Ajouter bouton micro + ecouteurs apres chaque reponse
try{initVoice()}catch(e){}

// ---- KEYBOARD ----
function showKeyboard(target){kbTarget=target||'ka-sms-inp';hideKeyboard();requestAnimationFrame(function(){$('ka-keyboard-overlay').classList.add('visible')})}
function hideKeyboard(){$('ka-keyboard-overlay').classList.remove('visible');kbTarget=null}
function kbPress(ch){
  if(ch==='BACK'){var el=$(kbTarget);if(el){var v=el.value;if(shift)v=v.slice(0,-2);else v=v.slice(0,-1);el.value=v;el.focus()}shift=false;return}
  if(ch==='SHIFT'){shift=!shift;return}
  if(ch==='123'){return}
  var el=$(kbTarget);if(!el)return;
  var c=shift?ch.toUpperCase():ch;el.value+=c;el.focus();if(ch!==' ')shift=false;
}
function kbPredict(word){var el=$(kbTarget);if(!el)return;var v=el.value,lastSpace=v.lastIndexOf(' ');el.value=(lastSpace>=0?v.substring(0,lastSpace+1):'')+word+' ';el.focus()}

// ---- SMS ----
function openSMS(contact){
  $('ka-sms-conversations').style.display='none';$('ka-sms-view').style.display='flex';
  $('ka-sms-contact').textContent=contact;
  var msgs=$('ka-sms-messages');msgs.innerHTML='';
  if(!smsHist[contact])smsHist[contact]=['Salut!','Comment vas-tu?','On se voit demain?'];
  smsHist[contact].forEach(function(m,i){var d=document.createElement('div');d.className='km '+(i%2===0?'km-bot':'km-user');d.textContent=m;msgs.appendChild(d);d.scrollIntoView({behavior:'smooth'})});
}
function closeSMS(){$('ka-sms-conversations').style.display='block';$('ka-sms-view').style.display='none';hideKeyboard()}
function sendSMS(){
  var inp=$('ka-sms-inp'),txt=inp.value.trim();if(!txt)return;
  var contact=$('ka-sms-contact').textContent;if(!smsHist[contact])smsHist[contact]=[];
  smsHist[contact].push(txt);
  var msgs=$('ka-sms-messages');var d=document.createElement('div');d.className='km km-user';d.textContent=txt;msgs.appendChild(d);d.scrollIntoView({behavior:'smooth'});
  inp.value='';hideKeyboard();
}

function addSMSMsg(containerId,text,color){
  var el=$(containerId);if(!el)return;
  var d=document.createElement('div');d.className='sms-thread';
  d.innerHTML='<div class="sms-avatar">📞</div><div class="sms-preview"><span style="color:var(--'+color+')">'+text+'</span></div>';
  el.insertBefore(d,el.firstChild);
}

// ---- GPS ----
$('ka-gps-btn').onclick=function(){
  var out=$('ka-gps-out');if(!out)return;
  out.innerHTML='<b>📍 Position simulée</b><br>Lat: 48.8566° N · Lon: 2.3522° E<br>Paris, France<br><small style="color:var(--dim)">GPS hors-ligne actif | Précision: 5m</small>';
};

// ---- SYSTEM ----
(function loadStatus(){
  try{
    var r=fetch(API+'/api/system/status').then(function(r){return r.json()}).then(function(d){
      var el=$('ka-sys-info');if(el)el.innerHTML='<b>v'+d.version+'</b><br>Hologramme: '+d.hologramme_tokens.toLocaleString()+' tokens<br>LLM: '+(d.llm_loaded?'Qwen2.5-3B':'MGH hors-ligne')+'<br>Mode: '+d.mode;
      var tok=$('ka-st-tok');if(tok)tok.textContent=(d.hologramme_tokens/1e6).toFixed(0)+'M tok';
    });
  }catch(e){var el=$('ka-sys-info');if(el)el.innerHTML='Serveur hors-ligne'}
})();

// Keyboard overlay click-outside
$('ka-keyboard-overlay').addEventListener('click',function(e){if(e.target===this)hideKeyboard()});