# Step 42 — Explainable AI Report

## Model
- **Selected Model**: Linear Regression
- **Model Storage Path**: `models/linear_regression.joblib`
- **Preprocessor Storage Path**: `data/processed/model_data/preprocessor.joblib`
- **Feature Count**: 46 features

## Forecast Being Explained
- **Target Date**: 2026-11-08 (Diwali 2026 Reference Estimate)
- **Frozen Diwali Forecast**: ₹142,442.41 per 10g
- **Calculated Forecast**: ₹142,442.41 per 10g
- **Reconstruction Residual**: 0.0000000000

## Prediction Reconstruction
- **Formula**: `prediction = intercept + sum(coefficient × transformed_feature_value)`
- **Intercept**: -139,595.86
- **Sum of Upward (Positive) Contributions**: +₹492,606.55
- **Sum of Downward (Negative) Contributions**: -₹210,568.29
- **Reconstructed Total**: ₹142,442.41
- **Validation Status**: **PASS**

## Intercept
The Linear Regression intercept baseline is **-139,595.86**. This reflects the baseline offset of the fitted linear surface before accounting for weighted feature contributions.

## Positive Drivers
The model identifies 27 positive drivers contributing upward pressure (+₹492,606.55 aggregate). Top positive contributors:
1. **USD/INR Day High Exchange Rate** (`usdinr_high`): +₹109,408.82 (Coef: 1222.2742, Transformed: 89.5125)
2. **USD/INR Closing Exchange Rate** (`usdinr_close`): +₹95,437.91 (Coef: 970.8046, Transformed: 98.3081)
3. **International Gold Day High (USD/oz)** (`gold_usd_high`): +₹94,830.95 (Coef: 22.4942, Transformed: 4215.7998)
4. **USD/INR Open Exchange Rate** (`usdinr_open`): +₹78,720.08 (Coef: 882.9289, Transformed: 89.1579)
5. **International Gold Day Low (USD/oz)** (`gold_usd_low`): +₹32,935.98 (Coef: 7.9103, Transformed: 4163.7002)

## Negative Drivers
The model identifies 19 negative drivers contributing downward pressure (-₹210,568.29 aggregate). Top negative contributors:
1. **USD/INR Day Low Exchange Rate** (`usdinr_low`): -₹94,600.18 (Coef: -1063.0290, Transformed: 88.9911)
2. **International Gold Close (USD/oz)** (`gold_usd_close`): -₹59,069.82 (Coef: -13.7914, Transformed: 4283.0946)
3. **3-Day Moving Average Gold Price** (`gold_ma_3`): -₹17,814.58 (Coef: -0.1255, Transformed: 141994.4280)
4. **7-Day Moving Average Gold Price** (`gold_ma_7`): -₹15,706.98 (Coef: -0.1108, Transformed: 141767.7633)
5. **14-Day Lagged Gold Price (t-14)** (`gold_lag_14`): -₹9,529.14 (Coef: -0.0677, Transformed: 140733.3260)

## Top Contributors
Summary of top 5 positive and negative drivers sorted by absolute mathematical contribution:

| Rank | Feature | Display Name | Direction | Contribution (INR) | Coefficient | Transformed Value |
|---|---|---|---|---|---|---|
| 1 | `usdinr_high` | USD/INR Day High Exchange Rate | POSITIVE | +109,408.82 | 1222.2742 | 89.5125 |
| 2 | `usdinr_close` | USD/INR Closing Exchange Rate | POSITIVE | +95,437.91 | 970.8046 | 98.3081 |
| 3 | `gold_usd_high` | International Gold Day High (USD/oz) | POSITIVE | +94,830.95 | 22.4942 | 4215.7998 |
| 4 | `usdinr_low` | USD/INR Day Low Exchange Rate | NEGATIVE | -94,600.18 | -1063.0290 | 88.9911 |
| 5 | `usdinr_open` | USD/INR Open Exchange Rate | POSITIVE | +78,720.08 | 882.9289 | 89.1579 |
| 6 | `gold_usd_close` | International Gold Close (USD/oz) | NEGATIVE | -59,069.82 | -13.7914 | 4283.0946 |
| 7 | `gold_usd_low` | International Gold Day Low (USD/oz) | POSITIVE | +32,935.98 | 7.9103 | 4163.7002 |
| 8 | `gold_inr_proxy` | Implied INR Gold Proxy (USD Gold × USD/INR) | POSITIVE | +27,871.00 | 0.0662 | 421062.6668 |
| 9 | `gold_lag_3` | 3-Day Lagged Gold Price (t-3) | POSITIVE | +18,335.08 | 0.1291 | 141981.0681 |
| 10 | `gold_ma_3` | 3-Day Moving Average Gold Price | NEGATIVE | -17,814.58 | -0.1255 | 141994.4280 |

## Methodology
1. **Prediction Space Mapping**: Linear Regression predictions are exact linear inner products $y = w^T X + b$.
2. **Preprocessing Handling**: Features are transformed using the exact fit preprocessor `ColumnTransformer` (median imputation for unobserved futures). Contributions are computed strictly on $X_{\text{transformed}}$.
3. **Diwali Midpoint Representation**: As Diwali 2026 (2026-11-08) falls on a Sunday, the forecast uses the midpoint reference estimate of the surrounding business days. By linearity, the feature contribution vector for the Diwali reference estimate is the exact midpoint vector of contributions.

## Limitations
- **Mathematical Contribution vs Real-World Causality**: The feature contributions explain *how the model computes its numerical output*. They **do not prove real-world causal relationships** in the gold market.
- **Correlated Predictors**: High collinearity among market indicators (such as USD/INR high, open, close) means individual coefficients absorb shared variance.

## Validation
- **Reconstruction Check**: `PASS` (Residual = 0.000000)
- **Model Binary Modified**: `NO`
- **Forecast Modified**: `NO`
