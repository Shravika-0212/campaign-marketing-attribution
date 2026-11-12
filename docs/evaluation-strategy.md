# Chronological Evaluation Strategy & Ground Truth Segregation
**Platform:** Marketing Attribution and ROI Analytics Platform  
**Target:** Elimination of Data Leakage & Reproducible Model Evaluation

---

## 1. Chronological Splitting Strategy

Standard machine learning and data pipelines often rely on random row-level k-fold or train-test splits. In marketing attribution, **random splits cause severe data leakage**: future touchpoints and conversion outcomes from late in the year would leak into earlier training intervals.

To guarantee chronological integrity, data is split along strict time boundaries:

| Period | Start Date | End Date | Purpose |
| :--- | :--- | :--- | :--- |
| **TRAIN** | `2026-01-01 00:00:00` | `2026-07-31 23:59:59` | Baseline customer journeys & model training |
| **VALIDATION** | `2026-08-01 00:00:00` | `2026-09-30 23:59:59` | Parameter tuning (lookback window optimization) |
| **TEST** | `2026-10-01 00:00:00` | `2026-12-31 23:59:59` | Out-of-sample attribution & ROI evaluation |

Attribution results track `evaluation_period` explicitly based on conversion timestamps.

---

## 2. Ground Truth Segregation & Provenance

Ground truth is generated alongside synthetic data using deterministic rules initialized from seed `20261022`.

### Strict Anti-Leakage Rules:
1. **Physical Segregation:** Ground truth data is exported to `data/ground_truth/ground_truth.json` and `data/ground_truth/ground_truth.csv`. It is not stored in operational transactional tables.
2. **Feature Isolation:** The Anomaly Detection Engine and Attribution Engine do not query or read ground truth files during their execution turns.
3. **Evaluation Purpose:** Ground truth is imported strictly within `evaluate_against_ground_truth()` to compute:
   - True Positives (TP)
   - False Positives (FP)
   - False Negatives (FN)
   - Precision, Recall, and F1-Scores

---

## 3. Cryptographic Checksums & Reproducibility Audit

Running the generator with seed `20261022` produces consistent cryptographic hashes:

- **Manifest:** `data/manifests/manifest_starter.json`
- **Output Tables Checksum:** Generated deterministically across all 21 tables.
- **SQL Seed:** `data/exports/sql/seed_data.sql`
- **Ground Truth Checksum:** Confirmed identical across consecutive generation runs.
