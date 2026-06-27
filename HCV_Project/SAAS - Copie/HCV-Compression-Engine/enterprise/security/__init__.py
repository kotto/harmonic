"""HCV Enterprise Security Layer."""

from .hardware import get_fingerprint, get_fingerprint_components
from .license import (
    License, LicenseError, generate_license, verify_license,
    load_license_from_file,
    FEATURE_PRO_CODEC, FEATURE_VIDEO_BOOST, FEATURE_4K_SUPPORT,
    FEATURE_8K_SUPPORT, FEATURE_BATCH_API, FEATURE_PRIORITY_QUEUE,
    FEATURE_WHITE_LABEL, FEATURE_ALL,
)
from .integrity import (
    IntegrityError, TamperingDetected,
    hash_file, build_manifest, verify_manifest,
    save_manifest, load_manifest,
    is_debugger_attached, assert_no_debugger, secure_startup,
)

__all__ = [
    'get_fingerprint', 'get_fingerprint_components',
    'License', 'LicenseError',
    'generate_license', 'verify_license', 'load_license_from_file',
    'FEATURE_PRO_CODEC', 'FEATURE_VIDEO_BOOST', 'FEATURE_4K_SUPPORT',
    'FEATURE_8K_SUPPORT', 'FEATURE_BATCH_API', 'FEATURE_PRIORITY_QUEUE',
    'FEATURE_WHITE_LABEL', 'FEATURE_ALL',
    'IntegrityError', 'TamperingDetected',
    'hash_file', 'build_manifest', 'verify_manifest',
    'save_manifest', 'load_manifest',
    'is_debugger_attached', 'assert_no_debugger', 'secure_startup',
]
