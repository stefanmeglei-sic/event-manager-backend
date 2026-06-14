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

## Database Migrations

Apply the SQL migrations in this order before running the app against a fresh database:

1. `supabase/migrations/20260422000001_initial_schema.sql`
2. `supabase/migrations/20260422000002_seed_lookups.sql`
3. `supabase/migrations/20260427000003_seed_default_users.sql`
4. `supabase/migrations/20260503000004_seed_demo_test_data.sql`
5. `supabase/migrations/20260504000005_add_user_name.sql`
6. `supabase/migrations/20260602000001_soft_delete_lookup_tables.sql`

You can apply them through the Supabase SQL editor, with `psql`, or with the Supabase CLI.

If this repository is not linked yet, link it once first:

```bash
supabase link --project-ref <your-project-ref>
```

After linking, push the migrations with:

```bash
supabase db push
```

If you prefer to apply them manually with `psql`, run the files one at a time in the order above.

If you want a local one-liner with the CLI, use the command from your own Supabase workflow, but keep the same migration order.

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

## Default Demo Users

If seed migrations are applied, the following users are available for testing:

- `admin@usv.ro` -> `Admin1234!`
- `organizer@usv.ro` -> `Organizer1234!`
- `organizer2@usv.ro` -> `Organizer1234!`
- `student@student.usv.ro` -> `Student1234!`
- `student2@student.usv.ro` -> `Student1234!`
- `student3@student.usv.ro` -> `Student1234!`

Source: `supabase/migrations/20260503000004_seed_demo_test_data.sql` (plus defaults from migration 003).

## Notes

- Backend is built from current directory (`.`).
- Frontend is built from sibling folder `../event-manager-frontend`.
- Backend env file is loaded from `./.env`.
