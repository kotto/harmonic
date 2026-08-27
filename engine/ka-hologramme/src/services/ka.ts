import type { Hologramme } from '../types';

// Types
export interface ReponseKA {
  resultat: number;
  resultat_formate: string;
  explication: string;
  trajectoire_psi: string;
  conclusion: string;
  style: string;
}

export type StyleKA = 'conversationnel' | 'vocal' | 'bref' | 'pedagogique';

// Enrichisseur (version TypeScript de enrichisseur.py)
const CONCLUSIONS: Record<string, string> = {
  gain: 'Le gain total s eleve a {r}.',
  rapporte: 'Le gain total s eleve a {r}.',
  profit: 'Le profit est de {r}.',
  perte: 'La perte totale s eleve a {r}.',
  total: 'Le resultat est {r}.',
  augmentation: 'L augmentation est de {r}.',
  cout: 'Le cout est de {r}.',
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
  return 'Le resultat est ' + r + '.';
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
      parties.push('valeur initiale : ' + vs);
    } else if (op === 'MUL' && acc !== null) {
      const mulR: number = acc * valStr;
      parties.push('x ' + vs + ' -> ' + formaterNombre(acc) + ' x ' + vs + ' = ' + formaterNombre(mulR));
      acc = mulR;
    } else if (op === 'DIV' && acc !== null) {
      const divR: number = valStr ? acc / valStr : acc;
      parties.push('/ ' + vs + ' -> ' + formaterNombre(divR));
      acc = divR;
    } else if (op === 'ADD' && acc !== null) {
      const addR: number = acc + valStr;
      parties.push('+ ' + vs + ' -> ' + formaterNombre(addR));
      acc = addR;
    } else if (op === 'SUB' && acc !== null) {
      const subR: number = acc - valStr;
      parties.push('- ' + vs + ' -> ' + formaterNombre(subR));
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

/**
 * Pipeline complet : question vers codec psi vers enrichisseur
 * Utilise d'abord l'API /api/resoudre si disponible,
 * sinon fallback simulation locale.
 */
export async function resoudreAvecKA(
  question: string,
  hologramme: Hologramme | null,
  style: StyleKA = 'conversationnel'
): Promise<ReponseKA | { erreur: string }> {
  try {
    const resp = await fetch('/api/resoudre', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, style }),
    });
    if (!resp.ok) throw new Error('Erreur serveur');
    const data = await resp.json();
    if (data.success) {
      return {
        resultat: data.resultat,
        resultat_formate: data.resultat_formate,
        explication: data.etapes,
        trajectoire_psi: data.operations,
        conclusion: data.resultat_formate,
        style: data.style,
      };
    }
    throw new Error(data.error || 'Erreur inconnue');
  } catch {
    // Fallback simulation locale
    const m = question.match(/\d+/g);
    const vals = m ? m.map(Number) : [0];
    const ops = 'INIT(' + (vals[0] || 0) + ') MUL(' + ((vals[1] || 0) / 100) + ')';
    let rslt = (vals[0] || 0) * ((vals[1] || 0) / 100);
    return reponseRedigee(question, ops, rslt, style);
  }
}
