"""Audit repository unit tests (EP09 3.3)."""

from app.repositories.audit_repository import mask_email_for_audit


def test_mask_email_for_audit_keeps_domain_only():
    assert mask_email_for_audit("user@example.com") == "***@example.com"


def test_mask_email_for_audit_handles_missing_domain():
    assert mask_email_for_audit("not-an-email") == "***"
