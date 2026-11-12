# Assumptions & Known Limitations
**Platform:** Marketing Attribution and ROI Analytics Platform  
**Compliance Context:** YottaFlex AI Recruitment Drive Engineering Specification

---

## 1. Technical & Business Assumptions

1. **Conversion Event Definition:** A valid marketing conversion is defined as a closed-won opportunity with an associated order having `status = 'COMPLETED'` and `is_duplicate_flag = False`.
2. **Revenue Recognition:** Revenue is recognized strictly from finalized order records, not from estimated pipeline amounts or lead valuations.
3. **Attribution Lookback Window:** A default lookback window of 90 calendar days is applied (`conversion_timestamp - 90 days <= touchpoint_timestamp <= conversion_timestamp`). Interactions occurring outside this window do not receive credit.
4. **Base Currency Standardization:** All primary financial accounting is executed in United States Dollars (`USD`). Spending records in foreign currencies (`EUR`, `GBP`) are quarantined until formal conversion rates are ingested.
5. **Multi-Touch Weight Distribution:** Linear equal-weight attribution ($w_i = 1/N$) is implemented. Residual rounding differences in fractional cents are allocated to the final touchpoint so total attributed revenue equals the order amount exactly.
6. **Chronological Splitting Strategy:** Evaluation splits are chronological rather than randomized:
   - `TRAIN`: 2026-01-01 to 2026-07-31
   - `VALIDATION`: 2026-08-01 to 2026-09-30
   - `TEST`: 2026-10-01 to 2026-12-31
   This prevents temporal information leakage from future events into prior evaluation windows.

---

## 2. Known Limitations & Future Enhancements

1. **Currency Exchange Rates:** While the system detects and quarantines non-USD spend records, dynamic currency conversion via third-party exchange rate APIs is intentionally avoided to preserve the zero-external-dependency requirement.
2. **Algorithmic / Shapley Attribution:** Current multi-touch modeling uses deterministic linear weighting ($1/N$). Future iterations could incorporate cooperative game theory (Shapley Value) or Markov Chain state-transition modeling.
3. **Database Concurrency:** SQLite in WAL mode provides ultra-fast, zero-configuration local performance. In high-concurrency production deployments with millions of concurrent writes, migrating to PostgreSQL with partitioned tables would be recommended.
