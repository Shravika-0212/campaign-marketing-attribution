"""Data Export & Manifest Service for Marketing Attribution Platform.
Exports CSV, JSON, and SQL database dumps, computes SHA-256 checksums,
and generates metadata manifests for reproducibility.
"""
import os
import csv
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.entities import (
    Campaign, Channel, Creative, Audience, Contact, WebSession,
    Touchpoint, Lead, Opportunity, Order, CostRecord, AttributionResult,
    AnomalyIssue, ValidationResult, AttributionModel
)
from backend.app.generators.config import RANDOM_SEED

CORE_EXPORT_TABLES = [
    ("campaigns", Campaign),
    ("channels", Channel),
    ("creatives", Creative),
    ("audiences", Audience),
    ("contacts", Contact),
    ("web_sessions", WebSession),
    ("touchpoints", Touchpoint),
    ("leads", Lead),
    ("opportunities", Opportunity),
    ("orders", Order),
    ("cost_records", CostRecord),
    ("attribution_results", AttributionResult),
    ("anomaly_issues", AnomalyIssue),
    ("validation_results", ValidationResult),
    ("attribution_models", AttributionModel)
]

class ExportService:
    def __init__(self, db: Session, export_root: Optional[Path] = None):
        self.db = db
        self.export_root = export_root or (Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports")
        self.export_root.mkdir(parents=True, exist_ok=True)

    def export_all(self, config_name: str = "STARTER", seed: int = RANDOM_SEED) -> Dict[str, Any]:
        """Export CSV, JSON, SQL seed, and manifest with checksums."""
        csv_dir = self.export_root / "csv"
        json_dir = self.export_root / "json"
        sql_dir = self.export_root / "sql"
        csv_dir.mkdir(parents=True, exist_ok=True)
        json_dir.mkdir(parents=True, exist_ok=True)
        sql_dir.mkdir(parents=True, exist_ok=True)

        manifest_files = []

        # 1. Export each table to CSV and JSON
        for table_name, model_cls in CORE_EXPORT_TABLES:
            records = self.db.query(model_cls).all()
            if not records:
                # Query columns even if table is empty
                columns = [c.name for c in model_cls.__table__.columns]
                dict_records = []
            else:
                columns = [c.name for c in model_cls.__table__.columns]
                dict_records = []
                for rec in records:
                    row = {}
                    for col in columns:
                        val = getattr(rec, col)
                        if isinstance(val, datetime):
                            val = val.isoformat()
                        row[col] = val
                    dict_records.append(row)

            # Write CSV
            csv_path = csv_dir / f"{table_name}.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                for r in dict_records:
                    writer.writerow(r)

            csv_checksum = self._compute_sha256(csv_path)
            manifest_files.append({
                "dataset_name": table_name,
                "file_name": f"csv/{table_name}.csv",
                "format": "CSV",
                "record_count": len(dict_records),
                "sha256": csv_checksum
            })

            # Write JSON
            json_path = json_dir / f"{table_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(dict_records, f, indent=2)

            json_checksum = self._compute_sha256(json_path)
            manifest_files.append({
                "dataset_name": table_name,
                "file_name": f"json/{table_name}.json",
                "format": "JSON",
                "record_count": len(dict_records),
                "sha256": json_checksum
            })

        # 2. Export SQL Seed
        sql_path = sql_dir / "seed_data.sql"
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write(f"-- Marketing Attribution Seed Data Export\n-- Generated at: {datetime.utcnow().isoformat()}\n-- Seed: {seed}\n\n")
            for table_name, model_cls in CORE_EXPORT_TABLES:
                records = self.db.query(model_cls).all()
                columns = [c.name for c in model_cls.__table__.columns]
                for rec in records:
                    vals = []
                    for col in columns:
                        v = getattr(rec, col)
                        if v is None:
                            vals.append("NULL")
                        elif isinstance(v, (int, float)):
                            vals.append(str(v))
                        elif isinstance(v, bool):
                            vals.append("1" if v else "0")
                        elif isinstance(v, datetime):
                            vals.append(f"'{v.isoformat()}'")
                        else:
                            clean_v = str(v).replace("'", "''")
                            vals.append(f"'{clean_v}'")
                    cols_str = ", ".join(columns)
                    vals_str = ", ".join(vals)
                    f.write(f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str});\n")
                f.write("\n")

        sql_checksum = self._compute_sha256(sql_path)
        manifest_files.append({
            "dataset_name": "full_sql_seed",
            "file_name": "sql/seed_data.sql",
            "format": "SQL",
            "record_count": sum(m["record_count"] for m in manifest_files if m["format"] == "CSV"),
            "sha256": sql_checksum
        })

        # 3. Create Manifest file
        manifest_data = {
            "platform": "Marketing Attribution and ROI Analytics Platform",
            "generation_config": config_name,
            "seed": seed,
            "schema_version": "1.0.0",
            "exported_at": datetime.utcnow().isoformat(),
            "total_files": len(manifest_files),
            "files": manifest_files
        }

        manifest_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"manifest_{config_name.lower()}.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return {
            "status": "COMPLETED",
            "manifest_file": manifest_path.as_posix(),
            "manifest_sha256": self._compute_sha256(manifest_path),
            "total_files_exported": len(manifest_files),
            "exports": manifest_data
        }

    @staticmethod
    def _compute_sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
