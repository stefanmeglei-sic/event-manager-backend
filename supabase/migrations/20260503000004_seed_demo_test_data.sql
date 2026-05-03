-- Migration 004: Seed demo/test data for manual functional testing
-- Run after:
--   001_initial_schema.sql
--   002_seed_lookups.sql
--   003_seed_default_users.sql
--
-- Test accounts added by this migration:
--   organizer2@usv.ro        -> Organizer1234!
--   student@student.usv.ro   -> Student1234!
--   student2@student.usv.ro  -> Student1234!
--   student3@student.usv.ro  -> Student1234!
--
-- Existing accounts from migration 003 remain available:
--   admin@usv.ro             -> Admin1234!
--   organizer@usv.ro         -> Organizer1234!

-- =========================================================
-- Extra status required by waiting-list flows
-- =========================================================
INSERT INTO statusuri (id, nume) VALUES
    ('00000000-0000-0000-0001-000000000008', 'waiting')
ON CONFLICT (nume) DO NOTHING;

-- =========================================================
-- Extra locations for richer manual testing
-- =========================================================
INSERT INTO locatii (id, nume_sala, corp_cladire, capacitate, deleted_at)
SELECT
    '00000000-0000-0000-0004-000000000003'::uuid,
    'Sala Senatului',
    'E',
    80,
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM locatii
    WHERE nume_sala = 'Sala Senatului'
      AND corp_cladire = 'E'
      AND deleted_at IS NULL
);

INSERT INTO locatii (id, nume_sala, corp_cladire, capacitate, deleted_at)
SELECT
    '00000000-0000-0000-0004-000000000004'::uuid,
    'Amfiteatrul 1/5',
    'D',
    180,
    NULL
WHERE NOT EXISTS (
    SELECT 1
    FROM locatii
    WHERE nume_sala = 'Amfiteatrul 1/5'
      AND corp_cladire = 'D'
      AND deleted_at IS NULL
);

-- =========================================================
-- Demo users
-- =========================================================
INSERT INTO utilizatori (id, email, password_hash, rol_id, deleted_at) VALUES
    (
        '00000000-0000-0000-0009-000000000003',
        'student@student.usv.ro',
        '$2b$12$QXIQx3.MMgz0YGj7RDcVMerewyrOyzf40jE0hsPfM/d.trmYR8zxK',
        '00000000-0000-0000-0000-000000000003',
        NULL
    ),
    (
        '00000000-0000-0000-0009-000000000004',
        'student2@student.usv.ro',
        '$2b$12$KU2xRVxBqDWUNSfnD8M8wO26.usBaF/lZsdp/2FBEXkqO6wyiSdfG',
        '00000000-0000-0000-0000-000000000003',
        NULL
    ),
    (
        '00000000-0000-0000-0009-000000000005',
        'student3@student.usv.ro',
        '$2b$12$zgUVZqQgUfRM1l7rt1x5hufuWrbtsNglwVBFPJ6LDvieFWVFOUdpy',
        '00000000-0000-0000-0000-000000000003',
        NULL
    ),
    (
        '00000000-0000-0000-0009-000000000006',
        'organizer2@usv.ro',
        '$2b$12$AhahCa9KqOBOq.lp8adH1.tehp71YJz4svXU5GceOFd.RthGGRMr6',
        '00000000-0000-0000-0000-000000000002',
        NULL
    )
ON CONFLICT (email) DO NOTHING;

-- =========================================================
-- Demo events
-- Purpose:
--   1001 published future event for normal enrollment
--   1002 draft event for validate/edit flows
--   1003 completed past event for feedback flows
--   1004 full published event with waiting-list data
--   1005 cancelled event for filtering/detail checks
--
-- Note:
--   link_inscriere is intended as an optional external registration/info URL.
--   For these demo events, registration is meant to happen inside the app via
--   the Enroll button, so the field is left NULL to avoid circular/self links.
-- =========================================================
INSERT INTO evenimente (
    id,
    titlu,
    descriere,
    start_date,
    end_date,
    locatie_id,
    categorie_id,
    status_id,
    organizer_id,
    tip_participare_id,
    max_participanti,
    deadline_inscriere,
    link_inscriere,
    created_at,
    deleted_at
) SELECT
    data.id,
    data.titlu,
    data.descriere,
    data.start_date,
    data.end_date,
    locatie.id,
    categorie.id,
    status_eveniment.id,
    organizator.id,
    tip.id,
    data.max_participanti,
    data.deadline_inscriere,
    data.link_inscriere,
    data.created_at,
    NULL
FROM (
    VALUES
        (
            '10000000-0000-0000-0000-000000000001'::uuid,
            'USV AI Conference 2026',
            'Main public event for testing listing, detail view, QR, ICS export, Google Calendar and standard enrollment.',
            '2026-06-15T09:00:00+00:00'::timestamptz,
            '2026-06-15T15:00:00+00:00'::timestamptz,
            'Aula Magna',
            'A',
            'conference',
            'published',
            'organizer@usv.ro',
            'hybrid',
            120,
            '2026-06-14T23:59:00+00:00'::timestamptz,
            NULL,
            '2026-05-01T08:00:00+00:00'::timestamptz
        ),
        (
            '10000000-0000-0000-0000-000000000002'::uuid,
            'Docker Workshop Draft',
            'Draft event used to test organizer editing and admin validation workflows.',
            '2026-06-20T10:00:00+00:00'::timestamptz,
            '2026-06-20T13:00:00+00:00'::timestamptz,
            'Laborator C2',
            'C',
            'workshop',
            'draft',
            'organizer@usv.ro',
            'in-person',
            30,
            '2026-06-19T18:00:00+00:00'::timestamptz,
            NULL,
            '2026-05-01T09:00:00+00:00'::timestamptz
        ),
        (
            '10000000-0000-0000-0000-000000000003'::uuid,
            'Cybersecurity Seminar Spring Recap',
            'Past event for testing completed status, participant history, and feedback/rating functionality.',
            '2026-04-10T12:00:00+00:00'::timestamptz,
            '2026-04-10T14:00:00+00:00'::timestamptz,
            'Sala Senatului',
            'E',
            'seminar',
            'completed',
            'organizer2@usv.ro',
            'in-person',
            60,
            '2026-04-09T18:00:00+00:00'::timestamptz,
            NULL,
            '2026-03-20T11:00:00+00:00'::timestamptz
        ),
        (
            '10000000-0000-0000-0000-000000000004'::uuid,
            'Hackathon Warmup Lab',
            'Published small-capacity event seeded with confirmed and waiting registrations for waiting-list tests.',
            '2026-05-25T08:00:00+00:00'::timestamptz,
            '2026-05-25T11:00:00+00:00'::timestamptz,
            'Laborator C2',
            'C',
            'hackathon',
            'published',
            'organizer2@usv.ro',
            'in-person',
            1,
            '2026-05-24T20:00:00+00:00'::timestamptz,
            NULL,
            '2026-05-02T10:00:00+00:00'::timestamptz
        ),
        (
            '10000000-0000-0000-0000-000000000005'::uuid,
            'Student Social Night Cancelled',
            'Cancelled event for testing status filters and cancelled detail state.',
            '2026-06-28T17:00:00+00:00'::timestamptz,
            '2026-06-28T20:00:00+00:00'::timestamptz,
            'Amfiteatrul 1/5',
            'D',
            'social',
            'cancelled',
            'organizer@usv.ro',
            'hybrid',
            200,
            '2026-06-26T18:00:00+00:00'::timestamptz,
            NULL,
            '2026-05-02T12:00:00+00:00'::timestamptz
        )
) AS data(
    id,
    titlu,
    descriere,
    start_date,
    end_date,
    locatie_nume,
    locatie_corp,
    categorie_nume,
    status_nume,
    organizer_email,
    tip_participare_nume,
    max_participanti,
    deadline_inscriere,
    link_inscriere,
    created_at
)
JOIN locatii AS locatie
  ON locatie.nume_sala = data.locatie_nume
 AND COALESCE(locatie.corp_cladire, '') = COALESCE(data.locatie_corp, '')
 AND locatie.deleted_at IS NULL
JOIN categorii_eveniment AS categorie
  ON categorie.nume = data.categorie_nume
JOIN statusuri AS status_eveniment
  ON status_eveniment.nume = data.status_nume
JOIN utilizatori AS organizator
  ON organizator.email = data.organizer_email
 AND organizator.deleted_at IS NULL
JOIN tip_participare AS tip
  ON tip.nume = data.tip_participare_nume
ON CONFLICT (id) DO NOTHING;

-- =========================================================
-- Demo registrations
-- Purpose:
--   future event: pending + confirmed
--   completed event: confirmed + checked_in for feedback
--   full event: one confirmed + one waiting for auto-promotion testing
--   cancelled registration for profile/status testing
-- =========================================================
INSERT INTO inscrieri (
    id,
    eveniment_id,
    user_id,
    tip_participare_id,
    status_id,
    check_in_at,
    qr_token,
    created_at
) SELECT
    data.id,
    data.eveniment_id,
    participant.id,
    tip.id,
    status_inscriere.id,
    data.check_in_at,
    data.qr_token,
    data.created_at
FROM (
    VALUES
        (
            '20000000-0000-0000-0000-000000000001'::uuid,
            '10000000-0000-0000-0000-000000000001'::uuid,
            'student@student.usv.ro',
            'hybrid',
            'pending',
            NULL::timestamptz,
            'seed-qr-future-pending-1',
            '2026-05-03T09:00:00+00:00'::timestamptz
        ),
        (
            '20000000-0000-0000-0000-000000000002'::uuid,
            '10000000-0000-0000-0000-000000000001'::uuid,
            'student2@student.usv.ro',
            'hybrid',
            'confirmed',
            NULL::timestamptz,
            'seed-qr-future-confirmed-1',
            '2026-05-03T09:05:00+00:00'::timestamptz
        ),
        (
            '20000000-0000-0000-0000-000000000003'::uuid,
            '10000000-0000-0000-0000-000000000003'::uuid,
            'student@student.usv.ro',
            'in-person',
            'confirmed',
            NULL::timestamptz,
            'seed-qr-past-confirmed-1',
            '2026-04-01T08:30:00+00:00'::timestamptz
        ),
        (
            '20000000-0000-0000-0000-000000000004'::uuid,
            '10000000-0000-0000-0000-000000000003'::uuid,
            'student2@student.usv.ro',
            'in-person',
            'checked_in',
            '2026-04-10T11:55:00+00:00'::timestamptz,
            'seed-qr-past-checked-1',
            '2026-04-01T08:35:00+00:00'::timestamptz
        ),
        (
            '20000000-0000-0000-0000-000000000005'::uuid,
            '10000000-0000-0000-0000-000000000004'::uuid,
            'student3@student.usv.ro',
            'in-person',
            'confirmed',
            NULL::timestamptz,
            'seed-qr-full-confirmed-1',
            '2026-05-02T09:00:00+00:00'::timestamptz
        ),
        (
            '20000000-0000-0000-0000-000000000006'::uuid,
            '10000000-0000-0000-0000-000000000004'::uuid,
            'student@student.usv.ro',
            'in-person',
            'waiting',
            NULL::timestamptz,
            'seed-qr-full-waiting-1',
            '2026-05-02T09:05:00+00:00'::timestamptz
        ),
        (
            '20000000-0000-0000-0000-000000000007'::uuid,
            '10000000-0000-0000-0000-000000000005'::uuid,
            'student2@student.usv.ro',
            'hybrid',
            'cancelled',
            NULL::timestamptz,
            'seed-qr-cancelled-1',
            '2026-05-02T10:00:00+00:00'::timestamptz
        )
) AS data(
    id,
    eveniment_id,
    user_email,
    tip_participare_nume,
    status_nume,
    check_in_at,
    qr_token,
    created_at
)
JOIN evenimente AS eveniment
    ON eveniment.id = data.eveniment_id
 AND eveniment.deleted_at IS NULL
JOIN utilizatori AS participant
  ON participant.email = data.user_email
 AND participant.deleted_at IS NULL
JOIN tip_participare AS tip
  ON tip.nume = data.tip_participare_nume
JOIN statusuri AS status_inscriere
  ON status_inscriere.nume = data.status_nume
ON CONFLICT (id) DO NOTHING;

-- =========================================================
-- Demo feedback
-- =========================================================
INSERT INTO feedback (
    id,
    eveniment_id,
    user_id,
    rating,
    comentariu,
    sentiment_score,
    created_at
) SELECT
    data.id,
    data.eveniment_id,
    participant.id,
    data.rating,
    data.comentariu,
    data.sentiment_score,
    data.created_at
FROM (
    VALUES
        (
            '30000000-0000-0000-0000-000000000001'::uuid,
            '10000000-0000-0000-0000-000000000003'::uuid,
            'student@student.usv.ro',
            5,
            'Very useful seminar with practical examples and a clear presentation.',
            0.95,
            '2026-04-10T15:00:00+00:00'::timestamptz
        ),
        (
            '30000000-0000-0000-0000-000000000002'::uuid,
            '10000000-0000-0000-0000-000000000003'::uuid,
            'student2@student.usv.ro',
            4,
            'Good content overall. The Q and A session was especially helpful.',
            0.70,
            '2026-04-10T15:10:00+00:00'::timestamptz
        )
) AS data(id, eveniment_id, user_email, rating, comentariu, sentiment_score, created_at)
JOIN evenimente AS eveniment
    ON eveniment.id = data.eveniment_id
 AND eveniment.deleted_at IS NULL
JOIN utilizatori AS participant
  ON participant.email = data.user_email
 AND participant.deleted_at IS NULL
ON CONFLICT (id) DO NOTHING;

-- =========================================================
-- Demo sponsors and event links
-- =========================================================
INSERT INTO sponsori (id, nume, logo_url, deleted_at) VALUES
    (
        '40000000-0000-0000-0000-000000000001',
        'USV Tech Club',
        'https://example.com/assets/usv-tech-club.png',
        NULL
    ),
    (
        '40000000-0000-0000-0000-000000000002',
        'Code4Students',
        'https://example.com/assets/code4students.png',
        NULL
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO eveniment_sponsori (eveniment_id, sponsor_id)
SELECT
    data.eveniment_id,
    sponsor.id
FROM (
    VALUES
        (
            '10000000-0000-0000-0000-000000000001'::uuid,
            'USV Tech Club'
        ),
        (
            '10000000-0000-0000-0000-000000000003'::uuid,
            'Code4Students'
        )
) AS data(eveniment_id, sponsor_nume)
JOIN evenimente AS eveniment
  ON eveniment.id = data.eveniment_id
 AND eveniment.deleted_at IS NULL
JOIN sponsori AS sponsor
  ON sponsor.nume = data.sponsor_nume
 AND sponsor.deleted_at IS NULL
ON CONFLICT (eveniment_id, sponsor_id) DO NOTHING;

-- =========================================================
-- Demo files
-- =========================================================
INSERT INTO fisiere (id, eveniment_id, url, file_type, categorie, dimensiune, created_at)
SELECT
    data.id,
    data.eveniment_id,
    data.url,
    data.file_type,
    data.categorie,
    data.dimensiune,
    data.created_at
FROM (
    VALUES
        (
            '50000000-0000-0000-0000-000000000001'::uuid,
            '10000000-0000-0000-0000-000000000001'::uuid,
            'https://example.com/files/usv-ai-conference-program.pdf',
            'application/pdf',
            'program',
            245760,
            '2026-05-05T10:00:00+00:00'::timestamptz
        ),
        (
            '50000000-0000-0000-0000-000000000002'::uuid,
            '10000000-0000-0000-0000-000000000003'::uuid,
            'https://example.com/files/cybersecurity-seminar-slides.pdf',
            'application/pdf',
            'slides',
            532480,
            '2026-04-10T14:30:00+00:00'::timestamptz
        )
) AS data(id, eveniment_id, url, file_type, categorie, dimensiune, created_at)
JOIN evenimente AS eveniment
  ON eveniment.id = data.eveniment_id
 AND eveniment.deleted_at IS NULL
ON CONFLICT (id) DO NOTHING;

-- =========================================================
-- Demo notifications
-- =========================================================
INSERT INTO notificari (id, user_id, eveniment_id, mesaj, is_read, created_at)
SELECT
    data.id,
    participant.id,
    data.eveniment_id,
    data.mesaj,
    data.is_read,
    data.created_at
FROM (
    VALUES
        (
            '60000000-0000-0000-0000-000000000001'::uuid,
            'student@student.usv.ro',
            '10000000-0000-0000-0000-000000000001'::uuid,
            'Your registration for USV AI Conference 2026 is pending review.',
            FALSE,
            '2026-05-03T09:02:00+00:00'::timestamptz
        ),
        (
            '60000000-0000-0000-0000-000000000002'::uuid,
            'student2@student.usv.ro',
            '10000000-0000-0000-0000-000000000001'::uuid,
            'Your participation for USV AI Conference 2026 has been confirmed.',
            FALSE,
            '2026-05-03T09:07:00+00:00'::timestamptz
        ),
        (
            '60000000-0000-0000-0000-000000000003'::uuid,
            'organizer2@usv.ro',
            '10000000-0000-0000-0000-000000000004'::uuid,
            'Hackathon Warmup Lab reached full capacity. A waiting list entry is present for testing.',
            TRUE,
            '2026-05-02T10:15:00+00:00'::timestamptz
        )
) AS data(id, user_email, eveniment_id, mesaj, is_read, created_at)
JOIN evenimente AS eveniment
    ON eveniment.id = data.eveniment_id
 AND eveniment.deleted_at IS NULL
JOIN utilizatori AS participant
  ON participant.email = data.user_email
 AND participant.deleted_at IS NULL
ON CONFLICT (id) DO NOTHING;

-- =========================================================
-- Demo settings
-- =========================================================
INSERT INTO setari (id, cheie, valoare) VALUES
    ('70000000-0000-0000-0000-000000000001', 'demo_seed_version', '20260503'),
    ('70000000-0000-0000-0000-000000000002', 'support_email', 'events-support@usv.ro')
ON CONFLICT (cheie) DO NOTHING;