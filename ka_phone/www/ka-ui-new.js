// KA Phone UI — canonic endpoint: port 8420 /api/chat
var API='';
function showScreen(name){
  document.querySelectorAll('.ka-screen').forEach(function(s){s.classList.remove('active')});
  document.getElementById('screen-'+name).classList.add('active');
  var screens=['home','calls','chat','camera','system'];
  document.querySelectorAll('.ka-nav-btn').forEach(function(b,i){
    b.classList.toggle('active',screens[i]===name);
  });
}
function addMsg(t,w,meta){
  var d=document.createElement('div');d.className='km km-'+w;
  // 🌊 Détection diagnostic ondulatoire
  if(meta&&meta.source==='wave-debugger'){
    d.classList.add('km-debug');
    d.innerHTML='<span class="km-debug-badge">🌊</span>'+t;
  }else if(w==='bot'){
    d.innerHTML='<b>KA</b><br>'+t;
  }else{
    d.innerHTML=t;
  }
  document.getElementById('chat-overlay').appendChild(d);
  d.scrollIntoView({behavior:'smooth'});
}
async function sendChat(txt){
  var inp=document.getElementById('ka-inp'),t=txt||inp.value.trim();
  if(!t)return;addMsg(t,'user');if(!txt)inp.value='';
  try{
    var r=await fetch(API+'/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:t})});
    var d=await r.json();
    var meta={source:d.source||'',confidence:d.confidence!=null?d.confidence:d.confiance,latency:d.temps_ms||''};
    var txt=d.text||d.reponse||'';
    // Formater le texte markdown simple en HTML basique
    txt=txt.replace(/### (.*)/g,'<h4>$1</h4>');
    txt=txt.replace(/## (.*)/g,'<h3>$1</h3>');
    txt=txt.replace(/\\*\\*(.*?)\\*\\*/g,'<b>$1</b>');
    txt=txt.replace(/\\*(.*?)\\*/g,'<i>$1</i>');
    txt=txt.replace(/\|(.*)\|/g,'<tr><td>$1</td></tr>');
    txt=txt.replace(/> (.*)/g,'<blockquote>$1</blockquote>');
    txt=txt.replace(/```(.*?)```/gs,'<pre><code>$1</code></pre>');
    txt=txt.replace(/\n/g,'<br>');
    var footer='<br><small style="color:#a0a0b8">['+(meta.source||'KA')+' | '+(meta.latency||'')+'ms]</small>';
    addMsg(txt+footer,'bot',meta);
  }catch(e){addMsg('Erreur: '+e.message,'bot')}
}
document.getElementById('ka-send').onclick=function(){sendChat()};
document.getElementById('ka-inp').onkeydown=function(e){if(e.key==='Enter')sendChat()};

// 🌊 Raccourci /debug — tape /debug suivi du symptôme
var inp=document.getElementById('ka-inp');
inp.addEventListener('input',function(){
  var v=inp.value;
  if(v.startsWith('/debug ')||v.startsWith('debug:')||v.startsWith('🌊')){
    inp.style.borderColor='#00bcd4';
    inp.style.boxShadow='0 0 12px rgba(0,188,212,0.3)';
  }else{
    inp.style.borderColor='';
    inp.style.boxShadow='';
  }
});

var recognition=null,isListening=false;
function initVoice(){
  if(!('webkitSpeechRecognition' in window)&&!('SpeechRecognition' in window))return false;
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  recognition=new SR();recognition.lang='fr-FR';recognition.interimResults=false;recognition.continuous=false;
  recognition.onresult=function(e){var t=e.results[0][0].transcript;document.getElementById('ka-inp').value=t;sendChat(t)};
  recognition.onerror=function(){isListening=false;updateMicBtn()};
  recognition.onend=function(){isListening=false;updateMicBtn()};
  return true;
}
function toggleVoice(){
  if(!recognition&&!initVoice()){alert('Micro non supporte sur ce navigateur.');return}
  if(isListening){recognition.stop();isListening=false}else{recognition.start();isListening=true}
  updateMicBtn();
}
function updateMicBtn(){var b=document.getElementById('mic-btn');if(b){b.classList.toggle('listening',isListening);b.textContent=isListening?'🔴':'🎤'}}
try{initVoice()}catch(e){}