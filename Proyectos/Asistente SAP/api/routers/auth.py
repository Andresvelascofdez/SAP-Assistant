"""
Router de autenticación
Wiki Inteligente SAP IS-U
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db.database import get_db
from ..db.models import User, Tenant
from ..models.schemas import UserLogin, UserCreate, UserResponse, Token
from ..services.auth import (
    get_current_active_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_token,
    get_user_by_id,
    require_admin
)
from ..utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Autenticar usuario y generar tokens"""
    user = await authenticate_user(credentials.email, credentials.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener tenant slug
    tenant_slug = None
    if user.tenant_id:
        stmt = select(Tenant).where(Tenant.id == user.tenant_id)
        result = await db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if tenant:
            tenant_slug = tenant.slug
    
    # Crear tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_slug": tenant_slug
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info("User logged in", user_id=str(user.id), email=user.email)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=3600 * 24  # 24 hours
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Refrescar token de acceso"""
    token_data = verify_token(refresh_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verificar que el usuario sigue activo
    user = await get_user_by_id(str(token_data.user_id), db)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Crear nuevos tokens
    new_token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "tenant_slug": token_data.tenant_slug
    }
    
    new_access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=3600 * 24
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Obtener información del usuario actual"""
    tenant_slug = None
    if current_user.tenant:
        tenant_slug = current_user.tenant.slug
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        tenant_slug=tenant_slug,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Registrar nuevo usuario (solo admins)"""
    # Verificar que el email no existe
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Verificar que el tenant existe
    tenant = None
    if user_data.tenant_slug:
        stmt = select(Tenant).where(Tenant.slug == user_data.tenant_slug)
        result = await db.execute(stmt)
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant not found"
            )
    
    # Crear usuario
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        tenant_id=tenant.id if tenant else None
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info("User registered", user_id=str(new_user.id), email=new_user.email)
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        role=new_user.role,
        tenant_slug=user_data.tenant_slug,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        last_login=new_user.last_login
    )
