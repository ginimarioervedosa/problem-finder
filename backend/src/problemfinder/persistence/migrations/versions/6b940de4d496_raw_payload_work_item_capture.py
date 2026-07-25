"""raw payload work item capture

The archive index gains the work item that produced each payload (external_id,
request_hints), so `pf reparse` can reconstruct parse inputs without refetching.
Existing fos_complaints rows are backfilled from their stored signals: every
signal of one payload shares the payload's period hints, so any one row per
sha256 recovers them exactly as discovery originally supplied them.

Revision ID: 6b940de4d496
Revises: b9e7867a66a4
Create Date: 2026-07-25 12:05:10.704062
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '6b940de4d496'
down_revision: str | None = 'b9e7867a66a4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_BACKFILL_FOS_COMPLAINTS = """
UPDATE raw_payloads AS rp
SET external_id = s.period,
    request_hints = jsonb_build_object(
        'period', s.period,
        'period_start', s.period_start::text,
        'period_end', s.period_end::text,
        'page_url', s.url,
        'published_at', to_char(
            s.published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS+00:00'
        )
    )
FROM (
    SELECT DISTINCT ON (raw_payload_sha256)
        raw_payload_sha256,
        extras ->> 'period' AS period,
        period_start,
        period_end,
        url,
        published_at
    FROM signals
    WHERE source_key = 'fos_complaints'
) AS s
WHERE rp.sha256 = s.raw_payload_sha256
  AND rp.source_key = 'fos_complaints'
"""


def upgrade() -> None:
    op.add_column('raw_payloads', sa.Column('external_id', sa.String(length=256), nullable=True))
    op.add_column(
        'raw_payloads',
        sa.Column(
            'request_hints',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.execute(_BACKFILL_FOS_COMPLAINTS)


def downgrade() -> None:
    # Restores the pre-capture schema; the captured work-item metadata is lost,
    # which is exactly what this revision added.
    op.drop_column('raw_payloads', 'request_hints')
    op.drop_column('raw_payloads', 'external_id')
