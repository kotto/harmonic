import type { Hologramme } from '../App';

// ─── Types ───
export interface ReponseKA {
  resultat: number;
  resultat_formate: string;
  explication: string;
  trajectoire_psi: string;
  conclusion: string;
  style: string;
}

// ─── Styles ───
export type StyleKA = 'conversationnel' | 'vocal' | 'bref' | 'pédagogique';

// ─── Enrichisseur (version TypeScript de enrichisseur.py) ───

const CONCLUSIONS: Record<string, string> = {
  gain: '💰 Le gain total s\'élève à {r}.',
  rapporte: '💰 Le gain total s\'élève à {r}.',
  profit: '💰 Le profit est de {r}.',
  perte: '📉 La perte totale s\'élève à {r}.',
  perd: '📉 La perte totale s\'élève à {r}.',
  total: '📊 Le résultat est {r}.',
  augmentation: '📈 L\'augmentation est de {r}.',
  augmente: '📈 L\'augmentation est de {r}.',
  cout: '💵 Le coût est de {r}.',
  investissement: '💎 Le retour sur investissement est de {r}.',
  loan: '🏦 Les intérêts du prêt sont de {r}.',
  prêt: '🏦 Les intérêts du prêt sont de {r}.',
  salaire: '👔 L\'augmentation de salaire est de {r}.',
};

function formaterNombre(v: number): string {
  return v === Math.floor(v)
    ? v.toLocaleString('fr-FR')
    : v.toLocaleString('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function detecterType(question: string): string {
  const q = question.toLowerCase();
  for (const kw of Object.keys(CONCLUSIONS)) {
    if (q.includes(kw)) return kw;
  }
  return 'CALC';
}

function conclure(question: string, r: string): string {
  const t = detecterType(question);
  if (t !== 'CALC' && CONCLUSIONS[t]) {
    return CONCLUSIONS[t].replace('{r}', r);
  }
  return `✅ Le résultat est ${r}.`;
}

function expliquerEtapes(operationsText: string): string {
  const ops = operationsText.replace(/\n/g, ' ').split(' ').filter(Boolean);
  let acc: number | null = null;
  const parties: string[] = [];

  for (const token of ops) {
    const m = token.match(/(INIT|MUL|SUB|ADD|DIV)\(([^)]+)\)/);
    if (!m) continue;
    const [op, valStr] = [m[1], parseFloat(m[2])];
    if (isNaN(valStr)) continue;
    const vs = formaterNombre(valStr);

    if (op === 'INIT') {
      acc = valStr;
      parties.push(`valeur initiale : ${vs}`);
    } else if (op === 'MUL' && acc !== null) {
      const mulR: number = acc * valStr;
      parties.push(`× ${vs} → ${formaterNombre(acc)} × ${vs} = ${formaterNombre(mulR)}`);
      acc = mulR;
    } else if (op === 'DIV' && acc !== null) {
      const divR: number = valStr ? acc / valStr : acc;
      parties.push(`÷ ${vs} → ${formaterNombre(divR)}`);
      acc = divR;
    } else if (op === 'ADD' && acc !== null) {
      const addR: number = acc + valStr;
      parties.push(`+ ${vs} → ${formaterNombre(addR)}`);
      acc = addR;
    } else if (op === 'SUB' && acc !== null) {
      const subR: number = acc - valStr;
      parties.push(`− ${vs} → ${formaterNombre(subR)}`);
      acc = subR;
    }
  }
  return parties.join(' · ');
}

export function reponseRedigee(
  question: string,
  operations: string,
  resultat: number,
  style: StyleKA = 'conversationnel'
): ReponseKA {
  const rs = formaterNombre(resultat);
  const expl = expliquerEtapes(operations);
  const stream = operations.replace(/\n/g, ' ').trim();
  const concl = conclure(question, rs);

  return {
    resultat,
    resultat_formate: rs,
    explication: expl,
    trajectoire_psi: stream,
    conclusion: concl,
    style,
  };
}

// ─── Pipeline complet : question → codec ψ → enrichisseur ───

export async function resoudreAvecKA(
  question: string,
  hologramme: Hologramme | null,
  style: StyleKA = 'conversationnel'
): Promise<ReponseKA | { erreur: string }> {
  // Appel à l'API Python /solveur_structure.py (via le backend)
  // Pour l'instant, on utilise une simulation qui sera remplacée par le vrai appel
  try {
    const resp = await fetch('/api/resoudre', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        hologramme_id: hologramme?.id,
        style,
      }),
    });
    if (!resp.ok) throw new Error('Erreur serveur');
    const data = await resp.json();
    return reponseRedigee(question, data.operations, data.resultat, style);
  } catch {
    // Fallback simulation pour le développement
    const m = question.match(/(\d+)/g);
    const vals = m ? m.map(Number) : [0];
    const ops = `INIT(${vals[0] || 0}) MUL(${(vals[1] || 0) / 100})`;
    let rslt: number = (vals[0] || 0) * ((vals[1] || 0) / 100);
    return reponseRedigee(question, ops, rslt, style);
  }
}