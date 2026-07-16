/**
 * KA Phone — Call Screen
 */
/* global callSecs, callIv */

let callSecs = 0, callIv = null;

function startCall() {
  callSecs = 0; clearInterval(callIv);
  callIv = setInterval(function() {
    callSecs++;
    var m = String(Math.floor(callSecs/60)).padStart(2,'0'), s = String(callSecs%60).padStart(2,'0');
    var el = document.getElementById('ctmr');
    if (el) el.textContent = m + ':' + s;
  }, 1000);
  var w = document.getElementById('cwv');
  if (!w) return;
  w.innerHTML = '';
  for (var i = 0; i < 22; i++) {
    var b = document.createElement('div');
    b.className = 'wb';
    b.style.cssText = '--wh:' + (3+Math.random()*22) + 'px;animation-duration:' + (0.35+Math.random()*0.5) + 's;animation-delay:' + (Math.random()*0.4) + 's';
    w.appendChild(b);
  }
}

function stopCall() { clearInterval(callIv); }

function buildCapWave() {
  var w = document.getElementById('capwv');
  if (!w) return;
  w.innerHTML = '';
  for (var i = 0; i < 18; i++) {
    var b = document.createElement('div');
    b.style.cssText = 'width:2.5px;border-radius:2px;background:rgba(61,219,160,.6);--wh:' + (3+Math.random()*16) + 'px;animation:wave ' + (0.35+Math.random()*0.5) + 's ease-in-out infinite alternate ' + (Math.random()*0.4) + 's';
    w.appendChild(b);
  }
}
