"""Master orchestration script.
Generates synthetic data, executes attribution, detects anomalies, runs validation,
and exports all artifacts (CSV, JSON, SQL, manifests).
Supports --config STARTER (default) and --config FULL.
"""
import sys
import argparse
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.app.models.database import SessionLocal, reset_db
from backend.app.generators.synthetic_data import SyntheticDataGenerator
from backend.app.generators.config import get_dataset_config, RANDOM_SEED
from backend.app.attribution.engine import AttributionEngine
from backend.app.analytics.anomaly_detector import AnomalyDetectionEngine
from backend.app.validation.validator import ValidationEngine
from backend.app.services.export_service import ExportService

def run_pipeline(config_name: str = "STARTER", seed: int = RANDOM_SEED):
    config = get_dataset_config(config_name)
    print("=" * 65)
    print(f"MARKETING ATTRIBUTION ANALYTICS PIPELINE: [{config.name}] (SEED: {seed})")
    print("=" * 65)

    print("\n[Step 1/5] Resetting database & generating synthetic records...")
    reset_db()
    db = SessionLocal()
    try:
        gen = SyntheticDataGenerator(db=db, config=config, seed=seed)
        gen_summary = gen.generate()
        print(f" -> Generation completed. Checksum: {gen_summary['checksum']}")

        print("\n[Step 2/5] Executing attribution models (First, Last, Multi-Touch)...")
        att = AttributionEngine(db)
        att_summary = att.run_all_models()
        print(f" -> Attribution completed: {att_summary['records_created']['total']} attribution records generated.")

        print("\n[Step 3/5] Running anomaly detection engine & ground truth evaluation...")
        detector = AnomalyDetectionEngine(db)
        det_summary = detector.run_detection()
        eval_summary = detector.evaluate_against_ground_truth()
        print(f" -> Detected anomalies: {det_summary['total_anomalies_detected']}")
        print(f" -> Evaluation vs Ground Truth: Precision={eval_summary['overall_metrics']['precision']}, Recall={eval_summary['overall_metrics']['recall']}, F1={eval_summary['overall_metrics']['f1_score']}")

        print("\n[Step 4/5] Executing 15 automated validation rules...")
        val = ValidationEngine(db)
        val_summary = val.run_all_validations()
        print(f" -> Validation completed: {val_summary['summary']['rules_passed']} PASS, {val_summary['summary']['rules_warned']} WARN, {val_summary['summary']['rules_failed']} FAIL")

        print("\n[Step 5/6] Exporting CSV, JSON, SQL seed, and manifest...")
        exporter = ExportService(db)
        exp_summary = exporter.export_all(config_name=config.name, seed=seed)
        print(f" -> Export complete: {exp_summary['total_files_exported']} files exported. Manifest: {exp_summary['manifest_file']}")

        print("\n[Step 6/6] Generating publication-quality charts using Matplotlib & Pandas...")
        from backend.app.analytics.visualizations import generate_all_analytics_charts
        charts_summary = generate_all_analytics_charts(db)
        print(f" -> Generated {charts_summary['charts_generated']} analytics charts in {charts_summary['directory']}")

        print("\n" + "=" * 65)
        print("PIPELINE EXECUTED SUCCESSFULLY")
        print("=" * 65)

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete marketing attribution pipeline")
    parser.add_argument("--config", choices=["STARTER", "FULL", "FULL_BASELINE", "FULL BASELINE"], default="STARTER", help="Dataset size config")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random generation seed")
    args = parser.parse_args()
    run_pipeline(config_name=args.config, seed=args.seed)
