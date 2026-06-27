// KA Phone UI — canonic endpoint: port 8420 /api/ask
var API='';
function showScreen(name){
  document.querySelectorAll('.ka-screen').forEach(function(s){s.classList.remove('active')});
  document.getElementById('screen-'+name).classList.add('active');
  var screens=['home','calls','chat','camera','system'];
  document.querySelectorAll('.ka-nav-btn').forEach(function(b,i){
    b.classList.toggle('active',screens[i]===name);
  });
}
function addMsg(t,w){
  var d=document.createElement('div');d.className='km km-'+w;
  d.innerHTML=w==='bot'?'<b>KA</b><br>'+t:t;
  document.getElementById('chat-overlay').appendChild(d);
  d.scrollIntoView({behavior:'smooth'});
}
async function sendChat(txt){
  var inp=document.getElementById('ka-inp'),t=txt||inp.value.trim();
  if(!t)return;addMsg(t,'user');if(!txt)inp.value='';
  try{
    var r=await fetch(API+'/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:t})});
    var d=await r.json();
    var meta=d.source?d.source+' | '+(d.confidence!=null?d.confidence:d.confiance):'KA';
    var txt=d.text||d.reponse||'';
    addMsg(txt+'<br><small style="color:#a0a0b8">['+meta+' | '+(d.temps_ms||'')+'ms]</small>','bot');
  }catch(e){addMsg('Erreur: '+e.message,'bot')}
}
document.getElementById('ka-send').onclick=function(){sendChat()};
document.getElementById('ka-inp').onkeydown=function(e){if(e.key==='Enter')sendChat()};

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