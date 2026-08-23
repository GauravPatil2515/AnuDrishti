#!/usr/bin/env python3
"""
Unit and Integration Tests for 21 CFR Part 11 Audit Trail Service & Endpoints
=============================================================================
Phase 4 / Track 4 — Immutable, Tamper-Evident Regulatory Audit Logging
"""

import os
import tempfile
import sqlite3
import pytest
from pathlib import Path

from services.audit_trail import AuditTrailService, GENESIS_HASH


@pytest.fixture
def temp_audit_service():
    """Create a temporary AuditTrailService backed by an ephemeral SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_db = Path(f.name)

    svc = AuditTrailService(db_path=temp_db, secret_key="test_secret_key_123")
    yield svc

    # Cleanup
    if temp_db.exists():
        temp_db.unlink(missing_ok=True)


class TestAuditTrailServiceCore:
    """Core tests for append-only audit trail logging and hash chaining."""

    def test_genesis_block_and_empty_verify(self, temp_audit_service):
        res = temp_audit_service.verify_integrity()
        assert res["valid"] is True
        assert res["total_records"] == 0

    def test_log_single_event(self, temp_audit_service):
        rec = temp_audit_service.log_event(
            action="TEST_PREDICTION",
            user_id="dr_smith",
            resource_type="molecule",
            molecule_smiles="CC(=O)OC1=CC=CC=C1",
            molecule_name="Aspirin",
            prediction_hash="predhash123",
            model_version="v3.0.0",
            details={"risk": "LOW", "ld50": 200.0}
        )

        assert rec["id"] == 1
        assert rec["user_id"] == "dr_smith"
        assert rec["action"] == "TEST_PREDICTION"
        assert rec["prev_record_hash"] == GENESIS_HASH
        assert len(rec["record_hash"]) == 64
        assert len(rec["hmac_signature"]) == 64

        verify = temp_audit_service.verify_integrity()
        assert verify["valid"] is True
        assert verify["verified_records"] == 1

    def test_sequential_hash_chaining(self, temp_audit_service):
        rec1 = temp_audit_service.log_event(action="EVENT_1", user_id="user_1", molecule_smiles="C1=CC=CC=C1")
        rec2 = temp_audit_service.log_event(action="EVENT_2", user_id="user_2", molecule_smiles="CC(=O)O")
        rec3 = temp_audit_service.log_event(action="EVENT_3", user_id="user_3", molecule_smiles="CCO")

        assert rec1["prev_record_hash"] == GENESIS_HASH
        assert rec2["prev_record_hash"] == rec1["record_hash"]
        assert rec3["prev_record_hash"] == rec2["record_hash"]

        verify = temp_audit_service.verify_integrity()
        assert verify["valid"] is True
        assert verify["verified_records"] == 3

    def test_immutability_triggers_prevent_update(self, temp_audit_service):
        temp_audit_service.log_event(action="CANNOT_MODIFY", user_id="user_1")

        # Attempt direct SQL UPDATE on audit table
        conn = temp_audit_service._get_connection()
        with pytest.raises(sqlite3.IntegrityError, match="21 CFR Part 11 Violation"):
            conn.execute("UPDATE audit_records SET action = 'MODIFIED' WHERE id = 1;")
        conn.close()

    def test_immutability_triggers_prevent_delete(self, temp_audit_service):
        temp_audit_service.log_event(action="CANNOT_DELETE", user_id="user_1")

        # Attempt direct SQL DELETE on audit table
        conn = temp_audit_service._get_connection()
        with pytest.raises(sqlite3.IntegrityError, match="21 CFR Part 11 Violation"):
            conn.execute("DELETE FROM audit_records WHERE id = 1;")
        conn.close()

    def test_tamper_detection_on_content_change(self, temp_audit_service):
        rec1 = temp_audit_service.log_event(action="EVENT_1", user_id="user_1")
        rec2 = temp_audit_service.log_event(action="EVENT_2", user_id="user_2")

        # Disable trigger temporarily via raw sqlite bypass or raw file manipulation to simulate attacker
        conn = temp_audit_service._get_connection()
        conn.execute("DROP TRIGGER IF EXISTS audit_records_prevent_update;")
        conn.execute("UPDATE audit_records SET user_id = 'attacker' WHERE id = 1;")
        conn.commit()
        conn.close()

        # Verification must now fail!
        verify = temp_audit_service.verify_integrity()
        assert verify["valid"] is False
        assert verify["tampered_record_id"] == 1

    def test_query_filter_and_pagination(self, temp_audit_service):
        temp_audit_service.log_event(action="PREDICTION", user_id="alice", molecule_smiles="CC")
        temp_audit_service.log_event(action="DOSSIER", user_id="bob", molecule_smiles="CCC")
        temp_audit_service.log_event(action="PREDICTION", user_id="alice", molecule_smiles="CCCC")

        alice_records = temp_audit_service.get_trail(user_id="alice")
        assert alice_records["total"] == 2
        assert len(alice_records["records"]) == 2

        dossier_records = temp_audit_service.get_trail(action="DOSSIER")
        assert dossier_records["total"] == 1
        assert dossier_records["records"][0]["user_id"] == "bob"


class TestAuditTrailEndpoints:
    """Integration tests for Flask audit endpoints."""

    def test_get_audit_trail_api(self, client):
        resp = client.get("/api/v1/audit/trail?limit=10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "records" in data

    def test_get_audit_verify_api(self, client):
        resp = client.get("/api/v1/audit/verify")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["valid"] is True

    def test_log_audit_event_api(self, client):
        resp = client.post("/api/v1/audit/log", json={
            "action": "BENCHMARK_EVALUATION",
            "user_id": "test_qa_auditor",
            "smiles": "c1ccccc1",
            "details": {"benchmark": "Tox21", "result": "PASS"}
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["action"] == "BENCHMARK_EVALUATION"
        assert "record_hash" in data
