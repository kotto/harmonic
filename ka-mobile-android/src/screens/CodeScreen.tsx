import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import SpaceHeader from '@/components/layout/SpaceHeader'
import Button from '@/components/ui/Button'
import Pill from '@/components/ui/Pill'

export default function CodeScreen() {
  const navigate = useNavigate()
  const [mathInput, setMathInput] = useState('')
  const [mathResult, setMathResult] = useState('')
  const [codeInput, setCodeInput] = useState('')
  const [codeResult, setCodeResult] = useState('')

  const mathSolve = () => {
    try {
      // Simple math evaluation with safety
      const sanitized = mathInput
        .replace(/×/g, '*')
        .replace(/÷/g, '/')
        .replace(/% de /g, '*0.01*')
      // eslint-disable-next-line no-eval
      const result = Function('"use strict"; return (' + sanitized + ')')()
      setMathResult(String(result))
    } catch {
      setMathResult('❌ Expression invalide')
    }
  }

  const codeGen = async () => {
    setCodeResult('// Génération...\n')
    // Simulate code generation
    setTimeout(() => {
      const examples: Record<string, string> = {
        factorielle: `def factorielle(n):
    if n <= 1:
        return 1
    return n * factorielle(n - 1)

print(factorielle(10))  # 3628800`,
        'tri à bulles': `def tri_bulles(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr`,
        api: `from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/hello')
def hello():
    return jsonify({"message": "Hello World!"})

if __name__ == '__main__':
    app.run(debug=True)`,
      }

      const input = codeInput.toLowerCase()
      let code = ''
      if (input.includes('factorielle')) code = examples.factorielle
      else if (input.includes('tri') || input.includes('bulles')) code = examples['tri à bulles']
      else if (input.includes('api') || input.includes('flask')) code = examples.api
      else {
        code = `# Généré pour : ${codeInput}\n# (simulation — connectez-vous au serveur pour la génération réelle)\n\ndef reponse():\n    return "Code généré pour : ${codeInput}"`
      }
      setCodeResult(code)
    }, 800)
  }

  const quickCode = (prompt: string) => {
    setCodeInput(prompt)
    setTimeout(() => codeGen(), 100)
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden min-h-0"
      style={{ background: 'linear-gradient(160deg, #14201e 0%, #0a0e0d 100%)' }}>
      <SpaceHeader title="KA" badge="CODE & MATHS" badgeColor="life" backPath="/" />

      <div className="flex-1 overflow-y-auto px-5 hide-scrollbar min-h-0">
        <div className="text-center text-[12px] text-[var(--t4)] py-2">
          Calculs, algorithmes, formules — testez ici.
        </div>

        {/* Calculator */}
        <div className="mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">🧮 CALCULATRICE</div>
        <div className="flex gap-[6px] mb-3">
          <input
            value={mathInput}
            onChange={e => setMathInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && mathSolve()}
            placeholder="ex: 2+2, sqrt(144), 15% de 200"
            className="flex-1 px-[14px] py-[10px] rounded-[12px] text-[13px] outline-none"
            style={{ background: 'var(--g1)', border: '0.5px solid var(--b2)', color: 'var(--t1)' }}
          />
          <button
            onClick={mathSolve}
            className="rounded-[26px] px-4 py-[10px] text-[13px] cursor-pointer border-[0.5px]"
            style={{ background: 'var(--life-d)', borderColor: 'var(--life-g)', color: 'var(--life)' }}
          >
            =
          </button>
        </div>
        <div className="text-center text-[22px] font-bold text-[var(--life)] min-h-[30px] mb-4">
          {mathResult}
        </div>

        {/* Code generator */}
        <div className="mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">💻 GÉNÉRATEUR DE CODE</div>
        <div className="flex gap-[6px] mb-3">
          <input
            value={codeInput}
            onChange={e => setCodeInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && codeGen()}
            placeholder="ex: fonction fibonacci, trie une liste, api flask..."
            className="flex-1 px-[14px] py-[10px] rounded-[12px] text-[13px] outline-none"
            style={{ background: 'var(--g1)', border: '0.5px solid var(--b2)', color: 'var(--t1)' }}
          />
          <button
            onClick={codeGen}
            className="rounded-[26px] px-4 py-[10px] text-[13px] cursor-pointer border-[0.5px]"
            style={{ background: 'var(--soul-d)', borderColor: 'var(--soul-g)', color: 'var(--soul-l)' }}
          >
            ▶
          </button>
        </div>

        {/* Code output */}
        {codeResult && (
          <div className="rounded-[12px] p-4 mb-3 overflow-auto max-h-[300px]"
            style={{ background: '#0d1117', fontFamily: "'SF Mono', monospace", fontSize: '12px', color: '#c9d1d9', whiteSpace: 'pre-wrap' }}>
            {codeResult}
          </div>
        )}

        {/* Examples */}
        <div className="mb-2 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">📋 EXEMPLES DE REQUÊTES</div>
        <div className="grid grid-cols-2 gap-[6px] mb-4">
          {[
            'factorielle', 'tri à bulles', 'API Flask', 'palindrome', 'regex email', 'CSV Reader',
          ].map(ex => (
            <div
              key={ex}
              className="inline-flex items-center justify-center rounded-[20px] px-[10px] py-[4px] text-[10.5px] font-medium border-[0.5px] cursor-pointer text-center"
              style={{ background: 'var(--g1)', borderColor: 'var(--b2)', color: 'var(--t3)' }}
              onClick={() => quickCode('ecris un' + (ex.startsWith('API') ? 'e ' : 'e ') + ex + (ex === 'API Flask' ? '' : ' en python'))}
            >
              {ex.charAt(0).toUpperCase() + ex.slice(1)}
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-2 px-5 pb-[calc(14px+var(--sb))] pt-[10px] shrink-0">
        <Button color="ghost" onClick={() => navigate('/')}>Fermer</Button>
      </div>
    </div>
  )
}