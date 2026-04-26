-- Migration 003: Seed default admin and organizer accounts
-- Passwords are bcrypt hashes:
--   admin@usv.ro     →  Admin1234!
--   organizer@usv.ro →  Organizer1234!
--
-- Change these passwords immediately in any non-local environment.

INSERT INTO utilizatori (id, email, password_hash, rol_id, deleted_at)
VALUES
    (
        '00000000-0000-0000-0009-000000000001',
        'admin@usv.ro',
        '$2b$12$1wgX1rB0JsecvL.5doDgzeV/Fo6F5.a/lVtAIY0MsWlpHsTwU9sTS',
        '00000000-0000-0000-0000-000000000001',  -- admin role
        NULL
    ),
    (
        '00000000-0000-0000-0009-000000000002',
        'organizer@usv.ro',
        '$2b$12$wQO6isDx7Xo4OY87j4JLJ.ULxM1UGTkyKHFavqz0LDbnndcWMK0XO',
        '00000000-0000-0000-0000-000000000002',  -- organizer role
        NULL
    )
ON CONFLICT (email) DO NOTHING;
