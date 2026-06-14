# Event Manager Backend

FastAPI backend for the university event management system.

## Docker Compose

This repository includes a local Compose file for report packaging:

- [event-manager-backend/docker-compose.yml](docker-compose.yml)

Canonical project compose remains at:

- [docker-compose.yml](../docker-compose.yml)

## Requirements For Docker Run

Before running Compose, make sure all of the following are true:

1. Docker Engine and Docker Compose are installed.
2. The sibling frontend repository/folder exists at `../event-manager-frontend`.
3. Backend env file exists at `./.env`.
4. Required backend env values are set in `./.env`:
	- `SUPABASE_URL`
	- `SUPABASE_SERVICE_ROLE_KEY`
	- `JWT_SECRET_KEY`
	- `FRONTEND_PUBLIC_URL` (usually `http://localhost:3000`)

## How To Run

From inside the event-manager-backend folder:

```bash
cp .env.example .env
docker compose up --build
```

If `.env` already exists, update it instead of recreating it.

To run in background:

```bash
docker compose up -d --build
```

To stop:

```bash
docker compose down
```

## After Start

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1
- Backend Swagger: http://localhost:8000/docs

## Notes

- Backend is built from current directory (`.`).
- Frontend is built from sibling folder `../event-manager-frontend`.
- Backend env file is loaded from `./.env`.
