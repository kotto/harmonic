"""
simulation.py — Simulation multi-agents de téléphones réels via internet
========================================================================
Simule des interactions entre plusieurs téléphones (patients, médecins, diaspora)
qui ne sont PAS sur le même réseau local mais communiquent à travers internet.

Chaque agent est un « téléphone virtuel » avec :
  - Une identité (wallet_id, rôle, nom, localisation)
  - Des conditions réseau simulées (latence, débit, coupures)
  - Un comportement autonome (créditer, payer, convertir, etc.)

La simulation orchestre ces agents et enregistre chaque événement dans une
timeline horodatée, comme si les vrais téléphones échangeaient via l'API KARE.

Stockage des résultats : data/banking/simulation_results.json (persistant).
"""

from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import settlement
from .ecobank_gateway import get_ecobank_client, UM_TO_CFA
from .sonic_id import sonic_id_wav

log = logging.getLogger(__name__)

# ── Répertoire de persistance ─────────────────────────────────────────────────

def _sim_dir() -> Path:
    raw = os.environ.get("KA_BANKING_DIR", "")
    base = Path(raw) if raw else Path(__file__).resolve().parent.parent.parent / "data" / "banking"
    return base


def _sim_results_path() -> Path:
    return _sim_dir() / "simulation_results.json"


_sim_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════════════════════════
#  Modèles
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SimAgent:
    """Un téléphone virtuel participant à la simulation.

    Chaque agent vit dans une ville, a un rôle, et communique avec une latence
    réseau simulée (ping aléatoire entre min_ms et max_ms).
    """
    wallet_id: str
    role: str          # patient | medecin | pharmacie | labo | solidarite
    name: str          # nom humain lisible
    location: str      # ville / pays
    network_latency_min_ms: int = 50   # ping minimum
    network_latency_max_ms: int = 300  # ping maximum
    reliability: float = 0.95          # probabilité qu'une requête réussisse
    bank_account: Optional[str] = None

    # État interne (géré par la simulation)
    balance_um: float = 0.0
    transactions: List[Dict] = field(default_factory=list)
    online: bool = True

    def simulate_latency(self):
        """Simule le délai réseau (bloque le thread courant)."""
        if not self.online:
            raise ConnectionError(f"{self.name} est hors-ligne")
        latency = random.randint(self.network_latency_min_ms,
                                 self.network_latency_max_ms)
        if latency > 0:
            time.sleep(latency / 1000.0)

    def simulate_reliability(self):
        """Simule une perte de paquet ou timeout."""
        if random.random() > self.reliability:
            raise TimeoutError(f"{self.name} : timeout réseau (perte {1-self.reliability:.0%})")


@dataclass
class SimEvent:
    """Un événement atomique de la simulation."""
    timestamp: float
    agent: str          # wallet_id qui a déclenché l'action
    action: str         # credit | debit | conversion | collect | reconcile
    detail: str         # description lisible
    amount_um: float = 0.0
    amount_fiat: float = 0.0
    currency: str = "XOF"
    success: bool = True
    error: Optional[str] = None
    latency_ms: float = 0.0
    target: Optional[str] = None  # wallet_id destinataire
    tx_id: Optional[str] = None      # identifiant de transaction (ledger)
    sonic_id: Optional[str] = None    # empreinte sonore pseudo-aléatoire (URL)
    sonic_variant: Optional[str] = None  # mobile | care | default


# ── Rôles → variante sonore (même système que l'API Sonic ID) ────────────────

ROLE_SONIC_VARIANT = {
    "patient": "mobile",
    "medecin": "care",
    "pharmacie": "mobile",
    "labo": "care",
    "solidarite": "default",
}


@dataclass
class SimScenario:
    """Configuration d'un scénario de simulation."""
    name: str
    description: str
    agents: List[SimAgent]
    script: List[Callable]  # liste de fonctions à exécuter dans l'ordre
    iterations: int = 1      # nombre de répétitions du script


# ═══════════════════════════════════════════════════════════════════════════════
#  Moteur de simulation
# ═══════════════════════════════════════════════════════════════════════════════

class SimulationEngine:
    """Orchestre la simulation multi-agents.

    Usage :
        engine = SimulationEngine()
        engine.load_scenario("consultation_transfrontaliere")
        engine.run()  # les agents communiquent via l'API KARE
        engine.save_results()
        engine.summary()  # résumé de la simulation
    """

    def __init__(self):
        self.agents: Dict[str, SimAgent] = {}
        self.events: List[SimEvent] = []
        self._running = False
        self._scenario_name = ""
        self._scenario_description = ""
        self._start_time = 0.0
        self._end_time = 0.0

    # ── Chargement des scénarios ────────────────────────────────────────────

    def load_scenario(self, name: str):
        """Charge un scénario prédéfini par son nom."""
        scenarios = self._builtin_scenarios()
        if name not in scenarios:
            raise ValueError(f"Scénario inconnu : {name}. "
                             f"Disponibles : {list(scenarios.keys())}")
        scenario = scenarios[name]
        self._scenario_name = scenario.name
        self._scenario_key = name  # clé machine (pour le résumé)
        self._scenario_description = scenario.description
        self.agents = {a.wallet_id: a for a in scenario.agents}
        self._script = scenario.script
        log.info(f"📋 Scénario chargé : {scenario.name} ({len(scenario.agents)} agents, "
                 f"{len(scenario.script)} étapes)")

    def load_custom_scenario(self, name: str, description: str,
                             agents: List[Dict], steps: List[Dict]):
        """Charge un scénario personnalisé depuis un dict JSON."""
        parsed_agents = []
        for a in agents:
            parsed_agents.append(SimAgent(
                wallet_id=a["wallet_id"],
                role=a.get("role", "patient"),
                name=a.get("name", a["wallet_id"]),
                location=a.get("location", "Inconnu"),
                network_latency_min_ms=a.get("latency_min_ms", 50),
                network_latency_max_ms=a.get("latency_max_ms", 300),
                reliability=a.get("reliability", 0.95),
                bank_account=a.get("bank_account"),
            ))
        self._scenario_name = name
        self._scenario_key = "custom"  # clé machine
        self._scenario_description = description
        self.agents = {a.wallet_id: a for a in parsed_agents}
        self._script = self._parse_custom_steps(steps)
        log.info(f"📋 Scénario personnalisé chargé : {name} ({len(parsed_agents)} agents, "
                 f"{len(steps)} étapes)")

    def _parse_custom_steps(self, steps: List[Dict]) -> List[Callable]:
        """Convertit des étapes dict en fonctions exécutables."""
        parsed = []
        for step in steps:
            action = step.get("action", "")
            params = {k: v for k, v in step.items() if k != "action"}

            def _make(act=action, pa=params):
                def _fn(engine):
                    return engine._execute_step(act, **pa)
                return _fn
            parsed.append(_make())
        return parsed

    # ── Scénarios intégrés ───────────────────────────────────────────────────

    def _builtin_scenarios(self) -> Dict[str, SimScenario]:
        return {
            "consultation_transfrontaliere": SimScenario(
                name="Consultation transfrontalière Abidjan ↔ Paris",
                description="Un patient à Abidjan consulte un médecin de la diaspora à Paris "
                            "par téléconsultation. Le médecin prescrit, le pharmacien délivre, "
                            "le médecin convertit ses honoraires en EUR.",
                agents=[
                    SimAgent("PAT-ABIDJAN", "patient", "Moussa Diallo",
                             "Abidjan, Côte d'Ivoire", 80, 250, 0.92),
                    SimAgent("MED-PARIS", "medecin", "Dr. Fatoumata Koné",
                             "Paris, France", 120, 400, 0.88,
                             bank_account="BANK_MED_PARIS"),
                    SimAgent("PHM-ABIDJAN", "pharmacie", "Pharmacie Centrale",
                             "Abidjan, Côte d'Ivoire", 50, 200, 0.95,
                             bank_account="BANK_PHM_ABIDJAN"),
                ],
                script=self._build_consultation_script(),
            ),
            "aide_diaspora": SimScenario(
                name="Aide de la diaspora — New York → Bamako",
                description="Une membre de la diaspora à New York envoie de l'argent "
                            "à sa famille à Bamako via UM. Le patient paie une consultation "
                            "et des médicaments. Le médecin convertit en CFA.",
                agents=[
                    SimAgent("SOL-NEWYORK", "solidarite", "Aïssata Traoré",
                             "New York, USA", 200, 600, 0.85),
                    SimAgent("PAT-BAMAKO", "patient", "Amadou Traoré",
                             "Bamako, Mali", 100, 350, 0.90),
                    SimAgent("MED-BAMAKO", "medecin", "Dr. Sékou Camara",
                             "Bamako, Mali", 80, 250, 0.92,
                             bank_account="BANK_MED_BAMAKO"),
                    SimAgent("PHM-BAMAKO", "pharmacie", "Pharmacie du Fleuve",
                             "Bamako, Mali", 60, 200, 0.94,
                             bank_account="BANK_PHM_BAMAKO"),
                ],
                script=self._build_diaspora_script(),
            ),
            "reseau_soins_urgents": SimScenario(
                name="Réseau de soins urgents — 3 patients, 2 médecins, 1 labo",
                description="Trois patients dans différentes villes consultent des médecins "
                            "en urgence. La solidarité se mobilise. Les labos analysent. "
                            "Les prestataires convertissent leurs UM en CFA.",
                agents=[
                    SimAgent("PAT-URG1", "patient", "Kadiatou Diallo",
                             "Conakry, Guinée", 70, 250, 0.88),
                    SimAgent("PAT-URG2", "patient", "Mamadou Barry",
                             "Conakry, Guinée", 80, 300, 0.85),
                    SimAgent("PAT-URG3", "patient", "Aminata Sow",
                             "Dakar, Sénégal", 90, 280, 0.90),
                    SimAgent("MED-URG1", "medecin", "Dr. Ibrahima Sy",
                             "Conakry, Guinée", 50, 200, 0.95,
                             bank_account="BANK_MED_URG1"),
                    SimAgent("MED-URG2", "medecin", "Dr. Mariam Touré",
                             "Dakar, Sénégal", 60, 220, 0.94,
                             bank_account="BANK_MED_URG2"),
                    SimAgent("LABO-URG", "labo", "Labo BioMed",
                             "Conakry, Guinée", 40, 180, 0.96,
                             bank_account="BANK_LABO_URG"),
                    SimAgent("SOL-URG", "solidarite", "Solidarité Guinée",
                             "Paris, France", 150, 500, 0.87),
                ],
                script=self._build_urgence_script(),
            ),
        }

    # ── Scripts intégrés ──────────────────────────────────────────────────

    def _build_consultation_script(self) -> List[Callable]:
        def s01(e): return e._create_account("PAT-ABIDJAN")
        def s02(e): return e._create_account("MED-PARIS")
        def s03(e): return e._create_account("PHM-ABIDJAN")
        def s04(e): return e._credit("PAT-ABIDJAN", 200, "Aide famille — ouverture dossier")
        def s05(e): return e._debit("PAT-ABIDJAN", "MED-PARIS", 50, "Téléconsultation cardiologie")
        def s06(e): return e._debit("PAT-ABIDJAN", "PHM-ABIDJAN", 35, "Médicaments prescrits")
        def s07(e): return e._conversion("MED-PARIS", 50, "EUR")
        def s08(e): return e._reconcile()
        return [s01, s02, s03, s04, s05, s06, s07, s08]

    def _build_diaspora_script(self) -> List[Callable]:
        def s01(e): return e._create_account("SOL-NEWYORK")
        def s02(e): return e._create_account("PAT-BAMAKO")
        def s03(e): return e._create_account("MED-BAMAKO")
        def s04(e): return e._create_account("PHM-BAMAKO")
        def s05(e): return e._solidarite_credit("SOL-NEWYORK", "PAT-BAMAKO", 150, "Envoi famille — Aïssata → Amadou")
        def s06(e): return e._debit("PAT-BAMAKO", "MED-BAMAKO", 40, "Consultation générale")
        def s07(e): return e._debit("PAT-BAMAKO", "PHM-BAMAKO", 25, "Traitement antipaludéen")
        def s08(e): return e._conversion("MED-BAMAKO", 40, "XOF")
        def s09(e): return e._conversion("PHM-BAMAKO", 25, "XOF")
        def s10(e): return e._reconcile()
        return [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10]

    def _build_urgence_script(self) -> List[Callable]:
        def s01(e): return e._create_account("SOL-URG")
        def s02(e): return e._create_account("PAT-URG1")
        def s03(e): return e._create_account("PAT-URG2")
        def s04(e): return e._create_account("PAT-URG3")
        def s05(e): return e._create_account("MED-URG1")
        def s06(e): return e._create_account("MED-URG2")
        def s07(e): return e._create_account("LABO-URG")
        # Urgence : solidarité se mobilise
        def s08(e): return e._solidarite_credit("SOL-URG", "PAT-URG1", 300, "Urgence — Kadiatou")
        def s09(e): return e._solidarite_credit("SOL-URG", "PAT-URG2", 150, "Urgence — Mamadou")
        def s10(e): return e._solidarite_credit("SOL-URG", "PAT-URG3", 200, "Urgence — Aminata")
        # Consultations
        def s11(e): return e._debit("PAT-URG1", "MED-URG1", 60, "Consultation urgente — Kadiatou")
        def s12(e): return e._debit("PAT-URG2", "MED-URG1", 40, "Consultation — Mamadou")
        def s13(e): return e._debit("PAT-URG3", "MED-URG2", 55, "Consultation urgente — Aminata")
        # Analyses labo
        def s14(e): return e._debit("PAT-URG1", "LABO-URG", 45, "Analyses sanguines complètes")
        def s15(e): return e._debit("PAT-URG2", "LABO-URG", 30, "Bilan infectieux")
        # Conversions
        def s16(e): return e._conversion("MED-URG1", 100, "XOF")
        def s17(e): return e._conversion("MED-URG2", 55, "XOF")
        def s18(e): return e._conversion("LABO-URG", 75, "XOF")
        def s19(e): return e._reconcile()
        return [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10,
                s11, s12, s13, s14, s15, s16, s17, s18, s19]

    # ── Exécution des actions ────────────────────────────────────────────────

    def _execute_step(self, action: str, **kwargs):
        """Exécute une action atomique et retourne l'événement."""
        action_map = {
            "create_account": self._create_account,
            "credit": self._credit,
            "debit": self._debit,
            "solidarite_credit": self._solidarite_credit,
            "conversion": self._conversion,
            "reconcile": self._reconcile,
            "sleep": self._sleep,
        }
        fn = action_map.get(action)
        if fn is None:
            raise ValueError(f"Action inconnue : {action}")
        return fn(**kwargs)

    def _record(self, agent_id: str, action: str, detail: str, *,
                amount_um=0.0, amount_fiat=0.0, currency="XOF",
                success=True, error=None, latency_ms=0.0, target=None,
                tx_id=None, sonic_id=None, sonic_variant=None):
        event = SimEvent(
            timestamp=time.time(),
            agent=agent_id,
            action=action,
            detail=detail,
            amount_um=amount_um,
            amount_fiat=amount_fiat,
            currency=currency,
            success=success,
            error=error,
            latency_ms=latency_ms,
            target=target,
            tx_id=tx_id,
            sonic_id=sonic_id,
            sonic_variant=sonic_variant,
        )
        self.events.append(event)
        return event

    def _sonic_emit(self, agent_id: str, tx_id: str) -> str:
        """Génère l'URL d'empreinte sonore pseudo-aléatoire pour une transaction.

        Le son est déterministe : le même tx_id produira toujours le même WAV.
        Chaque téléphone (agent) a sa variante sonore selon son rôle :
          - patient    → "mobile" (vif, majeur)
          - medecin    → "care"   (lent, grave, apaisant)
          - pharmacie  → "mobile"
          - labo       → "care"
          - solidarite → "default" (équilibré)

        Le WAV est pré-généré et mis en cache (LRU 512) par sonic_id_wav(),
        donc la première génération est lente (~50ms) mais les suivantes
        sont instantanées.

        Retourne l'URL API : /api/sonic-id/{tx_id}?variant={variant}
        """
        agent = self._agent(agent_id)
        variant = ROLE_SONIC_VARIANT.get(agent.role, "default")
        # Pré-génération pour remplir le cache (le navigateur ira chercher l'URL)
        try:
            sonic_id_wav(tx_id, variant=variant)
        except Exception:
            pass  # le cache n'est pas critique
        return f"/api/sonic-id/{tx_id}?variant={variant}"

    def _agent(self, wallet_id: str) -> SimAgent:
        agent = self.agents.get(wallet_id)
        if not agent:
            raise ValueError(f"Agent inconnu : {wallet_id}")
        return agent

    def _ensure_account(self, agent: SimAgent):
        """Crée le compte sur le serveur (idempotent)."""
        settlement.upsert_account(agent.wallet_id, agent.role,
                                  bank_account=agent.bank_account)

    def _create_account(self, wallet_id: str, **kwargs):
        agent = self._agent(wallet_id)
        agent.simulate_latency()
        agent.simulate_reliability()
        t0 = time.time()
        try:
            self._ensure_account(agent)
            latency = (time.time() - t0) * 1000
            agent.balance_um = 0.0
            return self._record(wallet_id, "create_account",
                                f"📱 {agent.name} ({agent.role}) — {agent.location}",
                                latency_ms=latency)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return self._record(wallet_id, "create_account",
                                f"❌ {agent.name} : échec création compte",
                                success=False, error=str(e), latency_ms=latency)

    def _credit(self, wallet_id: str, amount_um: float, description: str = "", **kwargs):
        agent = self._agent(wallet_id)
        agent.simulate_latency()
        agent.simulate_reliability()
        t0 = time.time()
        try:
            result = settlement.credit_um(wallet_id, amount_um,
                                          description=description,
                                          tx_type="solidarite_credit")
            latency = (time.time() - t0) * 1000
            if result.get("ok"):
                tx_id = result["tx"]["txId"]
                sonic_url = self._sonic_emit(wallet_id, tx_id)
                agent.balance_um = settlement.get_account(wallet_id)["balance_um"]
                return self._record(wallet_id, "credit",
                                    f"💚 +{amount_um} UM → {agent.name} ({description})",
                                    amount_um=amount_um, latency_ms=latency,
                                    tx_id=tx_id, sonic_id=sonic_url,
                                    sonic_variant=ROLE_SONIC_VARIANT.get(agent.role, "default"))
            else:
                return self._record(wallet_id, "credit",
                                    f"❌ {agent.name} : {result.get('error', 'refus')}",
                                    success=False, amount_um=amount_um,
                                    error=result.get("error"), latency_ms=latency)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return self._record(wallet_id, "credit", f"❌ {agent.name} : {str(e)}",
                                success=False, amount_um=amount_um, error=str(e),
                                latency_ms=latency)

    def _debit(self, wallet_id: str, target: str, amount_um: float,
               description: str = "", **kwargs):
        agent = self._agent(wallet_id)
        target_agent = self._agent(target)
        agent.simulate_latency()
        agent.simulate_reliability()
        t0 = time.time()
        try:
            result = settlement.debit_um(wallet_id, amount_um, target,
                                         description=description)
            latency = (time.time() - t0) * 1000
            if result.get("ok"):
                tx_id = result["tx"]["txId"]
                # L'émetteur (payeur) génère le son
                sonic_url = self._sonic_emit(wallet_id, tx_id)
                agent.balance_um = settlement.get_account(wallet_id)["balance_um"]
                target_agent.balance_um = settlement.get_account(target)["balance_um"]
                return self._record(wallet_id, "debit",
                                    f"💳 {agent.name} → {target_agent.name} : {amount_um} UM ({description})",
                                    amount_um=amount_um, target=target, latency_ms=latency,
                                    tx_id=tx_id, sonic_id=sonic_url,
                                    sonic_variant=ROLE_SONIC_VARIANT.get(agent.role, "default"))
            else:
                return self._record(wallet_id, "debit",
                                    f"❌ {agent.name} → {target_agent.name} : {result.get('error', 'refus')}",
                                    success=False, amount_um=amount_um,
                                    target=target, error=result.get("error"),
                                    latency_ms=latency)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return self._record(wallet_id, "debit", f"❌ {agent.name} : {str(e)}",
                                success=False, amount_um=amount_um,
                                target=target, error=str(e), latency_ms=latency)

    def _solidarite_credit(self, from_id: str, to_id: str, amount_um: float,
                           description: str = "", **kwargs):
        """Crédit de solidarité : le donneur identifie le bénéficiaire."""
        agent = self._agent(from_id)
        target = self._agent(to_id)
        agent.simulate_latency()
        agent.simulate_reliability()
        t0 = time.time()
        try:
            result = settlement.credit_um(to_id, amount_um,
                                          description=description,
                                          tx_type="solidarite_credit")
            latency = (time.time() - t0) * 1000
            if result.get("ok"):
                tx_id = result["tx"]["txId"]
                # Le donneur (diaspora) émet le son de la transaction
                sonic_url = self._sonic_emit(from_id, tx_id)
                target.balance_um = settlement.get_account(to_id)["balance_um"]
                return self._record(from_id, "solidarite_credit",
                                    f"🤝 {agent.name} → {target.name} : +{amount_um} UM ({description})",
                                    amount_um=amount_um, target=to_id, latency_ms=latency,
                                    tx_id=tx_id, sonic_id=sonic_url,
                                    sonic_variant=ROLE_SONIC_VARIANT.get(agent.role, "default"))
            else:
                return self._record(from_id, "solidarite_credit",
                                    f"❌ {agent.name} → {target.name} : {result.get('error', 'refus')}",
                                    success=False, amount_um=amount_um,
                                    target=to_id, error=result.get("error"),
                                    latency_ms=latency)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return self._record(from_id, "solidarite_credit",
                                f"❌ {agent.name} : {str(e)}",
                                success=False, amount_um=amount_um,
                                target=to_id, error=str(e), latency_ms=latency)

    def _conversion(self, wallet_id: str, amount_um: float, currency: str = "XOF",
                    **kwargs):
        agent = self._agent(wallet_id)
        agent.simulate_latency()
        agent.simulate_reliability()
        t0 = time.time()
        try:
            result = settlement.request_conversion(
                wallet_id, amount_um, currency,
                {"bank_account": agent.bank_account})
            latency = (time.time() - t0) * 1000
            if not result.get("ok"):
                return self._record(wallet_id, "conversion",
                                    f"❌ {agent.name} : {result.get('error', 'refus')}",
                                    success=False, amount_um=amount_um,
                                    error=result.get("error"), latency_ms=latency)

            conv_id = result["conversion"]["id"]
            # Émission sonore : le prestataire émet un son pour la conversion
            sonic_url = self._sonic_emit(wallet_id, conv_id)

            # Exécuter le règlement
            agent.simulate_latency()
            settle_result = settlement.execute_settlement(conv_id)
            latency2 = (time.time() - t0) * 1000
            settled = settle_result.get("conversion", {}).get("status") == "settled"
            cfa = amount_um * UM_TO_CFA
            if settled:
                agent.balance_um = settlement.get_account(wallet_id)["balance_um"]
                return self._record(wallet_id, "conversion",
                                    f"🔁 {agent.name} : {amount_um} UM → {cfa:,.0f} {currency} ✅",
                                    amount_um=amount_um, amount_fiat=cfa,
                                    currency=currency, latency_ms=latency2,
                                    tx_id=conv_id, sonic_id=sonic_url,
                                    sonic_variant=ROLE_SONIC_VARIANT.get(agent.role, "default"))
            else:
                return self._record(wallet_id, "conversion",
                                    f"❌ {agent.name} : conversion {amount_um} UM échouée",
                                    success=False, amount_um=amount_um,
                                    error="settlement_failed", latency_ms=latency2)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return self._record(wallet_id, "conversion", f"❌ {agent.name} : {str(e)}",
                                success=False, amount_um=amount_um, error=str(e),
                                latency_ms=latency)

    def _reconcile(self, **kwargs):
        t0 = time.time()
        try:
            date_iso = time.strftime("%Y-%m-%d")
            result = settlement.reconcile(date_iso)
            latency = (time.time() - t0) * 1000
            return self._record("SYSTEM", "reconcile",
                                f"⚖️ Rapprochement {date_iso} : "
                                + ("✅ équilibré" if result.get("balanced") else "❌ écart détecté"),
                                success=result.get("balanced", False),
                                latency_ms=latency)
        except Exception as e:
            latency = (time.time() - t0) * 1000
            return self._record("SYSTEM", "reconcile",
                                f"❌ Rapprochement : {str(e)}",
                                success=False, error=str(e), latency_ms=latency)

    def _sleep(self, seconds: float = 1.0, **kwargs):
        time.sleep(seconds)
        return self._record("SYSTEM", "sleep",
                            f"⏸️ Pause {seconds}s",
                            success=True, latency_ms=seconds*1000)

    # ── Lancement de la simulation ───────────────────────────────────────────

    def run(self, *, reset_first: bool = True, on_event: Optional[Callable] = None) -> List[SimEvent]:
        """Exécute la simulation complète.

        Args:
            reset_first: Si True, reset l'état avant de commencer.
            on_event: Callback optionnel appelé à chaque événement (pour UI temps réel).

        Retourne la liste des événements.
        """
        self._running = True
        self._start_time = time.time()
        self.events = []

        if reset_first:
            settlement.reset_state()
            get_ecobank_client().reset()

        log.info(f"▶️ Simulation démarrée : {self._scenario_name}")

        for i, step_fn in enumerate(self._script):
            if not self._running:
                break
            try:
                event = step_fn(self)
                if on_event:
                    on_event(event)
                self._log_event(event)
            except Exception as e:
                event = self._record("SYSTEM", "error",
                                     f"💥 Erreur inattendue étape {i}: {str(e)}",
                                     success=False, error=str(e))
                if on_event:
                    on_event(event)
                self._log_event(event)
                break

        self._end_time = time.time()
        self._running = False
        log.info(f"✅ Simulation terminée : {len(self.events)} événements en "
                 f"{self._end_time - self._start_time:.1f}s")
        self.save_results()
        return self.events

    def stop(self):
        """Arrête la simulation en cours."""
        self._running = False
        log.info("⏹️ Simulation arrêtée")

    def _log_event(self, event: SimEvent):
        icon = "✅" if event.success else "❌"
        log.info(f"  {icon} [{event.agent}] {event.detail} "
                 f"({event.latency_ms:.0f}ms)")

    # ── Persistance ──────────────────────────────────────────────────────────

    def save_results(self):
        """Sauvegarde les résultats dans un fichier JSON."""
        data = self.to_dict()
        with _sim_lock:
            path = _sim_results_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            # Charger l'historique
            try:
                if path.exists():
                    history = json.loads(path.read_text(encoding="utf-8"))
                else:
                    history = []
            except Exception:
                history = []
            # Ajouter cette simulation
            history.append(data)
            # Garder les 10 dernières
            if len(history) > 10:
                history = history[-10:]
            path.write_text(json.dumps(history, indent=2, ensure_ascii=False),
                            encoding="utf-8")

    def to_dict(self) -> Dict:
        """Sérialise la simulation (pour l'API et la sauvegarde)."""
        return {
            "scenario": self._scenario_name,
            "scenario_key": getattr(self, '_scenario_key', ''),
            "description": self._scenario_description,
            "started_at": self._start_time,
            "ended_at": self._end_time,
            "duration_s": round(self._end_time - self._start_time, 1),
            "agents": [
                {
                    "wallet_id": a.wallet_id,
                    "role": a.role,
                    "name": a.name,
                    "location": a.location,
                    "balance_um": a.balance_um,
                    "network_latency_ms": f"{a.network_latency_min_ms}-{a.network_latency_max_ms}",
                    "reliability": a.reliability,
                }
                for a in self.agents.values()
            ],
            "events": [
                {
                    "time": e.timestamp,
                    "time_str": time.strftime("%H:%M:%S", time.localtime(e.timestamp)),
                    "agent": e.agent,
                    "action": e.action,
                    "detail": e.detail,
                    "amount_um": e.amount_um,
                    "amount_fiat": e.amount_fiat,
                    "currency": e.currency,
                    "success": e.success,
                    "error": e.error,
                    "latency_ms": round(e.latency_ms, 1),
                    "target": e.target,
                    "tx_id": e.tx_id,
                    "sonic_id": e.sonic_id,
                    "sonic_variant": e.sonic_variant,
                }
                for e in self.events
            ],
            "events_count": len(self.events),
            "success_count": sum(1 for e in self.events if e.success),
            "fail_count": sum(1 for e in self.events if not e.success),
            "total_um_moved": sum(e.amount_um for e in self.events
                                  if e.action in ("credit", "debit", "solidarite_credit") and e.success),
        }

    def summary(self) -> Dict:
        """Résumé de la simulation (pour l'API)."""
        return {
            "scenario": self._scenario_name,
            "scenario_key": getattr(self, '_scenario_key', ''),
            "description": self._scenario_description,
            "duration_s": round(self._end_time - self._start_time, 1) if self._end_time else 0,
            "agents": len(self.agents),
            "events": len(self.events),
            "success": sum(1 for e in self.events if e.success),
            "fail": sum(1 for e in self.events if not e.success),
            "total_um": sum(e.amount_um for e in self.events
                            if e.action in ("credit", "debit", "solidarite_credit") and e.success),
            "running": self._running,
        }

    def get_events_since(self, since_time: float) -> List[Dict]:
        """Retourne les événements depuis un timestamp (pour polling UI)."""
        return [
            e for e in self.to_dict()["events"]
            if e["time"] > since_time
        ]


# ═══════════════════════════════════════════════════════════════════════════════
#  Singleton (le moteur est global pour permettre le polling UI)
# ═══════════════════════════════════════════════════════════════════════════════

_engine: Optional[SimulationEngine] = None
_engine_lock = threading.Lock()


def get_engine() -> SimulationEngine:
    """Retourne le moteur de simulation courant (singleton)."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = SimulationEngine()
        return _engine


def run_scenario(name: str, *, reset_first: bool = True,
                 on_event: Optional[Callable] = None,
                 deterministic: bool = False) -> Dict:
    """Charge et exécute un scénario intégré. Retourne le résumé.

    Args:
        name: Nom du scénario intégré.
        reset_first: Reset l'état avant de commencer.
        on_event: Callback optionnel pour chaque événement.
        deterministic: Si True, force tous les agents à 100% de fiabilité
                       et latence minimale (pour les tests).
    """
    engine = get_engine()
    engine.load_scenario(name)
    if deterministic:
        for agent in engine.agents.values():
            agent.reliability = 1.0
            agent.network_latency_min_ms = 0
            agent.network_latency_max_ms = 0
    engine.run(reset_first=reset_first, on_event=on_event)
    return engine.summary()


def run_custom_scenario(name: str, description: str,
                        agents: List[Dict], steps: List[Dict],
                        *, reset_first: bool = True,
                        on_event: Optional[Callable] = None) -> Dict:
    """Charge et exécute un scénario personnalisé. Retourne le résumé."""
    engine = get_engine()
    engine.load_custom_scenario(name, description, agents, steps)
    engine.run(reset_first=reset_first, on_event=on_event)
    return engine.summary()


def list_scenarios() -> List[Dict]:
    """Liste les scénarios intégrés disponibles."""
    engine = SimulationEngine()
    return [
        {"name": name, "description": s.description,
         "agents": len(s.agents), "steps": len(s.script)}
        for name, s in engine._builtin_scenarios().items()
    ]


def list_results() -> List[Dict]:
    """Liste les résultats des simulations précédentes."""
    path = _sim_results_path()
    if not path.exists():
        return []
    try:
        with _sim_lock:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


__all__ = [
    "SimulationEngine", "SimAgent", "SimEvent",
    "get_engine", "run_scenario", "run_custom_scenario",
    "list_scenarios", "list_results",
]