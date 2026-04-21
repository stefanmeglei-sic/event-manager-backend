-- Migration 001: Initial schema
-- Run against your Supabase/PostgreSQL project via the SQL editor or psql.

-- Extensie pentru generare automata UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================
-- 1. Lookup / nomenclator tables (no foreign keys)
-- =========================================================

CREATE TABLE IF NOT EXISTS roluri (
    id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nume TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS statusuri (
    id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nume TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS categorii_eveniment (
    id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nume TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS tip_participare (
    id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nume TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS locatii (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nume_sala    TEXT    NOT NULL,
    corp_cladire TEXT,
    capacitate   INTEGER,
    deleted_at   TIMESTAMPTZ
);

-- =========================================================
-- 2. Utilizatori
-- =========================================================

CREATE TABLE IF NOT EXISTS utilizatori (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         TEXT        UNIQUE NOT NULL,
    password_hash TEXT,
    rol_id        UUID        REFERENCES roluri(id),
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    deleted_at    TIMESTAMPTZ
);

-- FK index
CREATE INDEX IF NOT EXISTS idx_utilizatori_rol_id ON utilizatori(rol_id);

-- =========================================================
-- 3. Evenimente
-- =========================================================

CREATE TABLE IF NOT EXISTS evenimente (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titlu               TEXT        NOT NULL,
    descriere           TEXT,
    start_date          TIMESTAMPTZ NOT NULL,
    end_date            TIMESTAMPTZ NOT NULL,
    locatie_id          UUID        REFERENCES locatii(id),
    categorie_id        UUID        REFERENCES categorii_eveniment(id),
    status_id           UUID        REFERENCES statusuri(id),
    organizer_id        UUID        REFERENCES utilizatori(id),
    tip_participare_id  UUID        REFERENCES tip_participare(id),
    max_participanti    INTEGER,
    deadline_inscriere  TIMESTAMPTZ,
    link_inscriere      TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

-- FK indexes
CREATE INDEX IF NOT EXISTS idx_evenimente_locatie_id         ON evenimente(locatie_id);
CREATE INDEX IF NOT EXISTS idx_evenimente_categorie_id       ON evenimente(categorie_id);
CREATE INDEX IF NOT EXISTS idx_evenimente_status_id          ON evenimente(status_id);
CREATE INDEX IF NOT EXISTS idx_evenimente_organizer_id       ON evenimente(organizer_id);
CREATE INDEX IF NOT EXISTS idx_evenimente_tip_participare_id ON evenimente(tip_participare_id);

-- Partial index for soft-delete queries (active records only)
CREATE INDEX IF NOT EXISTS idx_evenimente_active ON evenimente(start_date) WHERE deleted_at IS NULL;

-- =========================================================
-- 4. Inscrieri (registrations)
-- =========================================================

CREATE TABLE IF NOT EXISTS inscrieri (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    eveniment_id       UUID        REFERENCES evenimente(id),
    user_id            UUID        REFERENCES utilizatori(id),
    tip_participare_id UUID        REFERENCES tip_participare(id),
    status_id          UUID        REFERENCES statusuri(id),
    check_in_at        TIMESTAMPTZ,
    qr_token           TEXT        UNIQUE,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- FK indexes
CREATE INDEX IF NOT EXISTS idx_inscrieri_eveniment_id       ON inscrieri(eveniment_id);
CREATE INDEX IF NOT EXISTS idx_inscrieri_user_id            ON inscrieri(user_id);
CREATE INDEX IF NOT EXISTS idx_inscrieri_status_id          ON inscrieri(status_id);
CREATE INDEX IF NOT EXISTS idx_inscrieri_tip_participare_id ON inscrieri(tip_participare_id);

-- =========================================================
-- 5. Feedback
-- =========================================================

CREATE TABLE IF NOT EXISTS feedback (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    eveniment_id    UUID    REFERENCES evenimente(id),
    user_id         UUID    REFERENCES utilizatori(id),
    rating          INTEGER CHECK (rating >= 1 AND rating <= 5),
    comentariu      TEXT,
    sentiment_score FLOAT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, eveniment_id)
);

CREATE INDEX IF NOT EXISTS idx_feedback_eveniment_id ON feedback(eveniment_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user_id      ON feedback(user_id);

-- =========================================================
-- 6. Sponsori
-- =========================================================

CREATE TABLE IF NOT EXISTS sponsori (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nume       TEXT NOT NULL,
    logo_url   TEXT,
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS eveniment_sponsori (
    eveniment_id UUID REFERENCES evenimente(id) ON DELETE CASCADE,
    sponsor_id   UUID REFERENCES sponsori(id)   ON DELETE CASCADE,
    PRIMARY KEY (eveniment_id, sponsor_id)
);

CREATE INDEX IF NOT EXISTS idx_eveniment_sponsori_sponsor_id ON eveniment_sponsori(sponsor_id);

-- =========================================================
-- 7. Fisiere, Notificari, Setari
-- =========================================================

CREATE TABLE IF NOT EXISTS fisiere (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    eveniment_id UUID        REFERENCES evenimente(id) ON DELETE CASCADE,
    url          TEXT        NOT NULL,
    file_type    TEXT,
    categorie    TEXT,
    dimensiune   INTEGER,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fisiere_eveniment_id ON fisiere(eveniment_id);

CREATE TABLE IF NOT EXISTS notificari (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID        REFERENCES utilizatori(id),
    eveniment_id UUID        REFERENCES evenimente(id),
    mesaj        TEXT,
    is_read      BOOLEAN     DEFAULT FALSE,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notificari_user_id      ON notificari(user_id);
CREATE INDEX IF NOT EXISTS idx_notificari_eveniment_id ON notificari(eveniment_id);

CREATE TABLE IF NOT EXISTS setari (
    id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cheie  TEXT UNIQUE NOT NULL,
    valoare TEXT NOT NULL
);
