  

---

## 1. Summary of Project Ownership

This project was built by me as part of a technical assignment to demonstrate my core technical skills in **Python**, **SQL**, **FastAPI**, **Pandas**, **NumPy**, and **Matplotlib**. 

e.

---

## 2. Who Did What? (Human vs. AI Breakdown)

| Project Area | What the AI Assistant Helped With | What I (Student / Developer) Owned, Reviewed & Fixed |
| :--- | :--- | :--- |
| **Project Planning & Logic** | Helped write out the step-by-step implementation plan based on my requirements. | Provided the problem statement: joining campaign touches, sessions, leads, opportunities, orders, and ad spend to calculate ROI. |
| **SQL Database (12 Tables)** | Drafted SQLAlchemy entity models and table columns with primary and foreign keys. | Verified table relationships, ensured cascade behaviors work in SQLite, and verified that all 12 tables and 4 bridge tables create cleanly. |
| **Synthetic Data Generator** | Wrote the Python generation loops and math functions (using random distributions). | Ensured data generation is 100% deterministic using seed `20261022`. Made sure Indian names are used (Shravika, Sharanya, Srinivas, Shailaja, Krish). |
| **Attribution Engine** | Drafted the Python functions for First-Touch, Last-Touch, and Multi-Touch models. | Verified the math: ensured eligible touchpoints cannot be after the order conversion date and that attribution percentages always sum to 100%. |
| **Financial & ROI Logic** | Wrote the ROI formula: `(Revenue - Spend) / Spend * 100`. | Enforced base currency in Indian Rupees (`₹ INR`). Handled missing campaign costs properly so the UI displays `INCOMPLETE` instead of dividing by zero. |
| **Anomaly Detection & QA** | Wrote heuristic check functions for detecting duplicate orders, currency mismatches, etc. | Verified that ground-truth labels are kept separate in `ground_truth.json` and `ground_truth.csv` to prevent data leakage. Confirmed 100% Precision and Recall. |
| **FastAPI REST API** | Drafted REST API routes, Pydantic schemas, and path operations. | Tested all endpoints using the interactive Swagger UI (`/docs`) in the browser. Verified HTTP status codes and response formats. |
| **Matplotlib Charts** | Generated Python Matplotlib scripts to plot financial trends, ROI, and journey timelines. | Configured headless rendering (`matplotlib.use('Agg')`), verified dark-theme colors, and checked the saved `.png` files in `data/exports/charts/`. |
| **Interactive Frontend** | Provided React, Tailwind CSS, and Recharts component code for the dashboard. | Reviewed layout, verified role switcher functionality, checked responsiveness, and compiled the production build with `npm run build`. |
| **Debugging & Testing** | Helped troubleshoot errors when scripts failed. | Encountered and diagnosed the `pytest 9.2` incompatibility on Python 3.10. Downgraded to `pytest 8.4.2` and ran all 40 tests successfully in Windows CMD. |

---

## 3. Key Learning Outcomes & Practical Experience Gained

Through building and testing this project, I gained hands-on practical experience in:
1. **Relational Database Design:** Structuring normalized schemas in SQL with foreign keys, composite keys, and indexing in SQLite.
2. **Data Science & Analytics in Python:** Using Pandas and NumPy for joining multiple tables, filtering date windows, calculating derived metrics, and handling edge cases.
3. **Backend API Engineering:** Building REST APIs using FastAPI with dependency injection, Pydantic validation, and role-based permissions.
4. **Data Visualization:** Using Matplotlib to programmatically render high-resolution charts and saving them as exportable image assets.
5. **Real-World Problem Solving:** Handling edge cases such as duplicate revenue, currency pollution, missing cost records, and Python environment dependency debugging.
