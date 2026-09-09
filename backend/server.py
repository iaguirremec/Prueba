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

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr


# ---------- Config ----------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_MIN = 60 * 24  # 24h for simplicity


# ---------- Predefined Apps (data-entry forms) ----------
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


def public_user(u: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": u["id"],
        "email": u["email"],
        "name": u.get("name", ""),
        "role": u.get("role", "user"),
        "allowed_apps": u.get("allowed_apps", []),
        "created_at": u.get("created_at"),
    }


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    token = None
    if creds and creds.credentials:
        token = creds.credentials
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

    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


def require_role(*roles: str):
    async def _dep(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if user.get("role") not in roles:
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


# ---------- App & Router ----------
app = FastAPI()
api = APIRouter(prefix="/api")


@api.get("/")
async def root():
    return {"message": "Portal API"}


# ----- Auth -----
@api.post("/auth/login")
async def login(payload: LoginIn):
    email = payload.email.lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    token = create_access_token(user["id"], user["email"], user["role"])
    return {"token": token, "user": public_user(user)}


@api.get("/auth/me")
async def me(user: Dict[str, Any] = Depends(get_current_user)):
    return public_user(user)


@api.post("/auth/logout")
async def logout(user: Dict[str, Any] = Depends(get_current_user)):
    # Stateless JWT — frontend just discards token.
    return {"ok": True}


# ----- Apps -----
@api.get("/apps")
async def list_apps(user: Dict[str, Any] = Depends(get_current_user)):
    allowed = user.get("allowed_apps", [])
    role = user.get("role", "user")
    result = []
    for a in APPS:
        if role == "admin" or a["id"] in allowed:
            result.append({k: v for k, v in a.items() if k != "fields"})
    return result


@api.get("/apps/{app_id}")
async def get_app(app_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    if app_id not in APPS_BY_ID:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    if user.get("role") != "admin" and app_id not in user.get("allowed_apps", []):
        raise HTTPException(status_code=403, detail="Sin acceso a esta aplicación")
    return APPS_BY_ID[app_id]


@api.post("/apps/{app_id}/submissions")
async def submit_form(
    app_id: str,
    payload: SubmissionIn,
    user: Dict[str, Any] = Depends(get_current_user),
):
    if app_id not in APPS_BY_ID:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    if user.get("role") != "admin" and app_id not in user.get("allowed_apps", []):
        raise HTTPException(status_code=403, detail="Sin acceso a esta aplicación")

    app_def = APPS_BY_ID[app_id]
    # Validate required fields (skip auto-generated ones)
    for f in app_def["fields"]:
        if f.get("auto"):
            continue
        if f.get("required"):
            v = payload.data.get(f["name"])
            if v is None or (isinstance(v, str) and not v.strip()):
                raise HTTPException(
                    status_code=400, detail=f"El campo '{f['label']}' es obligatorio"
                )

    # Auto-generate values for fields marked as auto (atomic counter per app+field)
    data = dict(payload.data)
    for f in app_def["fields"]:
        if not f.get("auto"):
            continue
        counter_key = f"{app_id}:{f['name']}"
        counter = await db.counters.find_one_and_update(
            {"_id": counter_key},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
        )
        data[f["name"]] = counter["seq"]

    doc = {
        "id": str(uuid.uuid4()),
        "app_id": app_id,
        "user_id": user["id"],
        "user_email": user["email"],
        "user_name": user.get("name", ""),
        "data": data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.submissions.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api.get("/apps/{app_id}/submissions")
async def list_submissions(
    app_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    if app_id not in APPS_BY_ID:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")
    if user.get("role") != "admin" and app_id not in user.get("allowed_apps", []):
        raise HTTPException(status_code=403, detail="Sin acceso a esta aplicación")

    query: Dict[str, Any] = {"app_id": app_id}
    if user.get("role") == "user":
        query["user_id"] = user["id"]

    cursor = db.submissions.find(query, {"_id": 0}).sort("created_at", -1).limit(500)
    return await cursor.to_list(500)


# ----- Admin: Users -----
@api.get("/admin/users")
async def admin_list_users(_: Dict[str, Any] = Depends(require_role("admin"))):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return users


@api.post("/admin/users")
async def admin_create_user(
    payload: UserCreateIn,
    _: Dict[str, Any] = Depends(require_role("admin")),
):
    email = payload.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    # Validate allowed_apps
    bad = [a for a in payload.allowed_apps if a not in APPS_BY_ID]
    if bad:
        raise HTTPException(status_code=400, detail=f"Apps inválidas: {bad}")
    doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "name": payload.name.strip(),
        "role": payload.role,
        "allowed_apps": payload.allowed_apps,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    return public_user(doc)


@api.patch("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    payload: UserUpdateIn,
    _: Dict[str, Any] = Depends(require_role("admin")),
):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    updates: Dict[str, Any] = {}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.role is not None:
        updates["role"] = payload.role
    if payload.allowed_apps is not None:
        bad = [a for a in payload.allowed_apps if a not in APPS_BY_ID]
        if bad:
            raise HTTPException(status_code=400, detail=f"Apps inválidas: {bad}")
        updates["allowed_apps"] = payload.allowed_apps
    if payload.password:
        updates["password_hash"] = hash_password(payload.password)
    if updates:
        await db.users.update_one({"id": user_id}, {"$set": updates})
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return public_user(user)


@api.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    current: Dict[str, Any] = Depends(require_role("admin")),
):
    if user_id == current["id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")
    res = await db.users.delete_one({"id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"ok": True}


@api.get("/admin/apps")
async def admin_list_all_apps(_: Dict[str, Any] = Depends(require_role("admin"))):
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
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.submissions.create_index("app_id")
    await db.submissions.create_index("user_id")

    admin_email = os.environ["ADMIN_EMAIL"].lower().strip()
    admin_password = os.environ["ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "name": "Administrador",
            "role": "admin",
            "allowed_apps": [a["id"] for a in APPS],
            "password_hash": hash_password(admin_password),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Admin sembrado: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )

    # Seed sample editor + user for convenience if not present
    for email, name, role, pw in [
        ("editor@portal.com", "Editor Demo", "editor", "editor123"),
        ("user@portal.com", "Usuario Demo", "user", "user123"),
    ]:
        if not await db.users.find_one({"email": email}):
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": email,
                "name": name,
                "role": role,
                "allowed_apps": ["clientes", "incidentes", "reclamaciones"] if role == "editor" else ["clientes", "reclamaciones"],
                "password_hash": hash_password(pw),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    # Grant existing non-admin users access to new "reclamaciones" app (idempotent)
    await db.users.update_many(
        {"role": {"$in": ["editor", "user"]}, "allowed_apps": {"$ne": "reclamaciones"}},
        {"$push": {"allowed_apps": "reclamaciones"}},
    )
    # Ensure admins have all apps in allowed_apps (for consistency)
    all_app_ids = [a["id"] for a in APPS]
    await db.users.update_many(
        {"role": "admin"},
        {"$set": {"allowed_apps": all_app_ids}},
    )


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
