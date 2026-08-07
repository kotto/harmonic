#!/usr/bin/env python3
"""
Endpoints HPC / Calcul Scientifique
=====================================
Repliement protéique, simulation quantique, calcul NP-complet.
"""

import logging
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.hpc_job import HPCJob, HPCJobType, HPCJobStatus
from app.schemas.hpc import (
    ProteinFoldingRequest, ProteinStructure,
    QuantumSimulationRequest, QuantumSimulationResult,
    NPCompleteRequest, NPCompleteSolution,
    HPCJobRequest, HPCJobResponse, HPCStatsResponse,
)
from app.services.hpc_service import get_hpc_service, HPCService
import uuid
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


# ---- PROTEIN FOLDING ----

@router.post("/protein-folding", response_model=ProteinStructure)
async def protein_folding(
    request: ProteinFoldingRequest,
    current_user: User = Depends(get_current_user),
    service: HPCService = Depends(get_hpc_service),
    db: Session = Depends(get_db),
) -> Any:
    """Simulation de repliement protéique par résonance harmonique."""
    try:
        result = service.protein_folding(
            sequence=request.sequence,
            temperature=request.temperature,
            ph=request.ph,
            ensemble_size=request.ensemble_size,
            use_harmonic=request.use_harmonic_acceleration,
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Erreur de repliement"))

        # Créer un job HPC pour le suivi
        job = HPCJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=f"Protein Folding: {request.pdb_id or request.sequence[:20]}",
            job_type=HPCJobType.PROTEIN_FOLDING,
            status=HPCJobStatus.COMPLETED,
            parameters={"sequence": request.sequence, "temperature": request.temperature, "ph": request.ph},
            result=result,
            actual_duration_ms=result.get("computation_time_ms"),
            harmonic_speedup=result.get("harmonic_speedup"),
            confidence=result.get("confidence"),
            progress_percent=100.0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()

        return ProteinStructure(
            confidence=result["confidence"],
            free_energy=result["free_energy_kcal_mol"],
            harmonic_score=result["harmonic_score"],
            secondary_structure=result["secondary_structure"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Protein folding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---- QUANTUM SIMULATION ----

@router.post("/quantum-sim", response_model=QuantumSimulationResult)
async def quantum_simulation(
    request: QuantumSimulationRequest,
    current_user: User = Depends(get_current_user),
    service: HPCService = Depends(get_hpc_service),
    db: Session = Depends(get_db),
) -> Any:
    """Simulation quantique harmonique."""
    try:
        result = service.quantum_simulation(
            hamiltonian_type=request.hamiltonian_type,
            n_qubits=request.n_qubits,
            n_steps=request.n_steps,
            coupling_strength=request.coupling_strength,
            use_harmonic=request.use_harmonic_optimization,
        )

        job = HPCJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=f"Quantum: {request.hamiltonian_type} ({request.n_qubits}q)",
            job_type=HPCJobType.QUANTUM_SIMULATION,
            status=HPCJobStatus.COMPLETED,
            parameters=request.model_dump(),
            result=result,
            actual_duration_ms=result.get("computation_time_ms"),
            harmonic_speedup=result.get("harmonic_efficiency"),
            progress_percent=100.0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()

        return QuantumSimulationResult(**result)
    except Exception as e:
        logger.error(f"Quantum simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---- NP-COMPLETE ----

@router.post("/np-compute", response_model=NPCompleteSolution)
async def np_complete(
    request: NPCompleteRequest,
    current_user: User = Depends(get_current_user),
    service: HPCService = Depends(get_hpc_service),
    db: Session = Depends(get_db),
) -> Any:
    """Résolution NP-complète harmonique."""
    try:
        result = service.np_complete(
            problem_type=request.problem_type,
            problem_data=request.problem_data,
            time_limit=request.time_limit_seconds,
        )

        job = HPCJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=f"NP: {request.problem_type}",
            job_type=HPCJobType.NP_COMPLETE,
            status=HPCJobStatus.COMPLETED,
            parameters=request.model_dump(),
            result=result,
            actual_duration_ms=result.get("computation_time_ms"),
            harmonic_speedup=result.get("harmonic_speedup"),
            progress_percent=100.0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(job)
        db.commit()

        return NPCompleteSolution(**result)
    except Exception as e:
        logger.error(f"NP compute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---- JOBS ----

@router.get("/jobs", response_model=List[HPCJobResponse])
async def list_hpc_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Liste les jobs HPC de l'utilisateur."""
    jobs = db.query(HPCJob).filter(
        HPCJob.user_id == current_user.id
    ).order_by(HPCJob.created_at.desc()).limit(50).all()
    return [
        HPCJobResponse(
            job_id=j.id,
            job_type=j.job_type,
            status=j.status,
            created_at=j.created_at.isoformat() if j.created_at else "",
            result=j.result,
            progress_percent=j.progress_percent or 0.0,
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=HPCJobResponse)
async def get_hpc_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Récupère un job HPC spécifique."""
    job = db.query(HPCJob).filter(
        HPCJob.id == job_id,
        HPCJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job HPC non trouvé")
    return HPCJobResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at.isoformat() if job.created_at else "",
        estimated_duration_seconds=job.estimated_duration_seconds,
        result=job.result,
        progress_percent=job.progress_percent or 0.0,
        error_message=job.error_message,
    )


@router.get("/stats", response_model=HPCStatsResponse)
async def get_hpc_stats(
    service: HPCService = Depends(get_hpc_service),
) -> Any:
    """Statistiques des services HPC."""
    return HPCStatsResponse(**service.get_stats())
