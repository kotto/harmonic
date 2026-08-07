#!/usr/bin/env python3
"""
Schémas HPC / Calcul Scientifique
===================================
Modèles pour le calcul haute performance : repliement protéique, simulation quantique,
calcul NP-complet, dynamique moléculaire.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class HPCJobType(str, Enum):
    """Types de jobs HPC supportés."""
    PROTEIN_FOLDING = "protein_folding"
    QUANTUM_SIMULATION = "quantum_simulation"
    NP_COMPLETE = "np_complete"
    MOLECULAR_DYNAMICS = "molecular_dynamics"
    FLUID_DYNAMICS = "fluid_dynamics"
    WEATHER_MODELING = "weather_modeling"
    GENOMIC_ANALYSIS = "genomic_analysis"
    FINANCIAL_MODELING = "financial_modeling"


class HPCJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---- Protein Folding ----

class ProteinFoldingRequest(BaseModel):
    """Requête de simulation de repliement protéique."""
    sequence: str = Field(..., min_length=3, max_length=5000, description="Séquence d'acides aminés (1 lettre)")
    fasta: Optional[str] = Field(default=None, description="Séquence au format FASTA")
    pdb_id: Optional[str] = Field(default=None, description="ID PDB de référence (optionnel)")
    temperature: float = Field(default=310.0, ge=273.0, le=373.0, description="Température en Kelvin")
    ph: float = Field(default=7.0, ge=0.0, le=14.0)
    ensemble_size: int = Field(default=10, ge=1, le=100, description="Nombre de conformations à générer")
    use_harmonic_acceleration: bool = Field(default=True, description="Activer l'accélération harmonique φ")


class ProteinStructure(BaseModel):
    """Structure protéique prédite."""
    pdb_data: Optional[str] = Field(default=None, description="Structure au format PDB")
    confidence: float = Field(ge=0.0, le=1.0)
    free_energy: float = Field(description="Énergie libre calculée (kcal/mol)")
    rmsd: Optional[float] = Field(default=None, description="RMSD par rapport à la référence")
    secondary_structure: Dict[str, float] = Field(default_factory=dict, description="% hélice α, feuillet β, boucle")
    harmonic_score: float = Field(description="Score de cohérence harmonique (φ)")

# ---- Quantum Simulation ----

class QuantumSimulationRequest(BaseModel):
    """Requête de simulation quantique."""
    hamiltonian_type: str = Field(default="ising", description="Type d'hamiltonien: ising, heisenberg, hubbard")
    n_qubits: int = Field(default=8, ge=2, le=64)
    n_steps: int = Field(default=100, ge=10, le=10000)
    coupling_strength: float = Field(default=1.0)
    use_harmonic_optimization: bool = Field(default=True)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class QuantumSimulationResult(BaseModel):
    """Résultat de simulation quantique."""
    ground_state_energy: float
    energy_spectrum: List[float] = Field(default_factory=list)
    wave_function_summary: Dict[str, float] = Field(default_factory=dict)
    entanglement_entropy: Optional[float] = None
    computation_time_ms: float
    harmonic_efficiency: float = Field(description="Gain harmonique vs méthode classique")

# ---- NP-Complete ----

class NPCompleteRequest(BaseModel):
    """Requête de résolution NP-complète harmonique."""
    problem_type: str = Field(default="sat", description="Type: sat, tsp, knapsack, graph_coloring")
    problem_data: Dict[str, Any] = Field(..., description="Données du problème")
    max_solutions: int = Field(default=1, ge=1, le=100)
    time_limit_seconds: float = Field(default=60.0, ge=1.0, le=3600.0)


class NPCompleteSolution(BaseModel):
    """Solution NP-complète trouvée."""
    solution: Dict[str, Any]
    is_optimal: bool = False
    objective_value: float
    computation_time_ms: float
    harmonic_speedup: float = Field(description="Facteur d'accélération harmonique")

# ---- Generic HPC Job ----

class HPCJobRequest(BaseModel):
    """Requête générique de job HPC."""
    job_type: HPCJobType
    name: str = Field(default="HPC Job")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    input_data: Optional[str] = Field(default=None, description="Données d'entrée (texte)")
    input_file_url: Optional[str] = Field(default=None)
    priority: int = Field(default=1, ge=1, le=5)

class HPCJobResponse(BaseModel):
    """Réponse à un job HPC."""
    job_id: str
    job_type: HPCJobType
    status: HPCJobStatus
    created_at: str
    estimated_duration_seconds: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class HPCStatsResponse(BaseModel):
    """Statistiques HPC."""
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    average_speedup: float
    co2_saved_kg: float = Field(description="CO₂ économisé vs calcul classique")
    cpu_hours_saved: float
