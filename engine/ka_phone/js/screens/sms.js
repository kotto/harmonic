/**
 * KA Phone — SMS
 */
/* global API_URL */

var smsCurrentContact = '';
var smsHistory = JSON.parse(localStorage.getItem('ka_sms_history') || '{}');

function smsOpen(name) {
  smsCurrentContact = name;
  document.getElementById('sms-contacts').style.display = 'none';
  document.getElementById('sms-chat').style.display = 'block';
  document.getElementById('sms-chat-name').textContent = name;
  
  var messages = smsHistory[name] || [];
  var html = '';
  messages.forEach(function(m) {
    var cls = m.from === 'me' ? 'msg--m' : 'msg--t';
    html += '<div class="msg ' + cls + '" style="margin-bottom:4px">' + m.text + '</div>';
  });
  if (!messages.length) html = '<div style="text-align:center;color:var(--t4);padding:20px;font-size:12px">Aucun message. Dites bonjour !</div>';
  document.getElementById('sms-messages').innerHTML = html;
}

function smsSend() {
  var input = document.getElementById('sms-input');
  var text = input.value.trim();
  if (!text || !smsCurrentContact) return;
  
  if (!smsHistory[smsCurrentContact]) smsHistory[smsCurrentContact] = [];
  smsHistory[smsCurrentContact].push({ from: 'me', text: text, time: Date.now() });
  localStorage.setItem('ka_sms_history', JSON.stringify(smsHistory));
  
  input.value = '';
  smsOpen(smsCurrentContact);
  
  // Tenter l'envoi via SMS URI
  try { window.open('sms:?body=' + encodeURIComponent(text), '_blank'); } catch(e) {}
}

function smsNew() {
  var name = prompt('Nom du contact :');
  if (!name) return;
  smsHistory[name] = smsHistory[name] || [];
  localStorage.setItem('ka_sms_history', JSON.stringify(smsHistory));
  smsOpen(name);
}
