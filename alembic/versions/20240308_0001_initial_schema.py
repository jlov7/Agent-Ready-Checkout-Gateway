"""Initial schema

Revision ID: 20240308_0001
Revises: 
Create Date: 2024-03-08 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240308_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "order_intents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("nonce", sa.String(length=128), nullable=False),
        sa.Column("stripe_intent_id", sa.String(length=255), nullable=False),
        sa.Column("client_secret", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("agent_id", sa.String(length=255), nullable=False),
        sa.Column("customer_id", sa.String(length=255), nullable=False),
        sa.Column("transcript_hash", sa.String(length=64), nullable=True),
        sa.Column("authorization_id", sa.String(length=36), nullable=True),
        sa.Column("payment_reference", sa.String(length=128), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("receipts", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_order_intents_transcript_hash", "order_intents", ["transcript_hash"])

    op.create_table(
        "consent_ledger",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("intent_id", sa.String(length=36), nullable=False),
        sa.Column("transcript_hash", sa.String(length=64), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=True),
        sa.Column("entry_hash", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("customer_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_consent_ledger_intent_id", "consent_ledger", ["intent_id"])
    op.create_index("ix_consent_ledger_transcript_hash", "consent_ledger", ["transcript_hash"])

    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("endpoint", sa.String(length=64), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("key", "endpoint"),
    )
    op.create_unique_constraint("uq_idempotency_endpoint", "idempotency_keys", ["key", "endpoint"])


def downgrade() -> None:
    op.drop_constraint("uq_idempotency_endpoint", "idempotency_keys", type_="unique")
    op.drop_table("idempotency_keys")
    op.drop_index("ix_consent_ledger_transcript_hash", table_name="consent_ledger")
    op.drop_index("ix_consent_ledger_intent_id", table_name="consent_ledger")
    op.drop_table("consent_ledger")
    op.drop_index("ix_order_intents_transcript_hash", table_name="order_intents")
    op.drop_table("order_intents")
