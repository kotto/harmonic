# ──────────────────────────────────────────────
# Migration Initiale - Tables de base
# ──────────────────────────────────────────────
"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ──────────────────────────────────────────────
    # Enum types
    # ──────────────────────────────────────────────
    user_role = postgresql.ENUM('admin', 'validator', name='user_role', create_type=True)
    user_status = postgresql.ENUM('active', 'inactive', 'locked', name='user_status', create_type=True)
    doctor_status = postgresql.ENUM('pending', 'under_review', 'validated', 'rejected', 'suspended', 'expired', name='doctor_status', create_type=True)
    kyc_doc_type = postgresql.ENUM('identity', 'medical_degree', 'license', 'specialty_cert', 'proof_address', 'cv', 'other', name='kyc_document_type', create_type=True)
    release_channel = postgresql.ENUM('alpha', 'beta', 'stable', name='release_channel', create_type=True)

    user_role.create(op.get_bind(), checkfirst=True)
    user_status.create(op.get_bind(), checkfirst=True)
    doctor_status.create(op.get_bind(), checkfirst=True)
    kyc_doc_type.create(op.get_bind(), checkfirst=True)
    release_channel.create(op.get_bind(), checkfirst=True)

    # ──────────────────────────────────────────────
    # Users (Admins, Validateurs)
    # ──────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('role', user_role, nullable=False, server_default='validator'),
        sa.Column('status', user_status, nullable=False, server_default='active'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('totp_secret', sa.String(32), nullable=True),
        sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_role_status', 'users', ['role', 'status'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ──────────────────────────────────────────────
    # Doctors
    # ──────────────────────────────────────────────
    op.create_table(
        'doctors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('license_number', sa.String(50), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('sub_specialty', sa.String(100), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('country', sa.String(100), nullable=False, server_default='France'),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('practice_address', sa.Text(), nullable=True),
        sa.Column('coordinates', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', doctor_status, nullable=False, server_default='pending'),
        sa.Column('validated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('license_number'),
    )
    op.create_index('ix_doctors_status_created', 'doctors', ['status', 'created_at'])
    op.create_index('ix_doctors_specialty_city', 'doctors', ['specialty', 'city'])
    op.create_index('ix_doctors_email', 'doctors', ['email'], unique=True)
    op.create_index('ix_doctors_license', 'doctors', ['license_number'], unique=True)

    # ──────────────────────────────────────────────
    # KYC Documents
    # ──────────────────────────────────────────────
    op.create_table(
        'kyc_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_type', kyc_doc_type, nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doctor_id', 'document_type', name='uq_doctor_document_type'),
    )
    op.create_index('ix_kyc_documents_doctor_id', 'kyc_documents', ['doctor_id'])

    # ──────────────────────────────────────────────
    # Verification Logs
    # ──────────────────────────────────────────────
    op.create_table(
        'verification_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('from_status', doctor_status, nullable=True),
        sa.Column('to_status', doctor_status, nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_verification_logs_doctor_created', 'verification_logs', ['doctor_id', 'created_at'])

    # ──────────────────────────────────────────────
    # APK Versions
    # ──────────────────────────────────────────────
    op.create_table(
        'apk_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_name', sa.String(50), nullable=False),
        sa.Column('version_code', sa.Integer(), nullable=False),
        sa.Column('channel', release_channel, nullable=False, server_default='stable'),
        sa.Column('apk_file_path', sa.String(500), nullable=False),
        sa.Column('apk_file_size', sa.Integer(), nullable=False),
        sa.Column('apk_sha256', sa.String(64), nullable=False),
        sa.Column('bundle_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('min_app_version', sa.String(50), nullable=True),
        sa.Column('build_number', sa.Integer(), nullable=True),
        sa.Column('git_commit', sa.String(40), nullable=True),
        sa.Column('git_branch', sa.String(100), nullable=True),
        sa.Column('built_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('built_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['built_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['bundle_id'], ['hologram_bundles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_code'),
    )
    op.create_index('ix_apk_versions_channel_active', 'apk_versions', ['channel', 'is_active'])
    op.create_index('ix_apk_versions_version_code', 'apk_versions', ['version_code'])

    # ──────────────────────────────────────────────
    # Hologram Bundles
    # ──────────────────────────────────────────────
    op.create_table(
        'hologram_bundles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bundle_file_path', sa.String(500), nullable=False),
        sa.Column('bundle_file_size', sa.Integer(), nullable=False),
        sa.Column('bundle_sha256', sa.String(64), nullable=False),
        sa.Column('domains_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('facts_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('pathologies_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('built_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('built_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['built_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
    )
    op.create_index('ix_hologram_bundles_version', 'hologram_bundles', ['version'])

    # ──────────────────────────────────────────────
    # Webhook Logs
    # ──────────────────────────────────────────────
    op.create_table(
        'webhook_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['apk_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_logs_version_created', 'webhook_logs', ['version_id', 'created_at'])

    # ──────────────────────────────────────────────
    # System Config
    # ──────────────────────────────────────────────
    op.create_table(
        'system_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False, server_default='general'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_sensitive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index('ix_system_config_category', 'system_config', ['category'])

    # ──────────────────────────────────────────────
    # Audit Logs
    # ──────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('user_role', sa.String(50), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_action_created', 'audit_logs', ['action', 'created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('system_config')
    op.drop_table('webhook_logs')
    op.drop_table('hologram_bundles')
    op.drop_table('apk_versions')
    op.drop_table('verification_logs')
    op.drop_table('kyc_documents')
    op.drop_table('doctors')
    op.drop_table('users')

    # Drop enums
    release_channel = postgresql.ENUM('alpha', 'beta', 'stable', name='release_channel')
    kyc_doc_type = postgresql.ENUM('identity', 'medical_degree', 'license', 'specialty_cert', 'proof_address', 'cv', 'other', name='kyc_document_type')
    doctor_status = postgresql.ENUM('pending', 'under_review', 'validated', 'rejected', 'suspended', 'expired', name='doctor_status')
    user_status = postgresql.ENUM('active', 'inactive', 'locked', name='user_status')
    user_role = postgresql.ENUM('admin', 'validator', name='user_role')

    release_channel.drop(op.get_bind(), checkfirst=True)
    kyc_doc_type.drop(op.get_bind(), checkfirst=True)
    doctor_status.drop(op.get_bind(), checkfirst=True)
    user_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)