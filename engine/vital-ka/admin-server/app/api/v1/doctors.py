# ──────────────────────────────────────────────
# API Docteurs - Inscription, KYC, Validation, Annuaire
# ──────────────────────────────────────────────
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from fastapi import (
    APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
)
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import (
    get_db, get_current_user, get_current_doctor, require_permission,
    get_client_info, log_audit, ClientInfo
)
from app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    Role, Permission,
)
from app.models import Doctor, KYCDocument, VerificationLog, User, DoctorStatus, KYCDocumentType
from app.schemas import (
    DoctorRegisterRequest, DoctorProfileUpdate, DoctorValidateRequest,
    DoctorRejectRequest, DoctorSuspendRequest, DoctorSearchFilters,
    KYCDocumentUploadRequest, KYCDocumentVerifyRequest,
    DoctorResponse, DoctorListResponse, DoctorSearchResponse,
    DoctorStatusResponse, KYCDocumentResponse, VerificationLogResponse,
    TokenResponse, DoctorLoginRequest, DoctorLoginResponse,
)
from app.services.storage_service import storage_service
from app.services.email_service import email_service


router = APIRouter(prefix="/doctors", tags=["Doctors"])


# ──────────────────────────────────────────────
# PUBLIC: Inscription Médecin
# ──────────────────────────────────────────────
@router.post("/register", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
async def register_doctor(
    data: DoctorRegisterRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Inscription d'un nouveau médecin (public)"""
    from app.core.config import settings
    
    if not settings.enable_doctor_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inscriptions temporairement fermées",
        )

    # Vérifier email unique
    existing = await db.execute(
        select(Doctor).where(Doctor.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email déjà utilisé",
        )

    # Vérifier license_number unique
    existing = await db.execute(
        select(Doctor).where(Doctor.license_number == data.license_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Numéro de licence déjà enregistré",
        )

    # Créer médecin
    doctor = Doctor(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        license_number=data.license_number,
        specialty=data.specialty,
        sub_specialty=data.sub_specialty,
        years_experience=data.years_experience,
        country=data.country,
        city=data.city,
        practice_address=data.practice_address,
        coordinates=data.coordinates,
        status=DoctorStatus.PENDING,
    )
    db.add(doctor)
    await db.flush()

    # Log audit
    await log_audit(
        db, "doctor.register", "doctor", doctor.id,
        doctor=doctor, client=client,
        new_values={"email": data.email, "license_number": data.license_number},
        success=True,
    )

    await db.commit()
    await db.refresh(doctor)

    # Email de confirmation
    try:
        await email_service.send_doctor_registration_confirmation(doctor)
    except Exception:
        pass  # Log mais ne pas faire échouer

    return doctor


# ──────────────────────────────────────────────
# PUBLIC: Connexion Médecin
# ──────────────────────────────────────────────
@router.post("/login", response_model=DoctorLoginResponse)
async def login_doctor(
    data: DoctorLoginRequest,
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Connexion médecin"""
    result = await db.execute(
        select(Doctor).where(Doctor.email == data.email)
    )
    doctor = result.scalar_one_or_none()

    if not doctor or not verify_password(data.password, doctor.password_hash):
        # Log tentative échouée
        await log_audit(
            db, "doctor.login_failed", "doctor", None,
            client=client,
            metadata={"email": data.email},
            success=False,
            error_message="Identifiants invalides",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    if doctor.status not in (DoctorStatus.VALIDATED, DoctorStatus.UNDER_REVIEW):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Compte non validé (statut: {doctor.status.value})",
        )

    # Mettre à jour last_login
    doctor.last_login = datetime.now(timezone.utc)
    doctor.login_count += 1

    # Créer tokens
    access_token = create_access_token(doctor.id, doctor.email, Role.DOCTOR)
    refresh_token = create_refresh_token(doctor.id, doctor.email, Role.DOCTOR)

    # Log audit
    await log_audit(
        db, "doctor.login", "doctor", doctor.id,
        doctor=doctor, client=client,
        success=True,
    )

    await db.commit()

    return DoctorLoginResponse(
        doctor=doctor,
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=1800,  # 30 min
        ),
    )


# ──────────────────────────────────────────────
# PROTECTED: Profil médecin connecté
# ──────────────────────────────────────────────
@router.get("/me", response_model=DoctorResponse)
async def get_my_profile(
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Profil du médecin connecté"""
    # Charger relations
    result = await db.execute(
        select(Doctor)
        .options(selectinload(Doctor.documents), selectinload(Doctor.verification_logs))
        .where(Doctor.id == doctor.id)
    )
    return result.scalar_one()


@router.put("/me", response_model=DoctorResponse)
async def update_my_profile(
    data: DoctorProfileUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Mise à jour profil médecin connecté"""
    old_values = {
        "first_name": doctor.first_name,
        "last_name": doctor.last_name,
        "phone": doctor.phone,
        "specialty": doctor.specialty,
        "city": doctor.city,
        "country": doctor.country,
    }

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)

    doctor.updated_at = datetime.now(timezone.utc)

    await log_audit(
        db, "doctor.profile_update", "doctor", doctor.id,
        doctor=doctor, client=client,
        old_values=old_values,
        new_values=update_data,
        success=True,
    )

    await db.commit()
    await db.refresh(doctor)

    # Recharger avec relations
    result = await db.execute(
        select(Doctor)
        .options(selectinload(Doctor.documents), selectinload(Doctor.verification_logs))
        .where(Doctor.id == doctor.id)
    )
    return result.scalar_one()


# ──────────────────────────────────────────────
# PROTECTED: Statut KYC médecin connecté
# ──────────────────────────────────────────────
@router.get("/me/status", response_model=DoctorStatusResponse)
async def get_my_status(
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Statut KYC du médecin connecté"""
    docs_verified = sum(1 for d in doctor.documents if d.is_verified)
    docs_total = len(doctor.documents)

    return DoctorStatusResponse(
        id=doctor.id,
        email=doctor.email,
        status=doctor.status,
        validated_at=doctor.validated_at,
        rejection_reason=doctor.rejection_reason,
        documents_verified=docs_verified,
        documents_total=docs_total,
    )


# ──────────────────────────────────────────────
# KYC Documents - Upload
# ──────────────────────────────────────────────
@router.post("/me/documents", response_model=KYCDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_kyc_document(
    document_type: KYCDocumentType = Form(...),
    file: UploadFile = File(...),
    doctor: Doctor = Depends(get_current_doctor),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Upload document KYC"""
    from app.core.config import settings
    
    # Vérifier type MIME
    allowed_types = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    }
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non supporté: {file.content_type}",
        )

    # Vérifier taille (max 10MB)
    max_size = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop volumineux (max 10MB)",
        )

    # Vérifier si document existe déjà
    existing = await db.execute(
        select(KYCDocument).where(
            KYCDocument.doctor_id == doctor.id,
            KYCDocument.document_type == document_type,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document {document_type.value} déjà existant",
        )

    # Upload vers MinIO
    file_path = f"kyc/{doctor.id}/{document_type.value}/{file.filename}"
    await storage_service.upload_file(file_path, content, file.content_type)

    # Créer entrée en base
    doc = KYCDocument(
        doctor_id=doctor.id,
        document_type=document_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
    )
    db.add(doc)

    await log_audit(
        db, "doctor.kyc_upload", "kyc_document", doc.id,
        doctor=doctor, client=client,
        new_values={"document_type": document_type.value, "file_name": file.filename},
        success=True,
    )

    await db.commit()
    await db.refresh(doc)

    return doc


@router.get("/me/documents", response_model=list[KYCDocumentResponse])
async def list_my_documents(
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Lister documents KYC du médecin connecté"""
    result = await db.execute(
        select(KYCDocument).where(KYCDocument.doctor_id == doctor.id)
        .order_by(KYCDocument.created_at.desc())
    )
    return result.scalars().all()


@router.get("/me/documents/{doc_id}/download")
async def download_my_document(
    doc_id: UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Télécharger document KYC (URL signée)"""
    result = await db.execute(
        select(KYCDocument).where(
            KYCDocument.id == doc_id,
            KYCDocument.doctor_id == doctor.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    url = await storage_service.get_presigned_url(doc.file_path, expires_in=3600)
    return {"url": url, "expires_in": 3600}


# ──────────────────────────────────────────────
# ADMIN/VALIDATOR: Gestion médecins
# ──────────────────────────────────────────────
@router.get("", response_model=DoctorSearchResponse)
async def search_doctors(
    filters: DoctorSearchFilters = Depends(),
    current_user: User = Depends(require_permission(Permission.DOCTOR_LIST)),
    db: AsyncSession = Depends(get_db),
):
    """Recherche/Liste médecins (admin/validator)"""
    query = select(Doctor)

    # Filtres
    conditions = []
    if filters.status:
        conditions.append(Doctor.status == filters.status)
    if filters.specialty:
        conditions.append(Doctor.specialty.ilike(f"%{filters.specialty}%"))
    if filters.city:
        conditions.append(Doctor.city.ilike(f"%{filters.city}%"))
    if filters.country:
        conditions.append(Doctor.country.ilike(f"%{filters.country}%"))
    if filters.validated_only:
        conditions.append(Doctor.status == DoctorStatus.VALIDATED)
    if filters.query:
        search = f"%{filters.query}%"
        conditions.append(
            or_(
                Doctor.first_name.ilike(search),
                Doctor.last_name.ilike(search),
                Doctor.email.ilike(search),
                Doctor.license_number.ilike(search),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Pagination
    query = query.order_by(Doctor.created_at.desc())
    query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)

    result = await db.execute(query)
    doctors = result.scalars().all()

    return DoctorSearchResponse(
        items=[DoctorListResponse.model_validate(d) for d in doctors],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size,
    )


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: UUID,
    current_user: User = Depends(require_permission(Permission.DOCTOR_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Détail médecin (admin/validator)"""
    result = await db.execute(
        select(Doctor)
        .options(selectinload(Doctor.documents), selectinload(Doctor.verification_logs))
        .where(Doctor.id == doctor_id)
    )
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")
    return doctor


@router.post("/{doctor_id}/validate", response_model=DoctorResponse)
async def validate_doctor(
    doctor_id: UUID,
    data: DoctorValidateRequest,
    current_user: User = Depends(require_permission(Permission.DOCTOR_VALIDATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Valider médecin"""
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")

    if doctor.status == DoctorStatus.VALIDATED:
        raise HTTPException(status_code=400, detail="Déjà validé")

    old_status = doctor.status
    doctor.status = DoctorStatus.VALIDATED
    doctor.validated_by = current_user.id
    doctor.validated_at = datetime.now(timezone.utc)
    doctor.updated_at = datetime.now(timezone.utc)

    # Log vérification
    log = VerificationLog(
        doctor_id=doctor.id,
        action="validated",
        from_status=old_status,
        to_status=DoctorStatus.VALIDATED,
        performed_by=current_user.id,
        notes=data.notes,
    )
    db.add(log)

    await log_audit(
        db, "doctor.validate", "doctor", doctor.id,
        user=current_user, client=client,
        old_values={"status": old_status.value},
        new_values={"status": DoctorStatus.VALIDATED.value, "validated_by": str(current_user.id)},
        success=True,
    )

    await db.commit()
    await db.refresh(doctor)

    # Email notification
    try:
        await email_service.send_doctor_validated(doctor)
    except Exception:
        pass

    # Recharger avec relations
    result = await db.execute(
        select(Doctor)
        .options(selectinload(Doctor.documents), selectinload(Doctor.verification_logs))
        .where(Doctor.id == doctor.id)
    )
    return result.scalar_one()


@router.post("/{doctor_id}/reject", response_model=DoctorResponse)
async def reject_doctor(
    doctor_id: UUID,
    data: DoctorRejectRequest,
    current_user: User = Depends(require_permission(Permission.DOCTOR_VALIDATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Rejeter médecin"""
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")

    if doctor.status == DoctorStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Déjà rejeté")

    old_status = doctor.status
    doctor.status = DoctorStatus.REJECTED
    doctor.rejection_reason = data.reason
    doctor.updated_at = datetime.now(timezone.utc)

    log = VerificationLog(
        doctor_id=doctor.id,
        action="rejected",
        from_status=old_status,
        to_status=DoctorStatus.REJECTED,
        performed_by=current_user.id,
        notes=data.notes,
        metadata={"rejection_reason": data.reason},
    )
    db.add(log)

    await log_audit(
        db, "doctor.reject", "doctor", doctor.id,
        user=current_user, client=client,
        old_values={"status": old_status.value},
        new_values={"status": DoctorStatus.REJECTED.value, "rejection_reason": data.reason},
        success=True,
    )

    await db.commit()
    await db.refresh(doctor)

    try:
        await email_service.send_doctor_rejected(doctor, data.reason)
    except Exception:
        pass

    result = await db.execute(
        select(Doctor)
        .options(selectinload(Doctor.documents), selectinload(Doctor.verification_logs))
        .where(Doctor.id == doctor.id)
    )
    return result.scalar_one()


@router.post("/{doctor_id}/suspend", response_model=DoctorResponse)
async def suspend_doctor(
    doctor_id: UUID,
    data: DoctorSuspendRequest,
    current_user: User = Depends(require_permission(Permission.DOCTOR_DELETE)),  # Admin seulement
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Suspendre médecin (admin)"""
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Médecin non trouvé")

    old_status = doctor.status
    doctor.status = DoctorStatus.SUSPENDED
    doctor.is_active = False
    doctor.updated_at = datetime.now(timezone.utc)

    log = VerificationLog(
        doctor_id=doctor.id,
        action="suspended",
        from_status=old_status,
        to_status=DoctorStatus.SUSPENDED,
        performed_by=current_user.id,
        notes=data.reason,
        metadata={"suspend_reason": data.reason},
    )
    db.add(log)

    await log_audit(
        db, "doctor.suspend", "doctor", doctor.id,
        user=current_user, client=client,
        old_values={"status": old_status.value, "is_active": True},
        new_values={"status": DoctorStatus.SUSPENDED.value, "is_active": False},
        success=True,
    )

    await db.commit()
    await db.refresh(doctor)

    result = await db.execute(
        select(Doctor)
        .options(selectinload(Doctor.documents), selectinload(Doctor.verification_logs))
        .where(Doctor.id == doctor.id)
    )
    return result.scalar_one()


# ──────────────────────────────────────────────
# ADMIN/VALIDATOR: Gestion documents KYC
# ──────────────────────────────────────────────
@router.get("/{doctor_id}/documents", response_model=list[KYCDocumentResponse])
async def list_doctor_documents(
    doctor_id: UUID,
    current_user: User = Depends(require_permission(Permission.DOCTOR_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Lister documents KYC d'un médecin"""
    result = await db.execute(
        select(KYCDocument).where(KYCDocument.doctor_id == doctor_id)
        .order_by(KYCDocument.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{doctor_id}/documents/{doc_id}/verify", response_model=KYCDocumentResponse)
async def verify_kyc_document(
    doctor_id: UUID,
    doc_id: UUID,
    data: KYCDocumentVerifyRequest,
    current_user: User = Depends(require_permission(Permission.DOCTOR_VALIDATE)),
    client: ClientInfo = Depends(get_client_info),
    db: AsyncSession = Depends(get_db),
):
    """Valider/Rejeter document KYC"""
    result = await db.execute(
        select(KYCDocument).where(
            KYCDocument.id == doc_id,
            KYCDocument.doctor_id == doctor_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    old_verified = doc.is_verified
    doc.is_verified = data.is_verified
    doc.verified_by = current_user.id
    doc.verified_at = datetime.now(timezone.utc)
    if not data.is_verified:
        doc.rejection_reason = data.rejection_reason

    await log_audit(
        db, "doctor.kyc_verify", "kyc_document", doc.id,
        user=current_user, client=client,
        old_values={"is_verified": old_verified},
        new_values={"is_verified": data.is_verified, "verified_by": str(current_user.id)},
        success=True,
    )

    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/{doctor_id}/documents/{doc_id}/download")
async def download_doctor_document(
    doctor_id: UUID,
    doc_id: UUID,
    current_user: User = Depends(require_permission(Permission.DOCTOR_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Télécharger document KYC (admin/validator)"""
    result = await db.execute(
        select(KYCDocument).where(
            KYCDocument.id == doc_id,
            KYCDocument.doctor_id == doctor_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    url = await storage_service.get_presigned_url(doc.file_path, expires_in=3600)
    return {"url": url, "expires_in": 3600}


# ──────────────────────────────────────────────
# ADMIN/VALIDATOR: Logs vérification
# ──────────────────────────────────────────────
@router.get("/{doctor_id}/logs", response_model=list[VerificationLogResponse])
async def get_verification_logs(
    doctor_id: UUID,
    current_user: User = Depends(require_permission(Permission.DOCTOR_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Logs de vérification d'un médecin"""
    result = await db.execute(
        select(VerificationLog).where(VerificationLog.doctor_id == doctor_id)
        .order_by(VerificationLog.created_at.desc())
    )
    return result.scalars().all()