/**
 * KA Phone — Code Studio
 */
/* global API_URL */

function codeGen() {
  var prompt = document.getElementById('code-prompt')?.value?.trim();
  var lang = document.getElementById('code-lang')?.value || 'python';
  var res = document.getElementById('code-result');
  if (!prompt) { res.style.display = 'block'; res.innerHTML = '<span style="color:var(--coral)">Veuillez décrire le code souhaité</span>'; return; }
  res.style.display = 'block'; res.innerHTML = '<span style="color:var(--soul-l);animation:pulse 1.2s ease-in-out infinite">●</span> Génération…';
  fetch(API_URL + '/api/code/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: prompt, language: lang }) })
    .then(function(r) { return r.json(); })
    .then(function(d) { res.textContent = d.code; res.style.color = 'var(--life)'; })
    .catch(function() {
      res.innerHTML = '<span style="color:var(--coral)">⚠️ API inaccessible</span>';
      var p = prompt.toLowerCase();
      if (p.indexOf('tri') >= 0 || p.indexOf('sort') >= 0)
        res.textContent = lang === 'python' ? 'def tri_rapide(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[0]\n    gauche = [x for x in arr[1:] if x <= pivot]\n    droite = [x for x in arr[1:] if x > pivot]\n    return tri_rapide(gauche) + [pivot] + tri_rapide(droite)' : 'function quickSort(arr) {\n  if (arr.length <= 1) return arr;\n  const pivot = arr[0];\n  const left = arr.slice(1).filter(x => x <= pivot);\n  const right = arr.slice(1).filter(x => x > pivot);\n  return [...quickSort(left), pivot, ...quickSort(right)];\n}';
      else if (p.indexOf('fibo') >= 0)
        res.textContent = lang === 'python' ? 'def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b' : 'function* fibonacci(n) {\n  let a = 0, b = 1;\n  for (let i = 0; i < n; i++) {\n    yield a;\n    [a, b] = [b, a + b];\n  }\n}';
      else
        res.textContent = lang === 'python' ? 'def solve(data):\n    """' + prompt.slice(0,50) + '"""\n    return data' : 'function solve(data) {\n  // ' + prompt.slice(0,50) + '\n  return data;\n}';
    });
}
