-- Migration 005: Add display name for users

ALTER TABLE IF EXISTS utilizatori
ADD COLUMN IF NOT EXISTS nume TEXT;

-- Backfill readable names from email local-part for existing rows
UPDATE utilizatori
SET nume = INITCAP(REPLACE(REPLACE(SPLIT_PART(email, '@', 1), '.', ' '), '_', ' '))
WHERE nume IS NULL
  AND email IS NOT NULL;

-- Better defaults for seeded accounts
UPDATE utilizatori SET nume = 'Admin USV' WHERE email = 'admin@usv.ro';
UPDATE utilizatori SET nume = 'Organizer USV' WHERE email = 'organizer@usv.ro';
UPDATE utilizatori SET nume = 'Organizer 2 USV' WHERE email = 'organizer2@usv.ro';
