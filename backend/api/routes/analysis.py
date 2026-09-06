from fastapi import APIRouter
from backend.schemas.analysis import ComponentInput
from backend.schemas.common import APIResponse
from backend.services.analysis_service import AnalysisService
router = APIRouter()
service = AnalysisService()
@router.post("/analyze/component", response_model=APIResponse)
def analyze_component(req: ComponentInput):
    return APIResponse(data=service.analyze(req.component_id, req.lot_id, req.values, req.specification_limit))
