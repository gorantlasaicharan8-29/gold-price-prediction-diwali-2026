# Step 48.2 — Gold Weight Price Prediction Report

## Objective

Add a user-facing **Gold Weight Price Prediction** feature to the Gold Price Intelligence system, allowing users to calculate predicted Gold 999 prices for weights ranging from 1 gram to 15 grams for Diwali 2026 without modifying the underlying Machine Learning model or retraining any artifacts.

---

## Feature Description

The core ML model predicts the Diwali 2026 Gold 999 price in INR per 10 grams (₹142,442.41). The Gold Weight Price Prediction feature converts this 10g baseline prediction into equivalent predicted prices and estimated confidence bounds for any weight selected between 1.0g and 15.0g.

---

## Calculation Method

Proportional conversion based on exact 10-gram reference estimate:

$$\text{price\_per\_gram} = \frac{\text{price\_per\_10g}}{10.0}$$
$$\text{predicted\_price} = \text{round}(\text{price\_per\_gram} \times \text{requested\_weight}, 2)$$
$$\text{lower\_estimate} = \text{round}\left(\frac{\text{lower\_estimate}_{10g}}{10.0} \times \text{requested\_weight}, 2\right)$$
$$\text{upper\_estimate} = \text{round}\left(\frac{\text{upper\_estimate}_{10g}}{10.0} \times \text{requested\_weight}, 2\right)$$

Display values are rounded to 2 decimal places for monetary representation in INR.

---

## Supported Weight Range

- **Minimum:** 1.0 gram
- **Maximum:** 15.0 grams
- **Integer Weights Supported:** 1g, 2g, 3g, 4g, 5g, 6g, 7g, 8g, 9g, 10g, 11g, 12g, 13g, 14g, 15g
- **Decimal Weights Supported:** Yes (e.g., 1.5g, 2.5g, 5.5g, 10.25g)
- **Forbidden Inputs:** $0g$, negative values, weights $>15g$, non-numeric values.

---

## Backend API

- **Endpoint:** `GET /api/weight-prediction`
- **Query Parameter:** `weight` (float, required)
- **Tag:** `Forecast` in OpenAPI specification
- **Response Format:**
```json
{
  "weight_grams": 5.0,
  "price_per_10g": 142442.41,
  "price_per_gram": 14244.241,
  "predicted_price": 71221.20,
  "lower_estimate": 68944.95,
  "upper_estimate": 72429.86,
  "currency": "INR",
  "unit": "Gold 999",
  "reference_date": "2026-11-08",
  "model": "Linear Regression"
}
```

---

## API Validation

- `weight` parameter validated to ensure $1.0 \le \text{weight} \le 15.0$.
- Out-of-bounds inputs (e.g. `weight=0`, `weight=-2`, `weight=16`) return `HTTP 400 Bad Request`.
- Non-numeric inputs (e.g. `weight=abc`) return `HTTP 422 Unprocessable Entity`.
- No internal stack traces are exposed.

---

## Frontend UI

- Built `GoldWeightCalculator.jsx` component mounted inside the Forecast Desk (`/forecast`).
- Styled in accordance with existing clean fintech analytics aesthetic.
- Interactive range slider ($1g \to 15g$), live numeric input box, and quick-selection buttons ($1g, 2g, 5g, 8g, 10g, 12g, 15g$).
- Dynamic display of predicted price, per-gram rate, baseline 10g price, reference date, model name, and estimated range bar.

---

## API Integration

- Frontend calls `/api/weight-prediction?weight=N` dynamically via `getWeightPrediction()` in `src/services/api.js`.
- Zero hardcoded production prediction values in frontend JavaScript.
- Backend serves as the single source of truth.

---

## Accessibility

- Explicit `<label>` elements connected via `htmlFor` to slider and numeric input.
- ARIA attributes (`aria-label`, `aria-valuemin`, `aria-valuemax`, `aria-valuenow`).
- Full keyboard navigation for slider and quick-select buttons.

---

## Responsive Design

- Scalable layout built with CSS flexbox/grid.
- Tested across desktop, tablet, and mobile views with zero horizontal scroll overflow.

---

## Testing

- **Pytest Suite:** Executed `.\.venv\Scripts\python.exe -m pytest -q`.
- **Result:** **34 / 34 tests passed** (27 existing + 7 new weight prediction tests).
- Verified valid weights (1g, 5g, 10g, 15g, 2.5g) and error responses for out-of-bounds inputs.

---

## Frontend Build

- Executed `npm run build` inside `frontend/`.
- **Result:** Clean production compilation in 709ms without syntax or import errors.

---

## Calculation Verification

- **1g prediction:** ₹14,244.24
- **5g prediction:** ₹71,221.20 (lower: ₹68,944.95, upper: ₹72,429.86)
- **10g prediction:** ₹142,442.41 (matches frozen baseline exactly)
- **15g prediction:** ₹213,663.61
- **Consistency:** $P_{1g} \times 10 \approx P_{10g}$, $P_{5g} \times 2 = P_{10g}$, $P_{15g} = P_{1g} \times 15$.

---

## ML Integrity

- **Selected Model:** Linear Regression (UNTOUCHED)
- **Test Metrics:** MAE = ₹2,122.61, RMSE = ₹2,576.56, MAPE = 1.41778%, R² = 0.840884 (UNTOUCHED)
- **Retraining:** NONE performed.

---

## Frozen Forecast Integrity

- **Target Date:** Diwali (2026-11-08)
- **Frozen Reference Estimate (10g):** **₹142,442.41**
- **Forecast Range (10g):** ₹137,889.90 — ₹144,859.72
- **Forecast Files:** UNTOUCHED.

---

## Issues Found

None.

---

## Issues Fixed

N/A.

---

## Final Status

- **Feature Implementation:** COMPLETED
- **Backend Endpoint & Validation:** VERIFIED PASS
- **Frontend UI & API Integration:** VERIFIED PASS
- **Automated Tests:** 34 / 34 PASSED
- **Production Build:** PASSED
