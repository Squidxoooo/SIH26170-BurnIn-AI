from fastapi import APIRouter
router = APIRouter()
@router.post("/prediction/drift")
def drift_prediction(payload: dict):
    return {"success": False, "error":{"code":"MODEL_NOT_LOADED","message":"Train/load the drift model before inference."}}
