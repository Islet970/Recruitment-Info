from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.ml.anomaly_detector import detect_anomalies
from app.ml.association_rules import generate_association_rules
from app.ml.data import feature_options
from app.ml.feature_importance import get_feature_importance
from app.ml.salary_predictor import predict_salary, salary_metrics
from app.models.user import User

router = APIRouter()


class SalaryPredictRequest(BaseModel):
    features: dict[str, Any]


class AssociationRulesRequest(BaseModel):
    min_support: float = Field(default=0.02, ge=0.001, le=1)
    min_confidence: float = Field(default=0.4, ge=0.001, le=1)
    limit: int = Field(default=50, ge=1, le=200)


class AnomalyRequest(BaseModel):
    method: Literal["isolation_forest", "lof", "ocsvm", "zscore", "iqr"] = "isolation_forest"
    contamination: float = Field(default=0.05, ge=0.01, le=0.3)
    limit: int = Field(default=50, ge=1, le=200)


@router.get("/salary/features")
def get_salary_features(_: User = Depends(get_current_user)):
    return feature_options()


@router.post("/salary/predict")
def salary_predict(request: SalaryPredictRequest, _: User = Depends(get_current_user)):
    try:
        return predict_salary(request.features)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/salary/metrics")
def get_salary_metrics(_: User = Depends(get_current_user)):
    try:
        return salary_metrics()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/feature-importance")
def feature_importance(limit: int = 30, _: User = Depends(get_current_user)):
    try:
        return get_feature_importance(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/association-rules")
def association_rules(request: AssociationRulesRequest, _: User = Depends(get_current_user)):
    return generate_association_rules(request.min_support, request.min_confidence, request.limit)


@router.post("/anomalies")
def anomalies(request: AnomalyRequest, _: User = Depends(get_current_user)):
    return detect_anomalies(request.method, request.contamination, request.limit)
