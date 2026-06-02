-- Add soft delete support for event categories and participation types.

ALTER TABLE IF EXISTS categorii_eveniment
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

ALTER TABLE IF EXISTS tip_participare
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_categorii_eveniment_deleted_at ON categorii_eveniment(deleted_at);
CREATE INDEX IF NOT EXISTS idx_tip_participare_deleted_at ON tip_participare(deleted_at);
