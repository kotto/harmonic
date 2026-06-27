from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.core import security
from app.models.user import User

logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        """
        Authenticate user with email and password
        """
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not security.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    def create_user(db: Session, email: str, username: str, password: str, **kwargs) -> User:
        """
        Create new user
        """
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            raise ValueError("User with this email or username already exists")
        
        # Create new user
        hashed_password = security.get_password_hash(password)
        
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            **kwargs
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created: {user.email}")
        
        return user
    
    @staticmethod
    def update_password(db: Session, user: User, new_password: str) -> None:
        """
        Update user password
        """
        user.hashed_password = security.get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Password updated for user: {user.email}")
    
    @staticmethod
    def verify_email(db: Session, user: User) -> None:
        """
        Verify user email
        """
        user.email_verified = True
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Email verified for user: {user.email}")
    
    @staticmethod
    def deactivate_user(db: Session, user: User) -> None:
        """
        Deactivate user account
        """
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"User deactivated: {user.email}")
    
    @staticmethod
    def activate_user(db: Session, user: User) -> None:
        """
        Activate user account
        """
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"User activated: {user.email}")
    
    @staticmethod
    def update_profile(db: Session, user: User, update_data: dict) -> User:
        """
        Update user profile
        """
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"Profile updated for user: {user.email}")
        
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """
        Get user by email
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User | None:
        """
        Get user by username
        """
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User | None:
        """
        Get user by ID
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        """
        List users with pagination
        """
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def search_users(db: Session, query: str, skip: int = 0, limit: int = 100) -> list[User]:
        """
        Search users by email or username
        """
        return db.query(User).filter(
            (User.email.ilike(f"%{query}%")) | (User.username.ilike(f"%{query}%"))
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def count_users(db: Session) -> int:
        """
        Count total users
        """
        return db.query(User).count()
    
    @staticmethod
    def count_active_users(db: Session) -> int:
        """
        Count active users
        """
        return db.query(User).filter(User.is_active == True).count()
    
    @staticmethod
    def update_last_login(db: Session, user: User) -> None:
        """
        Update user's last login timestamp
        """
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.debug(f"Last login updated for user: {user.email}")