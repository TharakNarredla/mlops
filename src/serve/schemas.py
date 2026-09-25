from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

N_FEATURES = 13

# Strict: only real numbers are accepted (no "1.5" strings); NaN/Inf are rejected.
Feature = Annotated[float, Field(allow_inf_nan=False)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(
        strict=True,
        json_schema_extra={
            "example": {
                "features": [
                    0.00632, 18, 2.31, 0, 0.538, 6.575, 65.2,
                    4.09, 1, 296, 15.3, 396.9, 4.98,
                ]
            }
        },
    )

    features: list[Feature] = Field(
        min_length=N_FEATURES,
        max_length=N_FEATURES,
        description=f"Exactly {N_FEATURES} numeric features, in training-column order.",
    )


class PredictResponse(BaseModel):
    prediction: float
    model_version: str


class ErrorResponse(BaseModel):
    error: str
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"


class ReadyResponse(BaseModel):
    status: str


class ReloadResponse(BaseModel):
    status: str
    model_version: str


class MetricsResponse(BaseModel):
    total_requests: int
    errors_400: int
    errors_500: int
    latency_avg_sec: float
    latency_min_sec: float
    latency_max_sec: float
