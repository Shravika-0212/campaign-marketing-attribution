"""CLI script to execute Data Validation Engine."""
import sys
import json
from pathlib import Path

# Ensure root directory in python path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.models.database import SessionLocal
from backend.app.validation.validator import ValidationEngine

def main():
    db = SessionLocal()
    try:
        val = ValidationEngine(db)
        report = val.run_all_validations()
        print("=" * 60)
        print("DATA VALIDATION ENGINE REPORT")
        print("=" * 60)
        print(f"Timestamp: {report['validation_timestamp']}")
        print(f"Total Rules Checked: {report['summary']['total_rules']}")
        print(f"Rules Passed:        {report['summary']['rules_passed']}")
        print(f"Rules Warned:        {report['summary']['rules_warned']}")
        print(f"Rules Failed:        {report['summary']['rules_failed']}")
        print(f"Total Records:       {report['summary']['total_records_checked']}")
        print("-" * 60)
        for r in report["rule_results"]:
            print(f"[{r['status']:4s}] {r['rule_code']}: {r['rule_name']}")
            print(f"       Checked: {r['records_checked']} | Passed: {r['records_passed']} | Failed: {r['records_failed']}")
            for d in r["details"]:
                print(f"       -> {d}")
        print("=" * 60)

        # Save report output to data/exports/validation_report.json
        export_dir = root_dir / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        with open(export_dir / "validation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report exported to: {export_dir / 'validation_report.json'}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
