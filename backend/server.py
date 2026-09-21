from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import os
import logging
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr

from sqlalchemy import (
    Column, String, DateTime, Integer, ForeignKey, select, update, delete, func,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


# ---------- Config ----------
PG_HOST = os.environ["PG_HOST"]
PG_PORT = os.environ.get("PG_PORT", "5432")
PG_USER = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]
PG_DB = os.environ["PG_DB"]

DATABASE_URL = (
    f"postgresql+asyncpg://{quote_plus(PG_USER)}:{quote_plus(PG_PASSWORD)}"
    f"@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_MIN = 60 * 24


# ---------- Predefined Apps ----------
APPS: List[Dict[str, Any]] = [
    {
        "id": "clientes",
        "name": "Ingreso de Clientes",
        "description": "Registro de nuevos clientes corporativos y datos de contacto.",
        "icon": "UsersFour",
        "accent": "blue",
        "fields": [
            {"name": "nombre", "label": "Nombre Completo", "type": "text", "required": True},
            {"name": "empresa", "label": "Empresa", "type": "text", "required": True},
            {"name": "email", "label": "Correo Electrónico", "type": "email", "required": True},
            {"name": "telefono", "label": "Teléfono", "type": "text", "required": False},
            {"name": "segmento", "label": "Segmento", "type": "select", "required": True,
             "options": ["Corporativo", "PyME", "Retail", "Gobierno"]},
            {"name": "notas", "label": "Notas", "type": "textarea", "required": False},
        ],
    },
    {
        "id": "incidentes",
        "name": "Reporte de Incidentes",
        "description": "Registro de incidentes operacionales y de seguridad.",
        "icon": "Warning",
        "accent": "amber",
        "fields": [
            {"name": "titulo", "label": "Título del Incidente", "type": "text", "required": True},
            {"name": "severidad", "label": "Severidad", "type": "select", "required": True,
             "options": ["Baja", "Media", "Alta", "Crítica"]},
            {"name": "area", "label": "Área Afectada", "type": "text", "required": True},
            {"name": "fecha", "label": "Fecha del Incidente", "type": "date", "required": True},
            {"name": "descripcion", "label": "Descripción Detallada", "type": "textarea", "required": True},
        ],
    },
    {
        "id": "productos",
        "name": "Registro de Productos",
        "description": "Catálogo interno de productos y servicios.",
        "icon": "Package",
        "accent": "emerald",
        "fields": [
            {"name": "sku", "label": "SKU", "type": "text", "required": True},
            {"name": "nombre", "label": "Nombre del Producto", "type": "text", "required": True},
            {"name": "categoria", "label": "Categoría", "type": "select", "required": True,
             "options": ["Hardware", "Software", "Servicios", "Consumibles"]},
            {"name": "precio", "label": "Precio (USD)", "type": "number", "required": True},
            {"name": "stock", "label": "Stock Inicial", "type": "number", "required": False},
            {"name": "descripcion", "label": "Descripción", "type": "textarea", "required": False},
        ],
    },
    {
        "id": "empleados",
        "name": "Alta de Empleados",
        "description": "Onboarding y datos de nuevos colaboradores.",
        "icon": "IdentificationCard",
        "accent": "violet",
        "fields": [
            {"name": "nombre", "label": "Nombre y Apellido", "type": "text", "required": True},
            {"name": "documento", "label": "Documento de Identidad", "type": "text", "required": True},
            {"name": "email", "label": "Correo Corporativo", "type": "email", "required": True},
            {"name": "puesto", "label": "Puesto", "type": "text", "required": True},
            {"name": "departamento", "label": "Departamento", "type": "select", "required": True,
             "options": ["Tecnología", "Ventas", "Operaciones", "Finanzas", "Recursos Humanos"]},
            {"name": "fecha_ingreso", "label": "Fecha de Ingreso", "type": "date", "required": True},
        ],
    },
    {
        "id": "reclamaciones",
        "name": "Registro de Reclamaciones",
        "description": "Reclamaciones.",
        "icon": "ChatCircleDots",
        "accent": "rose",
        "fields": [
            {"name": "numero", "label": "Número de Reclamación", "type": "number", "required": False, "auto": True},
            {"name": "reclamante", "label": "Nombre del Reclamante", "type": "text", "required": True},
            {"name": "email", "label": "Email de Contacto", "type": "email", "required": True},
            {"name": "fecha_incidente", "label": "Fecha del Incidente", "type": "date", "required": True},
            {"name": "categoria", "label": "Categoría", "type": "select", "required": True,
             "options": ["Producto", "Servicio", "Facturación", "Atención al cliente", "Otro"]},
            {"name": "prioridad", "label": "Prioridad", "type": "select", "required": True,
             "options": ["Baja", "Media", "Alta", "Urgente"]},
            {"name": "descripcion", "label": "Descripción de la Reclamación", "type": "textarea", "required": True},
            {"name": "resolucion_esperada", "label": "Resolución Esperada", "type": "textarea", "required": False},
        ],
    },
]

APPS_BY_ID = {a["id"]: a for a in APPS}


# ---------- ORM Models ----------
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, default="")
    role = Column(String, nullable=False, default="user")
    allowed_apps = Column(ARRAY(String), nullable=False, default=list)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String, nullable=False)
    user_name = Column(String, nullable=False, default="")
    data = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Counter(Base):
    __tablename__ = "counters"
    key = Column(String, primary_key=True)
    seq = Column(Integer, nullable=False, default=0)


# ---------- Helpers ----------
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_TTL_MIN),
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def user_to_public(u: User) -> Dict[str, Any]:
    return {
        "id": u.id,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "allowed_apps": list(u.allowed_apps or []),
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


def submission_to_dict(s: Submission) -> Dict[str, Any]:
    return {
        "id": s.id,
        "app_id": s.app_id,
        "user_id": s.user_id,
        "user_email": s.user_email,
        "user_name": s.user_name,
        "data": s.data,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = creds.credentials if (creds and creds.credentials) else None
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Tipo de token inválido")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = (await session.execute(select(User).where(User.id == payload["sub"]))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


def require_role(*roles: str):
    async def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Permiso denegado")
        return user
    return _dep


# ---------- Pydantic Models ----------
class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserCreateIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    role: str = Field(pattern="^(admin|editor|user)$")
    allowed_apps: List[str] = Field(default_factory=list)


class UserUpdateIn(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = Field(default=None, pattern="^(admin|editor|user)$")
    allowed_apps: Optional[List[str]] = None
    password: Optional[str] = Field(default=None, min_length=6)


class SubmissionIn(BaseModel):
    data: Dict[str, Any]


# ---------- FastAPI ----------
app = FastAPI()
api = APIRouter(prefix="/api")


@api.get("/")
async def root():
    return {"message": "Portal API", "db": "postgresql"}


# ----- Auth -----
@api.post("/auth/login")
async def login(payload: LoginIn, session: AsyncSession = Depends(get_session)):
    email = payload.email.lower().strip()
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token(user.id, user.email, user.role)
    return {"token": token, "user": user_to_public(user)}


@api.get("/auth/me")
async def me(user: User = Depends(get_current_user)):
    return user_to_public(user)


@api.post("/auth/logout")
async def logout(user: User = Depends(get_current_user)):
    return {"ok": True}


# ----- Apps -----
@api.get("/apps")
async def list_apps(user: User = Depends(get_current_user)):
    allowed = list(user.allowed_apps or [])
    result = []
    for a in APPS:
        if user.role == "admin" or a["id"] in allowed:
            result.append({k: v for k, v in a.items() if k != "fields"})
    return result


@api.get("/apps/{app_id}")
async def get_app(app_id: str, user: User = Depends(get_current_user)):
    if app_id not in APPS_BY_ID:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    if user.role != "admin" and app_id not in list(user.allowed_apps or []):
        raise HTTPException(status_code=403, detail="Sin acceso a esta aplicación")
    return APPS_BY_ID[app_id]


async def next_counter(session: AsyncSession, key: str) -> int:
    """Atomic increment; INSERT if missing."""
    # Try update first
    stmt = (
        update(Counter)
        .where(Counter.key == key)
        .values(seq=Counter.seq + 1)
        .returning(Counter.seq)
    )
    res = await session.execute(stmt)
    val = res.scalar_one_or_none()
    if val is not None:
        return val
    # Row missing → insert seq=1
    session.add(Counter(key=key, seq=1))
    await session.flush()
    return 1


@api.post("/apps/{app_id}/submissions")
async def submit_form(
    app_id: str,
    payload: SubmissionIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if app_id not in APPS_BY_ID:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    if user.role != "admin" and app_id not in list(user.allowed_apps or []):
        raise HTTPException(status_code=403, detail="Sin acceso a esta aplicación")

    app_def = APPS_BY_ID[app_id]
    for f in app_def["fields"]:
        if f.get("auto"):
            continue
        if f.get("required"):
            v = payload.data.get(f["name"])
            if v is None or (isinstance(v, str) and not v.strip()):
                raise HTTPException(
                    status_code=400, detail=f"El campo '{f['label']}' es obligatorio"
                )

    data = dict(payload.data)
    for f in app_def["fields"]:
        if f.get("auto"):
            data[f["name"]] = await next_counter(session, f"{app_id}:{f['name']}")

    sub = Submission(
        id=str(uuid.uuid4()),
        app_id=app_id,
        user_id=user.id,
        user_email=user.email,
        user_name=user.name or "",
        data=data,
        created_at=datetime.now(timezone.utc),
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return submission_to_dict(sub)


@api.get("/apps/{app_id}/submissions")
async def list_submissions(
    app_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if app_id not in APPS_BY_ID:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    if user.role != "admin" and app_id not in list(user.allowed_apps or []):
        raise HTTPException(status_code=403, detail="Sin acceso a esta aplicación")

    q = select(Submission).where(Submission.app_id == app_id)
    if user.role == "user":
        q = q.where(Submission.user_id == user.id)
    q = q.order_by(Submission.created_at.desc()).limit(500)
    subs = (await session.execute(q)).scalars().all()
    return [submission_to_dict(s) for s in subs]


# ----- Admin: Users -----
@api.get("/admin/users")
async def admin_list_users(
    _: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    users = (
        await session.execute(select(User).order_by(User.created_at.desc()))
    ).scalars().all()
    return [user_to_public(u) for u in users]


@api.post("/admin/users")
async def admin_create_user(
    payload: UserCreateIn,
    _: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    email = payload.email.lower().strip()
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    bad = [a for a in payload.allowed_apps if a not in APPS_BY_ID]
    if bad:
        raise HTTPException(status_code=400, detail=f"Apps inválidas: {bad}")
    u = User(
        id=str(uuid.uuid4()),
        email=email,
        name=payload.name.strip(),
        role=payload.role,
        allowed_apps=payload.allowed_apps,
        password_hash=hash_password(payload.password),
        created_at=datetime.now(timezone.utc),
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return user_to_public(u)


@api.patch("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    payload: UserUpdateIn,
    _: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    u = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if payload.name is not None:
        u.name = payload.name.strip()
    if payload.role is not None:
        u.role = payload.role
    if payload.allowed_apps is not None:
        bad = [a for a in payload.allowed_apps if a not in APPS_BY_ID]
        if bad:
            raise HTTPException(status_code=400, detail=f"Apps inválidas: {bad}")
        u.allowed_apps = payload.allowed_apps
    if payload.password:
        u.password_hash = hash_password(payload.password)
    await session.commit()
    await session.refresh(u)
    return user_to_public(u)


@api.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    current: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")
    u = (await session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
    return {"ok": True}


@api.get("/admin/apps")
async def admin_list_all_apps(_: User = Depends(require_role("admin"))):
    return [{k: v for k, v in a.items() if k != "fields"} for a in APPS]


# ---------- Startup ----------
app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def on_startup():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed users
    async with SessionLocal() as session:
        admin_email = os.environ["ADMIN_EMAIL"].lower().strip()
        admin_password = os.environ["ADMIN_PASSWORD"]
        all_app_ids = [a["id"] for a in APPS]

        existing = (
            await session.execute(select(User).where(User.email == admin_email))
        ).scalar_one_or_none()
        if not existing:
            session.add(User(
                id=str(uuid.uuid4()),
                email=admin_email,
                name="Administrador",
                role="admin",
                allowed_apps=all_app_ids,
                password_hash=hash_password(admin_password),
                created_at=datetime.now(timezone.utc),
            ))
            logger.info(f"Admin sembrado: {admin_email}")
        elif not verify_password(admin_password, existing.password_hash):
            existing.password_hash = hash_password(admin_password)

        for email, name, role, pw, apps in [
            ("editor@portal.com", "Editor Demo", "editor", "editor123", ["clientes", "incidentes", "reclamaciones"]),
            ("user@portal.com", "Usuario Demo", "user", "user123", ["clientes", "reclamaciones"]),
        ]:
            found = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
            if not found:
                session.add(User(
                    id=str(uuid.uuid4()),
                    email=email,
                    name=name,
                    role=role,
                    allowed_apps=apps,
                    password_hash=hash_password(pw),
                    created_at=datetime.now(timezone.utc),
                ))

        # Ensure all admins have all apps
        admins = (await session.execute(select(User).where(User.role == "admin"))).scalars().all()
        for a in admins:
            a.allowed_apps = all_app_ids

        await session.commit()


@app.on_event("shutdown")
async def on_shutdown():
    await engine.dispose()
