from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import Token, LoginRequest, PasswordResetRequest, PasswordResetConfirm
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    logger.info(f"Login attempt for email: {form_data.username}")
    
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = security.datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = security.create_refresh_token(
        data={"sub": user.id}
    )
    
    logger.info(f"Successful login for user: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/login-json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    JSON login endpoint
    """
    logger.info(f"JSON login attempt for email: {login_data.email}")
    
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        logger.warning(f"Failed JSON login attempt for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user JSON login attempt: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = security.datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    
    refresh_token = security.create_refresh_token(
        data={"sub": user.id}
    )
    
    logger.info(f"Successful JSON login for user: {user.email}")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token
    """
    try:
        payload = security.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=access_token_expires
        )
        
        # Create new refresh token (optional - can reuse old one)
        new_refresh_token = security.create_refresh_token(
            data={"sub": user.id}
        )
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/register")
async def register(
    user_data: LoginRequest,  # Reusing LoginRequest for simplicity
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.email.split("@")[0])
    ).first()
    
    if existing_user:
        logger.warning(f"Registration failed - user already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    new_user = AuthService.create_user(
        db,
        email=user_data.email,
        username=user_data.email.split("@")[0],
        password=user_data.password
    )
    
    logger.info(f"User registered successfully: {new_user.email}")
    
    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "email": new_user.email
    }

@router.post("/password-reset/request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request password reset
    """
    logger.info(f"Password reset request for email: {reset_request.email}")
    
    user = db.query(User).filter(User.email == reset_request.email).first()
    
    if user and user.is_active:
        # Generate reset token
        reset_token = security.create_password_reset_token(user.email)
        
        # Send reset email
        EmailService.send_password_reset_email(user.email, reset_token)
        
        logger.info(f"Password reset email sent to: {user.email}")
    
    # Always return success to prevent email enumeration
    return {
        "message": "If the email exists, a password reset link has been sent"
    }

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """
    Confirm password reset with token
    """
    try:
        payload = security.verify_token(reset_confirm.token, "password_reset")
        email = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found or inactive"
            )
        
        # Update password
        AuthService.update_password(db, user, reset_confirm.new_password)
        
        logger.info(f"Password reset confirmed for user: {user.email}")
        
        return {
            "message": "Password reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )