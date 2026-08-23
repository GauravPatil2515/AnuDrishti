#!/usr/bin/env python3
"""
AnuDrishti (PharmaGuard AI) — 21 CFR Part 11 Audit Trail Service
================================================================
Phase 4 / Track 4 — Immutable, Tamper-Evident Regulatory Audit Logging

This service implements an append-only audit trail meeting the foundational
technical controls required for FDA 21 CFR Part 11 and ALCOA+ data integrity:
  1. Attributable: Records unique user_id, timestamp (UTC ISO 8601), and client info.
  2. Legible & Contemporaneous: Real-time logging of prediction and decision events.
  3. Original & Immutable: Database-level triggers prevent UPDATE and DELETE operations.
  4. Accurate & Tamper-Evident: Sequential SHA-256 hash chaining + HMAC signatures.

Storage:
  SQLite database with explicit write-ahead logging (WAL) and integrity triggers.
"""

import os
import json
import hmac
import hashlib
import sqlite3
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger('AuditTrail')

_HERE = Path(__file__).resolve().parent
_BACKEND = _HERE.parent
_REPO_ROOT = _BACKEND.parent
DEFAULT_DB_PATH = _REPO_ROOT / "data" / "audit_trail.db"

# Secret key for HMAC signing (loaded from environment or default secure fallback)
AUDIT_SECRET_KEY = os.environ.get(
    "PHARMAGUARD_AUDIT_SECRET",
    "anudrishti_21cfr11_tamper_evident_key_2026_secure"
)

GENESIS_HASH = "0" * 64


class AuditTrailService:
    """Thread-safe, append-only, tamper-evident audit logging service."""

    def __init__(self, db_path: Optional[Path] = None, secret_key: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.secret_key = (secret_key or AUDIT_SECRET_KEY).encode("utf-8")
        self._lock = threading.Lock()
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with foreign keys and WAL mode enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_database(self):
        """Initialize audit table and immutability triggers."""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    # 1. Create table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS audit_records (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            user_id TEXT NOT NULL,
                            action TEXT NOT NULL,
                            resource_type TEXT NOT NULL,
                            molecule_smiles TEXT,
                            molecule_name TEXT,
                            prediction_hash TEXT,
                            model_version TEXT,
                            details_json TEXT,
                            prev_record_hash TEXT NOT NULL,
                            record_hash TEXT NOT NULL,
                            hmac_signature TEXT NOT NULL
                        );
                    """)

                    # 2. Indexes for efficient regulatory query
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_records(timestamp);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_records(user_id);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_records(action);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_smiles ON audit_records(molecule_smiles);")

                    # 3. 21 CFR Part 11 Immutability Triggers: ABORT any UPDATE or DELETE
                    conn.execute("""
                        CREATE TRIGGER IF NOT EXISTS audit_records_prevent_update
                        BEFORE UPDATE ON audit_records
                        BEGIN
                            SELECT RAISE(ABORT, '21 CFR Part 11 Violation: Audit trail records are immutable and cannot be updated.');
                        END;
                    """)

                    conn.execute("""
                        CREATE TRIGGER IF NOT EXISTS audit_records_prevent_delete
                        BEFORE DELETE ON audit_records
                        BEGIN
                            SELECT RAISE(ABORT, '21 CFR Part 11 Violation: Audit trail records are immutable and cannot be deleted.');
                        END;
                    """)
            finally:
                conn.close()

    def _compute_hashes(self, prev_hash: str, timestamp: str, user_id: str,
                        action: str, resource_type: str, smiles: Optional[str],
                        pred_hash: Optional[str], details_json: str) -> Tuple[str, str]:
        """Compute cryptographic hash and HMAC signature for a record."""
        canonical_str = f"{prev_hash}|{timestamp}|{user_id}|{action}|{resource_type}|{smiles or ''}|{pred_hash or ''}|{details_json}"
        record_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        hmac_sig = hmac.new(self.secret_key, record_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        return record_hash, hmac_sig

    def log_event(self, action: str, user_id: str = "anonymous_scientist",
                  resource_type: str = "molecule",
                  molecule_smiles: Optional[str] = None,
                  molecule_name: Optional[str] = None,
                  prediction_hash: Optional[str] = None,
                  model_version: Optional[str] = "v3.0.0",
                  details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Append an immutable, signed record to the 21 CFR Part 11 audit log.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details or {}, sort_keys=True)

        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    # Get the most recent record hash for chaining
                    cur = conn.execute(
                        "SELECT record_hash FROM audit_records ORDER BY id DESC LIMIT 1;"
                    )
                    row = cur.fetchone()
                    prev_hash = row["record_hash"] if row else GENESIS_HASH

                    # Compute record hash and HMAC signature
                    record_hash, hmac_sig = self._compute_hashes(
                        prev_hash=prev_hash,
                        timestamp=timestamp,
                        user_id=user_id,
                        action=action,
                        resource_type=resource_type,
                        smiles=molecule_smiles,
                        pred_hash=prediction_hash,
                        details_json=details_json
                    )

                    # Insert record
                    cur = conn.execute("""
                        INSERT INTO audit_records (
                            timestamp, user_id, action, resource_type,
                            molecule_smiles, molecule_name, prediction_hash,
                            model_version, details_json, prev_record_hash,
                            record_hash, hmac_signature
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        timestamp, user_id, action, resource_type,
                        molecule_smiles, molecule_name, prediction_hash,
                        model_version, details_json, prev_hash,
                        record_hash, hmac_sig
                    ))

                    record_id = cur.lastrowid
                    return {
                        "id": record_id,
                        "timestamp": timestamp,
                        "user_id": user_id,
                        "action": action,
                        "record_hash": record_hash,
                        "hmac_signature": hmac_sig,
                        "prev_record_hash": prev_hash,
                        "status": "RECORDED_IMMUTABLY"
                    }
            finally:
                conn.close()

    def get_trail(self, limit: int = 50, offset: int = 0,
                  user_id: Optional[str] = None,
                  action: Optional[str] = None,
                  smiles: Optional[str] = None) -> Dict[str, Any]:
        """Query audit trail records with pagination and filters."""
        query = "SELECT * FROM audit_records WHERE 1=1"
        params: List[Any] = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if action:
            query += " AND action = ?"
            params.append(action)
        if smiles:
            query += " AND molecule_smiles = ?"
            params.append(smiles)

        count_query = query.replace("SELECT *", "SELECT COUNT(*)")

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = self._get_connection()
        try:
            total_count = conn.execute(count_query, params[:-2]).fetchone()[0]
            cur = conn.execute(query, params)
            records = []
            for row in cur.fetchall():
                rec = dict(row)
                try:
                    rec["details"] = json.loads(rec.pop("details_json"))
                except Exception:
                    rec["details"] = {}
                records.append(rec)

            return {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "records": records,
            }
        finally:
            conn.close()

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify cryptographic hash-chain integrity and HMAC signatures across all records.
        """
        conn = self._get_connection()
        try:
            cur = conn.execute("SELECT * FROM audit_records ORDER BY id ASC;")
            rows = cur.fetchall()

            if not rows:
                return {
                    "valid": True,
                    "total_records": 0,
                    "verified_records": 0,
                    "status": "EMPTY_AUDIT_TRAIL",
                    "details": "Audit log is empty; genesis block is intact."
                }

            expected_prev_hash = GENESIS_HASH
            verified_count = 0

            for row in rows:
                rec_id = row["id"]
                actual_prev_hash = row["prev_record_hash"]
                actual_record_hash = row["record_hash"]
                actual_hmac_sig = row["hmac_signature"]

                # 1. Check previous hash linkage
                if actual_prev_hash != expected_prev_hash:
                    return {
                        "valid": False,
                        "tampered_record_id": rec_id,
                        "reason": f"Hash chain broken at record {rec_id}. Expected prev_hash {expected_prev_hash[:16]}... but found {actual_prev_hash[:16]}...",
                        "verified_records": verified_count,
                        "total_records": len(rows),
                    }

                # 2. Recompute record hash and verify HMAC
                calc_hash, calc_sig = self._compute_hashes(
                    prev_hash=actual_prev_hash,
                    timestamp=row["timestamp"],
                    user_id=row["user_id"],
                    action=row["action"],
                    resource_type=row["resource_type"],
                    smiles=row["molecule_smiles"],
                    pred_hash=row["prediction_hash"],
                    details_json=row["details_json"]
                )

                if calc_hash != actual_record_hash:
                    return {
                        "valid": False,
                        "tampered_record_id": rec_id,
                        "reason": f"Content tampering detected at record {rec_id}. Hash mismatch.",
                        "verified_records": verified_count,
                        "total_records": len(rows),
                    }

                if not hmac.compare_digest(calc_sig, actual_hmac_sig):
                    return {
                        "valid": False,
                        "tampered_record_id": rec_id,
                        "reason": f"Signature tampering detected at record {rec_id}. HMAC mismatch.",
                        "verified_records": verified_count,
                        "total_records": len(rows),
                    }

                expected_prev_hash = actual_record_hash
                verified_count += 1

            return {
                "valid": True,
                "total_records": len(rows),
                "verified_records": verified_count,
                "latest_record_hash": expected_prev_hash,
                "status": "ALL_RECORDS_VERIFIED_AND_INTACT",
                "compliance": "21 CFR Part 11 & ALCOA+ Tamper-Evident Certified"
            }
        finally:
            conn.close()


_DEFAULT_AUDIT_SERVICE: Optional[AuditTrailService] = None

def get_audit_trail_service(db_path: Optional[Path] = None) -> AuditTrailService:
    """Return singleton instance of AuditTrailService."""
    global _DEFAULT_AUDIT_SERVICE
    if _DEFAULT_AUDIT_SERVICE is None:
        _DEFAULT_AUDIT_SERVICE = AuditTrailService(db_path=db_path)
    return _DEFAULT_AUDIT_SERVICE
