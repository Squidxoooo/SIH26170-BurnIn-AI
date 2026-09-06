from fastapi import APIRouter
from app.schemas.common import APIResponse
from app.services.analysis_service import AnalysisService
router = APIRouter()
service = AnalysisService()
@router.get("/health", response_model=APIResponse)
def health():
    return APIResponse(data={"status":"healthy","anomaly_model_loaded":service.anomaly is not None,"drift_model_loaded":service.drift is not None,"database_connected":True})
