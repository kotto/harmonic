/* ══════════════════════════════════════════════════════════════════════════
   KA SERVER SWITCH — reconfiguration du serveur KA (WebView uniquement)
   ══════════════════════════════════════════════════════════════════════════
   Ajoute un bouton discret « ⚙ » (coin supérieur droit) dans KA Phone Android :
   prompt avec l'adresse actuelle → sauvegarde localStorage['ka_api_url'] → reload.
   Inactif hors WebView (window.Capacitor absent).
   ══════════════════════════════════════════════════════════════════════════ */
(function () {
  if (typeof window.Capacitor === 'undefined') return;
  var KEY = 'ka_api_url';
  function current() {
    try { return localStorage.getItem(KEY) || ''; } catch (e) { return ''; }
  }
  function setUrl(u) {
    try { localStorage.setItem(KEY, u); return true; } catch (e) { return false; }
  }
  window.addEventListener('load', function () {
    var b = document.createElement('div');
    b.id = 'ka-srv-switch';
    b.textContent = '⚙';
    b.title = 'Changer le serveur KA';
    b.setAttribute('role', 'button');
    b.setAttribute('aria-label', 'Changer le serveur KA');
    b.style.cssText =
      'position:fixed;top:14px;right:14px;z-index:99999;width:36px;height:36px;border-radius:50%;' +
      'display:flex;align-items:center;justify-content:center;font-size:17px;cursor:pointer;' +
      'background:rgba(212,168,83,.12);border:1px solid rgba(212,168,83,.35);color:#d4a853;' +
      'opacity:.55;backdrop-filter:blur(6px);-webkit-tap-highlight-color:transparent';
    b.addEventListener('pointerdown', function (ev) { ev.stopPropagation(); });
    b.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var u = prompt('Adresse du serveur KA (ex. 192.168.1.42:8765) :', current());
      if (u === null) return;
      u = u.trim().replace(/\/+$/, '');
      if (!u) return;
      if (!/^https?:\/\//i.test(u)) u = 'http://' + u;
      var host = u.replace(/^https?:\/\//i, '').split('/')[0];
      if (!/:\d+$/.test(host)) u = u + ':8765';
      if (setUrl(u)) { location.reload(); }
    });
    document.body.appendChild(b);
  });
})();
