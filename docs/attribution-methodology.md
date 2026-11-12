# Marketing Attribution Methodology & Mathematical Formulations
**Platform:** Marketing Attribution and ROI Analytics Platform  
**Engine Implementation:** `backend/app/attribution/engine.py`

---

## 1. Attribution Logic & Eligibility Rules

For any conversion event (represented by a completed, non-duplicate Order with timestamp $T_{\text{conv}}$ and amount $A$), a touchpoint $TP_i$ with timestamp $t_i$ is eligible for attribution credit if and only if all of the following conditions are satisfied:

1. **Identity Linkage:**
   $$\text{ContactID}(TP_i) = \text{ContactID}(\text{Order})$$
2. **Temporal Precedence (No Post-Conversion Touches):**
   $$t_i \le T_{\text{conv}}$$
   Touchpoints occurring strictly after $T_{\text{conv}}$ are quarantined and excluded.
3. **Lookback Window Constraint:**
   $$t_i \ge T_{\text{conv}} - \Delta_{\text{lookback}}$$
   Where $\Delta_{\text{lookback}}$ defaults to 90 days ($7,776,000$ seconds), and is configurable between 1 and 365 days.
4. **Order Validity:**
   $$\text{Order}.\text{status} = \text{'COMPLETED'} \quad \land \quad \text{Order}.\text{is\_duplicate\_flag} = \text{False}$$

If $N = 0$ eligible touchpoints exist, the conversion is classified as **Unattributed Revenue**.

---

## 2. Mathematical Models

### A. First-Touch Attribution
First-Touch attribution allocates 100% of conversion credit to the earliest chronological eligible marketing touchpoint:

$$w_i = \begin{cases} 1.0 & \text{if } t_i = \min_{j \in \{1,\dots,N\}} (t_j) \\ 0.0 & \text{otherwise} \end{cases}$$

$$\text{Revenue}(TP_i) = w_i \times A$$

**Strategic Use Case:** Highlights top-of-funnel customer acquisition, initial brand discovery, and campaign reach.

---

### B. Last-Touch Attribution
Last-Touch attribution allocates 100% of conversion credit to the latest chronological eligible marketing touchpoint immediately prior to or at conversion:

$$w_i = \begin{cases} 1.0 & \text{if } t_i = \max_{j \in \{1,\dots,N\}} (t_j) \\ 0.0 & \text{otherwise} \end{cases}$$

$$\text{Revenue}(TP_i) = w_i \times A$$

**Strategic Use Case:** Highlights bottom-of-funnel conversion campaigns, sales follow-ups, and closing offers.

---

### C. Multi-Touch Attribution (Equal-Weight / Linear)
Multi-Touch equal-weight attribution divides conversion credit evenly across all $N$ eligible touchpoints in the customer journey:

$$w_i = \frac{1}{N} \quad \forall i \in \{1, \dots, N\}$$

$$\text{Revenue}(TP_i) = \text{round}\left(\frac{A}{N}, 2\right)$$

#### Numerical Tolerance & Rounding Reconciliation
Because fractional cent rounding in financial databases can introduce precision drift, the final touchpoint $TP_N$ absorbs the residual cent rounding:

$$\text{Revenue}(TP_N) = A - \sum_{i=1}^{N-1} \text{Revenue}(TP_i)$$

$$\sum_{i=1}^{N} w_i = 1.000000 \pm 10^{-6}$$

**Strategic Use Case:** Balanced, unbiased journey attribution that values every touchpoint equally across discovery, consideration, and conversion.

---

## 3. Reconciled Campaign ROI Formulation

For any campaign $C$, total attributed revenue is calculated as the sum of credited revenues across all attributed orders:

$$\text{AttributedRevenue}(C) = \sum_{r \in \text{Results}(C)} r.\text{attributed\_revenue}$$

Campaign spend is derived strictly from validated base currency (`USD`) cost records:

$$\text{Spend}(C) = \sum_{k \in \text{Costs}(C), k.\text{currency} = \text{'USD'}} k.\text{amount}$$

$$\text{ROI}(C) = \begin{cases} \left(\frac{\text{AttributedRevenue}(C) - \text{Spend}(C)}{\text{Spend}(C)}\right) \times 100 & \text{if } \text{Spend}(C) > 0 \\ \text{None (Unavailable / Missing Cost)} & \text{if } \text{Spend}(C) \le 0 \end{cases}$$

When $\text{Spend}(C) \le 0$, division by zero is strictly avoided, ROI is rendered as `None / Unavailable`, and a data-quality issue (`MISSING_CAMPAIGN_COST`) is raised.
