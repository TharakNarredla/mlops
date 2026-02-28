# Inference API — Contract

This document defines the **API contract** for the production-style inference service. The service serves the trained ML model (Boston Housing–style regression); it does **not** train. Training produces artifacts under `models/` and logs under `experiments/runs.json`; the inference service **reads** those (loads model by version, optionally uses `runs.json` to resolve "latest" or run_id → path).

---

## Base

- **Service:** Local inference API (e.g. HTTP).
- **Purpose:** Accept a feature vector, return a single prediction (MEDV).

---

## Endpoint: `POST /predict`

### Request

- **Method:** `POST`
- **Content-Type:** `application/json`
- **Body:** One JSON object with one key: **`features`** — an array of **13 numbers** in this order (same as training):

  1. CRIM  
  2. ZN  
  3. INDUS  
  4. CHAS  
  5. NOX  
  6. RM  
  7. AGE  
  8. DIS  
  9. RAD  
  10. TAX  
  11. PTRATIO  
  12. B  
  13. LSTAT  

**Example:**

```json
{
  "features": [0.00632, 18, 2.31, 0, 0.538, 6.575, 65.2, 4.09, 1, 296, 15.3, 396.9, 4.98]
}
```

- **Validation (server will enforce):** `features` must be present, must be an array of exactly 13 numbers, no null/NaN/Inf. Wrong shape or invalid values → **400**.

### Success response

- **Status:** `200 OK`
- **Content-Type:** `application/json`
- **Body:**

```json
{
  "prediction": 24.5,
  "model_version": "20260206_175154"
}
```

- **`prediction`:** Single number (MEDV).
- **`model_version`:** Identifier of the loaded model (e.g. run_id or path); used for observability and rollback.

### Error responses

**400 Bad Request — Invalid input**

- Missing `features`, wrong type, wrong length, or non-numeric/invalid values.

```json
{
  "error": "invalid_input",
  "message": "features must be an array of 13 numbers"
}
```

**500 Internal Server Error — Prediction failed**

- Model not loaded, or predict failed (e.g. internal exception).

```json
{
  "error": "prediction_failed",
  "message": "model not loaded"
}
```

---

## How this fits with the rest of the project

- **Training pipeline** (`src/train.py`, `src/retrain.py`) produces artifacts in `models/` (e.g. `model_YYYYMMDD_HHMMSS.pkl`) and logs runs in `experiments/runs.json`.
- **Inference service** only **reads**: it loads one artifact from `models/` by version (e.g. "latest" from `runs.json` or a configurable run_id/path), uses the same scaler and model for every request, and does not write to `models/` or `experiments/`.
- **Separation:** Training = batch/offline; inference = online request/response. They share artifacts and run metadata but are separate processes.
