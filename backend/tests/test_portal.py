"""Smoke tests for Spanish corporate portal after requirements.txt trim."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://secure-launcher-8.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": "admin@portal.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="session")
def user_token():
    r = requests.post(f"{API}/auth/login", json={"email": "user@portal.com", "password": "user123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="session")
def editor_token():
    r = requests.post(f"{API}/auth/login", json={"email": "editor@portal.com", "password": "editor123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---- Auth ----
class TestAuth:
    def test_root(self):
        r = requests.get(f"{API}/")
        assert r.status_code == 200
        assert r.json()["db"] == "postgresql"

    def test_admin_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": "admin@portal.com", "password": "admin123"})
        assert r.status_code == 200
        d = r.json()
        assert "token" in d
        assert d["user"]["role"] == "admin"
        assert len(d["user"]["allowed_apps"]) == 5

    def test_user_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": "user@portal.com", "password": "user123"})
        assert r.status_code == 200
        d = r.json()
        assert d["user"]["role"] == "user"
        assert set(d["user"]["allowed_apps"]) == {"clientes", "reclamaciones"}

    def test_editor_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": "editor@portal.com", "password": "editor123"})
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "editor"

    def test_invalid_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": "admin@portal.com", "password": "wrong"})
        assert r.status_code == 401
        assert "Credenciales" in r.json()["detail"]

    def test_me(self, admin_token):
        r = requests.get(f"{API}/auth/me", headers=H(admin_token))
        assert r.status_code == 200
        assert r.json()["email"] == "admin@portal.com"

    def test_no_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401


# ---- Apps ----
class TestApps:
    def test_admin_list_apps(self, admin_token):
        r = requests.get(f"{API}/apps", headers=H(admin_token))
        assert r.status_code == 200
        apps = r.json()
        assert len(apps) == 5
        ids = {a["id"] for a in apps}
        assert ids == {"clientes", "incidentes", "productos", "empleados", "reclamaciones"}

    def test_user_list_apps(self, user_token):
        r = requests.get(f"{API}/apps", headers=H(user_token))
        assert r.status_code == 200
        ids = {a["id"] for a in r.json()}
        assert ids == {"clientes", "reclamaciones"}

    def test_get_reclamaciones_schema(self, admin_token):
        r = requests.get(f"{API}/apps/reclamaciones", headers=H(admin_token))
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == "reclamaciones"
        assert any(f["name"] == "numero" and f.get("auto") for f in d["fields"])

    def test_user_cannot_access_denied_app(self, user_token):
        r = requests.get(f"{API}/apps/incidentes", headers=H(user_token))
        assert r.status_code == 403


# ---- Submissions ----
class TestSubmissions:
    def test_submit_reclamacion_and_auto_numero(self, admin_token):
        payload = {"data": {
            "reclamante": "TEST_" + uuid.uuid4().hex[:6],
            "email": "test@example.com",
            "fecha_incidente": "2026-01-01",
            "categoria": "Servicio",
            "prioridad": "Alta",
            "descripcion": "Descripción de prueba",
        }}
        r = requests.post(f"{API}/apps/reclamaciones/submissions", json=payload, headers=H(admin_token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert "numero" in d["data"]
        assert isinstance(d["data"]["numero"], int)
        assert d["data"]["numero"] >= 1
        # Submit second and verify increment
        r2 = requests.post(f"{API}/apps/reclamaciones/submissions", json=payload, headers=H(admin_token))
        assert r2.status_code == 200
        assert r2.json()["data"]["numero"] == d["data"]["numero"] + 1

    def test_missing_required_returns_400_spanish(self, admin_token):
        payload = {"data": {"reclamante": "X"}}  # missing many required
        r = requests.post(f"{API}/apps/reclamaciones/submissions", json=payload, headers=H(admin_token))
        assert r.status_code == 400
        assert "obligatorio" in r.json()["detail"].lower()

    def test_list_submissions_admin_sees_all(self, admin_token):
        r = requests.get(f"{API}/apps/reclamaciones/submissions", headers=H(admin_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_user_sees_only_own(self, user_token, admin_token):
        # user submits one
        payload = {"data": {
            "reclamante": "TEST_user_" + uuid.uuid4().hex[:6],
            "email": "u@e.com",
            "fecha_incidente": "2026-01-02",
            "categoria": "Producto",
            "prioridad": "Baja",
            "descripcion": "x",
        }}
        r = requests.post(f"{API}/apps/reclamaciones/submissions", json=payload, headers=H(user_token))
        assert r.status_code == 200
        r2 = requests.get(f"{API}/apps/reclamaciones/submissions", headers=H(user_token))
        assert r2.status_code == 200
        subs = r2.json()
        assert all(s["user_email"] == "user@portal.com" for s in subs)


# ---- Admin CRUD ----
class TestAdminUsers:
    def test_list_users(self, admin_token):
        r = requests.get(f"{API}/admin/users", headers=H(admin_token))
        assert r.status_code == 200
        users = r.json()
        emails = {u["email"] for u in users}
        assert {"admin@portal.com", "editor@portal.com", "user@portal.com"}.issubset(emails)
        assert len(users) >= 3

    def test_non_admin_forbidden(self, user_token):
        r = requests.get(f"{API}/admin/users", headers=H(user_token))
        assert r.status_code == 403

    def test_create_update_delete(self, admin_token):
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        # Create
        r = requests.post(f"{API}/admin/users", headers=H(admin_token), json={
            "email": email, "password": "secret1", "name": "TEST User",
            "role": "user", "allowed_apps": ["clientes"],
        })
        assert r.status_code == 200, r.text
        uid = r.json()["id"]
        assert r.json()["role"] == "user"

        # Patch
        r2 = requests.patch(f"{API}/admin/users/{uid}", headers=H(admin_token),
                            json={"name": "TEST Updated", "allowed_apps": ["clientes", "reclamaciones"]})
        assert r2.status_code == 200
        assert r2.json()["name"] == "TEST Updated"
        assert set(r2.json()["allowed_apps"]) == {"clientes", "reclamaciones"}

        # Verify via GET
        rl = requests.get(f"{API}/admin/users", headers=H(admin_token))
        assert any(u["id"] == uid and u["name"] == "TEST Updated" for u in rl.json())

        # Delete
        r3 = requests.delete(f"{API}/admin/users/{uid}", headers=H(admin_token))
        assert r3.status_code == 200
        rl2 = requests.get(f"{API}/admin/users", headers=H(admin_token))
        assert not any(u["id"] == uid for u in rl2.json())
