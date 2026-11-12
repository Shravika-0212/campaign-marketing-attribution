"""Ground Truth tracking and export utilities.
Records known injected anomalies and ground truth decisions for evaluation.
Never leaked to attribution or anomaly detection feature inputs.
"""
import csv
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

class GroundTruthTracker:
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def record(
        self,
        case_id: str,
        entity_type: str,
        entity_id: str,
        anomaly_type: str,
        expected_decision: str,
        severity: str,
        description: str,
        related_ids: str = ""
    ):
        """Record an injected ground truth anomaly."""
        self.entries.append({
            "case_id": case_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "anomaly_type": anomaly_type,
            "expected_decision": expected_decision,
            "severity": severity,
            "description": description,
            "related_ids": related_ids
        })

    def export(self, output_dir: Path) -> Dict[str, str]:
        """Export ground truth to JSON and CSV and return their SHA-256 checksums."""
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "ground_truth.json"
        csv_path = output_dir / "ground_truth.csv"

        # Deterministic sorting
        sorted_entries = sorted(self.entries, key=lambda x: x["case_id"])

        # Write JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(sorted_entries, f, indent=2)

        # Write CSV
        fieldnames = [
            "case_id", "entity_type", "entity_id", "anomaly_type",
            "expected_decision", "severity", "description", "related_ids"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in sorted_entries:
                writer.writerow(row)

        # Compute SHA-256
        def get_sha256(filepath: Path) -> str:
            h = hashlib.sha256()
            with open(filepath, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
            return h.hexdigest()

        return {
            "ground_truth_json": json_path.as_posix(),
            "ground_truth_json_sha256": get_sha256(json_path),
            "ground_truth_csv": csv_path.as_posix(),
            "ground_truth_csv_sha256": get_sha256(csv_path),
            "total_anomalies_recorded": len(self.entries)
        }
