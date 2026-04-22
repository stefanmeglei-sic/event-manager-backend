-- Migration 002: Seed lookup / nomenclator tables
-- Run after 001_initial_schema.sql

-- =========================================================
-- Roluri
-- =========================================================
INSERT INTO roluri (id, nume) VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin'),
    ('00000000-0000-0000-0000-000000000002', 'organizer'),
    ('00000000-0000-0000-0000-000000000003', 'student')
ON CONFLICT (nume) DO NOTHING;

-- =========================================================
-- Statusuri (shared by events and registrations)
-- =========================================================
INSERT INTO statusuri (id, nume) VALUES
    ('00000000-0000-0000-0001-000000000001', 'draft'),
    ('00000000-0000-0000-0001-000000000002', 'published'),
    ('00000000-0000-0000-0001-000000000003', 'cancelled'),
    ('00000000-0000-0000-0001-000000000004', 'completed'),
    ('00000000-0000-0000-0001-000000000005', 'pending'),
    ('00000000-0000-0000-0001-000000000006', 'confirmed'),
    ('00000000-0000-0000-0001-000000000007', 'checked_in')
ON CONFLICT (nume) DO NOTHING;

-- =========================================================
-- Categorii eveniment
-- =========================================================
INSERT INTO categorii_eveniment (id, nume) VALUES
    ('00000000-0000-0000-0002-000000000001', 'conference'),
    ('00000000-0000-0000-0002-000000000002', 'workshop'),
    ('00000000-0000-0000-0002-000000000003', 'seminar'),
    ('00000000-0000-0000-0002-000000000004', 'hackathon'),
    ('00000000-0000-0000-0002-000000000005', 'social')
ON CONFLICT (nume) DO NOTHING;

-- =========================================================
-- Tip participare
-- =========================================================
INSERT INTO tip_participare (id, nume) VALUES
    ('00000000-0000-0000-0003-000000000001', 'in-person'),
    ('00000000-0000-0000-0003-000000000002', 'online'),
    ('00000000-0000-0000-0003-000000000003', 'hybrid')
ON CONFLICT (nume) DO NOTHING;

-- =========================================================
-- Locatii
-- =========================================================
INSERT INTO locatii (id, nume_sala, corp_cladire, capacitate, deleted_at)
SELECT
    '00000000-0000-0000-0004-000000000001'::uuid,
    'Aula Magna',
    'A',
    500,
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM locatii
    WHERE nume_sala = 'Aula Magna'
      AND corp_cladire = 'A'
      AND deleted_at IS NULL
);

INSERT INTO locatii (id, nume_sala, corp_cladire, capacitate, deleted_at)
SELECT
    '00000000-0000-0000-0004-000000000002'::uuid,
    'Laborator C2',
    'C',
    35,
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM locatii
    WHERE nume_sala = 'Laborator C2'
      AND corp_cladire = 'C'
      AND deleted_at IS NULL
);
