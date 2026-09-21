# Portal Corporativo — Despliegue con Docker Compose

Guía rápida para levantar toda la aplicación (PostgreSQL + Backend + Frontend) en tu propio servidor con un solo comando.

---

## Requisitos previos

- **Docker Engine** 24+ ([instalar](https://docs.docker.com/engine/install/))
- **Docker Compose** v2 (incluido en Docker Desktop y en instalaciones recientes de Docker Engine)
- Puerto **80** libre en el servidor (o cambiar `WEB_PORT` en `.env`)

Verifica:

```bash
docker --version
docker compose version
```

---

## 1. Clonar el repositorio

```bash
git clone <TU-REPO-GITHUB> portal
cd portal
```

---

## 2. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Ajusta como mínimo:

- `PG_PASSWORD` — contraseña de PostgreSQL
- `JWT_SECRET` — genera con: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` — credenciales del admin inicial
- `REACT_APP_BACKEND_URL` — URL pública desde donde se accederá al portal (ej. `https://portal.tuempresa.com`)
- `CORS_ORIGINS` — mismo valor que arriba, separado por coma si son varios

### Si usas un PostgreSQL corporativo externo

1. Edita `docker-compose.yml` y **comenta o elimina** todo el servicio `postgres` y el volumen `postgres_data`.
2. En el servicio `backend`, cambia `PG_HOST: postgres` por `PG_HOST: ${PG_HOST}`.
3. Añade en tu `.env`:

   ```env
   PG_HOST=tu-servidor.empresa.com
   ```

---

## 3. Levantar la aplicación

```bash
docker compose up -d --build
```

Esto:

1. Construye la imagen del backend (Python + FastAPI)
2. Construye la imagen del frontend (React → Nginx)
3. Arranca PostgreSQL 16
4. Espera a que Postgres esté sano y luego arranca el backend
5. El backend crea automáticamente las tablas y las cuentas semilla (admin, editor, user)

Verifica:

```bash
docker compose ps
docker compose logs -f backend
```

Deberías ver: `Admin sembrado: admin@tuempresa.com` y `Application startup complete.`

Accede a `http://IP-DEL-SERVIDOR/` (o el dominio que hayas apuntado por DNS).

---

## 4. HTTPS con dominio propio (recomendado)

**Opción A · Nginx + Certbot en el host** (por delante de docker):

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

`/etc/nginx/sites-available/portal`:

```nginx
server {
    listen 80;
    server_name portal.tuempresa.com;
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/portal /etc/nginx/sites-enabled/
sudo certbot --nginx -d portal.tuempresa.com
```

Cambia `WEB_PORT=8080` en `.env` para no chocar con Nginx del host, y reconstruye: `docker compose up -d`.

**Opción B · Traefik/Caddy como reverse proxy** (más avanzado, dime si quieres el compose).

---

## 5. Operación diaria

```bash
# Ver logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Reiniciar un servicio
docker compose restart backend

# Actualizar tras un git pull
git pull
docker compose up -d --build

# Parar todo
docker compose down

# Parar y borrar volúmenes (¡BORRA LA BD!)
docker compose down -v
```

---

## 6. Backups de PostgreSQL

```bash
# Manual
docker compose exec postgres pg_dump -U portal portal_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Restaurar
gunzip < backup_20260215.sql.gz | docker compose exec -T postgres psql -U portal -d portal_db
```

Automatizar con cron (en el host):

```cron
0 2 * * * cd /opt/portal && docker compose exec -T postgres pg_dump -U portal portal_db | gzip > /var/backups/portal_$(date +\%Y\%m\%d).sql.gz
```

---

## 7. Cuentas semilla iniciales

Al primer arranque se crean automáticamente:

| Rol | Email | Password |
|---|---|---|
| Admin | valor de `ADMIN_EMAIL` en `.env` | valor de `ADMIN_PASSWORD` |
| Editor | editor@portal.com | editor123 |
| User | user@portal.com | user123 |

**⚠ Cambia las contraseñas de editor/user desde el panel admin en cuanto entres.**

---

## Solución de problemas

**El frontend carga pero login da error de red / CORS**
- Revisa que `REACT_APP_BACKEND_URL` en `.env` coincida exactamente con el dominio desde el que abres el portal (incluyendo `https://`).
- Reconstruye el frontend tras cambiarlo: `docker compose up -d --build frontend`.

**Backend no arranca — "connection refused" a postgres**
- Espera unos segundos; el healthcheck retrasará el backend hasta que postgres esté listo.
- `docker compose logs postgres` para ver errores de arranque de la BD.

**Cambié `JWT_SECRET` y los tokens antiguos ya no funcionan**
- Es esperado. Los usuarios deben volver a iniciar sesión.
