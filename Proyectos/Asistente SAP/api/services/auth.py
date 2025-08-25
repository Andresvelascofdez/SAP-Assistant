"""
Servicio de autenticación y autorización
Wiki Inteligente SAP IS-U
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from db.database import get_db
from db.models import User, Tenant
from models.schemas import TokenData

# Configuración de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hashear contraseña"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crear token de acceso"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Crear token de refresco"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verificar y decodificar token"""
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            tenant_slug: str = payload.get("tenant_slug")
            
            if user_id is None:
                return None
                
            return TokenData(
                user_id=user_id,
                email=email,
                role=role,
                tenant_slug=tenant_slug
            )
        except JWTError:
            return None
    
    @staticmethod
    async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[User]:
        """Autenticar usuario"""
        stmt = select(User).where(User.email == email, User.is_active == True)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
            
        # Actualizar último login
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return user
    
    @staticmethod
    async def get_user_by_id(user_id: str, db: AsyncSession) -> Optional[User]:
        """Obtener usuario por ID"""
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency para obtener usuario actual"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = AuthService.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = await AuthService.get_user_by_id(str(token_data.user_id), db)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency para obtener usuario activo"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency para requerir rol admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def require_tenant_access(tenant_slug: str):
    """Dependency factory para verificar acceso a tenant específico"""
    def _verify_tenant_access(current_user: User = Depends(get_current_active_user)) -> User:
        # Admins pueden acceder a cualquier tenant
        if current_user.role == "admin":
            return current_user
        
        # Usuarios regulares solo pueden acceder a su tenant o STANDARD
        user_tenant = current_user.tenant.slug if current_user.tenant else None
        if tenant_slug not in [user_tenant, "STANDARD"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to tenant"
            )
        
        return current_user
    
    return _verify_tenant_access


# Funciones standalone para compatibilidad
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return AuthService.verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashear contraseña"""
    return AuthService.get_password_hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token de acceso"""
    return AuthService.create_access_token(data, expires_delta)

def create_refresh_token(data: dict) -> str:
    """Crear token de refresco"""
    return AuthService.create_refresh_token(data)

def verify_token(token: str) -> Optional[TokenData]:
    """Verificar y decodificar token"""
    return AuthService.verify_token(token)

async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[User]:
    """Autenticar usuario"""
    return await AuthService.authenticate_user(email, password, db)

async def get_user_by_id(user_id: str, db: AsyncSession) -> Optional[User]:
    """Obtener usuario por ID"""
    return await AuthService.get_user_by_id(user_id, db)
