#!/usr/bin/env python3
"""
Tests de la conversion v1 → v2 à la demande (HologramStore.ensure_v2).
=====================================================================
Mesures du 10/08/2026 : le processus de conversion (cahier des charges)
est porté dans l'engine ; ensure_v2() convertit un hologramme v1 dormant
et REBUILD le NPZ au format wave v2 (ψ redérivé des faits) quand la
conversion est ACCEPTÉE.

Ces tests utilisent un store_dir TEMPORAIRE (aucune écriture dans le
store de production) — le backup v1 est lu depuis
data/hologram_store/backup_v1_conversion/.
"""

import os
import shutil

import pytest

sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PYTHONPATH", sys_path)

from hologram_store import HologramStore

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP = os.path.join(ENGINE, "data", "hologram_store", "backup_v1_conversion")


def test_ensure_v2_id_inconnu(tmp_path):
    """Id inconnu (aucun NPZ, aucune table) → inconnu, rien n'est écrit."""
    store = HologramStore(store_dir=str(tmp_path))
    res = store.ensure_v2("official_zzz_inexistant")
    assert res["status"] == "inconnu"
    assert res["rebuilt"] is False


@pytest.mark.skipif(
    not os.path.exists(os.path.join(ENGINE, "data",
                                    "domaine_converti_official_culture",
                                    "rapport_conversion.json")),
    reason="cache de conversion absent (data/domaine_converti_official_culture)")
def test_ensure_v2_rebuild_dans_store_temp(tmp_path):
    """Cache de conversion existant + NPZ absent → le NPZ v2 est rebuildé
    dans le STORE TEMPORAIRE (jamais dans le store de production)."""
    store = HologramStore(store_dir=str(tmp_path))
    res = store.ensure_v2("official_culture")
    assert res["rebuilt"] is True
    assert res["facts_count"] >= 200
    assert (tmp_path / "official_culture.npz").exists()
    # Le NPZ produit est wave v2 (ψ redérivé des faits du cache).
    # NB : _GLOBAL_DEDUP (cross-domaine) peut écarter quelques faits déjà
    # enregistrés par un autre domaine (ex. capitales partagées géo/culture)
    # → le compte du NPZ peut être légèrement inférieur au cache.
    facts_v2, psi = store.download("official_culture")
    assert 200 <= len(facts_v2) <= res["facts_count"]
    assert "hologram_memory" in psi


@pytest.mark.skipif(
    not os.path.exists(os.path.join(BACKUP, "official_geographie.npz")),
    reason="backup v1 absent (data/hologram_store/backup_v1_conversion)")
def test_ensure_v2_bout_en_bout_rebuild(tmp_path):
    """Bout en bout : NPZ v1 → conversion ACCEPTÉE → NPZ v2 rebuildé
    dans le store temporaire (le store de production n'est pas touché)."""
    shutil.copy(os.path.join(BACKUP, "official_geographie.npz"),
                tmp_path / "official_geographie.npz")
    shutil.copy(os.path.join(BACKUP, "registry.json"),
                tmp_path / "registry.json")

    store = HologramStore(store_dir=str(tmp_path))
    facts_v1, _ = store.download("official_geographie")
    assert len(facts_v1) > 0, "le NPZ v1 du backup doit contenir des faits"

    res = store.ensure_v2("official_geographie")
    assert res["rebuilt"] is True
    assert res["facts_count"] >= 300  # ≥ la démo vérifiée (313)

    facts_v2, psi = store.download("official_geographie")
    assert len(facts_v2) == res["facts_count"]
    assert "hologram_memory" in psi, "le NPZ rebuildé est wave v2"
    assert "psi_subjects" in psi and "psi_objects" in psi

    meta = store._registry["official_geographie"]
    assert meta.version == 2
    # Les faits v2 sont les faits vérifiés de la conversion (0 contradiction
    # sur les relations fonctionnelles — contrôlé par la conversion elle-même)
    assert any(str(f[0]) == "bresil" and str(f[2]) == "brasilia"
               for f in facts_v2), "le domaine converti contient les faits vérifiés"
