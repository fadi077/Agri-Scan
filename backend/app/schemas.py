from pydantic import BaseModel, Field


class TopPrediction(BaseModel):
    disease: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    class_id: int = Field(..., ge=0)


class PredictionResponse(BaseModel):
    disease: str = Field(..., description="Predicted disease label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    class_id: int = Field(..., ge=-1, description="Predicted class index")
    uncertain: bool = Field(False, description="Whether prediction is below confidence threshold")
    top_predictions: list[TopPrediction] = Field(default_factory=list)
    rejected: bool = Field(False, description="Whether scan was rejected by quality checks")
    rejection_reason: str | None = None
    selected_crop: str = "any"


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "agri-scan-api"


class ModelInfoResponse(BaseModel):
    model_loaded: bool
    model_path: str
    class_count: int
    confidence_threshold: float
    uncertain_label: str
    supported_crops: list[str] = Field(default_factory=list)
