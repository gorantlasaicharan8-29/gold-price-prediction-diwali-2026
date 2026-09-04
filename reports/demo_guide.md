# Gold Price Intelligence — Academic & HOD Presentation Demo Guide

This guide provides a structured 10-step presentation flow for demonstrating the **Gold Price Intelligence — Gold Price Prediction System during Diwali 2026** during academic reviews, Head of Department (HOD) evaluation, or live technical demonstrations.

---

## Prerequisites for Live Demo

Before starting the live presentation, launch both system servers:

### 1. Terminal 1 — Start FastAPI Backend Server
```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload --port 8000
```
- **Backend Base URL:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`

### 2. Terminal 2 — Start React / Vite Frontend Server
```powershell
cd frontend
npm run dev
```
- **Frontend Application URL:** `http://localhost:5173`

---

## 10-Step Academic Presentation Flow

```
[ Step 1: Dashboard ] ──► [ Step 2: Historical Data ] ──► [ Step 3: Diwali Forecast ]
                                                                   │
[ Step 6: Drivers ] ◄── [ Step 5: Model Comparison ] ◄── [ Step 4: Forecast Range ]
         │
         ▼
[ Step 7: What-If ] ──► [ Step 8: Weight Calc ] ──► [ Step 9: Data Integrity ] ──► [ Step 10: System Architecture ]
```

---

### Step 1: Open Market Intelligence Dashboard
- **Action:** Open browser to `http://localhost:5173/`.
- **Talking Point:** "Welcome to Gold Price Intelligence, a financial engineering platform designed to forecast domestic IBJA Gold 999 prices leading up to Diwali 2026. The dashboard provides real-time spot market signals, historical trend snapshots, and the primary model forecast."
- **Visual Focus:** Point out topbar navigation, API connectivity indicator (`API Connected`), and the hero title banner.

---

### Step 2: Explain Historical Gold Price Data & Dataset Characteristics
- **Action:** Scroll to the **Latest Observed IBJA Target** panel and **Historical vs. Forecast Transition Chart**.
- **Talking Point:** "Our primary target is official IBJA Gold 999 (24 Karat) in INR per 10 grams. The historical dataset contains 168 business-day observations from 02 Sep 2025 to 01 Sep 2026, representing 64.12% weekday calendar coverage."
- **Key Academic Caveat:** "Crucially, IBJA does not publish quotes on weekends or bank holidays. We strictly preserve this trading calendar without artificially fabricating unobserved dates."

---

### Step 3: Showcase Diwali 2026 Prediction
- **Action:** Highlight the **Diwali 2026 Forecast Spotlight Card** (08 November 2026).
- **Talking Point:** "For Diwali 2026 (08 Nov 2026), our primary model predicts an official reference estimate of **₹142,442.41 per 10 grams**."
- **Supporting Detail:** Show surrounding business-day estimates:
  - Previous Business Day (06 Nov 2026): ₹142,180.23 / 10g
  - Next Business Day (09 Nov 2026): ₹142,704.58 / 10g

---

### Step 4: Showcase Estimated Forecast Range
- **Action:** Point out the **RangeBar** component on the Forecast Desk (`http://localhost:5173/forecast`).
- **Talking Point:** "Financial forecasts require uncertainty modeling. We provide a 5th to 95th percentile confidence interval of **₹137,889.90 to ₹144,859.72 per 10g** (Span: ₹6,969.82)."

---

### Step 5: Demonstrate Model Lab & Model Comparison
- **Action:** Navigate to **Model Lab** (`http://localhost:5173/model`).
- **Talking Point:** "We evaluated four candidate algorithms on a chronological validation split: Linear Regression, XGBoost, Gradient Boosting, and Random Forest. Linear Regression achieved the lowest validation RMSE (₹2,738.80 vs. XGBoost ₹6,832.94) and best test performance (Test MAE: ₹2,122.61, MAPE: 1.4178%, $R^2: 0.8409$)."

---

### Step 6: Demonstrate Explainable AI — Prediction Drivers
- **Action:** Scroll to **Prediction Drivers** section on the Forecast Desk.
- **Talking Point:** "Black-box predictions are unacceptable in institutional finance. Using Linear Regression coefficient decomposition ($y = \beta_0 + \sum \beta_i x_i$), we explain exact feature contributions. Key positive drivers include `gold_inr_proxy` and `gold_ma_30`."

---

### Step 7: Demonstrate What-If Scenario Analysis
- **Action:** Scroll to **What-If Scenario Analysis** section.
- **Talking Point:** "Users can simulate macro market shocks. For example, a +5% rise in international spot gold increases the Diwali estimate by +₹2,200.64 to ₹144,643.05 (+1.54%), while a -2% USD/INR shift adjusts the estimate to ₹141,106.14 (-0.94%)."

---

### Step 8: Demonstrate Gold Weight Price Calculator (1g – 15g)
- **Action:** Interact with **Gold Weight Price Calculator** (`GoldWeightCalculator.jsx`).
  - Move slider from 5g to 8g, or click quick select `8g`.
  - Type `8.1` into the numeric input box.
- **Talking Point:** "Retail buyers rarely purchase gold in exact 10g blocks. Our weight calculator converts the 10g baseline estimate proportionally for weights from 1g to 15g ($\text{price} = \frac{\text{price}_{10g}}{10} \times \text{weight}$). For 8g, the predicted price is ₹1,13,953.93."

---

### Step 9: Highlight Data Transparency & Methodology Verification
- **Action:** Show **Data Integrity Checklist** badge panel.
- **Talking Point:** "We enforce rigorous data integrity: chronological train-only preprocessing fitting, zero lookahead target leakage, no random shuffling, and read-only frozen forecast protection."

---

### Step 10: Explain System Architecture & Technology Stack
- **Action:** Display [reports/system_architecture.png](file:///c:/Users/goran/OneDrive/Desktop/Gold_Price_Prediction_2026/reports/system_architecture.png).
- **Talking Point:** "The system uses a decoupled, high-performance architecture: Python FastAPI REST backend (11 routes, Pydantic validation, CORS middleware) serving static ML artifacts to a React/Vite single-page application built with Vanilla CSS tokens and Recharts."

---

## Recommended Q&A Quick Reference

| Question | Answer |
| :--- | :--- |
| **Why Linear Regression over XGBoost?** | On small time-series datasets (168 obs), tree-based models overfit or extrapolate poorly beyond historical range limits. Linear Regression generalized best on chronological validation. |
| **Why are weekends missing?** | IBJA does not publish official rates on weekends or bank holidays. Omitting unobserved dates preserves true market calendar characteristics without artificial interpolation leakage. |
| **Is the forecast updated dynamically?** | The baseline forecast is frozen for Diwali 2026 to ensure reproducible academic evaluation. What-If sensitivity scenarios allow dynamic macro shock testing. |
